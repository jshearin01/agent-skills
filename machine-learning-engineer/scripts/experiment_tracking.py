#!/usr/bin/env python3
"""
MLflow Experiment Tracking Template
====================================
Production-grade experiment tracking with full lineage, metrics, and model registration.

Usage:
    python experiment_tracking.py --config configs/params.yaml --experiment my-experiment

Requirements:
    pip install mlflow scikit-learn pandas numpy xgboost optuna
"""

import argparse
import json
import os
import subprocess
import sys
import time
import warnings
from pathlib import Path
from typing import Any

import mlflow
import mlflow.sklearn
import numpy as np
import pandas as pd
import yaml
from mlflow.models import infer_signature
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score, f1_score, precision_score, recall_score,
    roc_auc_score, average_precision_score, brier_score_loss,
)
from sklearn.model_selection import StratifiedKFold, cross_val_score
from sklearn.pipeline import Pipeline

warnings.filterwarnings("ignore")


# ──────────────────────────────────────────────
# Utilities
# ──────────────────────────────────────────────

def get_git_hash() -> str:
    """Return the current git commit hash, or 'unknown' if not in a git repo."""
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"], stderr=subprocess.DEVNULL
        ).decode().strip()
    except Exception:
        return "unknown"


def get_dvc_hash(path: str) -> str:
    """Return the DVC-tracked hash for a file, or 'untracked' if not versioned."""
    dvc_file = Path(f"{path}.dvc")
    if dvc_file.exists():
        with open(dvc_file) as f:
            content = yaml.safe_load(f)
            return content.get("outs", [{}])[0].get("md5", "unknown")
    return "untracked"


def load_params(config_path: str) -> dict:
    """Load hyperparameters from a YAML config file."""
    with open(config_path) as f:
        return yaml.safe_load(f)


def compute_metrics(y_true: np.ndarray, y_pred: np.ndarray,
                     y_proba: np.ndarray) -> dict[str, float]:
    """Compute a comprehensive set of classification metrics."""
    return {
        "auc_roc": roc_auc_score(y_true, y_proba),
        "auc_pr": average_precision_score(y_true, y_proba),
        "f1": f1_score(y_true, y_pred, zero_division=0),
        "precision": precision_score(y_true, y_pred, zero_division=0),
        "recall": recall_score(y_true, y_pred, zero_division=0),
        "accuracy": accuracy_score(y_true, y_pred),
        "brier_score": brier_score_loss(y_true, y_proba),
    }


# ──────────────────────────────────────────────
# Core Training Function
# ──────────────────────────────────────────────

def train_and_log(
    X_train: pd.DataFrame,
    y_train: pd.Series,
    X_val: pd.DataFrame,
    y_val: pd.Series,
    pipeline: Pipeline,
    params: dict[str, Any],
    experiment_name: str,
    run_name: str,
    data_path: str,
    register_model: bool = False,
    model_name: str = "MyModel",
) -> str:
    """
    Train a model and log everything to MLflow.

    Returns:
        The MLflow run ID.
    """
    mlflow.set_experiment(experiment_name)

    with mlflow.start_run(run_name=run_name, tags={
        "git_commit": get_git_hash(),
        "data_version": get_dvc_hash(data_path),
        "python_version": sys.version.split()[0],
        "mlflow_version": mlflow.__version__,
        "n_train_samples": str(len(X_train)),
        "n_val_samples": str(len(X_val)),
        "n_features": str(X_train.shape[1]),
    }) as run:

        # 1. Log all hyperparameters
        mlflow.log_params(params)

        # 2. Fit the pipeline (only on training data!)
        t0 = time.time()
        pipeline.fit(X_train, y_train)
        train_time = time.time() - t0
        mlflow.log_metric("train_time_seconds", train_time)

        # 3. Evaluate on training set (for overfitting detection)
        y_train_pred = pipeline.predict(X_train)
        y_train_proba = pipeline.predict_proba(X_train)[:, 1]
        train_metrics = {f"train_{k}": v for k, v in
                          compute_metrics(y_train, y_train_pred, y_train_proba).items()}
        mlflow.log_metrics(train_metrics)

        # 4. Evaluate on validation set
        y_val_pred = pipeline.predict(X_val)
        y_val_proba = pipeline.predict_proba(X_val)[:, 1]
        val_metrics = {f"val_{k}": v for k, v in
                        compute_metrics(y_val, y_val_pred, y_val_proba).items()}
        mlflow.log_metrics(val_metrics)

        # 5. Cross-validation (train+val combined for more robust estimate)
        X_combined = pd.concat([X_train, X_val])
        y_combined = pd.concat([y_train, y_val])
        cv_scores = cross_val_score(
            pipeline, X_combined, y_combined,
            cv=StratifiedKFold(n_splits=5, shuffle=True, random_state=42),
            scoring="roc_auc", n_jobs=-1
        )
        mlflow.log_metrics({
            "cv_auc_mean": cv_scores.mean(),
            "cv_auc_std": cv_scores.std(),
        })

        # 6. Log the feature list as an artifact
        feature_info = {
            "features": list(X_train.columns),
            "n_features": X_train.shape[1],
        }
        with open("/tmp/features.json", "w") as f:
            json.dump(feature_info, f, indent=2)
        mlflow.log_artifact("/tmp/features.json", artifact_path="metadata")

        # 7. Register the model with signature
        signature = infer_signature(X_train, pipeline.predict(X_train))
        input_example = X_train.head(5)

        model_uri = mlflow.sklearn.log_model(
            pipeline,
            artifact_path="model",
            signature=signature,
            input_example=input_example,
            registered_model_name=model_name if register_model else None,
        ).model_uri

        # 8. Print summary
        print(f"\n{'='*50}")
        print(f"Run: {run_name}  |  ID: {run.info.run_id[:8]}")
        print(f"  Val AUC-ROC:  {val_metrics['val_auc_roc']:.4f}")
        print(f"  Val AUC-PR:   {val_metrics['val_auc_pr']:.4f}")
        print(f"  Val F1:       {val_metrics['val_f1']:.4f}")
        print(f"  CV AUC:       {cv_scores.mean():.4f} ± {cv_scores.std():.4f}")
        print(f"  Train time:   {train_time:.1f}s")
        print(f"{'='*50}\n")

        return run.info.run_id


# ──────────────────────────────────────────────
# Hyperparameter Search with Optuna
# ──────────────────────────────────────────────

def hyperparameter_search(
    X_train: pd.DataFrame,
    y_train: pd.Series,
    X_val: pd.DataFrame,
    y_val: pd.Series,
    experiment_name: str,
    n_trials: int = 30,
) -> dict:
    """Run Optuna hyperparameter search, logging each trial to MLflow."""
    try:
        import optuna
        optuna.logging.set_verbosity(optuna.logging.WARNING)
    except ImportError:
        print("Optuna not installed. Run: pip install optuna")
        return {}

    def objective(trial):
        params = {
            "n_estimators": trial.suggest_int("n_estimators", 50, 500),
            "max_depth": trial.suggest_int("max_depth", 3, 12),
            "min_samples_split": trial.suggest_int("min_samples_split", 2, 20),
            "min_samples_leaf": trial.suggest_int("min_samples_leaf", 1, 10),
            "max_features": trial.suggest_categorical("max_features", ["sqrt", "log2", 0.5]),
        }

        pipeline = Pipeline([
            ("model", RandomForestClassifier(**params, random_state=42, n_jobs=-1))
        ])

        run_id = train_and_log(
            X_train, y_train, X_val, y_val,
            pipeline=pipeline,
            params=params,
            experiment_name=experiment_name,
            run_name=f"optuna_trial_{trial.number}",
            data_path="data/features/train.csv",
            register_model=False,
        )

        # Return the validation AUC for Optuna to maximize
        run = mlflow.get_run(run_id)
        return run.data.metrics.get("val_auc_roc", 0)

    study = optuna.create_study(direction="maximize")
    study.optimize(objective, n_trials=n_trials, show_progress_bar=True)

    print(f"\nBest trial: AUC-ROC = {study.best_value:.4f}")
    print(f"Best params: {study.best_params}")

    return study.best_params


# ──────────────────────────────────────────────
# CLI Entry Point
# ──────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Train and track an ML experiment")
    parser.add_argument("--config", default="configs/params.yaml",
                        help="Path to params YAML")
    parser.add_argument("--experiment", default="my-experiment",
                        help="MLflow experiment name")
    parser.add_argument("--run-name", default=None,
                        help="Name for this run (defaults to timestamp)")
    parser.add_argument("--tracking-uri", default="http://localhost:5000",
                        help="MLflow tracking server URI")
    parser.add_argument("--register", action="store_true",
                        help="Register model in MLflow Model Registry")
    parser.add_argument("--model-name", default="MyModel",
                        help="Registered model name (used if --register)")
    parser.add_argument("--search", action="store_true",
                        help="Run hyperparameter search with Optuna")
    args = parser.parse_args()

    mlflow.set_tracking_uri(args.tracking_uri)
    run_name = args.run_name or f"run_{int(time.time())}"

    # Load params
    params = load_params(args.config) if Path(args.config).exists() else {}

    # ── Replace this section with your actual data loading ──────────────────
    print("Loading sample data (replace with your actual data loading)...")
    from sklearn.datasets import make_classification
    from sklearn.model_selection import train_test_split

    X, y = make_classification(
        n_samples=5000, n_features=20, n_informative=15,
        n_redundant=3, random_state=42
    )
    X = pd.DataFrame(X, columns=[f"feature_{i}" for i in range(20)])
    y = pd.Series(y)

    X_train, X_val, y_train, y_val = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    # ────────────────────────────────────────────────────────────────────────

    if args.search:
        best_params = hyperparameter_search(
            X_train, y_train, X_val, y_val,
            experiment_name=args.experiment,
        )
        params.update(best_params)

    # Build final pipeline
    model_params = params.get("model", {
        "n_estimators": 200, "max_depth": 6, "random_state": 42, "n_jobs": -1
    })
    pipeline = Pipeline([
        ("model", RandomForestClassifier(**model_params))
    ])

    run_id = train_and_log(
        X_train, y_train, X_val, y_val,
        pipeline=pipeline,
        params=model_params,
        experiment_name=args.experiment,
        run_name=run_name,
        data_path="data/features/train.csv",
        register_model=args.register,
        model_name=args.model_name,
    )

    print(f"Run ID: {run_id}")
    print(f"View at: {args.tracking_uri}/#/experiments")


if __name__ == "__main__":
    main()
