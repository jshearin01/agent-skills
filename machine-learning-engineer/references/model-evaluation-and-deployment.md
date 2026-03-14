# Model Evaluation and Deployment Guide

## Table of Contents
1. [Evaluation Strategy](#evaluation-strategy)
2. [Metrics by Task Type](#metrics-by-task-type)
3. [Error Analysis](#error-analysis)
4. [Model Fairness](#model-fairness)
5. [Deployment Patterns](#deployment-patterns)
6. [Serving with FastAPI](#serving-with-fastapi)
7. [Containerization](#containerization)
8. [Deployment Strategies](#deployment-strategies)

---

## Evaluation Strategy

### The Golden Rules

1. **Split once, evaluate once**: Define your train/val/test split before any modeling. The test set is used exactly once — at the final evaluation. Never tune on the test set.
2. **Match your evaluation to your deployment**: Evaluate under conditions that mirror production (same latency constraints, same input format, same class distribution).
3. **Baseline first**: Always compare against a naive baseline. If your model doesn't beat it, you have a data problem.
4. **Business metrics beat ML metrics**: A model with lower AUC that improves revenue is better than a model with higher AUC that doesn't.

### Splitting Strategies

```python
import pandas as pd
from sklearn.model_selection import train_test_split, StratifiedKFold, TimeSeriesSplit

# Standard random split (for i.i.d. data)
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y  # stratify for classification
)

# Temporal split (for time-series / event data — CRITICAL for avoiding leakage)
# Sort by time, then split — never shuffle
df_sorted = df.sort_values("event_date")
cutoff = df_sorted["event_date"].quantile(0.8)
train_df = df_sorted[df_sorted["event_date"] <= cutoff]
test_df = df_sorted[df_sorted["event_date"] > cutoff]

# Group-aware split (prevent same user/entity appearing in both train and test)
from sklearn.model_selection import GroupShuffleSplit
gss = GroupShuffleSplit(n_splits=1, test_size=0.2, random_state=42)
train_idx, test_idx = next(gss.split(X, y, groups=df["user_id"]))

# Nested cross-validation (for model selection + evaluation without data leakage)
outer_cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
inner_cv = StratifiedKFold(n_splits=3, shuffle=True, random_state=42)
```

---

## Metrics by Task Type

### Binary Classification

```python
from sklearn.metrics import (
    roc_auc_score, average_precision_score, f1_score,
    precision_score, recall_score, accuracy_score,
    confusion_matrix, classification_report, brier_score_loss
)
import matplotlib.pyplot as plt
from sklearn.calibration import calibration_curve

def evaluate_binary_classifier(model, X_test, y_test, threshold=0.5):
    y_proba = model.predict_proba(X_test)[:, 1]
    y_pred = (y_proba >= threshold).astype(int)

    metrics = {
        "AUC-ROC": roc_auc_score(y_test, y_proba),
        "AUC-PR": average_precision_score(y_test, y_proba),   # Better for imbalanced
        "F1": f1_score(y_test, y_pred),
        "Precision": precision_score(y_test, y_pred),
        "Recall": recall_score(y_test, y_pred),
        "Accuracy": accuracy_score(y_test, y_pred),
        "Brier Score": brier_score_loss(y_test, y_proba),     # Calibration quality
    }

    print(classification_report(y_test, y_pred))
    print(f"\nConfusion Matrix:\n{confusion_matrix(y_test, y_pred)}")
    print("\nDetailed Metrics:")
    for k, v in metrics.items():
        print(f"  {k}: {v:.4f}")

    return metrics

# When to use which metric:
# AUC-ROC: general ranking quality, insensitive to threshold
# AUC-PR: better for highly imbalanced datasets (e.g., fraud: 0.1% positive rate)
# F1: when FP and FN have equal cost and you need a single threshold metric
# Precision/Recall: when FP and FN have different costs
# Brier Score: evaluating probability calibration
```

### Multiclass Classification

```python
from sklearn.metrics import (
    f1_score, accuracy_score, cohen_kappa_score,
    confusion_matrix, classification_report
)

# Macro avg: equal weight per class (good for balanced classes)
# Weighted avg: weight by class support (good for imbalanced classes)
# Micro avg: global TP/FP/FN aggregation

f1_macro = f1_score(y_test, y_pred, average="macro")
f1_weighted = f1_score(y_test, y_pred, average="weighted")

# Cohen's Kappa: accounts for chance agreement (important for ordinal labels)
kappa = cohen_kappa_score(y_test, y_pred, weights="quadratic")

print(classification_report(y_test, y_pred))
```

### Regression

```python
from sklearn.metrics import (
    mean_absolute_error, mean_squared_error, r2_score,
    mean_absolute_percentage_error
)
import numpy as np

def evaluate_regressor(model, X_test, y_test):
    y_pred = model.predict(X_test)

    metrics = {
        "MAE": mean_absolute_error(y_test, y_pred),
        "RMSE": np.sqrt(mean_squared_error(y_test, y_pred)),
        "MAPE": mean_absolute_percentage_error(y_test, y_pred),
        "R²": r2_score(y_test, y_pred),
    }

    # Residual plot (critical for diagnosing systematic errors)
    residuals = y_test - y_pred
    plt.figure(figsize=(10, 4))
    plt.scatter(y_pred, residuals, alpha=0.5)
    plt.axhline(0, color="r", linestyle="--")
    plt.xlabel("Predicted values")
    plt.ylabel("Residuals")
    plt.title("Residual Plot")
    plt.savefig("reports/residual_plot.png")

    return metrics
```

### Ranking / Recommendation

```python
# NDCG (Normalized Discounted Cumulative Gain): accounts for position
from sklearn.metrics import ndcg_score

ndcg = ndcg_score(y_true_relevance.reshape(1, -1), y_scores.reshape(1, -1), k=10)

# Mean Reciprocal Rank
def mean_reciprocal_rank(ranks):
    return np.mean([1 / r for r in ranks if r > 0])

# Precision@K and Recall@K
def precision_at_k(y_true, y_scores, k=10):
    top_k = np.argsort(-y_scores)[:k]
    return y_true[top_k].sum() / k
```

---

## Error Analysis

Error analysis reveals where and why your model fails — this drives better feature engineering and data collection.

```python
import pandas as pd
import numpy as np

def error_analysis(model, X_test, y_test, feature_names, threshold=0.5):
    """Comprehensive error analysis."""
    y_proba = model.predict_proba(X_test)[:, 1]
    y_pred = (y_proba >= threshold).astype(int)

    results = pd.DataFrame(X_test, columns=feature_names)
    results["y_true"] = y_test.values
    results["y_pred"] = y_pred
    results["y_proba"] = y_proba
    results["error_type"] = "correct"
    results.loc[(results.y_true == 1) & (results.y_pred == 0), "error_type"] = "false_negative"
    results.loc[(results.y_true == 0) & (results.y_pred == 1), "error_type"] = "false_positive"

    print("Error breakdown:")
    print(results["error_type"].value_counts())

    # High-confidence errors (most worth investigating)
    high_conf_errors = results[
        (results["error_type"] != "correct") &
        (results["y_proba"].between(0.1, 0.9) == False)
    ]
    print(f"\nHigh-confidence errors: {len(high_conf_errors)}")

    # Feature statistics by error type
    print("\nFeature means by error type:")
    print(results.groupby("error_type")[feature_names[:5]].mean())

    return results

# SHAP explanations for individual predictions
import shap

def explain_predictions(model, X, feature_names, n_samples=100):
    explainer = shap.TreeExplainer(model)
    shap_values = explainer.shap_values(X[:n_samples])

    # Global feature importance
    shap.summary_plot(shap_values, X[:n_samples],
                       feature_names=feature_names, show=False)
    plt.savefig("reports/shap_summary.png", bbox_inches="tight")

    # Dependence plots for top features
    top_features = np.abs(shap_values).mean(axis=0).argsort()[-3:][::-1]
    for feat_idx in top_features:
        shap.dependence_plot(feat_idx, shap_values, X[:n_samples],
                              feature_names=feature_names, show=False)
        plt.savefig(f"reports/shap_dependence_{feature_names[feat_idx]}.png",
                    bbox_inches="tight")
```

---

## Model Fairness

```python
from sklearn.metrics import confusion_matrix

def evaluate_fairness(model, X_test, y_test, sensitive_col, sensitive_values):
    """Evaluate model fairness across demographic groups."""
    y_pred = model.predict(X_test)

    print("=== Fairness Report ===")
    for value in sensitive_values:
        mask = X_test[sensitive_col] == value
        if mask.sum() < 10:
            continue

        group_y_true = y_test[mask]
        group_y_pred = y_pred[mask]

        tn, fp, fn, tp = confusion_matrix(group_y_true, group_y_pred).ravel()

        tpr = tp / (tp + fn) if (tp + fn) > 0 else 0   # True Positive Rate (Recall)
        fpr = fp / (fp + tn) if (fp + tn) > 0 else 0   # False Positive Rate
        ppv = tp / (tp + fp) if (tp + fp) > 0 else 0   # Precision

        print(f"\nGroup: {sensitive_col}={value} (n={mask.sum()})")
        print(f"  TPR (Recall): {tpr:.3f}")
        print(f"  FPR: {fpr:.3f}")
        print(f"  Precision: {ppv:.3f}")
        print(f"  Positive Rate: {group_y_pred.mean():.3f}")

# Key fairness criteria:
# Demographic Parity: equal positive prediction rate across groups
# Equal Opportunity: equal TPR across groups
# Equalized Odds: equal TPR AND FPR across groups
# Individual Fairness: similar individuals are treated similarly
```

---

## Deployment Patterns

### Choosing a Serving Pattern

| Pattern | Use Case | Latency | Throughput |
|---|---|---|---|
| **REST API** (sync) | Real-time predictions, interactive apps | <100ms | Medium |
| **Batch inference** | Nightly scoring, large datasets | Minutes-hours | Very high |
| **Streaming** (Kafka) | Event-driven, continuous predictions | ~1s | High |
| **Edge/mobile** | Offline, privacy-sensitive | <10ms | N/A |
| **Async queue** | Heavy models, variable load | Seconds | High |

---

## Serving with FastAPI

```python
# src/serving/app.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import mlflow.pyfunc
import pandas as pd
import time
import logging

logger = logging.getLogger(__name__)
app = FastAPI(title="ML Model API", version="1.0.0")

# Load model at startup (not per-request)
MODEL_VERSION = "Production"
MODEL_NAME = "FraudDetector"

@app.on_event("startup")
async def load_model():
    global model
    model = mlflow.pyfunc.load_model(f"models:/{MODEL_NAME}/{MODEL_VERSION}")
    logger.info(f"Loaded {MODEL_NAME} version {MODEL_VERSION}")

class PredictionRequest(BaseModel):
    amount: float
    merchant_category: str
    hour: int
    day_of_week: int
    country: str

class PredictionResponse(BaseModel):
    prediction: int
    probability: float
    model_version: str
    latency_ms: float

@app.post("/predict", response_model=PredictionResponse)
def predict(request: PredictionRequest):
    start = time.time()
    try:
        df = pd.DataFrame([request.dict()])
        result = model.predict(df)
        proba = float(result[0]) if hasattr(result[0], "__float__") else 0.5

        return PredictionResponse(
            prediction=int(proba >= 0.5),
            probability=proba,
            model_version=MODEL_VERSION,
            latency_ms=(time.time() - start) * 1000,
        )
    except Exception as e:
        logger.error(f"Prediction error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
def health_check():
    return {"status": "healthy", "model": MODEL_NAME, "version": MODEL_VERSION}

@app.get("/model-info")
def model_info():
    return {
        "model_name": MODEL_NAME,
        "model_version": MODEL_VERSION,
        "features": list(PredictionRequest.__fields__.keys()),
    }
```

---

## Containerization

```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies first (leverages Docker layer caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY src/serving/ ./serving/
COPY configs/ ./configs/

# Create non-root user for security
RUN useradd --create-home appuser && chown -R appuser /app
USER appuser

ENV PORT=8080
EXPOSE ${PORT}

CMD ["uvicorn", "serving.app:app", "--host", "0.0.0.0", "--port", "8080",
     "--workers", "4", "--timeout-keep-alive", "30"]
```

```yaml
# docker-compose.yml for local testing
services:
  model-api:
    build: .
    ports:
      - "8080:8080"
    environment:
      MLFLOW_TRACKING_URI: http://mlflow:5000
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8080/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 20s
```

---

## Deployment Strategies

### Blue-Green Deployment

Run two identical production environments. Switch traffic instantly; rollback by switching back.

```bash
# Kubernetes blue-green with kubectl
# Deploy new version (green) while old (blue) still serves traffic
kubectl apply -f k8s/deployment-green.yaml

# Test green environment
kubectl port-forward svc/model-api-green 8080:80

# Switch traffic to green
kubectl patch service model-api -p '{"spec":{"selector":{"version":"green"}}}'

# Rollback if needed
kubectl patch service model-api -p '{"spec":{"selector":{"version":"blue"}}}'
```

### Canary Deployment

Gradually shift traffic to the new model, monitoring metrics at each step.

```yaml
# Istio virtual service for canary routing
apiVersion: networking.istio.io/v1alpha3
kind: VirtualService
metadata:
  name: model-api
spec:
  http:
    - route:
        - destination:
            host: model-api-v1
          weight: 90   # 90% to stable
        - destination:
            host: model-api-v2
          weight: 10   # 10% to canary
```

### Shadow Mode / Challenger Model

Run the new model in parallel, logging predictions but not serving them — zero risk A/B testing.

```python
# Shadow mode in the serving layer
def predict_with_shadow(features: dict):
    # Production model serves the response
    production_response = production_model.predict(features)

    # Shadow model runs silently
    try:
        shadow_response = shadow_model.predict(features)
        # Log for offline comparison
        log_shadow_prediction(
            features=features,
            production_pred=production_response,
            shadow_pred=shadow_response,
        )
    except Exception as e:
        logger.warning(f"Shadow model failed: {e}")  # Never block production

    return production_response
```

### A/B Testing

Statistically compare two models using user-level random assignment.

```python
import hashlib

def get_model_for_user(user_id: str, traffic_split: float = 0.5) -> str:
    """Deterministically assign users to model A or B."""
    hash_val = int(hashlib.md5(user_id.encode()).hexdigest(), 16)
    return "model_b" if (hash_val % 100) < (traffic_split * 100) else "model_a"
```

### Rollback Procedure

```python
# Automated rollback script
def rollback_to_previous_production(model_name: str):
    """Roll back to the most recently archived model version."""
    client = MlflowClient()

    # Get current production version
    current_prod = client.get_latest_versions(model_name, stages=["Production"])
    if not current_prod:
        raise ValueError("No production model found")

    # Get the most recent archived version
    archived = client.get_latest_versions(model_name, stages=["Archived"])
    if not archived:
        raise ValueError("No archived model to roll back to")

    rollback_version = max(archived, key=lambda v: int(v.version))

    # Demote current production to archived
    client.transition_model_version_stage(
        name=model_name,
        version=current_prod[0].version,
        stage="Archived",
    )

    # Restore previous version to production
    client.transition_model_version_stage(
        name=model_name,
        version=rollback_version.version,
        stage="Production",
    )

    logger.critical(
        f"ROLLBACK: {model_name} reverted from v{current_prod[0].version} "
        f"to v{rollback_version.version}"
    )
```
