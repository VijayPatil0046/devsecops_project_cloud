from __future__ import annotations

import pandas as pd

from model import FEATURE_COLUMNS, build_pipeline, predict_with_artifacts, train_and_predict


def _training_frame() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "vcpu_usage": [5, 8, 12, 15, 18, 22, 30, 35, 40, 45, 55, 60],
            "ram_usage": [10, 14, 16, 18, 22, 24, 28, 32, 36, 40, 44, 48],
            "cost": [12, 16, 20, 24, 28, 32, 36, 40, 44, 48, 52, 56],
            "rule_anomaly": [0, 1] * 6,
            "server_id": [f"vm-{index + 1}" for index in range(12)],
            "region": ["India"] * 12,
            "target_region": ["Europe"] * 12,
            "carbon_intensity": [700.0] * 12,
            "carbon_saving": [100.0] * 12,
            "vm_status": ["Healthy"] * 12,
            "final_action": ["Stay in current region"] * 12,
            "reason": ["Healthy"] * 12,
        }
    )


def test_build_pipeline_contains_expected_feature_columns() -> None:
    pipeline = build_pipeline()

    assert list(FEATURE_COLUMNS) == ["vcpu_usage", "ram_usage", "cost"]
    assert pipeline.named_steps["scaler"] is not None
    assert pipeline.named_steps["isolation_forest"] is not None


def test_train_and_predict_produces_scored_test_frame() -> None:
    frame = _training_frame()

    artifacts = train_and_predict(frame, test_size=0.25, random_state=42, contamination=0.1)

    assert artifacts.train_size == 9
    assert artifacts.test_size == 3
    assert len(artifacts.test_frame) == 3
    assert "ml_anomaly" in artifacts.test_frame.columns
    assert set(artifacts.test_frame["ml_anomaly"].unique()).issubset({0, 1})


def test_predict_with_artifacts_scores_inference_frame() -> None:
    frame = _training_frame()
    artifacts = train_and_predict(frame, test_size=0.25, random_state=42, contamination=0.1)

    scored = predict_with_artifacts(
        frame.loc[artifacts.test_frame.index, FEATURE_COLUMNS],
        model=artifacts.pipeline.named_steps["isolation_forest"],
        scaler=artifacts.pipeline.named_steps["scaler"],
    )

    assert len(scored) == len(artifacts.test_frame)
    assert "ml_anomaly" in scored.columns
