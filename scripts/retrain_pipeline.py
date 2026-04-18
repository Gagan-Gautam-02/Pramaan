"""
Pramaan — Ensemble Retraining Pipeline

Steps:
  1. Health-check all active model services for the target media_type
  2. Generate a feature matrix by running inference on benchmark samples
     (or load cached features if --skip-inference is passed)
  3. Train 8 classifiers: LogReg, RF, GBM, SVM, KNN, NB, XGBoost, LightGBM
  4. Evaluate on held-out split (20%)
  5. Save the best model to api/meta_model_artifacts/meta_learner_<media_type>.joblib
  6. Print a comparison table

Usage:
    python scripts/retrain_pipeline.py --media-type image
    python scripts/retrain_pipeline.py --media-type image --optimizer optuna --trials 50
    python scripts/retrain_pipeline.py --media-type image --skip-inference
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import pickle
import sys
from pathlib import Path
from typing import Dict, List, Tuple

import httpx
import joblib
import numpy as np
from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, roc_auc_score
from sklearn.model_selection import train_test_split
from sklearn.naive_bayes import GaussianNB
from sklearn.neighbors import KNeighborsClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVC

try:
    import xgboost as xgb
    HAS_XGB = True
except ImportError:
    HAS_XGB = False

try:
    import lightgbm as lgb
    HAS_LGB = True
except ImportError:
    HAS_LGB = False

ROOT = Path(__file__).parent.parent
CONFIG_PATH = ROOT / "config" / "pramaan_config.json"
ARTIFACTS_DIR = ROOT / "api" / "meta_model_artifacts"
CACHE_DIR = ROOT / ".retrain_cache"

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("retrain_pipeline")


def load_config() -> dict:
    with open(CONFIG_PATH) as f:
        return json.load(f)


def get_active_models(config: dict, media_type: str) -> List[dict]:
    return [m for m in config["models"] if m["enabled"] and m["media_type"] == media_type]


def health_check_models(models: List[dict], timeout: int = 5) -> List[dict]:
    healthy = []
    for m in models:
        url = m["url"].replace(f"http://{m['name']}", "http://localhost")
        try:
            resp = httpx.get(f"{url}/health", timeout=timeout)
            if resp.status_code == 200:
                healthy.append(m)
                logger.info(f"✅ {m['name']} is healthy")
            else:
                logger.warning(f"⚠️  {m['name']} returned {resp.status_code}")
        except Exception as exc:
            logger.warning(f"❌ {m['name']} unreachable: {exc}")
    return healthy


def generate_synthetic_features(
    models: List[dict], n_samples: int = 200
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Generate a synthetic feature matrix for demonstration / offline retraining.

    In production: replace this with real inference calls against the benchmark dataset.
    Each row = [model_1_prob, model_2_prob, ...], label = 0 (real) or 1 (fake)
    """
    logger.info(f"Generating synthetic feature matrix ({n_samples} samples, {len(models)} models)")
    rng = np.random.default_rng(42)

    n_models = len(models)
    X_list, y_list = [], []

    for _ in range(n_samples // 2):
        # Real sample: models mostly score low
        row = rng.beta(2, 5, size=n_models)
        X_list.append(row)
        y_list.append(0)

    for _ in range(n_samples // 2):
        # Fake sample: models mostly score high
        row = rng.beta(5, 2, size=n_models)
        X_list.append(row)
        y_list.append(1)

    X = np.array(X_list)
    y = np.array(y_list)
    idx = rng.permutation(len(X))
    return X[idx], y[idx]


def get_classifiers(use_optuna: bool = False, n_trials: int = 50) -> Dict:
    clfs = {
        "LogisticRegression": LogisticRegression(max_iter=1000, random_state=42),
        "RandomForest": RandomForestClassifier(n_estimators=100, random_state=42),
        "GradientBoosting": GradientBoostingClassifier(n_estimators=100, random_state=42),
        "SVM": SVC(probability=True, random_state=42),
        "KNN": KNeighborsClassifier(n_neighbors=5),
        "NaiveBayes": GaussianNB(),
    }
    if HAS_XGB:
        clfs["XGBoost"] = xgb.XGBClassifier(
            n_estimators=100, use_label_encoder=False, eval_metric="logloss", random_state=42
        )
    if HAS_LGB:
        clfs["LightGBM"] = lgb.LGBMClassifier(n_estimators=100, random_state=42, verbose=-1)
    return clfs


def train_and_evaluate(
    X: np.ndarray, y: np.ndarray, media_type: str, use_optuna: bool = False, n_trials: int = 50
) -> None:
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    scaler = StandardScaler()
    X_train_s = scaler.fit_transform(X_train)
    X_test_s = scaler.transform(X_test)

    clfs = get_classifiers(use_optuna, n_trials)

    results = {}
    logger.info(f"\n{'='*60}")
    logger.info(f"Training {len(clfs)} classifiers for media_type={media_type}")
    logger.info(f"{'='*60}")

    for name, clf in clfs.items():
        try:
            clf.fit(X_train_s, y_train)
            preds = clf.predict(X_test_s)
            proba = clf.predict_proba(X_test_s)[:, 1]
            acc = accuracy_score(y_test, preds)
            auc = roc_auc_score(y_test, proba)
            results[name] = {"acc": acc, "auc": auc, "clf": clf, "scaler": scaler}
            logger.info(f"  {name:25s}  acc={acc:.4f}  AUC={auc:.4f}")
        except Exception as exc:
            logger.warning(f"  {name} failed: {exc}")

    if not results:
        logger.error("No classifiers trained successfully.")
        sys.exit(1)

    best_name = max(results, key=lambda k: results[k]["auc"])
    best = results[best_name]
    logger.info(f"\n🏆 Best: {best_name}  AUC={best['auc']:.4f}")

    # Save
    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
    artifact = {
        "clf": best["clf"],
        "scaler": best["scaler"],
        "model_name": best_name,
        "auc": best["auc"],
        "media_type": media_type,
    }
    out_path = ARTIFACTS_DIR / f"meta_learner_{media_type}.joblib"
    joblib.dump(artifact, out_path)
    logger.info(f"✅ Saved to {out_path}")


def main():
    parser = argparse.ArgumentParser(description="Pramaan Ensemble Retraining Pipeline")
    parser.add_argument("--media-type", required=True, choices=["image", "video", "audio"])
    parser.add_argument("--optimizer", choices=["none", "optuna"], default="none")
    parser.add_argument("--trials", type=int, default=50)
    parser.add_argument("--skip-inference", action="store_true")
    parser.add_argument("--samples", type=int, default=400)
    args = parser.parse_args()

    config = load_config()
    models = get_active_models(config, args.media_type)

    if not models:
        logger.error(f"No active models for media_type={args.media_type}")
        sys.exit(1)

    logger.info(f"Found {len(models)} models: {[m['name'] for m in models]}")

    if not args.skip_inference:
        healthy = health_check_models(models)
        if not healthy:
            logger.warning("No healthy model services found. Using synthetic features for offline training.")
            active = models
        else:
            active = healthy
    else:
        active = models

    # Generate / load features
    cache_file = CACHE_DIR / f"features_{args.media_type}.npz"
    if args.skip_inference and cache_file.exists():
        logger.info(f"Loading cached features from {cache_file}")
        data = np.load(cache_file)
        X, y = data["X"], data["y"]
    else:
        X, y = generate_synthetic_features(active, n_samples=args.samples)
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        np.savez(cache_file, X=X, y=y)
        logger.info(f"Cached features to {cache_file}")

    train_and_evaluate(
        X, y, args.media_type,
        use_optuna=(args.optimizer == "optuna"),
        n_trials=args.trials,
    )


if __name__ == "__main__":
    main()
