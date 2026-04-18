"""
Pramaan SDK — shared base classes for all model microservices.

Each model container extends ImageModel, VideoModel, or AudioModel.
The SDK handles:
  - HTTP server setup (Flask)
  - /health and /predict endpoint registration
  - Lazy loading with thread-safe lock
  - Request/response schema validation
  - Base64 decoding helpers
"""

from .base import ImageModel, VideoModel, AudioModel
from .schemas import PredictionResult, PredictRequest, HealthResponse

__all__ = [
    "ImageModel",
    "VideoModel",
    "AudioModel",
    "PredictionResult",
    "PredictRequest",
    "HealthResponse",
]
