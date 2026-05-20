import asyncio
import logging

from fastapi import HTTPException

from shared.db.user_history import user_history_repo
from shared.retrieval.vectorstore import upsert_documents
from src.models.task_a import ReviewRequest, ReviewResponse
from task_a.agent import UserModelingAgent

logger = logging.getLogger(__name__)
_agent = UserModelingAgent()


async def handle_generate_review(req: ReviewRequest) -> ReviewResponse:
    """
    Controller for POST /api/v1/task-a/generate-review.

    1. Resolve item metadata (inline fields, optionally merged with catalogue).
    2. Fetch user history from DB — no history in request body.
    3. Delegate to UserModelingAgent.
    4. Write-back: persist the generated review to DB and ChromaDB asynchronously.
    """
    try:
        # Step 1: Resolve product dict — merge catalogue record if parent_asin supplied
        product_dict = req.product.model_dump()
        if req.product.parent_asin:
            catalogue_item = await user_history_repo.get_item(req.product.parent_asin)
            if catalogue_item:
                # Catalogue values fill gaps; request fields override
                for key, cat_val in catalogue_item.items():
                    if key == "parent_asin":
                        continue
                    req_key = "item_title" if key == "title" else key
                    if not product_dict.get(req_key) and cat_val:
                        product_dict[req_key] = cat_val

        # Step 2: Fetch history from DB
        history = await user_history_repo.get_history(req.user_id)
        logger.info(
            "Task A: user=%s history_len=%d cold_start=%s",
            req.user_id,
            len(history),
            len(history) == 0,
        )

        # Step 3: Run agent
        result = await _agent.run(
            user_id=req.user_id,
            history=history,
            product=product_dict,
        )

        # Step 4: Async write-back — fire-and-forget; never block the response
        asyncio.create_task(
            _write_back(req.user_id, product_dict, result)
        )

        return ReviewResponse(
            user_id=result["user_id"],
            rating=result["rating"],
            review=result["review"],
            persona_summary=result.get("persona_summary"),
            rag_metrics=result.get("rag_metrics"),
        )
    except Exception as exc:
        logger.error("Task A generation failed", extra={"user_id": req.user_id, "error": str(exc)})
        raise HTTPException(status_code=500, detail=f"Review generation failed: {exc}") from exc


async def _write_back(user_id: str, product: dict, result: dict) -> None:
    """
    Persist the generated review to both the relational DB and ChromaDB.
    Errors here are logged but never surfaced to the caller.
    """
    review_record = {
        "parent_asin": product.get("parent_asin"),
        "item_title": product.get("item_title", "Unknown"),
        "author": product.get("author"),
        "category": product.get("categories"),
        "rating": float(result["rating"]),
        "review_text": result["review"],
        "source": "generated",
    }
    try:
        await user_history_repo.save_review(user_id, review_record, source="generated")
        logger.info("Write-back: saved generated review for user=%s", user_id)
    except Exception as exc:
        logger.error("Write-back DB failed for user=%s: %s", user_id, exc)

    # Upsert into ChromaDB so the new review is immediately searchable
    try:
        paragraph = (
            f"[User {user_id}] rated '{product.get('item_title', 'Unknown')}' "
            f"{result['rating']}/5 stars. "
            f"Categories: {product.get('categories', 'Books')}. "
            f"Review: '{str(result['review'])[:500]}'"
        )
        doc_id = f"{user_id}_{product.get('parent_asin', 'gen')}_{result['rating']}_generated"
        upsert_documents(
            documents=[paragraph],
            metadatas=[{
                "user_id": user_id,
                "parent_asin": product.get("parent_asin") or "",
                "rating": float(result["rating"]),
                "item_title": product.get("item_title", ""),
                "categories": product.get("categories", ""),
                "source": "generated",
            }],
            ids=[doc_id],
        )
        logger.info("Write-back: upserted generated review into ChromaDB for user=%s", user_id)
    except Exception as exc:
        logger.error("Write-back ChromaDB failed for user=%s: %s", user_id, exc)
