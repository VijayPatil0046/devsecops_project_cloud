from __future__ import annotations

import os
from io import StringIO
from datetime import datetime, timedelta, timezone

import joblib
from jose import JWTError, jwt

import pandas as pd
from fastapi import Depends, FastAPI, File, HTTPException, UploadFile, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from passlib.context import CryptContext
from pydantic import BaseModel
from prometheus_fastapi_instrumentator import Instrumentator

from feature_engineering import add_inference_features, apply_decision_engine
from model import predict_with_artifacts
from vault_bootstrap import bootstrap_secrets_from_vault


app = FastAPI(title="Green FinOps API", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

bootstrap_secrets_from_vault()

SECRET_KEY = os.getenv("JWT_SECRET") or os.getenv("SECRET_KEY")
if not SECRET_KEY:
    raise RuntimeError("SECRET_KEY environment variable is required.")

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

security = HTTPBearer(auto_error=False)
pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")

ADMIN_USERNAME = "admin"
ADMIN_PASSWORD_HASH = pwd_context.hash("admin123")

MODEL_PATH = "model.pkl"
SCALER_PATH = "scaler.pkl"

if not os.path.exists(MODEL_PATH) or not os.path.exists(SCALER_PATH):
    raise RuntimeError(
        f"Missing model artifacts. Expected {MODEL_PATH} and {SCALER_PATH} in the container."
    )

try:
    MODEL = joblib.load(MODEL_PATH)
    SCALER = joblib.load(SCALER_PATH)
except Exception as exc:  # pragma: no cover - fail fast during startup
    raise RuntimeError(f"Failed to load model artifacts at startup: {exc}") from exc

Instrumentator().instrument(app).expose(app, include_in_schema=False)


class LoginRequest(BaseModel):
    username: str
    password: str


def create_access_token(data: dict[str, str | int | bool]) -> str:
    token_data = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    token_data.update({"exp": expire})
    return jwt.encode(token_data, SECRET_KEY, algorithm=ALGORITHM)


def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict[str, str | int | bool]:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authentication token.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        if username != ADMIN_USERNAME:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication token.",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return payload
    except JWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired authentication token.",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc


@app.post("/login")
async def login(credentials: LoginRequest) -> dict[str, str]:
    if credentials.username != ADMIN_USERNAME or not pwd_context.verify(credentials.password, ADMIN_PASSWORD_HASH):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token({"sub": credentials.username})
    return {"access_token": access_token, "token_type": "bearer"}


@app.get("/healthz")
async def healthz() -> dict[str, str]:
    return {"status": "ok"}


def _load_request_csv(upload: UploadFile) -> pd.DataFrame:
    if not upload.filename or not upload.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="Please upload a CSV file.")

    try:
        payload = upload.file.read().decode("utf-8")
        frame = pd.read_csv(StringIO(payload))
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Failed to parse CSV: {exc}") from exc

    frame.columns = frame.columns.str.strip().str.lower()
    required_columns = {"vcpu_usage", "ram_usage"}
    missing_columns = sorted(required_columns - set(frame.columns))
    if missing_columns:
        raise HTTPException(
            status_code=400,
            detail=f"Missing required columns: {', '.join(missing_columns)}",
        )

    try:
        frame["vcpu_usage"] = pd.to_numeric(frame["vcpu_usage"], errors="raise")
        frame["ram_usage"] = pd.to_numeric(frame["ram_usage"], errors="raise")
    except Exception as exc:
        raise HTTPException(
            status_code=400,
            detail=f"vcpu_usage and ram_usage must be numeric: {exc}",
        ) from exc

    prepared = frame.copy()
    if "server_id" not in prepared.columns:
        prepared["server_id"] = [f"vm-{index + 1}" for index in range(len(prepared))]

    return prepared[["server_id", "vcpu_usage", "ram_usage"]].copy()


def _add_estimated_savings(frame: pd.DataFrame) -> pd.DataFrame:
    enriched = frame.copy()
    enriched["estimated_savings"] = 0.0
    move_mask = enriched["final_action"].str.startswith("Move from ", na=False)
    enriched.loc[move_mask, "estimated_savings"] = enriched.loc[move_mask, "cost"] * 0.3
    return enriched


@app.post("/predict")
async def predict(
    file: UploadFile = File(...),
    token_payload: dict[str, str | int | bool] = Depends(verify_token),
) -> list[dict[str, float | int | str]]:
    request_frame = _load_request_csv(file)

    featured = add_inference_features(request_frame)
    scored = predict_with_artifacts(featured, model=MODEL, scaler=SCALER)
    decided = apply_decision_engine(scored)
    response_frame = _add_estimated_savings(decided)

    output_columns = [
        "server_id",
        "vcpu_usage",
        "ram_usage",
        "region",
        "target_region",
        "cost",
        "carbon_intensity",
        "carbon_saving",
        "ml_anomaly",
        "vm_status",
        "final_action",
        "estimated_savings",
        "reason",
    ]
    return response_frame[output_columns].to_dict(orient="records")
