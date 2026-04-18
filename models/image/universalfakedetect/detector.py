"""
UniversalFakeDetect — stub implementation.

Real implementation:
  1. Load CLIP ViT-L/14 feature extractor (frozen)
  2. Linear probe / MLP head trained on real vs. fake features
  3. Generalizes to unseen generators via CLIP's rich representation

Replace load() / predict() with real CLIP + linear probe.
Weights: https://huggingface.co/siddharthksah/deepsafe-weights
Paper: https://arxiv.org/abs/2302.10174
"""

from __future__ import annotations

import hashlib
import logging
import os

import numpy as np
from PIL import Image

logger = logging.getLogger("universalfakedetect")


class UniversalFakeDetector:
    MODEL_NAME = "universalfakedetect"

    def __init__(self) -> None:
        self._loaded = False
        self.clip_model = None
        self.linear_probe = None

    def load(self) -> None:
        """
        Real loading:
            import clip
            self.clip_model, self.preprocess = clip.load("ViT-L/14", device="cpu")
            self.linear_probe = torch.load(weights_path)
        """
        weights_path = os.environ.get("UFD_WEIGHTS_PATH", "")
        if weights_path and os.path.exists(weights_path):
            logger.info(f"Loading real UFD weights from {weights_path}")
        else:
            logger.warning("UFD weights not found. Running in stub mode.")
        self._loaded = True

    def predict(self, image: Image.Image, threshold: float = 0.5) -> dict:
        if not self._loaded:
            self.load()

        # --- STUB: simulate CLIP-based detection ---
        arr = np.array(image.resize((64, 64))).astype(np.uint8)
        digest = hashlib.md5(arr.tobytes()).hexdigest()
        seed = int(digest[8:16], 16)
        rng = np.random.default_rng(seed)

        # UFD tends to look at colour saturation / frequency artifacts
        hsv_arr = np.array(image.convert("HSV").resize((64, 64)), dtype=float) if hasattr(image, "convert") else arr
        saturation = float(np.std(arr))
        sat_norm = float(np.clip(saturation / 80.0, 0, 1))

        noise = rng.uniform(0.0, 0.35)
        probability = float(np.clip(0.5 * sat_norm + 0.5 * noise, 0.0, 1.0))

        label = "fake" if probability >= threshold else "real"
        confidence = abs(probability - threshold) / max(threshold, 1 - threshold)
        confidence = float(min(confidence, 1.0))

        logger.info(
            f"[UFD] prob={probability:.3f} label={label} conf={confidence:.3f}"
        )
        return {
            "model_name": self.MODEL_NAME,
            "probability": round(probability, 4),
            "label": label,
            "confidence": round(confidence, 4),
            "threshold_used": threshold,
            "extra": {"mode": "stub", "saturation_proxy": round(sat_norm, 4)},
        }
