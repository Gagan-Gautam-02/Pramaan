"""
Pramaan — Advanced Meta-Learner Training Suite

Trains the full suite of classifiers and optionally runs Optuna hyperparameter search.

Usage:
    python train_meta_learner_advanced.py --media-type image --features features_image.npz
    python train_meta_learner_advanced.py --media-type image --features features_image.npz \\
        --optimizer optuna --trials 100
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

import joblib
import numpy as np
from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    roc_auc_score,
)
from sklearn.model_selection import StratifiedKFold, cross_val_score, train_test_split
from sklearn.naive_bayes import GaussianNB
from sklearn.neighbors import KNeighborsClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVC

try:
    import xgboost as xgb
    HAS_XGB = True
except ImportError:
    HAS_XGB = False
    logging.warning("xgboost not installed. Skipping XGBoost.")

try:
    import lightgbm as lgb
    HAS_LGB = True
except ImportError:
    HAS_LGB = False
    logging.warning("lightgbm not installed. Skipping LightGBM.")

ROOT = Path(__file__).parent
ARTIFACTS_DIR = ROOT / "api" / "meta_model_artifacts"
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("train_meta_learner")


def build_classifiers() -> dict:
    clfs = {
        "LogisticRegression": LogisticRegression(max_iter=2000, random_state=42),
        "RandomForest": RandomForestClassifier(n_estimators=200, random_state=42),
        "GradientBoosting": GradientBoostingClassifier(n_estimators=200, random_state=42),
        "SVM_RBF": SVC(kernel="rbf", probability=True, random_state=42),
        "KNN": KNeighborsClassifier(n_neighbors=7),
        "NaiveBayes": GaussianNB(),
    }
    if HAS_XGB:
        clfs["XGBoost"] = xgb.XGBClassifier(
            n_estimators=200, use_label_encoder=False, eval_metric="logloss",
            random_state=42, verbosity=0,
        )
    if HAS_LGB:
        clfs["LightGBM"] = lgb.LGBMClassifier(n_estimators=200, random_state=42, verbose=-1)
    return clfs


def optuna_search(X_train, y_train, media_type: str, n_trials: int = 50) -> dict:
    """Run Optuna HPO for LightGBM or XGBoost."""
    try:
        import optuna
        optuna.logging.set_verbosity(optuna.logging.WARNING)
    except ImportError:
        logger.warning("optuna not installed. Skipping HPO.")
        return {}

    if not HAS_LGB:
        logger.warning("LightGBM not available for Optuna search.")
        return {}

    def objective(trial):
        params = {
            "n_estimators": trial.suggest_int("n_estimators", 50, 500),
            "max_depth": trial.suggest_int("max_depth", 2, 10),
            "learning_rate": trial.suggest_float("learning_rate", 1e-3, 0.3, log=True),
            "num_leaves": trial.suggest_int("num_leaves", 10, 150),
            "min_child_samples": trial.suggest_int("min_child_samples", 5, 50),
            "random_state": 42,
            "verbose": -1,
        }
        clf = lgb.LGBMClassifier(**params)
        cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
        scores = cross_val_score(clf, X_train, y_train, cv=cv, scoring="roc_auc")
        return scores.mean()

    study = optuna.create_study(direction="maximize")
    study.optimize(objective, n_trials=n_trials, show_progress_bar=True)

    best_params = study.best_params
    best_params.update({"random_state": 42, "verbose": -1})
    clf = lgb.LGBMClassifier(**best_params)
    return {"LightGBM_Optuna": clf}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--media-type", required=True, choices=["image", "video", "audio"])
    parser.add_argument("--features", required=True, help="Path to .npz feature file")
    parser.add_argument("--optimizer", choices=["none", "optuna"], default="none")
    parser.add_argument("--trials", type=int, default=50)
    args = parser.parse_args()

    data = np.load(args.features)
    X, y = data["X"], data["y"]
    logger.info(f"Loaded features: X={X.shape}, y={y.shape}")

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    scaler = StandardScaler()
    X_train_s = scaler.fit_transform(X_train)
    X_test_s = scaler.transform(X_test)

    clfs = build_classifiers()

    if args.optimizer == "optuna":
        optuna_clfs = optuna_search(X_train_s, y_train, args.media_type, args.trials)
        clfs.update(optuna_clfs)

    results = {}
    logger.info(f"\n{'='*70}")
    logger.info(f"{'Classifier':<30} {'Accuracy':>10} {'AUC':>10}")
    logger.info(f"{'='*70}")

    for name, clf in clfs.items():
        try:
            clf.fit(X_train_s, y_train)
            preds = clf.predict(X_test_s)
            proba = clf.predict_proba(X_test_s)[:, 1]
            acc = accuracy_score(y_test, preds)
            auc = roc_auc_score(y_test, proba)
            results[name] = {"acc": acc, "auc": auc, "clf": clf}
            logger.info(f"{name:<30} {acc:>10.4f} {auc:>10.4f}")
        except Exception as exc:
            logger.warning(f"{name} failed: {exc}")

    if not results:
        logger.error("No classifiers trained.")
        sys.exit(1)

    best_name = max(results, key=lambda k: results[k]["auc"])
    best = results[best_name]
    logger.info(f"\n🏆 Winner: {best_name}  AUC={best['auc']:.4f}  Acc={best['acc']:.4f}")

    # Full classification report
    preds = best["clf"].predict(X_test_s)
    logger.info(f"\n{classification_report(y_test, preds, target_names=['real','fake'])}")

    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
    artifact = {
        "clf": best["clf"],
        "scaler": scaler,
        "model_name": best_name,
        "auc": best["auc"],
        "media_type": args.media_type,
        "all_results": {k: {"acc": v["acc"], "auc": v["auc"]} for k, v in results.items()},
    }
    out_path = ARTIFACTS_DIR / f"meta_learner_{args.media_type}.joblib"
    joblib.dump(artifact, out_path)
    logger.info(f"✅ Saved meta-learner to {out_path}")


if __name__ == "__main__":
    main()
