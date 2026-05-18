from __future__ import annotations

import pandas as pd

from evaluate import evaluate_predictions, format_metrics


def test_evaluate_predictions_returns_expected_metrics() -> None:
    frame = pd.DataFrame(
        {
            "rule_anomaly": [0, 1, 1, 0],
            "ml_anomaly": [0, 1, 0, 0],
        }
    )

    metrics = evaluate_predictions(frame)

    assert metrics["accuracy"] == 0.75
    assert metrics["precision"] == 1.0
    assert metrics["recall"] == 0.5
    assert metrics["f1_score"] == 2 / 3
    assert metrics["confusion_matrix"] == [[2, 0], [1, 1]]


def test_format_metrics_renders_human_readable_text() -> None:
    message = format_metrics(
        {
            "accuracy": 0.75,
            "precision": 1.0,
            "recall": 0.5,
            "f1_score": 2 / 3,
            "confusion_matrix": [[2, 0], [1, 1]],
        }
    )

    assert "Accuracy: 0.7500" in message
    assert "Precision: 1.0000" in message
    assert "Recall: 0.5000" in message
    assert "F1 Score: 0.6667" in message
    assert "Confusion Matrix: [[2, 0], [1, 1]]" in message
