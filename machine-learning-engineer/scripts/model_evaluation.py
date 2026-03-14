#!/usr/bin/env python3
"""
Comprehensive Model Evaluation
================================
Full evaluation suite: metrics, plots, error analysis, fairness checks,
calibration, and SHAP explanations.

Usage:
    python model_evaluation.py \
        --model models/model.pkl \
        --test  data/features/test_features.csv \
        --target target \
        --output reports/ \
        --threshold 0.5

Requirements:
    pip install scikit-learn pandas numpy matplotlib seaborn shap joblib
"""

import argparse
import json
import logging
import warnings
from pathlib import Path
from typing import Optional

import joblib
import numpy as np
import pandas as pd
from sklearn.calibration import calibration_curve
from sklearn.metrics import (
    accuracy_score, average_precision_score, brier_score_loss,
    classification_report, confusion_matrix, f1_score,
    precision_recall_curve, precision_score, recall_score,
    roc_auc_score, roc_curve,
)

warnings.filterwarnings("ignore")
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


# ──────────────────────────────────────────────
# Core Metrics
# ──────────────────────────────────────────────

def compute_all_metrics(y_true: np.ndarray, y_pred: np.ndarray,
                         y_proba: np.ndarray, threshold: float = 0.5) -> dict:
    """Compute the full suite of classification metrics."""
    return {
        "auc_roc": roc_auc_score(y_true, y_proba),
        "auc_pr": average_precision_score(y_true, y_proba),
        "f1": f1_score(y_true, y_pred, zero_division=0),
        "precision": precision_score(y_true, y_pred, zero_division=0),
        "recall": recall_score(y_true, y_pred, zero_division=0),
        "accuracy": accuracy_score(y_true, y_pred),
        "brier_score": brier_score_loss(y_true, y_proba),
        "positive_rate": y_pred.mean(),
        "true_positive_rate": (y_true == 1).sum() / len(y_true),
        "threshold": threshold,
        "n_samples": len(y_true),
        "n_positive": int(y_true.sum()),
    }


def find_optimal_threshold(y_true: np.ndarray, y_proba: np.ndarray,
                             metric: str = "f1") -> tuple[float, float]:
    """
    Find the threshold that maximizes a given metric.
    Returns (optimal_threshold, best_score).
    """
    thresholds = np.linspace(0.01, 0.99, 200)
    best_score, best_threshold = -1, 0.5

    for t in thresholds:
        y_pred = (y_proba >= t).astype(int)
        if metric == "f1":
            score = f1_score(y_true, y_pred, zero_division=0)
        elif metric == "precision":
            score = precision_score(y_true, y_pred, zero_division=0)
        elif metric == "recall":
            score = recall_score(y_true, y_pred, zero_division=0)
        else:
            score = f1_score(y_true, y_pred, zero_division=0)

        if score > best_score:
            best_score = score
            best_threshold = t

    return best_threshold, best_score


# ──────────────────────────────────────────────
# Visualization
# ──────────────────────────────────────────────

def plot_roc_curve(y_true: np.ndarray, y_proba: np.ndarray,
                   output_path: str, label: str = "Model"):
    """Plot ROC curve with AUC annotation."""
    try:
        import matplotlib.pyplot as plt
    except ImportError:
        logger.warning("matplotlib not installed; skipping plots")
        return

    fpr, tpr, _ = roc_curve(y_true, y_proba)
    auc = roc_auc_score(y_true, y_proba)

    plt.figure(figsize=(7, 6))
    plt.plot(fpr, tpr, lw=2, label=f"{label} (AUC = {auc:.4f})")
    plt.plot([0, 1], [0, 1], "k--", alpha=0.5, label="Random classifier")
    plt.fill_between(fpr, tpr, alpha=0.1)
    plt.xlabel("False Positive Rate")
    plt.ylabel("True Positive Rate")
    plt.title("ROC Curve")
    plt.legend(loc="lower right")
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close()
    logger.info(f"ROC curve saved: {output_path}")


def plot_precision_recall_curve(y_true: np.ndarray, y_proba: np.ndarray,
                                  output_path: str):
    """Plot Precision-Recall curve (better for imbalanced datasets)."""
    try:
        import matplotlib.pyplot as plt
    except ImportError:
        return

    precision, recall, _ = precision_recall_curve(y_true, y_proba)
    auc_pr = average_precision_score(y_true, y_proba)
    baseline = y_true.mean()

    plt.figure(figsize=(7, 6))
    plt.plot(recall, precision, lw=2, label=f"Model (AUC-PR = {auc_pr:.4f})")
    plt.axhline(y=baseline, color="k", linestyle="--", alpha=0.5,
                label=f"Baseline (prevalence = {baseline:.3f})")
    plt.xlabel("Recall")
    plt.ylabel("Precision")
    plt.title("Precision-Recall Curve")
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close()
    logger.info(f"PR curve saved: {output_path}")


def plot_confusion_matrix(y_true: np.ndarray, y_pred: np.ndarray,
                           output_path: str, labels: Optional[list] = None):
    """Plot confusion matrix with counts and percentages."""
    try:
        import matplotlib.pyplot as plt
        import seaborn as sns
    except ImportError:
        return

    cm = confusion_matrix(y_true, y_pred)
    cm_normalized = cm.astype(float) / cm.sum(axis=1, keepdims=True)

    labels = labels or ["Negative", "Positive"]
    annotations = np.array([
        [f"{count}\n({pct:.1%})" for count, pct in zip(row_counts, row_pcts)]
        for row_counts, row_pcts in zip(cm, cm_normalized)
    ])

    plt.figure(figsize=(6, 5))
    sns.heatmap(cm, annot=annotations, fmt="", cmap="Blues",
                xticklabels=[f"Pred {l}" for l in labels],
                yticklabels=[f"True {l}" for l in labels])
    plt.title("Confusion Matrix")
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close()
    logger.info(f"Confusion matrix saved: {output_path}")


def plot_calibration_curve(y_true: np.ndarray, y_proba: np.ndarray,
                            output_path: str):
    """Plot calibration curve to check if predicted probabilities are reliable."""
    try:
        import matplotlib.pyplot as plt
    except ImportError:
        return

    prob_true, prob_pred = calibration_curve(y_true, y_proba, n_bins=10)

    plt.figure(figsize=(7, 6))
    plt.plot(prob_pred, prob_true, "s-", label="Model", linewidth=2)
    plt.plot([0, 1], [0, 1], "k--", alpha=0.7, label="Perfectly calibrated")
    plt.xlabel("Mean predicted probability")
    plt.ylabel("Fraction of positives")
    plt.title("Calibration Curve")
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close()
    logger.info(f"Calibration curve saved: {output_path}")


def plot_score_distribution(y_true: np.ndarray, y_proba: np.ndarray,
                              output_path: str, threshold: float = 0.5):
    """Plot predicted probability distributions split by true label."""
    try:
        import matplotlib.pyplot as plt
    except ImportError:
        return

    plt.figure(figsize=(8, 5))
    plt.hist(y_proba[y_true == 0], bins=50, alpha=0.6, label="Negative (true)",
             color="steelblue", density=True)
    plt.hist(y_proba[y_true == 1], bins=50, alpha=0.6, label="Positive (true)",
             color="salmon", density=True)
    plt.axvline(threshold, color="k", linestyle="--", label=f"Threshold ({threshold})")
    plt.xlabel("Predicted probability")
    plt.ylabel("Density")
    plt.title("Score Distribution by True Label")
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close()
    logger.info(f"Score distribution saved: {output_path}")


# ──────────────────────────────────────────────
# Error Analysis
# ──────────────────────────────────────────────

def run_error_analysis(X_test: pd.DataFrame, y_true: np.ndarray,
                        y_pred: np.ndarray, y_proba: np.ndarray,
                        output_path: str) -> pd.DataFrame:
    """
    Build an error analysis DataFrame with prediction metadata.
    Returns the full annotated test DataFrame for manual inspection.
    """
    results = X_test.copy()
    results["y_true"] = y_true
    results["y_pred"] = y_pred
    results["y_proba"] = y_proba
    results["confidence"] = np.where(y_proba >= 0.5, y_proba, 1 - y_proba)

    results["error_type"] = "correct"
    results.loc[(results.y_true == 1) & (results.y_pred == 0), "error_type"] = "false_negative"
    results.loc[(results.y_true == 0) & (results.y_pred == 1), "error_type"] = "false_positive"

    # High-confidence errors are the most egregious — inspect these first
    results["high_confidence_error"] = (
        (results["error_type"] != "correct") &
        (results["confidence"] > 0.8)
    ).astype(int)

    error_summary = results["error_type"].value_counts()
    logger.info(f"\nError Analysis Summary:\n{error_summary.to_string()}")

    n_high_conf = results["high_confidence_error"].sum()
    logger.info(f"High-confidence errors: {n_high_conf} ({n_high_conf/len(results):.2%})")

    results.to_csv(output_path, index=False)
    logger.info(f"Error analysis saved: {output_path}")

    return results


# ──────────────────────────────────────────────
# Fairness Evaluation
# ──────────────────────────────────────────────

def evaluate_fairness(X_test: pd.DataFrame, y_true: np.ndarray,
                       y_pred: np.ndarray, sensitive_col: str) -> dict:
    """
    Evaluate model fairness across a sensitive demographic attribute.
    Returns a dict with per-group metrics.
    """
    if sensitive_col not in X_test.columns:
        logger.warning(f"Sensitive column '{sensitive_col}' not in DataFrame")
        return {}

    fairness_report = {}

    for value in X_test[sensitive_col].unique():
        mask = X_test[sensitive_col] == value
        if mask.sum() < 20:
            continue

        group_true = y_true[mask.values]
        group_pred = y_pred[mask.values]

        tn, fp, fn, tp = confusion_matrix(
            group_true, group_pred, labels=[0, 1]
        ).ravel()

        fairness_report[str(value)] = {
            "n": int(mask.sum()),
            "positive_rate": float(group_pred.mean()),
            "true_positive_rate": float(tp / (tp + fn)) if (tp + fn) > 0 else 0,
            "false_positive_rate": float(fp / (fp + tn)) if (fp + tn) > 0 else 0,
            "precision": float(tp / (tp + fp)) if (tp + fp) > 0 else 0,
            "accuracy": float((tp + tn) / (tp + tn + fp + fn)),
        }

    # Print summary table
    print(f"\n=== Fairness Report: {sensitive_col} ===")
    print(f"{'Group':<20} {'N':>6} {'Pos Rate':>10} {'TPR':>8} {'FPR':>8} {'Precision':>10}")
    print("-" * 65)
    for group, metrics in fairness_report.items():
        print(f"{str(group):<20} {metrics['n']:>6} "
              f"{metrics['positive_rate']:>10.3f} "
              f"{metrics['true_positive_rate']:>8.3f} "
              f"{metrics['false_positive_rate']:>8.3f} "
              f"{metrics['precision']:>10.3f}")

    return fairness_report


# ──────────────────────────────────────────────
# SHAP Feature Importance
# ──────────────────────────────────────────────

def run_shap_analysis(model, X_test: pd.DataFrame, output_dir: str,
                       n_samples: int = 500) -> Optional[np.ndarray]:
    """Compute SHAP values and save summary plots."""
    try:
        import shap
        import matplotlib.pyplot as plt
    except ImportError:
        logger.warning("shap or matplotlib not installed; skipping SHAP analysis")
        return None

    sample = X_test.sample(min(n_samples, len(X_test)), random_state=42)
    output_dir = Path(output_dir)

    try:
        # Try TreeExplainer first (fast for tree-based models)
        try:
            explainer = shap.TreeExplainer(model)
            shap_values = explainer.shap_values(sample)
            if isinstance(shap_values, list):
                # For multiclass or binary sklearn models, take the positive class
                shap_values = shap_values[1]
        except Exception:
            # Fall back to KernelExplainer (model-agnostic, slower)
            background = shap.sample(X_test, 100)
            explainer = shap.KernelExplainer(
                model.predict_proba if hasattr(model, "predict_proba") else model.predict,
                background
            )
            shap_values = explainer.shap_values(sample)
            if isinstance(shap_values, list):
                shap_values = shap_values[1]

        # Summary bar plot
        plt.figure()
        shap.summary_plot(shap_values, sample, plot_type="bar", show=False,
                           max_display=20)
        plt.tight_layout()
        plt.savefig(output_dir / "shap_importance.png", dpi=150, bbox_inches="tight")
        plt.close()

        # Beeswarm plot
        plt.figure()
        shap.summary_plot(shap_values, sample, show=False, max_display=20)
        plt.tight_layout()
        plt.savefig(output_dir / "shap_beeswarm.png", dpi=150, bbox_inches="tight")
        plt.close()

        logger.info(f"SHAP analysis saved to {output_dir}")

        # Return global feature importance (mean |SHAP value|)
        return np.abs(shap_values).mean(axis=0)

    except Exception as e:
        logger.warning(f"SHAP analysis failed: {e}")
        return None


# ──────────────────────────────────────────────
# Full Evaluation Pipeline
# ──────────────────────────────────────────────

def run_full_evaluation(
    model_path: str,
    test_path: str,
    output_dir: str,
    target_col: str = "target",
    threshold: float = 0.5,
    sensitive_col: Optional[str] = None,
) -> dict:
    """
    Run the complete evaluation suite and save all reports.
    Returns a metrics dict suitable for logging to MLflow.
    """
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)

    # Load model and data
    logger.info(f"Loading model: {model_path}")
    model = joblib.load(model_path)

    logger.info(f"Loading test data: {test_path}")
    test_df = pd.read_csv(test_path)
    y_true = test_df[target_col].values
    X_test = test_df.drop(columns=[target_col])

    # Predictions
    y_pred = model.predict(X_test)
    y_proba = (
        model.predict_proba(X_test)[:, 1]
        if hasattr(model, "predict_proba")
        else model.predict(X_test).astype(float)
    )
    y_pred_at_threshold = (y_proba >= threshold).astype(int)

    # Core metrics
    metrics = compute_all_metrics(y_true, y_pred_at_threshold, y_proba, threshold)
    logger.info(f"\nCore Metrics:")
    for k, v in metrics.items():
        if isinstance(v, float):
            logger.info(f"  {k}: {v:.4f}")

    # Classification report
    print(f"\n{classification_report(y_true, y_pred_at_threshold)}")

    # Find optimal threshold
    opt_threshold, opt_f1 = find_optimal_threshold(y_true, y_proba, "f1")
    logger.info(f"Optimal threshold (max F1): {opt_threshold:.3f} → F1 = {opt_f1:.4f}")
    metrics["optimal_threshold"] = opt_threshold
    metrics["optimal_f1"] = opt_f1

    # Generate plots
    plot_roc_curve(y_true, y_proba, str(output / "roc_curve.png"))
    plot_precision_recall_curve(y_true, y_proba, str(output / "pr_curve.png"))
    plot_confusion_matrix(y_true, y_pred_at_threshold,
                          str(output / "confusion_matrix.png"))
    plot_calibration_curve(y_true, y_proba, str(output / "calibration.png"))
    plot_score_distribution(y_true, y_proba,
                            str(output / "score_distribution.png"), threshold)

    # Error analysis
    error_df = run_error_analysis(
        X_test, y_true, y_pred_at_threshold, y_proba,
        str(output / "error_analysis.csv")
    )

    # Fairness evaluation
    if sensitive_col:
        fairness_report = evaluate_fairness(X_test, y_true, y_pred_at_threshold,
                                             sensitive_col)
        with open(output / "fairness_report.json", "w") as f:
            json.dump(fairness_report, f, indent=2)

    # SHAP analysis
    try:
        base_model = (model.named_steps.get("model") or
                      model.named_steps.get("classifier") or model)
        shap_importance = run_shap_analysis(base_model, X_test, str(output))
        if shap_importance is not None:
            top_features = pd.Series(
                shap_importance, index=X_test.columns
            ).sort_values(ascending=False).head(10)
            logger.info(f"\nTop 10 features by SHAP importance:\n{top_features.to_string()}")
    except Exception as e:
        logger.debug(f"SHAP skipped: {e}")

    # Save metrics JSON
    with open(output / "metrics.json", "w") as f:
        json.dump({k: float(v) if isinstance(v, (float, np.floating)) else v
                   for k, v in metrics.items()}, f, indent=2)

    logger.info(f"\nAll evaluation artifacts saved to: {output}")
    return metrics


# ──────────────────────────────────────────────
# CLI Entry Point
# ──────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Comprehensive model evaluation")
    parser.add_argument("--model", required=True, help="Path to trained model (.pkl)")
    parser.add_argument("--test", required=True, help="Path to test features CSV")
    parser.add_argument("--target", default="target", help="Target column name")
    parser.add_argument("--output", default="reports/", help="Output directory for reports")
    parser.add_argument("--threshold", type=float, default=0.5, help="Classification threshold")
    parser.add_argument("--sensitive-col", default=None,
                        help="Column name for fairness analysis")
    args = parser.parse_args()

    metrics = run_full_evaluation(
        model_path=args.model,
        test_path=args.test,
        output_dir=args.output,
        target_col=args.target,
        threshold=args.threshold,
        sensitive_col=args.sensitive_col,
    )

    print(f"\n{'='*50}")
    print("FINAL TEST METRICS")
    print(f"{'='*50}")
    for k, v in metrics.items():
        if isinstance(v, float):
            print(f"  {k:<25} {v:.4f}")


if __name__ == "__main__":
    main()
