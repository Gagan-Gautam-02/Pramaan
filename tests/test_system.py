"""
Pramaan system tests.

Tests require the gateway to be running at http://localhost:8000.
Run: make start && make test
"""

import base64
import io
import os

import pytest
import httpx
from PIL import Image

GATEWAY = os.environ.get("GATEWAY_URL", "http://localhost:8000")


def make_b64_image(width=64, height=64) -> str:
    """Create a small JPEG as base64."""
    img = Image.new("RGB", (width, height), color=(128, 64, 200))
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    return base64.b64encode(buf.getvalue()).decode()


@pytest.fixture(scope="session")
def client():
    return httpx.Client(base_url=GATEWAY, timeout=30)


@pytest.fixture(scope="session")
def auth_token(client):
    """Register + login, return JWT."""
    import random
    username = f"testuser_{random.randint(10000, 99999)}"
    password = "testpassword123"
    client.post("/register", json={"username": username, "password": password})
    resp = client.post("/token", data={"username": username, "password": password})
    assert resp.status_code == 200
    return resp.json()["access_token"]


# ─────────────────────────────────────────────
# Health checks
# ─────────────────────────────────────────────

def test_gateway_health(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data.get("gateway") == "ok"


def test_list_models(client):
    resp = client.get("/models")
    assert resp.status_code == 200
    models = resp.json()["models"]
    assert len(models) >= 1


# ─────────────────────────────────────────────
# Auth
# ─────────────────────────────────────────────

def test_register_and_login(client):
    import random
    user = f"u{random.randint(100000, 999999)}"
    r = client.post("/register", json={"username": user, "password": "pass"})
    assert r.status_code == 200
    r2 = client.post("/token", data={"username": user, "password": "pass"})
    assert r2.status_code == 200
    assert "access_token" in r2.json()


def test_me(client, auth_token):
    resp = client.get("/users/me", headers={"Authorization": f"Bearer {auth_token}"})
    assert resp.status_code == 200
    assert "username" in resp.json()


def test_protected_endpoint_requires_auth(client):
    resp = client.get("/history")
    assert resp.status_code == 401


# ─────────────────────────────────────────────
# Prediction
# ─────────────────────────────────────────────

@pytest.mark.parametrize("method", ["voting", "average", "stacking"])
def test_predict_image_json(client, method):
    b64 = make_b64_image()
    resp = client.post("/predict", json={
        "media_type": "image",
        "image_data": b64,
        "ensemble_method": method,
        "threshold": 0.5,
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["verdict"] in ("fake", "real", "unknown")
    assert 0.0 <= data["ensemble_score_is_fake"] <= 1.0
    assert data["ensemble_method_used"] == method


def test_detect_file_upload(client):
    b64 = make_b64_image()
    raw = base64.b64decode(b64)
    resp = client.post(
        "/detect",
        files={"file": ("test.jpg", io.BytesIO(raw), "image/jpeg")},
        data={"ensemble_method": "voting"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "verdict" in data
    assert "model_results" in data


def test_invalid_media_type(client):
    resp = client.post("/predict", json={
        "media_type": "hologram",
        "image_data": "abc",
        "ensemble_method": "voting",
    })
    assert resp.status_code == 400


# ─────────────────────────────────────────────
# History
# ─────────────────────────────────────────────

def test_history(client, auth_token):
    headers = {"Authorization": f"Bearer {auth_token}"}
    # Run a detection first
    b64 = make_b64_image()
    client.post("/predict", json={
        "media_type": "image",
        "image_data": b64,
        "ensemble_method": "voting",
    }, headers=headers)

    resp = client.get("/history", headers=headers)
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)
