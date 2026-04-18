"""
UniversalFakeDetect — HTTP server entry point.

Exposes:
  GET  /health
  POST /predict  → {"input_data": "<base64>", "threshold": 0.5}
"""

import base64
import io
import logging
import os
import threading

from flask import Flask, jsonify, request
from PIL import Image

from detector import UniversalFakeDetector

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ufd_server")

app = Flask("universalfakedetect")
detector = UniversalFakeDetector()
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
    return jsonify({
        "status": "ok",
        "model_name": "universalfakedetect",
        "model_loaded": _loaded,
        "version": "1.0.0",
    })


@app.post("/predict")
def predict():
    ensure_loaded()
    body = request.get_json(force=True)
    input_data = body.get("input_data", "")
    threshold = float(body.get("threshold", 0.5))

    if not input_data:
        return jsonify({"error": "input_data is required"}), 422

    try:
        if "," in input_data:
            input_data = input_data.split(",", 1)[1]
        raw = base64.b64decode(input_data)
        image = Image.open(io.BytesIO(raw)).convert("RGB")
        result = detector.predict(image, threshold)
        return jsonify(result)
    except Exception as exc:
        logger.exception("Prediction error")
        return jsonify({"error": str(exc)}), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5004))
    ensure_loaded()
    app.run(host="0.0.0.0", port=port, threaded=True)
