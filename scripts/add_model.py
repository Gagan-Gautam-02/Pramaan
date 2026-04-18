"""
Pramaan — Add Model CLI

Usage:
    python scripts/add_model.py --name my_detector --media-type image --port 5008

What it does:
  1. Creates models/<media_type>/<name>/ scaffold (detector.py, server.py, requirements.txt, Dockerfile)
  2. Updates config/pramaan_config.json to register the new model
  3. Prints instructions for next steps
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
CONFIG_PATH = ROOT / "config" / "pramaan_config.json"

DETECTOR_TEMPLATE = '''"""
{name} — Detector stub.

Replace load() and predict() with real model inference.
"""
from __future__ import annotations
import logging
import os
import numpy as np

logger = logging.getLogger("{name}")


class {class_name}:
    MODEL_NAME = "{name}"

    def __init__(self):
        self._loaded = False

    def load(self):
        """Load model weights here."""
        logger.info("Loading {name}...")
        self._loaded = True

    def predict(self, input_data, threshold: float = 0.5) -> dict:
        """Run inference. Returns standardised result dict."""
        if not self._loaded:
            self.load()
        # TODO: Replace with real inference
        import hashlib
        rng = np.random.default_rng(int(hashlib.md5(str(input_data)[:64].encode()).hexdigest()[:8], 16))
        probability = float(rng.uniform(0, 1))
        label = "fake" if probability >= threshold else "real"
        confidence = abs(probability - threshold) / max(threshold, 1 - threshold)
        return {{
            "model_name": self.MODEL_NAME,
            "probability": round(probability, 4),
            "label": label,
            "confidence": round(min(confidence, 1.0), 4),
            "threshold_used": threshold,
            "extra": {{"mode": "stub"}},
        }}
'''

SERVER_TEMPLATE = '''"""
{name} — HTTP server entry point.
"""
import base64
import io
import logging
import os
import threading
from flask import Flask, jsonify, request
from detector import {class_name}

logging.basicConfig(level=logging.INFO)
app = Flask("{name}")
detector = {class_name}()
_lock = threading.Lock()
_loaded = False


def ensure_loaded():
    global _loaded
    if not _loaded:
        with _lock:
            if not _loaded:
                detector.load()
                _loaded = True


@app.get("/health")
def health():
    ensure_loaded()
    return jsonify({{"status": "ok", "model_name": "{name}", "model_loaded": _loaded, "version": "1.0.0"}})


@app.post("/predict")
def predict():
    ensure_loaded()
    body = request.get_json(force=True)
    input_data = body.get("input_data", "")
    threshold = float(body.get("threshold", 0.5))
    if not input_data:
        return jsonify({{"error": "input_data required"}}), 422
    try:
        if "," in input_data:
            input_data = input_data.split(",", 1)[1]
        raw = base64.b64decode(input_data)
        result = detector.predict(raw, threshold)
        return jsonify(result)
    except Exception as exc:
        return jsonify({{"error": str(exc)}}), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", {port}))
    ensure_loaded()
    app.run(host="0.0.0.0", port=port, threaded=True)
'''

DOCKERFILE_TEMPLATE = '''FROM python:3.11-slim
WORKDIR /app
COPY ../../../sdk /sdk
RUN pip install --no-cache-dir /sdk
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE {port}
CMD ["python", "server.py"]
'''

REQUIREMENTS_TEMPLATE = '''flask==3.0.3
pydantic==2.7.0
Pillow==10.3.0
numpy==1.26.4
'''


def to_class_name(name: str) -> str:
    return "".join(part.capitalize() for part in name.replace("-", "_").split("_")) + "Detector"


def add_model(name: str, media_type: str, port: int) -> None:
    model_dir = ROOT / "models" / media_type / name
    model_dir.mkdir(parents=True, exist_ok=True)

    class_name = to_class_name(name)

    # Write scaffold files
    (model_dir / "detector.py").write_text(
        DETECTOR_TEMPLATE.format(name=name, class_name=class_name)
    )
    (model_dir / "server.py").write_text(
        SERVER_TEMPLATE.format(name=name, class_name=class_name, port=port)
    )
    (model_dir / "requirements.txt").write_text(REQUIREMENTS_TEMPLATE)
    (model_dir / "Dockerfile").write_text(
        DOCKERFILE_TEMPLATE.format(port=port)
    )

    print(f"✅ Scaffold created at {model_dir}")

    # Update config
    with open(CONFIG_PATH) as f:
        config = json.load(f)

    # Check for duplicate
    existing_names = [m["name"] for m in config["models"]]
    if name in existing_names:
        print(f"⚠️  Model '{name}' already registered in config. Skipping config update.")
    else:
        config["models"].append({
            "name": name,
            "display_name": name.replace("_", " ").title(),
            "media_type": media_type,
            "port": port,
            "url": f"http://{name}:{port}",
            "description": f"{name} deepfake detector",
            "enabled": True,
        })
        with open(CONFIG_PATH, "w") as f:
            json.dump(config, f, indent=2)
        print(f"✅ Registered '{name}' in config/pramaan_config.json")

    print(f"\n📋 Next steps:")
    print(f"  1. Implement {model_dir}/detector.py")
    print(f"  2. Add weights to {model_dir}/weights/")
    print(f"  3. Run: make start")
    print(f"  4. Run: make retrain MEDIA_TYPE={media_type}")


def main():
    parser = argparse.ArgumentParser(description="Register a new Pramaan model")
    parser.add_argument("--name", required=True, help="Model name (snake_case)")
    parser.add_argument("--media-type", required=True, choices=["image", "video", "audio"])
    parser.add_argument("--port", type=int, required=True, help="Port number")
    args = parser.parse_args()

    add_model(args.name, args.media_type, args.port)


if __name__ == "__main__":
    main()
