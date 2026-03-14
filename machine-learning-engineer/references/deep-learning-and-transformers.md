# Deep Learning & Transformers Guide

## Table of Contents
1. [Choosing: Classical ML vs Deep Learning](#choosing-classical-ml-vs-deep-learning)
2. [PyTorch Fundamentals & Production Training Loop](#pytorch-fundamentals--production-training-loop)
3. [Architecture Patterns](#architecture-patterns)
4. [Training Stability & Optimization](#training-stability--optimization)
5. [Mixed Precision & Memory Optimization](#mixed-precision--memory-optimization)
6. [Transfer Learning with Hugging Face Transformers](#transfer-learning-with-hugging-face-transformers)
7. [Fine-Tuning: LoRA & QLoRA](#fine-tuning-lora--qlora)
8. [Computer Vision](#computer-vision)
9. [NLP & Text Classification](#nlp--text-classification)
10. [Regularization Techniques](#regularization-techniques)
11. [Distributed Training](#distributed-training)
12. [Deep Learning Debugging Checklist](#deep-learning-debugging-checklist)

---

## Choosing: Classical ML vs Deep Learning

**Use classical ML (XGBoost, scikit-learn) when:**
- Tabular data with < 1M rows
- Interpretability is required
- Limited GPU resources
- Fast iteration / prototyping
- Features are well understood

**Use deep learning when:**
- Unstructured data: images, text, audio, video
- Tabular data > 1M rows with complex interactions
- Sequence modeling (time series with long-term dependencies)
- State-of-the-art performance is required
- Pre-trained models (transformers) can be fine-tuned

**Neural network task → architecture mapping:**

| Task | Architecture |
|---|---|
| Tabular (structured) | MLP, TabNet, FT-Transformer |
| Image classification | CNN (ResNet, EfficientNet), ViT |
| Object detection | YOLO, Faster R-CNN, DETR |
| Text classification | BERT, RoBERTa, DeBERTa |
| Text generation | GPT-2, Llama, Mistral (fine-tuned) |
| Seq2Seq (translation, summarization) | T5, BART |
| Time series | Temporal Fusion Transformer, PatchTST |
| Multimodal | CLIP, LLaVA, Flamingo |

---

## PyTorch Fundamentals & Production Training Loop

### Device Management

```python
import torch

def get_device() -> torch.device:
    """Return the best available device — works on CPU, CUDA, and Apple Silicon."""
    if torch.cuda.is_available():
        return torch.device("cuda")
    elif torch.backends.mps.is_available():   # Apple M1/M2/M3
        return torch.device("mps")
    return torch.device("cpu")

device = get_device()

# Always move model AND data to the same device
model = MyModel().to(device)
X_batch = X_batch.to(device)       # Move inputs
y_batch = y_batch.to(device)       # Move labels
```

### Dataset & DataLoader Pattern

```python
from torch.utils.data import Dataset, DataLoader
import torch

class TabularDataset(Dataset):
    def __init__(self, X: np.ndarray, y: np.ndarray):
        self.X = torch.FloatTensor(X)
        self.y = torch.FloatTensor(y)

    def __len__(self):
        return len(self.X)

    def __getitem__(self, idx):
        return self.X[idx], self.y[idx]

# DataLoader best practices:
# num_workers > 0: parallel data loading (set to num CPU cores / 2)
# pin_memory=True: faster CPU→GPU transfer (CUDA only)
# persistent_workers=True: avoid re-creating workers each epoch
train_loader = DataLoader(
    train_dataset,
    batch_size=256,
    shuffle=True,
    num_workers=4,
    pin_memory=True,           # Only if using CUDA
    persistent_workers=True,   # Keep workers alive between epochs
    drop_last=True,            # Avoid partial batches affecting BatchNorm
)

val_loader = DataLoader(
    val_dataset,
    batch_size=512,
    shuffle=False,             # NEVER shuffle validation
    num_workers=4,
    pin_memory=True,
)
```

### Production Training Loop

```python
import torch
import torch.nn as nn
from torch.cuda.amp import GradScaler, autocast
import mlflow

def train_epoch(model, loader, optimizer, criterion, scaler, device, grad_clip=1.0):
    """One training epoch with mixed precision and gradient clipping."""
    model.train()
    total_loss, n_correct, n_total = 0, 0, 0

    for batch_idx, (X, y) in enumerate(loader):
        X, y = X.to(device, non_blocking=True), y.to(device, non_blocking=True)

        optimizer.zero_grad(set_to_none=True)   # Faster than zero_grad()

        # Mixed precision forward pass
        with autocast(device_type="cuda", enabled=device.type == "cuda"):
            logits = model(X)
            loss = criterion(logits, y)

        # Scaled backward pass
        scaler.scale(loss).backward()

        # Gradient clipping (prevents exploding gradients)
        scaler.unscale_(optimizer)
        torch.nn.utils.clip_grad_norm_(model.parameters(), grad_clip)

        scaler.step(optimizer)
        scaler.update()

        total_loss += loss.item() * len(y)
        n_correct += (logits.argmax(dim=1) == y).sum().item()
        n_total += len(y)

    return total_loss / n_total, n_correct / n_total


@torch.inference_mode()   # Faster than no_grad; disables autograd entirely
def evaluate(model, loader, criterion, device):
    """Evaluation with no gradient tracking."""
    model.eval()
    total_loss, n_correct, n_total = 0, 0, 0

    for X, y in loader:
        X, y = X.to(device, non_blocking=True), y.to(device, non_blocking=True)
        with autocast(device_type="cuda", enabled=device.type == "cuda"):
            logits = model(X)
            loss = criterion(logits, y)

        total_loss += loss.item() * len(y)
        n_correct += (logits.argmax(dim=1) == y).sum().item()
        n_total += len(y)

    return total_loss / n_total, n_correct / n_total


def train(model, train_loader, val_loader, optimizer, scheduler, criterion,
          n_epochs, device, patience=10, checkpoint_path="best_model.pt"):
    """
    Full training loop with:
    - Mixed precision
    - Early stopping
    - Learning rate scheduling
    - MLflow logging
    - Checkpointing
    """
    scaler = GradScaler(enabled=device.type == "cuda")
    best_val_loss, patience_counter = float("inf"), 0

    for epoch in range(1, n_epochs + 1):
        train_loss, train_acc = train_epoch(
            model, train_loader, optimizer, criterion, scaler, device
        )
        val_loss, val_acc = evaluate(model, val_loader, criterion, device)

        # Step LR scheduler
        if isinstance(scheduler, torch.optim.lr_scheduler.ReduceLROnPlateau):
            scheduler.step(val_loss)
        else:
            scheduler.step()

        current_lr = optimizer.param_groups[0]["lr"]

        # Log to MLflow
        mlflow.log_metrics({
            "train_loss": train_loss, "train_acc": train_acc,
            "val_loss": val_loss, "val_acc": val_acc,
            "lr": current_lr,
        }, step=epoch)

        print(f"Epoch {epoch:03d} | "
              f"Train Loss: {train_loss:.4f} | Val Loss: {val_loss:.4f} | "
              f"Val Acc: {val_acc:.4f} | LR: {current_lr:.2e}")

        # Checkpoint best model
        if val_loss < best_val_loss:
            best_val_loss = val_loss
            patience_counter = 0
            torch.save({
                "epoch": epoch,
                "model_state_dict": model.state_dict(),
                "optimizer_state_dict": optimizer.state_dict(),
                "val_loss": val_loss,
            }, checkpoint_path)
        else:
            patience_counter += 1
            if patience_counter >= patience:
                print(f"Early stopping at epoch {epoch}")
                break

    # Load best checkpoint for final evaluation
    ckpt = torch.load(checkpoint_path, map_location=device)
    model.load_state_dict(ckpt["model_state_dict"])
    return model
```

---

## Architecture Patterns

### MLP for Tabular Data

```python
class MLP(nn.Module):
    """Production MLP with BatchNorm, Dropout, and residual connections."""
    def __init__(self, input_dim, hidden_dims, output_dim, dropout=0.3):
        super().__init__()
        dims = [input_dim] + hidden_dims

        layers = []
        for in_d, out_d in zip(dims[:-1], dims[1:]):
            layers.extend([
                nn.Linear(in_d, out_d),
                nn.BatchNorm1d(out_d),  # Normalizes activations, stabilizes training
                nn.GELU(),              # Smoother than ReLU; preferred in 2025
                nn.Dropout(dropout),
            ])

        self.network = nn.Sequential(*layers)
        self.head = nn.Linear(hidden_dims[-1], output_dim)
        self._init_weights()

    def _init_weights(self):
        for m in self.modules():
            if isinstance(m, nn.Linear):
                nn.init.kaiming_normal_(m.weight, nonlinearity="relu")
                nn.init.zeros_(m.bias)

    def forward(self, x):
        return self.head(self.network(x))
```

### CNN for Images (Modern Pattern)

```python
import torchvision.models as models

# Always start with a pre-trained backbone (ImageNet weights)
# Fine-tune the head for your task

def build_image_classifier(num_classes, backbone="resnet50", freeze_backbone=False):
    """Build an image classifier with a pre-trained backbone."""
    model = getattr(models, backbone)(weights="IMAGENET1K_V2")

    if freeze_backbone:
        for param in model.parameters():
            param.requires_grad = False

    # Replace the classification head
    in_features = model.fc.in_features
    model.fc = nn.Sequential(
        nn.Dropout(0.3),
        nn.Linear(in_features, 512),
        nn.GELU(),
        nn.Dropout(0.2),
        nn.Linear(512, num_classes),
    )
    return model

# For production: use EfficientNet or ConvNeXt for better accuracy/compute tradeoff
model = models.efficientnet_v2_s(weights="IMAGENET1K_V1")
```

---

## Training Stability & Optimization

### Optimizer Selection

```python
# AdamW is the standard choice for most deep learning tasks
# Weight decay (L2 regularization) is built in and decouples from adaptive LR
optimizer = torch.optim.AdamW(
    model.parameters(),
    lr=1e-3,
    weight_decay=0.01,   # L2 penalty; 0.01 is a sensible default
    betas=(0.9, 0.999),  # Defaults work well in most cases
)

# For transformers, use different LR for backbone vs. head
optimizer = torch.optim.AdamW([
    {"params": model.backbone.parameters(), "lr": 1e-5},   # Small LR for pre-trained
    {"params": model.head.parameters(), "lr": 1e-3},       # Larger LR for new head
], weight_decay=0.01)
```

### Learning Rate Scheduling

```python
from torch.optim.lr_scheduler import (
    CosineAnnealingLR, LinearLR, SequentialLR, ReduceLROnPlateau, OneCycleLR
)

# Cosine annealing with linear warmup (best default for transformers)
warmup_scheduler = LinearLR(optimizer, start_factor=0.1, total_iters=10)
cosine_scheduler = CosineAnnealingLR(optimizer, T_max=n_epochs - 10, eta_min=1e-6)
scheduler = SequentialLR(optimizer, [warmup_scheduler, cosine_scheduler], milestones=[10])

# OneCycleLR (excellent for CNNs and tabular MLPs, enables superconvergence)
scheduler = OneCycleLR(
    optimizer,
    max_lr=1e-3,
    steps_per_epoch=len(train_loader),
    epochs=n_epochs,
    pct_start=0.3,          # 30% of training is warmup
)

# ReduceLROnPlateau (simple, works well when you don't know the epoch count)
scheduler = ReduceLROnPlateau(optimizer, mode="min", patience=5, factor=0.5, verbose=True)
```

### Loss Functions

```python
# Classification
criterion = nn.CrossEntropyLoss()                          # Multiclass
criterion = nn.CrossEntropyLoss(weight=class_weights)      # Imbalanced classes
criterion = nn.BCEWithLogitsLoss()                         # Binary (more numerically stable than BCE + Sigmoid)

# Regression
criterion = nn.MSELoss()                                   # Penalizes large errors heavily
criterion = nn.L1Loss()                                    # Robust to outliers
criterion = nn.HuberLoss(delta=1.0)                        # Best of both: robust + differentiable

# Label smoothing for classification (reduces overconfidence, improves calibration)
criterion = nn.CrossEntropyLoss(label_smoothing=0.1)

# Focal loss for heavily imbalanced data (focuses training on hard examples)
class FocalLoss(nn.Module):
    def __init__(self, alpha=1, gamma=2):
        super().__init__()
        self.alpha = alpha
        self.gamma = gamma

    def forward(self, logits, targets):
        ce_loss = nn.CrossEntropyLoss(reduction="none")(logits, targets)
        p_t = torch.exp(-ce_loss)
        return (self.alpha * (1 - p_t) ** self.gamma * ce_loss).mean()
```

---

## Mixed Precision & Memory Optimization

```python
from torch.cuda.amp import GradScaler, autocast

# ── Mixed Precision (AMP) ──────────────────────────────────────────────────
# Halves memory usage and speeds up training 1.5–3x on modern GPUs
# bfloat16 is preferred over float16 on Ampere+ GPUs (A100, H100, RTX 30/40xx)
scaler = GradScaler()

with autocast(device_type="cuda", dtype=torch.bfloat16):
    output = model(input)
    loss = criterion(output, target)

scaler.scale(loss).backward()
scaler.step(optimizer)
scaler.update()

# ── Gradient Checkpointing ────────────────────────────────────────────────
# Trades compute for memory: re-computes activations during backward pass
# Use for very large models that don't fit in GPU memory
from torch.utils.checkpoint import checkpoint_sequential
# In model.forward(): use checkpoint() around memory-heavy blocks

# ── torch.compile (PyTorch 2.x) ───────────────────────────────────────────
# Fuses operations and generates optimized kernels; often 15–40% speedup
model = torch.compile(model)   # Works on PyTorch 2.0+; drop-in replacement

# ── Memory profiling ──────────────────────────────────────────────────────
print(f"GPU memory allocated: {torch.cuda.memory_allocated() / 1e9:.2f} GB")
print(f"GPU memory reserved:  {torch.cuda.memory_reserved() / 1e9:.2f} GB")

with torch.profiler.profile(activities=[
    torch.profiler.ProfilerActivity.CPU,
    torch.profiler.ProfilerActivity.CUDA,
]) as prof:
    model(sample_input)
print(prof.key_averages().table(sort_by="cuda_time_total", row_limit=10))
```

---

## Transfer Learning with Hugging Face Transformers

### Text Classification (BERT-family)

```python
from transformers import AutoTokenizer, AutoModelForSequenceClassification
from transformers import TrainingArguments, Trainer
from datasets import Dataset
import evaluate

model_name = "distilbert-base-uncased"   # Fast; use "roberta-large" for max accuracy
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForSequenceClassification.from_pretrained(model_name, num_labels=2)

def tokenize(batch):
    return tokenizer(batch["text"], truncation=True, padding="max_length", max_length=256)

train_hf = Dataset.from_pandas(train_df)
val_hf = Dataset.from_pandas(val_df)
train_tok = train_hf.map(tokenize, batched=True)
val_tok = val_hf.map(tokenize, batched=True)

accuracy_metric = evaluate.load("accuracy")
f1_metric = evaluate.load("f1")

def compute_metrics(eval_pred):
    logits, labels = eval_pred
    predictions = logits.argmax(axis=-1)
    return {
        "accuracy": accuracy_metric.compute(predictions=predictions, references=labels)["accuracy"],
        "f1": f1_metric.compute(predictions=predictions, references=labels, average="weighted")["f1"],
    }

training_args = TrainingArguments(
    output_dir="./checkpoints",
    num_train_epochs=3,
    per_device_train_batch_size=32,
    per_device_eval_batch_size=64,
    learning_rate=2e-5,                   # Classic BERT fine-tuning LR
    warmup_ratio=0.06,                    # 6% warmup
    weight_decay=0.01,
    fp16=True,                            # Mixed precision
    eval_strategy="epoch",
    save_strategy="epoch",
    load_best_model_at_end=True,
    metric_for_best_model="f1",
    logging_steps=50,
    report_to="mlflow",                   # Log to MLflow automatically
)

trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=train_tok,
    eval_dataset=val_tok,
    compute_metrics=compute_metrics,
)
trainer.train()
trainer.save_model("./final-model")
```

### Choosing the Right Model Size

| Task | Recommended Model | Why |
|---|---|---|
| Binary/multiclass text classification | `distilbert-base-uncased` | 40% smaller, 60% faster than BERT |
| High-accuracy NLP tasks | `roberta-large` or `deberta-v3-large` | State-of-the-art on GLUE |
| Multilingual NLP | `xlm-roberta-base` | 100 languages |
| Sentence embeddings | `all-MiniLM-L6-v2` | Fast, 384-dim, excellent quality |
| Instruction-following (LLM) | `Llama-3.1-8B-Instruct` or `Mistral-7B-Instruct` | Best open models |
| On-device / edge inference | `Phi-3-mini` or `Gemma-3-1B` | Small but capable |
| Image classification | `vit-base-patch16-224` | Solid baseline ViT |
| Vision-language | `llava-v1.6-mistral-7b` | Image + text |

---

## Fine-Tuning: LoRA & QLoRA

LoRA (Low-Rank Adaptation) is the dominant PEFT technique in 2025. It freezes base model weights and adds trainable low-rank matrices — typically training only 0.1–1% of parameters with near-full-finetune performance.

### LoRA for Classification (PEFT + Transformers)

```python
from peft import LoraConfig, get_peft_model, TaskType
from transformers import AutoModelForSequenceClassification

base_model = AutoModelForSequenceClassification.from_pretrained(
    "roberta-large", num_labels=5
)

lora_config = LoraConfig(
    task_type=TaskType.SEQ_CLS,
    r=16,                              # Rank: 4-64; higher = more capacity & compute
    lora_alpha=32,                     # Scaling factor; set to 2*r as a starting point
    lora_dropout=0.1,
    target_modules=["query", "value"], # Apply LoRA to attention query and value projections
    bias="none",
)

model = get_peft_model(base_model, lora_config)
model.print_trainable_parameters()
# "trainable params: 2,359,296 || all params: 356,671,488 || trainable%: 0.66%"
```

### QLoRA for LLM Fine-Tuning (4-bit, fits on single GPU)

```python
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training
from trl import SFTTrainer, SFTConfig
from datasets import load_dataset

# 4-bit quantization config
bnb_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_quant_type="nf4",         # NormalFloat4: better than int4 for normal distributions
    bnb_4bit_compute_dtype=torch.bfloat16,
    bnb_4bit_use_double_quant=True,    # Quantize the quantization constants
)

model = AutoModelForCausalLM.from_pretrained(
    "meta-llama/Meta-Llama-3.1-8B",
    quantization_config=bnb_config,
    device_map="auto",                 # Automatically place layers across GPUs/CPU
    torch_dtype=torch.bfloat16,
    attn_implementation="flash_attention_2",  # 3x faster attention (requires flash-attn)
)
tokenizer = AutoTokenizer.from_pretrained("meta-llama/Meta-Llama-3.1-8B")
tokenizer.pad_token = tokenizer.eos_token

# Prepare model for kbit training (casts layer norms to float32 for stability)
model = prepare_model_for_kbit_training(model)

lora_config = LoraConfig(
    r=16,
    lora_alpha=16,                     # With rsLoRA, use lora_alpha/sqrt(r) scaling
    target_modules="all-linear",       # Target all linear layers (best for QLoRA)
    lora_dropout=0.05,
    bias="none",
    task_type="CAUSAL_LM",
    use_rslora=True,                   # Rank-Stabilized LoRA (better than plain LoRA)
)
model = get_peft_model(model, lora_config)

# Format data as instruction-response pairs
dataset = load_dataset("json", data_files="data/train.jsonl", split="train")

def format_instruction(example):
    return {"text": f"### Instruction:\n{example['instruction']}\n\n### Response:\n{example['output']}"}

dataset = dataset.map(format_instruction)

training_args = SFTConfig(
    output_dir="./qlora-output",
    num_train_epochs=2,
    per_device_train_batch_size=4,
    gradient_accumulation_steps=8,   # Effective batch = 4 * 8 = 32
    gradient_checkpointing=True,     # Save GPU memory; slower backward pass
    learning_rate=2e-4,
    lr_scheduler_type="cosine",
    warmup_ratio=0.1,
    bf16=True,
    logging_steps=10,
    save_steps=500,
    max_seq_length=1024,
    packing=True,                    # Packs multiple short sequences per batch
    report_to="mlflow",
)

trainer = SFTTrainer(
    model=model,
    args=training_args,
    train_dataset=dataset,
    dataset_text_field="text",
    peft_config=lora_config,
)
trainer.train()

# Merge adapter back into base model for standalone deployment
from peft import PeftModel
merged_model = model.merge_and_unload()
merged_model.save_pretrained("./merged-model")
tokenizer.save_pretrained("./merged-model")
```

### LoRA Hyperparameter Guide

| Hyperparameter | Range | Guidance |
|---|---|---|
| `r` (rank) | 4–64 | Start at 16; increase for complex tasks. Diminishing returns above 64 |
| `lora_alpha` | `r` to `2*r` | Set equal to `r` for simplicity; higher = stronger adaptation |
| `target_modules` | `"all-linear"` | Targeting all linear layers beats attention-only for most tasks |
| `lora_dropout` | 0.0–0.1 | Add dropout only if overfitting on small datasets |
| `use_rslora` | `True` | Almost always better; stabilizes training at higher ranks |

---

## Computer Vision

### Image Augmentation

```python
import torchvision.transforms.v2 as T

# Training augmentations (aggressive; adapted to your domain)
train_transform = T.Compose([
    T.RandomResizedCrop(224, scale=(0.8, 1.0)),
    T.RandomHorizontalFlip(p=0.5),
    T.ColorJitter(brightness=0.2, contrast=0.2, saturation=0.2, hue=0.1),
    T.RandomRotation(degrees=15),
    T.RandomGrayscale(p=0.05),
    T.ToImage(),
    T.ToDtype(torch.float32, scale=True),
    T.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),  # ImageNet stats
])

# Validation/test — NEVER augment (only normalize)
val_transform = T.Compose([
    T.Resize(256),
    T.CenterCrop(224),
    T.ToImage(),
    T.ToDtype(torch.float32, scale=True),
    T.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
])

# Advanced: MixUp / CutMix (state of the art for image classification)
mixup = T.MixUp(num_classes=num_classes, alpha=0.2)
cutmix = T.CutMix(num_classes=num_classes, alpha=1.0)
```

### Object Detection (YOLO)

```python
from ultralytics import YOLO

# Fine-tune YOLOv11 on custom data (fastest path to production detection)
model = YOLO("yolo11n.pt")          # nano; use yolo11s/m/l for more accuracy
results = model.train(
    data="dataset.yaml",            # Points to train/val/test image dirs + labels
    epochs=100,
    imgsz=640,
    batch=16,
    device=0,                       # GPU index
    optimizer="AdamW",
    lr0=0.001,
    weight_decay=0.0005,
    augment=True,
    project="runs/detect",
    name="yolov11-custom",
)
```

---

## NLP & Text Classification

### Tokenization Basics

```python
from transformers import AutoTokenizer

tokenizer = AutoTokenizer.from_pretrained("roberta-base")

# Single text
encoding = tokenizer("Hello world", return_tensors="pt",
                      truncation=True, max_length=512, padding="max_length")

# Batched (much faster)
encodings = tokenizer(
    list_of_texts,
    truncation=True,
    max_length=256,
    padding=True,           # Pads to the longest sequence in the batch
    return_tensors="pt",
)
# encodings.input_ids, encodings.attention_mask

# Sentence embeddings for similarity / retrieval
from sentence_transformers import SentenceTransformer
encoder = SentenceTransformer("all-MiniLM-L6-v2")
embeddings = encoder.encode(texts, batch_size=64, show_progress_bar=True,
                              normalize_embeddings=True)   # Normalize for cosine similarity
```

### LLM Inference Optimization

```python
from transformers import pipeline, AutoModelForCausalLM, AutoTokenizer
import torch

# Use pipeline for simple inference
generator = pipeline(
    "text-generation",
    model="meta-llama/Meta-Llama-3.1-8B-Instruct",
    torch_dtype=torch.bfloat16,
    device_map="auto",
)

output = generator(
    "Explain gradient descent in simple terms.",
    max_new_tokens=200,
    temperature=0.7,
    top_p=0.9,
    do_sample=True,
)

# For high-throughput serving: use vLLM (10–50x faster than HF generate)
from vllm import LLM, SamplingParams

llm = LLM(model="meta-llama/Meta-Llama-3.1-8B-Instruct",
          dtype="bfloat16", gpu_memory_utilization=0.9)

outputs = llm.generate(
    ["Explain gradient descent", "What is backpropagation?"],
    SamplingParams(temperature=0.7, max_tokens=200),
)
```

---

## Regularization Techniques

```python
# Dropout: randomly zero activations during training
# Use in fully-connected layers; AVOID in BatchNorm or after attention
nn.Dropout(p=0.3)

# BatchNorm: normalize activations per-batch; speeds training dramatically
# Use before activation function in CNNs
nn.BatchNorm1d(hidden_dim)  # Tabular / FC layers
nn.BatchNorm2d(channels)    # Conv layers

# LayerNorm: normalize per sample; used in Transformers and RNNs
# Does NOT depend on batch size → works with batch_size=1
nn.LayerNorm(hidden_dim)

# Weight Decay (L2 regularization): always use with AdamW
# Passed via optimizer: torch.optim.AdamW(..., weight_decay=0.01)

# Early stopping: stop when val_loss doesn't improve for N epochs
# Implemented in the training loop above

# Label smoothing: prevents overconfident predictions
nn.CrossEntropyLoss(label_smoothing=0.1)

# Stochastic Depth / DropPath (for ResNets and ViTs)
# from timm.layers import DropPath
# Randomly drops entire residual paths during training
```

---

## Distributed Training

```python
# Single-machine multi-GPU with PyTorch DDP (Distributed Data Parallel)
# Launch with: torchrun --nproc_per_node=4 train.py

import torch.distributed as dist
from torch.nn.parallel import DistributedDataParallel as DDP
from torch.utils.data.distributed import DistributedSampler

def setup(rank, world_size):
    dist.init_process_group("nccl", rank=rank, world_size=world_size)
    torch.cuda.set_device(rank)

def main(rank, world_size):
    setup(rank, world_size)
    model = MyModel().to(rank)
    model = DDP(model, device_ids=[rank])  # Wrap model in DDP

    # DistributedSampler ensures no data overlap between GPUs
    sampler = DistributedSampler(dataset, num_replicas=world_size, rank=rank)
    loader = DataLoader(dataset, batch_size=32, sampler=sampler)

    # Training loop is the same — DDP handles gradient synchronization
    # ...

    dist.destroy_process_group()

# For multi-node or large models: use HF Accelerate (simpler) or DeepSpeed (maximum scale)
# HF Accelerate:
from accelerate import Accelerator
accelerator = Accelerator(mixed_precision="bf16")
model, optimizer, train_loader = accelerator.prepare(model, optimizer, train_loader)
loss = criterion(model(X), y)
accelerator.backward(loss)
optimizer.step()
```

---

## Deep Learning Debugging Checklist

**Loss doesn't decrease:**
- [ ] Check learning rate — try 1e-3 → 1e-4 → 1e-5 range
- [ ] Verify labels are correct (print a few `(X, y)` pairs)
- [ ] Check for data leakage (accidentally using test data)
- [ ] Try training on a single batch — model should overfit immediately
- [ ] Check gradients: `torch.autograd.anomaly_mode.set_detect_anomaly(True)`

**Loss is NaN or Inf:**
- [ ] Add gradient clipping: `clip_grad_norm_(model.parameters(), max_norm=1.0)`
- [ ] Check for log(0) in custom loss — add epsilon: `torch.log(p + 1e-8)`
- [ ] Reduce learning rate
- [ ] Check for division by zero in custom layers

**Model overfits:**
- [ ] Add more Dropout; increase weight_decay
- [ ] Add more training data or augmentation
- [ ] Use a smaller model / fewer parameters
- [ ] Use early stopping
- [ ] Add label smoothing

**Training is slow:**
- [ ] Increase `num_workers` in DataLoader (start at 4)
- [ ] Add `pin_memory=True` (CUDA only)
- [ ] Enable mixed precision (`autocast + GradScaler`)
- [ ] Use `torch.compile(model)` (PyTorch 2.x)
- [ ] Profile with `torch.profiler` to find bottlenecks

**Out of GPU memory:**
- [ ] Reduce batch size; compensate with gradient accumulation
- [ ] Enable gradient checkpointing
- [ ] Use mixed precision (halves memory)
- [ ] Use QLoRA for LLMs (4-bit quantization)
- [ ] Call `torch.cuda.empty_cache()` between evaluations
