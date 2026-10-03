"""Compare AI-generated labels with a small, fictional human reference set."""

from __future__ import annotations

import csv
import json
from collections import Counter
from pathlib import Path
from typing import Iterable

ROOT = Path(__file__).resolve().parents[2]
LABELS_CSV = ROOT / "data" / "llm_evaluation" / "synthetic_labels.csv"
OUTPUT_JSON = ROOT / "data" / "processed" / "llm_evaluation_summary.json"
LABELS = ("trust", "price", "habit", "other")


def evaluate_labels(human: Iterable[str], model: Iterable[str]) -> dict:
    human, model = list(human), list(model)
    if len(human) != len(model) or not human:
        raise ValueError("human and model labels must have the same non-zero length")
    if any(label not in LABELS for label in human + model):
        raise ValueError(f"labels must be one of: {', '.join(LABELS)}")

    correct = sum(h == m for h, m in zip(human, model))
    n = len(human)
    human_counts, model_counts = Counter(human), Counter(model)
    observed = correct / n
    expected = sum(human_counts[label] * model_counts[label] for label in LABELS) / (n * n)
    kappa = (observed - expected) / (1 - expected) if expected < 1 else 1.0
    matrix = {
        actual: {predicted: 0 for predicted in LABELS}
        for actual in LABELS
    }
    for actual, predicted in zip(human, model):
        matrix[actual][predicted] += 1

    per_label = {}
    for label in LABELS:
        true_positive = matrix[label][label]
        predicted_positive = sum(matrix[actual][label] for actual in LABELS)
        actual_positive = sum(matrix[label].values())
        precision = true_positive / predicted_positive if predicted_positive else 0.0
        recall = true_positive / actual_positive if actual_positive else 0.0
        per_label[label] = {
            "precision": round(precision, 3),
            "recall": round(recall, 3),
        }

    return {
        "n": n,
        "agreement": round(observed, 3),
        "cohen_kappa": round(kappa, 3),
        "confusion_matrix_human_rows_model_columns": matrix,
        "per_label_precision_recall": per_label,
        "warning": "Tiny synthetic example; do not treat these scores as validation of a real model.",
    }


def evaluate_file(path: Path = LABELS_CSV, output_path: Path = OUTPUT_JSON) -> dict:
    with Path(path).open(newline="", encoding="utf-8") as stream:
        rows = list(csv.DictReader(stream))
    result = evaluate_labels(
        [row["human_label"] for row in rows],
        [row["model_label"] for row in rows],
    )
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    return result
