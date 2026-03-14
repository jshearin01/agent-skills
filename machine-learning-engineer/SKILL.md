---
name: machine-learning-engineer
description: "Expert ML engineering skill covering the full lifecycle — data ingestion, feature engineering, model training, evaluation, MLOps, and production deployment. Covers classical ML (scikit-learn, XGBoost) AND deep learning (PyTorch, CNNs, transformers, LoRA/QLoRA, LLMs). Trigger on building ML pipelines, training/evaluating models, experiment tracking, model versioning/deployment, drift detection, hyperparameter tuning, PyTorch training loops, fine-tuning BERT or LLMs, building CNNs, LoRA fine-tuning, MLflow setup, DVC, BentoML, FastAPI serving, or any MLOps question. Use for architecture decisions around PyTorch, scikit-learn, XGBoost, Hugging Face Transformers, PEFT, TRL, Kubeflow, or any ML framework."
---

# Machine Learning Engineer Skill

## Overview

This skill guides Claude through end-to-end ML engineering workflows — from problem framing and data processing through model training, evaluation, and production deployment — following 2025 best practices.

**When you use this skill, follow these phases:**
1. **Understand the problem** — Frame the ML task correctly before writing any code
2. **Data & Feature Engineering** — Build robust, reproducible data pipelines
3. **Model Development** — Train, tune, and evaluate models systematically
4. **MLOps & Experiment Tracking** — Log everything; version data, code, and models
5. **Deployment & Serving** — Package and deploy models safely to production
6. **Monitoring & Maintenance** — Detect drift and trigger retraining

For deep guidance on each phase, read the reference files below.

---

## Quick Reference: ML Engineering Checklist

### Problem Framing (Do First!)
- [ ] Define the business objective and translate it to an ML task type
  - Classification, regression, ranking, generation, anomaly detection, clustering
- [ ] Identify success metrics: both ML metrics (AUC, RMSE) and business metrics (revenue, churn)
- [ ] Determine data availability and feasibility
- [ ] Define latency/throughput SLAs for inference
- [ ] Assess class imbalance, data volume, and label quality

### Data Pipeline
- [ ] EDA: distributions, correlations, missing values, outliers
- [ ] Define train/val/test splits (avoid leakage!)
- [ ] Version datasets with DVC or a feature store
- [ ] Build reproducible preprocessing pipelines (scikit-learn `Pipeline` or similar)
- [ ] Document feature definitions and lineage

### Model Training
- [ ] Start with a strong baseline (logistic regression, linear model, mean predictor)
- [ ] Use experiment tracking (MLflow, W&B) from day one
- [ ] Log: hyperparameters, metrics, dataset version, code commit, model artifacts
- [ ] Automate hyperparameter search (Optuna, Ray Tune)
- [ ] Use cross-validation for small datasets; time-based splits for temporal data

### Evaluation
- [ ] Evaluate on held-out test set (only once — never tune on the test set)
- [ ] Use appropriate metrics for the task (see reference: model-evaluation-and-deployment.md)
- [ ] Perform error analysis: where and why does the model fail?
- [ ] Test for fairness and distributional bias
- [ ] Evaluate latency and memory footprint

### MLOps & Versioning
- [ ] Register model in MLflow Model Registry or cloud registry
- [ ] Tag every model with: dataset version, git commit, metrics, approved_by
- [ ] Stage promotion: Candidate → Staging → Production → Archived
- [ ] Never mutate a Production model; always create a new version

### Deployment
- [ ] Choose serving pattern: REST API (FastAPI/BentoML), batch, streaming, or edge
- [ ] Containerize with Docker; use pinned dependencies
- [ ] Implement health checks and `/predict` + `/health` endpoints
- [ ] Set up canary/blue-green deployments for safe rollout
- [ ] Gate deployment behind automated test suite (performance + latency thresholds)

### Monitoring
- [ ] Monitor: prediction distribution, input feature drift, business metric correlation
- [ ] Use Evidently AI, Arize, or custom Prometheus metrics for drift detection
- [ ] Set alerting thresholds for model degradation
- [ ] Plan retraining triggers: scheduled, drift-triggered, or performance-gated

### Deep Learning / Transformers (additional checks)
- [ ] Choose the right architecture for the data modality (see deep learning reference)
- [ ] Use pre-trained weights — never train from scratch if a backbone exists
- [ ] Enable mixed precision (`autocast` + `GradScaler`) before first run
- [ ] Add gradient clipping (`clip_grad_norm_`, max=1.0) to prevent exploding gradients
- [ ] Use `torch.compile(model)` for 15–40% speedup on PyTorch 2.x
- [ ] For LLM fine-tuning: prefer LoRA/QLoRA over full fine-tuning unless you have 100k+ examples
- [ ] Profile with `torch.profiler` when GPU utilization is low

---

## Core Technology Stack (2025)

| Category | Recommended Tools |
|---|---|
| Languages | Python 3.11+, SQL |
| Classical ML | scikit-learn, XGBoost, LightGBM |
| Deep Learning | PyTorch 2.x, torchvision, torchaudio |
| Transformers / LLMs | Hugging Face Transformers, PEFT (LoRA/QLoRA), TRL, vLLM |
| Experiment Tracking | MLflow (default), Weights & Biases |
| Data Versioning | DVC, lakeFS, Feast (feature store) |
| Pipeline Orchestration | Airflow, Kubeflow Pipelines, Prefect |
| Model Serving | FastAPI, BentoML, TorchServe, Ray Serve, vLLM |
| Containerization | Docker, Kubernetes |
| Cloud ML Platforms | AWS SageMaker, GCP Vertex AI, Azure ML |
| Monitoring | Evidently AI, Prometheus, Grafana |
| CI/CD | GitHub Actions, GitLab CI |

---

## Workflow: End-to-End ML Project

### Phase 1 — Problem Setup

```python
# Start every project with this structure
ml_project/
├── data/               # .dvc tracked, never commit raw data
│   ├── raw/
│   ├── processed/
│   └── features/
├── notebooks/          # Exploration only, not production code
├── src/
│   ├── data/           # Data loaders, preprocessing pipelines
│   ├── features/       # Feature engineering
│   ├── models/         # Model definitions and training
│   ├── evaluation/     # Metrics, error analysis
│   └── serving/        # API, serialization
├── tests/              # Unit + integration tests for pipelines
├── configs/            # Hydra or YAML configs (no hardcoded params)
├── dvc.yaml            # DVC pipeline stages
├── params.yaml         # Hyperparameters versioned with Git
└── MLproject           # MLflow project file
```

### Phase 2 — Data & Feature Engineering

See: `references/feature-engineering-guide.md`  
See script: `scripts/feature_pipeline.py`

Key principles:
- **Always build a scikit-learn Pipeline** — prevents train-serve skew
- **Never fit on validation/test data** — fit transformers on train only, transform all splits
- **Log feature statistics** after engineering to catch distribution drift early
- **Use DVC to version** both raw data and engineered features as separate pipeline stages

```python
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.compose import ColumnTransformer

# Good pattern: encapsulate all preprocessing in a Pipeline
preprocessor = ColumnTransformer([
    ("num", StandardScaler(), numeric_features),
    ("cat", OneHotEncoder(handle_unknown="ignore"), categorical_features),
])

pipeline = Pipeline([
    ("preprocessor", preprocessor),
    ("model", XGBClassifier(**params)),
])

# Fit only on training data!
pipeline.fit(X_train, y_train)
# Same pipeline used in serving — no skew
```

### Phase 3 — Experiment Tracking

See: `references/mlops-tools-and-workflow.md`  
See script: `scripts/experiment_tracking.py`

**Non-negotiable logging checklist per run:**
- Hyperparameters and model architecture
- Dataset version (DVC commit hash or feature store version)
- Git commit hash
- All evaluation metrics (train + val + test)
- Model artifact (registered, not just saved locally)
- Runtime environment (Python version, key package versions)

```python
import mlflow

mlflow.set_tracking_uri("http://mlflow.internal:5000")
mlflow.set_experiment("fraud-detection-v3")

with mlflow.start_run(tags={"git_commit": get_git_hash()}):
    mlflow.log_params(params)
    mlflow.log_param("dataset_version", dvc_dataset_hash())
    # ... train ...
    mlflow.log_metrics({"auc": auc, "f1": f1, "precision": precision})
    mlflow.sklearn.log_model(pipeline, "model",
                             signature=infer_signature(X_train, y_pred))
```

### Phase 4 — Model Evaluation

See: `references/model-evaluation-and-deployment.md`  
See script: `scripts/model_evaluation.py`

**Always ask:**
1. What is the null baseline? (predict the majority class, predict the mean)
2. What is the business cost of FP vs FN?
3. Does performance degrade on subgroups (demographic, temporal, geographic)?
4. What's the 95th percentile inference latency?

### Phase 5 — Deployment

See: `references/model-evaluation-and-deployment.md`

```python
# Minimal production serving pattern with FastAPI
from fastapi import FastAPI
import mlflow.pyfunc

app = FastAPI()
model = mlflow.pyfunc.load_model("models:/FraudDetector/Production")

@app.post("/predict")
def predict(features: dict):
    import pandas as pd
    df = pd.DataFrame([features])
    prediction = model.predict(df)
    return {"prediction": prediction.tolist()}

@app.get("/health")
def health():
    return {"status": "ok"}
```

### Phase 6 — Deep Learning & Transformers

For unstructured data (text, images, audio) or state-of-the-art performance, use neural networks and pre-trained foundation models.

See: `references/deep-learning-and-transformers.md`  
See script: `scripts/neural_network_training.py`

**Decision guide:**
- **Tabular data (<1M rows)** → XGBoost / LightGBM first; MLP only if tree models plateau
- **Text tasks** → Fine-tune a Hugging Face transformer (distilbert → roberta-large → LLM)
- **Image tasks** → Fine-tune ResNet/EfficientNet; use YOLO for detection
- **LLM fine-tuning** → Use LoRA (full GPU) or QLoRA (consumer GPU, 4-bit)

```python
# Production PyTorch training loop — key pattern
device = get_device()   # cuda / mps / cpu

model.train()
optimizer.zero_grad(set_to_none=True)   # Faster than zero_grad()

with autocast(device_type="cuda", enabled=device.type == "cuda"):
    logits = model(X.to(device))
    loss = criterion(logits, y.to(device))

scaler.scale(loss).backward()
scaler.unscale_(optimizer)
torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)  # Prevent exploding gradients
scaler.step(optimizer)
scaler.update()

# Quick fine-tuning with LoRA (0.66% of parameters trained)
from peft import LoraConfig, get_peft_model
lora_config = LoraConfig(r=16, lora_alpha=32, target_modules=["query", "value"])
model = get_peft_model(base_model, lora_config)
```

---

## Common Pitfalls to Avoid

| Pitfall | Prevention |
|---|---|
| **Data leakage** | Fit all transformers only on training data; use Pipeline |
| **Training-serving skew** | Use the same Pipeline object in training and serving |
| **Test set contamination** | Use test set exactly once, at the end |
| **Ignoring class imbalance** | Use stratified splits; try `class_weight="balanced"` |
| **Not versioning data** | Track all datasets with DVC from day one |
| **Models with no lineage** | Always register in MLflow with full metadata |
| **No monitoring in prod** | Deploy drift detection alongside every model |
| **Magic numbers in code** | All hyperparameters in `params.yaml`, not hardcoded |
| **Notebooks in production** | Convert notebooks to `.py` scripts for pipelines |
| **Silent failures** | Add schema validation at pipeline inputs/outputs |

---

## Reference Files

Read these files for detailed guidance on specific topics:

- **`references/feature-engineering-guide.md`** — Encoding, scaling, imputation, feature selection, time-series features, handling high cardinality
- **`references/mlops-tools-and-workflow.md`** — MLflow setup, DVC pipelines, model registry, CI/CD for ML, drift detection with Evidently
- **`references/model-evaluation-and-deployment.md`** — Metrics deep-dive, evaluation strategies, deployment patterns, monitoring setup
- **`references/deep-learning-and-transformers.md`** — PyTorch training loop, CNN/MLP/Transformer architectures, LoRA/QLoRA fine-tuning, training stability, distributed training, debugging

## Scripts

Ready-to-use scripts for common ML engineering tasks:

- **`scripts/feature_pipeline.py`** — End-to-end feature engineering pipeline with scikit-learn
- **`scripts/experiment_tracking.py`** — MLflow experiment tracking template with full logging
- **`scripts/model_evaluation.py`** — Comprehensive model evaluation with metrics, plots, and error analysis
- **`scripts/neural_network_training.py`** — Production PyTorch training loop with mixed precision, early stopping, and Hugging Face fine-tuning (LoRA/QLoRA)
