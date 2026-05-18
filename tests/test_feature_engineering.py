from __future__ import annotations

import pandas as pd

import feature_engineering as fe


def test_add_features_adds_expected_columns_without_network(monkeypatch) -> None:
    monkeypatch.setattr(fe, "get_carbon_intensity", lambda zone: {"IN": 700.0, "FR": 200.0, "US-CAL": 400.0, "CN": 650.0}[zone])

    frame = pd.DataFrame(
        {
            "server_id": ["vm-1", "vm-2", "vm-3", "vm-4"],
            "vcpu_usage": [2.0, 10.0, 85.0, 7.0],
            "ram_usage": [30.0, 12.0, 16.0, 18.0],
        }
    )

    enriched = fe.add_features(frame, random_state=7)

    assert {"cost", "region", "carbon_intensity", "target_region", "rule_anomaly"}.issubset(enriched.columns)
    assert len(enriched) == 4
    assert enriched["rule_anomaly"].isin([0, 1]).all()
    assert enriched["cost"].ge(0).all()


def test_apply_decision_engine_sets_action_and_status(monkeypatch) -> None:
    monkeypatch.setattr(fe, "get_carbon_intensity", lambda zone: {"IN": 700.0, "FR": 200.0, "US-CAL": 400.0, "CN": 650.0}[zone])

    frame = pd.DataFrame(
        {
            "server_id": ["vm-1", "vm-2"],
            "vcpu_usage": [92.0, 12.0],
            "ram_usage": [65.0, 22.0],
            "region": ["India", "US"],
            "carbon_intensity": [700.0, 400.0],
            "target_region": ["Europe", "US"],
            "target_carbon_intensity": [200.0, 400.0],
            "carbon_saving": [500.0, 0.0],
            "current_region_score": [700.0, 400.0],
            "target_region_score": [280.0, 400.0],
            "ml_anomaly": [1, 0],
        }
    )

    decided = fe.apply_decision_engine(frame)

    assert decided.loc[0, "final_action"].startswith("Move from India ->")
    assert decided.loc[0, "reason"] == "CPU spike anomaly"
    assert decided.loc[0, "vm_status"] == "Bad"
    assert decided.loc[1, "final_action"] == "Stay in current region"
