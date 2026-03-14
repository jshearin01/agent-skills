# MLOps Tools and Workflow Guide

## Table of Contents
1. [MLflow — Experiment Tracking & Registry](#mlflow)
2. [DVC — Data & Pipeline Versioning](#dvc)
3. [Model Registry Lifecycle](#model-registry-lifecycle)
4. [CI/CD for Machine Learning](#cicd-for-ml)
5. [Pipeline Orchestration](#pipeline-orchestration)
6. [Drift Detection & Monitoring](#drift-detection--monitoring)
7. [Recommended MLOps Stack by Team Size](#recommended-stack)

---

## MLflow — Experiment Tracking & Registry

MLflow is the de facto open-source standard for ML experiment management (17M+ monthly downloads as of 2026).

### Production Setup

```yaml
# docker-compose.yml — production MLflow server
services:
  mlflow-server:
    image: ghcr.io/mlflow/mlflow:v2.20.0
    ports:
      - "5000:5000"
    environment:
      MLFLOW_BACKEND_STORE_URI: "postgresql://mlflow:${DB_PASSWORD}@postgres:5432/mlflowdb"
      MLFLOW_DEFAULT_ARTIFACT_ROOT: "s3://mlflow-artifacts-prod/"
    command: >
      mlflow server
        --backend-store-uri postgresql://mlflow:${DB_PASSWORD}@postgres:5432/mlflowdb
        --default-artifact-root s3://mlflow-artifacts-prod/
        --host 0.0.0.0
        --port 5000
        --workers 4
  postgres:
    image: postgres:16-alpine
    environment:
      POSTGRES_USER: mlflow
      POSTGRES_PASSWORD: "${DB_PASSWORD}"
      POSTGRES_DB: mlflowdb
```

### Non-Negotiable Logging Per Run

```python
import mlflow
import mlflow.sklearn
from mlflow.models import infer_signature
import subprocess

def get_git_hash():
    return subprocess.check_output(["git", "rev-parse", "HEAD"]).decode().strip()

def get_dvc_data_hash(data_path):
    """Get the DVC hash of the data file."""
    try:
        return subprocess.check_output(
            ["dvc", "status", data_path]
        ).decode().strip()
    except Exception:
        return "unknown"

mlflow.set_tracking_uri("http://mlflow.internal:5000")
mlflow.set_experiment("fraud-detection-v3")

with mlflow.start_run(tags={
    "git_commit": get_git_hash(),
    "data_version": get_dvc_data_hash("data/features/train.csv"),
    "team": "ml-platform",
    "task_type": "binary_classification",
}):
    # Log all hyperparameters
    mlflow.log_params(params)
    mlflow.log_param("n_training_samples", len(X_train))
    mlflow.log_param("n_features", X_train.shape[1])
    mlflow.log_param("python_version", sys.version)

    # Train
    model.fit(X_train, y_train)
    y_pred = model.predict(X_val)
    y_proba = model.predict_proba(X_val)[:, 1]

    # Log all metrics
    mlflow.log_metrics({
        "val_auc": roc_auc_score(y_val, y_proba),
        "val_f1": f1_score(y_val, y_pred),
        "val_precision": precision_score(y_val, y_pred),
        "val_recall": recall_score(y_val, y_pred),
        "train_auc": roc_auc_score(y_train, model.predict_proba(X_train)[:, 1]),
    })

    # Log artifacts
    mlflow.log_artifact("reports/confusion_matrix.png")
    mlflow.log_artifact("reports/feature_importance.html")
    mlflow.log_artifact("configs/params.yaml")

    # Log the model with signature and input example
    signature = infer_signature(X_train, model.predict(X_train))
    mlflow.sklearn.log_model(
        model,
        artifact_path="model",
        signature=signature,
        input_example=X_train.iloc[:5],
        registered_model_name="FraudDetector",
    )
```

### Model Registry Promotion Workflow

```python
from mlflow.tracking import MlflowClient

client = MlflowClient()

def promote_to_production(model_name: str, version: int, approved_by: str,
                           min_auc: float = 0.90):
    """Promote a model to production with automated gates and audit trail."""

    # Fetch the candidate version and verify metrics
    run_id = client.get_model_version(model_name, version).run_id
    run = client.get_run(run_id)
    val_auc = float(run.data.metrics.get("val_auc", 0))

    if val_auc < min_auc:
        raise ValueError(
            f"Model AUC {val_auc:.3f} below threshold {min_auc}. Promotion blocked."
        )

    # Archive the current production model
    current = client.get_latest_versions(model_name, stages=["Production"])
    for prod_model in current:
        client.transition_model_version_stage(
            name=model_name,
            version=prod_model.version,
            stage="Archived",
        )

    # Promote new version to production
    client.transition_model_version_stage(
        name=model_name,
        version=version,
        stage="Production",
        archive_existing_versions=False,  # already done above
    )

    # Add governance metadata
    import pandas as pd
    client.set_model_version_tag(model_name, version, "approved_by", approved_by)
    client.set_model_version_tag(model_name, version, "promoted_at",
                                  pd.Timestamp.now().isoformat())
    client.set_model_version_tag(model_name, version, "val_auc_at_promotion",
                                  str(val_auc))

    print(f"Model {model_name} version {version} promoted to Production by {approved_by}")
    print(f"Validation AUC: {val_auc:.4f}")
```

---

## DVC — Data & Pipeline Versioning

DVC is "Git for data" — it versions large files and defines reproducible ML pipelines.

### Initial Setup

```bash
git init
dvc init

# Configure remote storage (S3, GCS, Azure, SSH)
dvc remote add -d myremote s3://my-ml-bucket/dvc-cache
dvc remote modify myremote region us-east-1

# Track your first dataset
dvc add data/raw/transactions.csv
git add data/raw/transactions.csv.dvc .gitignore
git commit -m "Track raw transactions data with DVC"
dvc push
```

### Pipeline Definition (dvc.yaml)

```yaml
# dvc.yaml — define each pipeline stage
stages:
  prepare:
    cmd: python src/data/prepare.py
    deps:
      - src/data/prepare.py
      - data/raw/transactions.csv
    params:
      - params.yaml:
          - prepare.test_size
          - prepare.random_seed
    outs:
      - data/processed/train.csv
      - data/processed/val.csv
      - data/processed/test.csv

  featurize:
    cmd: python src/features/build_features.py
    deps:
      - src/features/build_features.py
      - data/processed/train.csv
      - data/processed/val.csv
    outs:
      - data/features/train_features.csv
      - data/features/val_features.csv
      - models/preprocessor.pkl

  train:
    cmd: python src/models/train.py
    deps:
      - src/models/train.py
      - data/features/train_features.csv
      - models/preprocessor.pkl
    params:
      - params.yaml:
          - train.n_estimators
          - train.max_depth
          - train.learning_rate
    outs:
      - models/model.pkl
    metrics:
      - reports/metrics.json:
          cache: false

  evaluate:
    cmd: python src/evaluation/evaluate.py
    deps:
      - src/evaluation/evaluate.py
      - models/model.pkl
      - data/features/val_features.csv
    metrics:
      - reports/eval_metrics.json:
          cache: false
    plots:
      - reports/confusion_matrix.csv:
          cache: false
```

### Running the Pipeline

```bash
# Run the full pipeline (only re-runs changed stages)
dvc repro

# Run a specific stage
dvc repro train

# Compare experiments
dvc exp run --set-param train.n_estimators=200
dvc exp show  # tabular comparison of all experiments

# Switch back to a previous data version
git checkout v1.0
dvc checkout
```

---

## CI/CD for ML

### GitHub Actions Workflow

```yaml
# .github/workflows/ml-pipeline.yml
name: ML Training Pipeline

on:
  push:
    paths:
      - 'src/**'
      - 'params.yaml'
      - 'dvc.yaml'
  workflow_dispatch:

jobs:
  train-and-evaluate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"

      - name: Install dependencies
        run: pip install -r requirements.txt

      - name: Configure DVC remote
        run: |
          dvc remote modify myremote access_key_id ${{ secrets.AWS_ACCESS_KEY_ID }}
          dvc remote modify myremote secret_access_key ${{ secrets.AWS_SECRET_ACCESS_KEY }}

      - name: Pull data
        run: dvc pull data/features/

      - name: Run pipeline
        env:
          MLFLOW_TRACKING_URI: ${{ secrets.MLFLOW_TRACKING_URI }}
        run: dvc repro train evaluate

      - name: Gate on performance
        run: |
          python scripts/check_performance_gate.py \
            --metrics-file reports/eval_metrics.json \
            --min-auc 0.88 \
            --max-latency-ms 50

      - name: Register model if gate passes
        if: github.ref == 'refs/heads/main'
        env:
          MLFLOW_TRACKING_URI: ${{ secrets.MLFLOW_TRACKING_URI }}
        run: python scripts/register_model.py
```

---

## Pipeline Orchestration

### When to Use Each Tool

| Tool | Best For | Key Feature |
|---|---|---|
| **Apache Airflow** | Data engineering, complex DAGs, mature teams | Rich UI, extensive operators |
| **Kubeflow Pipelines** | Kubernetes-native, containerized steps | Native K8s, strong ML focus |
| **Prefect** | Python-native, quick iteration | Simple Python, easy local dev |
| **Metaflow** | Data science teams (Netflix-designed) | Easy parallelism, AWS native |
| **ZenML** | Framework-agnostic, reproducible | Stack-agnostic, integrates MLflow |

### Kubeflow Pipeline Example

```python
import kfp
from kfp import dsl

@dsl.component(base_image="python:3.11", packages_to_install=["scikit-learn", "pandas"])
def prepare_data(data_path: str, output_path: kfp.dsl.Output[kfp.dsl.Dataset]):
    import pandas as pd
    df = pd.read_csv(data_path)
    # ... preprocessing ...
    df.to_csv(output_path.path, index=False)

@dsl.component(base_image="python:3.11", packages_to_install=["scikit-learn", "mlflow"])
def train_model(
    dataset: kfp.dsl.Input[kfp.dsl.Dataset],
    model_output: kfp.dsl.Output[kfp.dsl.Model],
    n_estimators: int = 100,
):
    import mlflow
    # ... training logic ...
    mlflow.sklearn.save_model(model, model_output.path)

@dsl.pipeline(name="fraud-detection-pipeline")
def ml_pipeline(data_path: str = "gs://my-bucket/data/train.csv"):
    prepare_task = prepare_data(data_path=data_path)
    train_task = train_model(dataset=prepare_task.outputs["output_path"])

# Compile and run
kfp.compiler.Compiler().compile(ml_pipeline, "pipeline.yaml")
```

---

## Drift Detection & Monitoring

Model performance degrades due to data drift — input distributions change, or the relationship between features and labels shifts. Without monitoring, this is silent and catastrophic.

### Types of Drift

| Drift Type | Description | Detection Method |
|---|---|---|
| **Feature drift** (covariate shift) | Input distribution changes | KS test, PSI on features |
| **Label drift** (prior probability shift) | Target distribution changes | Monitor prediction distribution |
| **Concept drift** | Feature-label relationship changes | Monitor model accuracy over time |
| **Upstream data drift** | Pipeline/schema changes | Schema validation, null rate monitoring |

### Evidently AI Setup

```python
from evidently.report import Report
from evidently.metric_preset import DataDriftPreset, ClassificationPreset
from evidently import ColumnMapping

# Define column mapping
column_mapping = ColumnMapping(
    target="is_fraud",
    prediction="predicted_fraud",
    numerical_features=["amount", "hour", "day_of_week"],
    categorical_features=["merchant_category", "country"],
)

# Reference data = training distribution
# Current data = production data from the past week
report = Report(metrics=[
    DataDriftPreset(drift_share=0.3),   # Alert if >30% of features drift
    ClassificationPreset(),              # Full classification metrics
])

report.run(
    reference_data=train_df,
    current_data=production_df_last_week,
    column_mapping=column_mapping,
)

report.save_html("reports/drift_report.html")

# Programmatic access for alerting
result = report.as_dict()
drift_detected = result["metrics"][0]["result"]["dataset_drift"]

if drift_detected:
    # Trigger retraining pipeline
    trigger_retraining_pipeline()
    send_slack_alert("Data drift detected! Retraining triggered.")
```

### Prometheus + Custom Metrics

```python
from prometheus_client import Counter, Histogram, Gauge, start_http_server

# Define metrics
prediction_counter = Counter("ml_predictions_total", "Total predictions", ["model_version"])
prediction_latency = Histogram("ml_prediction_latency_seconds", "Prediction latency",
                                buckets=[0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0])
prediction_score = Histogram("ml_prediction_score", "Prediction probability distribution",
                              buckets=[0.1 * i for i in range(11)])

# In your serving code
@app.post("/predict")
def predict(features: dict):
    import time
    start = time.time()

    prediction = model.predict_proba([features])[0][1]

    # Record metrics
    prediction_counter.labels(model_version=MODEL_VERSION).inc()
    prediction_latency.observe(time.time() - start)
    prediction_score.observe(prediction)

    return {"score": prediction, "prediction": int(prediction > 0.5)}
```

---

## Recommended Stack by Team Size

### Solo / Small Team (1–5 people)
- **Tracking**: MLflow (local or simple server)
- **Data versioning**: DVC
- **Orchestration**: Prefect (simple Python)
- **Serving**: FastAPI + Docker
- **Monitoring**: Evidently reports (scheduled batch)
- **CI/CD**: GitHub Actions

### Medium Team (5–20 people)
- **Tracking**: MLflow (PostgreSQL + S3 backend) or Weights & Biases
- **Data versioning**: DVC + lakeFS or a feature store (Feast)
- **Orchestration**: Airflow or Kubeflow
- **Serving**: BentoML or Seldon Core
- **Monitoring**: Evidently + Prometheus + Grafana
- **CI/CD**: GitHub Actions with model gates

### Large / Enterprise (20+ people)
- **Tracking**: Databricks MLflow or Weights & Biases Teams
- **Data versioning**: Tecton or SageMaker Feature Store
- **Orchestration**: Kubeflow or managed (Vertex AI Pipelines, SageMaker Pipelines)
- **Serving**: KServe, SageMaker Endpoints, or Vertex AI
- **Monitoring**: Arize AI, Fiddler, or Aporia
- **CI/CD**: Full GitOps with approval workflows
