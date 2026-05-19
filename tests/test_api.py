from __future__ import annotations

import os
import sys
from pathlib import Path

import pandas as pd
import pytest
from fastapi.testclient import TestClient

REPO_ROOT = Path(__file__).parent.parent

sys.path.insert(0, str(REPO_ROOT))

os.environ.setdefault("JWT_SECRET", "test-jwt-secret")
os.environ.setdefault("ELECTRICITY_MAPS_API_KEY", "test-electricity-key")
os.environ.setdefault("ENABLE_VAULT_BOOTSTRAP", "false")

from model import FEATURE_COLUMNS, build_pipeline, save_model_artifacts  # noqa: E402
import feature_engineering  # noqa: E402


def _offline_requests_get(*_args, **_kwargs):
    raise RuntimeError("offline")


def _write_test_artifacts() -> None:
    frame = pd.DataFrame(
        [
            {"vcpu_usage": 10.0, "ram_usage": 20.0, "cost": 14.0},
            {"vcpu_usage": 15.0, "ram_usage": 25.0, "cost": 17.0},
            {"vcpu_usage": 85.0, "ram_usage": 60.0, "cost": 74.0},
            {"vcpu_usage": 7.0, "ram_usage": 15.0, "cost": 10.0},
        ]
    )
    pipeline = build_pipeline(random_state=42, contamination=0.25)
    pipeline.fit(frame[FEATURE_COLUMNS])
    save_model_artifacts(
        pipeline,
        model_path=REPO_ROOT / "model.pkl",
        scaler_path=REPO_ROOT / "scaler.pkl",
    )


_write_test_artifacts()

import api  # noqa: E402


@pytest.fixture()
def client(monkeypatch: pytest.MonkeyPatch) -> TestClient:
    monkeypatch.setattr(feature_engineering.requests, "get", _offline_requests_get)
    return TestClient(api.app)


def test_login_endpoint_returns_access_token(client: TestClient) -> None:
    response = client.post(
        "/login",
        json={"username": "admin", "password": "admin123"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["token_type"] == "bearer"
    assert payload["access_token"]


def test_predict_endpoint_processes_sample_csv(client: TestClient) -> None:
    login_response = client.post(
        "/login",
        json={"username": "admin", "password": "admin123"},
    )
    token = login_response.json()["access_token"]

    response = client.post(
        "/predict",
        files={
            "file": (
                "sample_predict.csv",
                "server_id,vcpu_usage,ram_usage\nvm-001,12,24\nvm-002,88,58\n",
                "text/csv",
            )
        },
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert isinstance(payload, list)
    assert len(payload) == 2
    expected_fields = {"server_id", "final_action", "reason", "estimated_savings"}
    assert expected_fields.issubset(payload[0].keys())


def test_predict_rejects_missing_columns(client: TestClient) -> None:
    login_response = client.post(
        "/login",
        json={"username": "admin", "password": "admin123"},
    )
    token = login_response.json()["access_token"]

    response = client.post(
        "/predict",
        files={
            "file": (
                "missing_column.csv",
                "server_id,vcpu_usage\nvm-001,12\n",
                "text/csv",
            )
        },
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 400
    assert "Missing required columns" in response.json()["detail"]


def test_predict_rejects_missing_jwt(client: TestClient) -> None:
    response = client.post(
        "/predict",
        files={
            "file": (
                "sample_predict.csv",
                "server_id,vcpu_usage,ram_usage\nvm-001,12,24\n",
                "text/csv",
            )
        },
    )

    assert response.status_code == 401
    assert "authentication token" in response.json()["detail"].lower()
