"""
Pramaan SDK — Base model classes.

Usage:
    from pramaan_sdk import ImageModel, PredictionResult

    class MyDetector(ImageModel):
        def load(self):
            self.model = torch.load(self.weights_path("weights/model.pth"))

        def predict(self, input_data: str, threshold: float) -> PredictionResult:
            image = self.decode_image(input_data)
            prob = self.run_inference(image)
            return PredictionResult.build(self.name, prob, threshold)
"""

from __future__ import annotations

import abc
import base64
import io
import logging
import os
import threading
from pathlib import Path
from typing import Any, Optional

from flask import Flask, jsonify, request

from .schemas import HealthResponse, PredictionResult, PredictRequest

logger = logging.getLogger(__name__)


class _BaseModel(abc.ABC):
    """Common functionality for all model types."""

    name: str = "base_model"
    version: str = "1.0.0"

    def __init__(self) -> None:
        self._loaded = False
        self._lock = threading.Lock()
        self._model: Any = None
        self.app = self._create_app()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def serve(self, host: str = "0.0.0.0", port: int = 5000) -> None:
        """Start the Flask HTTP server."""
        logger.info(f"Starting {self.name} on {host}:{port}")
        self._ensure_loaded()
        self.app.run(host=host, port=port, threaded=True)

    # ------------------------------------------------------------------
    # Abstract interface
    # ------------------------------------------------------------------

    @abc.abstractmethod
    def load(self) -> None:
        """Load model weights. Called once before serving."""
        ...

    @abc.abstractmethod
    def predict(self, input_data: str, threshold: float) -> PredictionResult:
        """Run inference. input_data is a base64-encoded string."""
        ...

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def weights_path(self, relative: str) -> Path:
        """Return absolute path relative to the model directory."""
        base = Path(os.environ.get("MODEL_DIR", Path(__file__).parent.parent))
        return base / relative

    def decode_bytes(self, b64_data: str) -> bytes:
        """Decode base64 string to raw bytes."""
        # Strip data URI prefix if present  (data:image/jpeg;base64,...)
        if "," in b64_data:
            b64_data = b64_data.split(",", 1)[1]
        return base64.b64decode(b64_data)

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _ensure_loaded(self) -> None:
        with self._lock:
            if not self._loaded:
                logger.info(f"Loading {self.name}...")
                self.load()
                self._loaded = True
                logger.info(f"{self.name} loaded.")

    def _create_app(self) -> Flask:
        app = Flask(self.name)

        @app.get("/health")
        def health():  # noqa: F811
            return jsonify(
                HealthResponse(
                    model_name=self.name,
                    model_loaded=self._loaded,
                    version=self.version,
                ).model_dump()
            )

        @app.post("/predict")
        def predict():  # noqa: F811
            self._ensure_loaded()
            body = request.get_json(force=True)
            try:
                req = PredictRequest(**body)
            except Exception as exc:
                return jsonify({"error": str(exc)}), 422

            try:
                result = self.predict(req.input_data, req.threshold)
                return jsonify(result.model_dump())
            except Exception as exc:
                logger.exception("Inference error")
                return jsonify({"error": str(exc)}), 500

        return app


class ImageModel(_BaseModel):
    """Base class for image deepfake detectors."""

    def decode_image(self, b64_data: str):
        """Decode base64 image → PIL Image."""
        from PIL import Image  # lazy import
        raw = self.decode_bytes(b64_data)
        return Image.open(io.BytesIO(raw)).convert("RGB")


class VideoModel(_BaseModel):
    """Base class for video deepfake detectors."""

    def decode_video_bytes(self, b64_data: str) -> bytes:
        return self.decode_bytes(b64_data)


class AudioModel(_BaseModel):
    """Base class for audio deepfake detectors."""

    def decode_audio_bytes(self, b64_data: str) -> bytes:
        return self.decode_bytes(b64_data)
