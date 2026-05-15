#!/bin/bash
# Run evaluation for both tasks
set -e

echo "=== Task A Evaluation ==="
python -m task_a.eval.evaluate \
  --predictions data/processed/task_a_predictions.json \
  --references  data/processed/task_a_references.json

echo ""
echo "=== Task B Evaluation ==="
python -m task_b.eval.evaluate \
  --predictions data/processed/task_b_predictions.json \
  --ground_truth data/processed/task_b_ground_truth.json \
  --k 10
