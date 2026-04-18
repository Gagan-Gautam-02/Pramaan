"""
Pramaan — FastAPI Gateway

Routes:
  POST /predict          — JSON payload (base64 media)
  POST /detect           — multipart file upload
  GET  /health           — gateway + all model health
  POST /register         — create user account
  POST /token            — login, get JWT
  GET  /users/me         — current user info
  GET  /history          — analysis history (protected)
  GET  /models           — list active models from config
"""

from __future__ import annotations

import json
import logging
import os
import base64
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

import httpx
import joblib
import numpy as np
from fastapi import (
    Depends,
    FastAPI,
    File,
    Form,
    HTTPException,
    UploadFile,
    status,
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel
from sqlalchemy.orm import Session

from database import (
    AnalysisHistory,
    SessionLocal,
    User,
    create_tables,
)

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
def _resolve_config() -> Path:
    """Resolve config file: local override → Docker mount → repo default."""
    repo_root = Path(__file__).parent.parent
    candidates = [
        repo_root / "config" / "pramaan_config.local.json",  # local dev override
        Path("/config/pramaan_config.json"),                   # Docker mount
        repo_root / "config" / "pramaan_config.json",         # repo default
    ]
    for p in candidates:
        if p.exists():
            return p
    raise FileNotFoundError("Could not find pramaan_config.json in any expected location")

CONFIG_PATH = _resolve_config()
with open(CONFIG_PATH) as f:
    CONFIG = json.load(f)

GATEWAY_CFG = CONFIG["gateway"]
SECRET_KEY: str = os.environ.get("SECRET_KEY", GATEWAY_CFG["secret_key"])
ALGORITHM: str = GATEWAY_CFG["algorithm"]
TOKEN_EXPIRE_MINUTES: int = GATEWAY_CFG["access_token_expire_minutes"]
REQUEST_TIMEOUT: int = GATEWAY_CFG.get("request_timeout_seconds", 30)

ACTIVE_MODELS = [m for m in CONFIG["models"] if m["enabled"]]

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("pramaan.gateway")

# ---------------------------------------------------------------------------
# Auth utilities
# ---------------------------------------------------------------------------
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/token")


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def create_access_token(data: dict) -> str:
    payload = data.copy()
    payload["exp"] = datetime.utcnow() + timedelta(minutes=TOKEN_EXPIRE_MINUTES)
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str) -> dict:
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")


# ---------------------------------------------------------------------------
# DB dependency
# ---------------------------------------------------------------------------

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_current_user(
    token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)
) -> User:
    payload = decode_token(token)
    username = payload.get("sub")
    if not username:
        raise HTTPException(status_code=401, detail="Invalid token payload")
    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user


# ---------------------------------------------------------------------------
# Pydantic schemas
# ---------------------------------------------------------------------------

class PredictRequest(BaseModel):
    media_type: str  # "image" | "video" | "audio"
    image_data: Optional[str] = None   # base64
    video_data: Optional[str] = None   # base64
    audio_data: Optional[str] = None   # base64
    ensemble_method: str = "voting"    # voting | average | stacking
    threshold: float = 0.5


class RegisterRequest(BaseModel):
    username: str
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class ModelResult(BaseModel):
    probability: float
    label: str
    confidence: float


class PredictResponse(BaseModel):
    verdict: str
    confidence_in_verdict: float
    ensemble_score_is_fake: float
    ensemble_method_used: str
    model_results: Dict[str, Dict[str, Any]]
    media_type: str
    timestamp: str


# ---------------------------------------------------------------------------
# Ensemble logic
# ---------------------------------------------------------------------------

def _voting_ensemble(scores: List[float], threshold: float = 0.5) -> float:
    votes_fake = sum(1 for s in scores if s >= threshold)
    return votes_fake / len(scores)


def _average_ensemble(scores: List[float]) -> float:
    return float(np.mean(scores))


def _stacking_ensemble(scores: List[float], media_type: str) -> float:
    artifact_dir = Path(__file__).parent / "meta_model_artifacts"
    artifact_file = artifact_dir / f"meta_learner_{media_type}.joblib"
    if not artifact_file.exists():
        logger.warning("Stacking artifact not found, falling back to average.")
        return _average_ensemble(scores)
    clf = joblib.load(artifact_file)
    X = np.array(scores).reshape(1, -1)
    try:
        prob = float(clf.predict_proba(X)[0][1])
    except Exception:
        prob = _average_ensemble(scores)
    return prob


def fuse_results(
    model_results: Dict[str, Dict[str, Any]],
    method: str,
    media_type: str,
    threshold: float = 0.5,
) -> tuple[str, float, float]:
    """Returns (verdict, confidence, ensemble_score_is_fake)."""
    scores = [r["probability"] for r in model_results.values() if "probability" in r]
    if not scores:
        return "unknown", 0.0, 0.0

    if method == "voting":
        raw = _voting_ensemble(scores, threshold)
    elif method == "stacking":
        raw = _stacking_ensemble(scores, media_type)
    else:
        raw = _average_ensemble(scores)

    verdict = "fake" if raw >= threshold else "real"
    confidence = abs(raw - threshold) / max(threshold, 1 - threshold)
    confidence = min(confidence, 1.0)
    return verdict, round(confidence, 4), round(raw, 4)


# ---------------------------------------------------------------------------
# Model dispatch
# ---------------------------------------------------------------------------

async def call_model(
    client: httpx.AsyncClient,
    model: dict,
    input_data: str,
    threshold: float,
) -> Optional[Dict[str, Any]]:
    url = f"{model['url']}/predict"
    try:
        resp = await client.post(
            url,
            json={"input_data": input_data, "threshold": threshold},
            timeout=REQUEST_TIMEOUT,
        )
        resp.raise_for_status()
        return resp.json()
    except Exception as exc:
        logger.warning(f"Model {model['name']} failed: {exc}")
        return None


# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------
app = FastAPI(
    title="Pramaan Gateway",
    description="Enterprise-grade deepfake detection API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup():
    create_tables()
    logger.info("Pramaan Gateway started.")


# ---------------------------------------------------------------------------
# Auth routes
# ---------------------------------------------------------------------------

@app.post("/register", tags=["auth"])
def register(req: RegisterRequest, db: Session = Depends(get_db)):
    if db.query(User).filter(User.username == req.username).first():
        raise HTTPException(status_code=400, detail="Username already taken")
    user = User(username=req.username, hashed_password=hash_password(req.password))
    db.add(user)
    db.commit()
    return {"message": "User created successfully"}


@app.post("/token", response_model=Token, tags=["auth"])
def login(
    form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.username == form.username).first()
    if not user or not verify_password(form.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Incorrect credentials")
    token = create_access_token({"sub": user.username})
    return Token(access_token=token)


@app.get("/users/me", tags=["auth"])
def me(current_user: User = Depends(get_current_user)):
    return {"username": current_user.username, "id": current_user.id}


# ---------------------------------------------------------------------------
# Core prediction routes
# ---------------------------------------------------------------------------

async def _run_prediction(
    media_type: str,
    input_data: str,
    ensemble_method: str,
    threshold: float,
    db: Session,
    user_id: Optional[int] = None,
) -> PredictResponse:
    relevant_models = [
        m for m in ACTIVE_MODELS if m["media_type"] == media_type
    ]
    if not relevant_models:
        raise HTTPException(
            status_code=400,
            detail=f"No active models for media_type='{media_type}'",
        )

    async with httpx.AsyncClient() as client:
        import asyncio
        tasks = [
            call_model(client, m, input_data, threshold) for m in relevant_models
        ]
        raw_results = await asyncio.gather(*tasks)

    model_results: Dict[str, Dict] = {}
    for model, result in zip(relevant_models, raw_results):
        if result:
            model_results[model["name"]] = {
                "probability": result.get("probability", 0.0),
                "label": result.get("label", "unknown"),
                "confidence": result.get("confidence", 0.0),
            }

    verdict, confidence, ensemble_score = fuse_results(
        model_results, ensemble_method, media_type, threshold
    )

    ts = datetime.utcnow().isoformat()

    # Persist to history
    if db and user_id:
        entry = AnalysisHistory(
            user_id=user_id,
            media_type=media_type,
            ensemble_method=ensemble_method,
            verdict=verdict,
            confidence=confidence,
            ensemble_score=ensemble_score,
            model_results=json.dumps(model_results),
            timestamp=ts,
        )
        db.add(entry)
        db.commit()

    return PredictResponse(
        verdict=verdict,
        confidence_in_verdict=confidence,
        ensemble_score_is_fake=ensemble_score,
        ensemble_method_used=ensemble_method,
        model_results=model_results,
        media_type=media_type,
        timestamp=ts,
    )


@app.post("/predict", response_model=PredictResponse, tags=["detection"])
async def predict_json(
    req: PredictRequest,
    db: Session = Depends(get_db),
):
    """Run deepfake detection on a base64-encoded media payload."""
    media_type = req.media_type
    input_data = req.image_data or req.video_data or req.audio_data
    if not input_data:
        raise HTTPException(status_code=422, detail="No media data provided")

    return await _run_prediction(
        media_type, input_data, req.ensemble_method, req.threshold, db
    )


@app.post("/detect", response_model=PredictResponse, tags=["detection"])
async def detect_upload(
    file: UploadFile = File(...),
    ensemble_method: str = Form("voting"),
    threshold: float = Form(0.5),
    db: Session = Depends(get_db),
):
    """Run deepfake detection on an uploaded file (multipart)."""
    content_type = file.content_type or ""
    if content_type.startswith("image/"):
        media_type = "image"
    elif content_type.startswith("video/"):
        media_type = "video"
    elif content_type.startswith("audio/"):
        media_type = "audio"
    else:
        # Guess from extension
        ext = Path(file.filename or "").suffix.lower()
        media_type = (
            "video" if ext in {".mp4", ".avi", ".mov", ".mkv"}
            else "audio" if ext in {".wav", ".mp3", ".flac", ".ogg"}
            else "image"
        )

    raw = await file.read()
    input_data = base64.b64encode(raw).decode()
    return await _run_prediction(
        media_type, input_data, ensemble_method, threshold, db
    )


# ---------------------------------------------------------------------------
# Health & metadata
# ---------------------------------------------------------------------------

@app.get("/health", tags=["system"])
async def health():
    results = {"gateway": "ok", "models": {}}
    async with httpx.AsyncClient() as client:
        for model in ACTIVE_MODELS:
            url = f"{model['url']}/health"
            try:
                resp = await client.get(url, timeout=5)
                results["models"][model["name"]] = resp.json()
            except Exception as exc:
                results["models"][model["name"]] = {"status": "unreachable", "error": str(exc)}
    return results


@app.get("/models", tags=["system"])
def list_models():
    return {"models": ACTIVE_MODELS}


@app.get("/history", tags=["history"])
def get_history(
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    rows = (
        db.query(AnalysisHistory)
        .filter(AnalysisHistory.user_id == current_user.id)
        .order_by(AnalysisHistory.id.desc())
        .limit(limit)
        .all()
    )
    return [
        {
            "id": r.id,
            "media_type": r.media_type,
            "verdict": r.verdict,
            "confidence": r.confidence,
            "ensemble_score": r.ensemble_score,
            "ensemble_method": r.ensemble_method,
            "model_results": json.loads(r.model_results),
            "timestamp": r.timestamp,
        }
        for r in rows
    ]
