"""
Pramaan — Meta-Feature Generator

Generates feature matrix by running inference on benchmark media through all active models.
Produces X (model probability vectors) and y (0=real, 1=fake) for meta-learner training.

Usage:
    python meta_feature_generator.py --media-type image --output features_image.npz
"""

from __future__ import annotations

import argparse
import base64
import json
import logging
import os
import sys
from pathlib import Path

import httpx
import numpy as np

ROOT = Path(__file__).parent
CONFIG_PATH = ROOT / "config" / "pramaan_config.json"

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("meta_feature_generator")


def load_config() -> dict:
    with open(CONFIG_PATH) as f:
        return json.load(f)


def get_model_url(model: dict) -> str:
    """Convert docker hostname to localhost for local dev."""
    return model["url"].replace(f"http://{model['name']}", "http://localhost")


def call_predict(client: httpx.Client, url: str, input_data: str, threshold: float = 0.5) -> float:
    try:
        resp = client.post(
            f"{url}/predict",
            json={"input_data": input_data, "threshold": threshold},
            timeout=30,
        )
        resp.raise_for_status()
        return float(resp.json().get("probability", 0.5))
    except Exception as exc:
        logger.warning(f"Model call failed: {exc}")
        return 0.5


def generate_synthetic_sample(media_type: str, is_fake: bool, rng: np.random.Generator) -> str:
    """Generate a synthetic base64-encoded sample for testing."""
    # Create a small random image
    if media_type == "image":
        if is_fake:
            arr = rng.integers(180, 255, size=(32, 32, 3), dtype=np.uint8)
        else:
            arr = rng.integers(50, 150, size=(32, 32, 3), dtype=np.uint8)
        from PIL import Image
        import io
        img = Image.fromarray(arr, "RGB")
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        return base64.b64encode(buf.getvalue()).decode()
    else:
        # For video/audio: random bytes
        size = rng.integers(1000, 5000)
        raw = rng.bytes(int(size))
        return base64.b64encode(raw).decode()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--media-type", required=True, choices=["image", "video", "audio"])
    parser.add_argument("--output", default=None)
    parser.add_argument("--samples", type=int, default=200)
    parser.add_argument("--benchmark-dir", default=None, help="Path to benchmark dataset directory")
    args = parser.parse_args()

    config = load_config()
    models = [m for m in config["models"] if m["enabled"] and m["media_type"] == args.media_type]

    if not models:
        logger.error(f"No active models for {args.media_type}")
        sys.exit(1)

    logger.info(f"Active models: {[m['name'] for m in models]}")

    rng = np.random.default_rng(42)
    X_rows = []
    y_rows = []

    with httpx.Client() as client:
        for i in range(args.samples):
            is_fake = i % 2 == 0
            label = 1 if is_fake else 0

            input_data = generate_synthetic_sample(args.media_type, is_fake, rng)

            row = []
            for model in models:
                url = get_model_url(model)
                prob = call_predict(client, url, input_data)
                row.append(prob)

            X_rows.append(row)
            y_rows.append(label)

            if (i + 1) % 10 == 0:
                logger.info(f"  Progress: {i+1}/{args.samples}")

    X = np.array(X_rows)
    y = np.array(y_rows)
    logger.info(f"Feature matrix shape: {X.shape}")

    output_path = args.output or f"features_{args.media_type}.npz"
    np.savez(output_path, X=X, y=y)
    logger.info(f"✅ Saved features to {output_path}")


if __name__ == "__main__":
    main()
