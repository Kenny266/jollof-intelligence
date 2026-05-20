"""
Generates a structured JSON + Markdown evaluation report from metric results.
"""
import json
from datetime import datetime
from pathlib import Path


def generate_report(
    task: str,
    metrics: dict,
    output_dir: str = "eval/reports",
) -> tuple[Path, Path]:
    """
    Write evaluation results as both JSON and Markdown.

    Args:
        task: 'a' or 'b'
        metrics: Dict of metric name -> float value
        output_dir: Directory to write reports into

    Returns:
        Tuple of (json_path, markdown_path)
    """
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    task_label = f"task_{task.upper()}"
    json_path = out / f"{task_label}_eval_{timestamp}.json"
    md_path = out / f"{task_label}_eval_{timestamp}.md"

    report = {
        "task": task.upper(),
        "timestamp": timestamp,
        "metrics": metrics,
    }

    json_path.write_text(json.dumps(report, indent=2), encoding="utf-8")

    lines = [
        f"# Evaluation Report — Task {task.upper()}",
        f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "",
        "## Metrics",
        "",
        "| Metric | Score |",
        "|---|---|",
    ]
    for k, v in metrics.items():
        lines.append(f"| {k} | {v:.4f} |")
    lines.append("")

    md_path.write_text("\n".join(lines), encoding="utf-8")
    return json_path, md_path
