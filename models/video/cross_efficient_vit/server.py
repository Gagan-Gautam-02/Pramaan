"""
Cross-Efficient ViT — HTTP server entry point.

Exposes:
  GET  /health
  POST /predict  → {"input_data": "<base64 video>", "threshold": 0.5}
"""

import base64
import logging
import os
import threading

from flask import Flask, jsonify, request

from detector import CrossEfficientViTDetector

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("cev_server")

app = Flask("cross_efficient_vit")
detector = CrossEfficientViTDetector()
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
        "model_name": "cross_efficient_vit",
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
        result = detector.predict(raw, threshold)
        return jsonify(result)
    except Exception as exc:
        logger.exception("Prediction error")
        return jsonify({"error": str(exc)}), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 7001))
    ensure_loaded()
    app.run(host="0.0.0.0", port=port, threaded=True)
