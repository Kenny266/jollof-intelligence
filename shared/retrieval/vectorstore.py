"""
FAISS vector store wrapper.
Indexes item embeddings for fast similarity retrieval.
"""
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer
from typing import List, Dict, Any

_model = SentenceTransformer("all-MiniLM-L6-v2")
_index = None
_items: List[Dict] = []


def build_index(items: List[Dict[str, Any]]) -> None:
    """Build FAISS index from a list of item dicts (must have 'text' key)."""
    global _index, _items
    _items = items
    texts = [f"{i.get('name','')} {i.get('category','')} {i.get('description','')}" for i in items]
    embeddings = _model.encode(texts, show_progress_bar=True).astype("float32")
    faiss.normalize_L2(embeddings)
    _index = faiss.IndexFlatIP(embeddings.shape[1])
    _index.add(embeddings)


def search(query: str, top_k: int = 10) -> List[Dict[str, Any]]:
    """Return top_k items most similar to query string."""
    if _index is None:
        raise RuntimeError("Index not built. Call build_index() first.")
    q_emb = _model.encode([query]).astype("float32")
    faiss.normalize_L2(q_emb)
    scores, indices = _index.search(q_emb, top_k)
    results = []
    for score, idx in zip(scores[0], indices[0]):
        if idx < len(_items):
            item = dict(_items[idx])
            item["similarity_score"] = float(score)
            results.append(item)
    return results
