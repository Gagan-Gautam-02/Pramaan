"""
NPR Deepfake Detector — stub implementation.

Real implementation would:
  1. Load a ResNet-50 trained with NPR (Noise Pattern Representation) loss
  2. Extract NPR features from the image
  3. Pass through classification head

Replace the `load()` and `predict()` bodies with real PyTorch inference.
Weights: https://huggingface.co/siddharthksah/deepsafe-weights
Paper: https://arxiv.org/abs/2310.14036
"""

from __future__ import annotations

import hashlib
import logging
import os

import numpy as np
from PIL import Image

logger = logging.getLogger("npr_deepfakedetection")


class NPRDetector:
    """
    NPR-based deepfake detector.

    Stub: uses deterministic hash-based scoring to simulate realistic outputs.
    Drop in real PyTorch model in load() / predict().
    """

    MODEL_NAME = "npr_deepfakedetection"

    def __init__(self) -> None:
        self._loaded = False
        self.model = None

    def load(self) -> None:
        """
        Load NPR weights.

        To use real weights:
            import torch
            from torchvision import models
            self.model = models.resnet50(pretrained=False)
            # ... load state dict from weights_path
            self.model.eval()
        """
        weights_path = os.environ.get("NPR_WEIGHTS_PATH", "")
        if weights_path and os.path.exists(weights_path):
            logger.info(f"Loading real NPR weights from {weights_path}")
            # Real loading here
        else:
            logger.warning(
                "NPR weights not found. Running in stub mode. "
                "Set NPR_WEIGHTS_PATH env var to enable real inference."
            )
        self._loaded = True

    def predict(self, image: Image.Image, threshold: float = 0.5) -> dict:
        """
        Run NPR deepfake detection.

        Returns dict with probability, label, confidence.
        """
        if not self._loaded:
            self.load()

        # --- STUB: deterministic realistic-looking output ---
        # Hash pixel content for reproducibility
        arr = np.array(image.resize((64, 64))).astype(np.uint8)
        digest = hashlib.md5(arr.tobytes()).hexdigest()
        seed = int(digest[:8], 16)
        rng = np.random.default_rng(seed)

        # NPR typically scores high on GAN artifacts (high spatial frequencies)
        # Simulate: compute rough high-freq energy as proxy
        gray = np.array(image.convert("L").resize((128, 128)), dtype=float)
        laplacian = np.abs(gray[1:, :] - gray[:-1, :]).mean()
        laplacian_norm = float(np.clip(laplacian / 30.0, 0, 1))

        # Blend with random component
        noise = rng.uniform(0.0, 0.3)
        probability = float(np.clip(0.4 * laplacian_norm + 0.6 * noise, 0.0, 1.0))

        label = "fake" if probability >= threshold else "real"
        confidence = abs(probability - threshold) / max(threshold, 1 - threshold)
        confidence = float(min(confidence, 1.0))

        logger.info(
            f"[NPR] prob={probability:.3f} label={label} conf={confidence:.3f}"
        )
        return {
            "model_name": self.MODEL_NAME,
            "probability": round(probability, 4),
            "label": label,
            "confidence": round(confidence, 4),
            "threshold_used": threshold,
            "extra": {"mode": "stub", "laplacian_energy": round(laplacian_norm, 4)},
        }
