#!/usr/bin/env python3
"""
Neural Network Training Script (PyTorch)
==========================================
Production-ready training loop for neural networks covering:
  - Tabular MLP, image CNN, and Hugging Face Transformer fine-tuning
  - Mixed precision (AMP / bfloat16)
  - Gradient clipping, early stopping, learning rate scheduling
  - MLflow experiment tracking
  - Checkpoint saving and loading
  - LoRA / QLoRA fine-tuning mode for LLMs

Usage:
    # Tabular MLP
    python neural_network_training.py --mode tabular --data data/features/

    # Fine-tune a BERT-family model for text classification
    python neural_network_training.py --mode transformer --model distilbert-base-uncased

    # QLoRA fine-tuning of an LLM
    python neural_network_training.py --mode qlora --model meta-llama/Meta-Llama-3.1-8B

Requirements:
    pip install torch torchvision transformers peft trl accelerate bitsandbytes
    pip install datasets evaluate mlflow scikit-learn pandas numpy
"""

import argparse
import logging
import os
import time
import warnings
from pathlib import Path
from typing import Optional

import mlflow
import numpy as np
import torch
import torch.nn as nn
from torch.cuda.amp import GradScaler, autocast

warnings.filterwarnings("ignore")
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


# ──────────────────────────────────────────────
# Device & Environment Setup
# ──────────────────────────────────────────────

def get_device() -> torch.device:
    """Return the best available compute device."""
    if torch.cuda.is_available():
        logger.info(f"Using CUDA: {torch.cuda.get_device_name(0)}")
        return torch.device("cuda")
    elif torch.backends.mps.is_available():
        logger.info("Using Apple Silicon MPS")
        return torch.device("mps")
    logger.info("Using CPU")
    return torch.device("cpu")


def seed_everything(seed: int = 42):
    """Set all random seeds for reproducibility."""
    import random
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)
        torch.backends.cudnn.deterministic = True
        torch.backends.cudnn.benchmark = False  # Set to True for fixed-size inputs


# ──────────────────────────────────────────────
# Model Architectures
# ──────────────────────────────────────────────

class MLP(nn.Module):
    """
    Production MLP for tabular data.
    Uses BatchNorm + GELU + Dropout + residual connections.
    """
    def __init__(self, input_dim: int, hidden_dims: list[int], output_dim: int,
                 dropout: float = 0.3):
        super().__init__()
        dims = [input_dim] + hidden_dims

        self.blocks = nn.ModuleList()
        for in_d, out_d in zip(dims[:-1], dims[1:]):
            self.blocks.append(nn.Sequential(
                nn.Linear(in_d, out_d),
                nn.BatchNorm1d(out_d),
                nn.GELU(),
                nn.Dropout(dropout),
            ))

        # Residual shortcut if dimensions match
        self.shortcuts = nn.ModuleList([
            nn.Linear(in_d, out_d, bias=False) if in_d != out_d else nn.Identity()
            for in_d, out_d in zip(dims[:-1], dims[1:])
        ])

        self.head = nn.Linear(hidden_dims[-1], output_dim)
        self._init_weights()

    def _init_weights(self):
        for m in self.modules():
            if isinstance(m, nn.Linear):
                nn.init.kaiming_normal_(m.weight, nonlinearity="relu")
                if m.bias is not None:
                    nn.init.zeros_(m.bias)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        for block, shortcut in zip(self.blocks, self.shortcuts):
            x = block(x) + shortcut(x)
        return self.head(x)


def build_image_classifier(num_classes: int, backbone: str = "resnet50",
                             pretrained: bool = True, freeze_layers: int = 0) -> nn.Module:
    """
    Image classifier with a pre-trained CNN backbone.
    freeze_layers: number of backbone layers to freeze (0 = train all)
    """
    import torchvision.models as models

    weights = "IMAGENET1K_V2" if pretrained else None
    model = getattr(models, backbone)(weights=weights)

    # Freeze early layers for fine-tuning with limited data
    if freeze_layers > 0:
        layers = list(model.children())
        for layer in layers[:freeze_layers]:
            for param in layer.parameters():
                param.requires_grad = False

    # Replace classification head
    if hasattr(model, "fc"):
        in_features = model.fc.in_features
        model.fc = nn.Sequential(
            nn.Dropout(0.3),
            nn.Linear(in_features, 512),
            nn.GELU(),
            nn.Dropout(0.2),
            nn.Linear(512, num_classes),
        )
    elif hasattr(model, "classifier"):
        in_features = model.classifier[-1].in_features
        model.classifier[-1] = nn.Sequential(
            nn.Dropout(0.3),
            nn.Linear(in_features, num_classes),
        )

    return model


# ──────────────────────────────────────────────
# Training Loop Components
# ──────────────────────────────────────────────

def train_epoch(model: nn.Module, loader, optimizer: torch.optim.Optimizer,
                criterion: nn.Module, scaler: GradScaler, device: torch.device,
                grad_clip: float = 1.0, scheduler=None) -> tuple[float, float]:
    """
    One full training epoch with mixed precision and gradient clipping.
    Returns (avg_loss, accuracy).
    """
    model.train()
    total_loss, n_correct, n_total = 0.0, 0, 0

    for X, y in loader:
        X = X.to(device, non_blocking=True)
        y = y.to(device, non_blocking=True)

        # !! Critical: zero_grad with set_to_none=True is faster
        optimizer.zero_grad(set_to_none=True)

        use_amp = device.type == "cuda"
        with autocast(device_type="cuda", enabled=use_amp):
            logits = model(X)
            loss = criterion(logits, y)

        scaler.scale(loss).backward()

        # Unscale before clipping (required when using GradScaler)
        scaler.unscale_(optimizer)
        torch.nn.utils.clip_grad_norm_(model.parameters(), grad_clip)

        scaler.step(optimizer)
        scaler.update()

        # Step per-batch schedulers (e.g., OneCycleLR)
        if scheduler is not None and hasattr(scheduler, "step"):
            try:
                scheduler.step()
            except Exception:
                pass

        total_loss += loss.item() * len(y)
        if logits.dim() > 1 and logits.size(1) > 1:
            n_correct += (logits.argmax(dim=1) == y).sum().item()
        else:
            n_correct += ((logits.squeeze() >= 0.5).long() == y.long()).sum().item()
        n_total += len(y)

    return total_loss / max(n_total, 1), n_correct / max(n_total, 1)


@torch.inference_mode()
def evaluate(model: nn.Module, loader, criterion: nn.Module,
             device: torch.device) -> tuple[float, float]:
    """
    Evaluate the model without gradient tracking.
    Returns (avg_loss, accuracy).
    """
    model.eval()
    total_loss, n_correct, n_total = 0.0, 0, 0

    for X, y in loader:
        X = X.to(device, non_blocking=True)
        y = y.to(device, non_blocking=True)

        with autocast(device_type="cuda", enabled=device.type == "cuda"):
            logits = model(X)
            loss = criterion(logits, y)

        total_loss += loss.item() * len(y)
        if logits.dim() > 1 and logits.size(1) > 1:
            n_correct += (logits.argmax(dim=1) == y).sum().item()
        else:
            n_correct += ((logits.squeeze() >= 0.5).long() == y.long()).sum().item()
        n_total += len(y)

    return total_loss / max(n_total, 1), n_correct / max(n_total, 1)


def run_training(
    model: nn.Module,
    train_loader,
    val_loader,
    optimizer: torch.optim.Optimizer,
    criterion: nn.Module,
    device: torch.device,
    n_epochs: int = 100,
    patience: int = 10,
    checkpoint_path: str = "best_model.pt",
    experiment_name: str = "neural-network-training",
    run_name: str = "run",
    scheduler=None,
    grad_clip: float = 1.0,
    log_interval: int = 1,
) -> nn.Module:
    """
    Full training orchestration with early stopping, logging, and checkpointing.
    """
    scaler = GradScaler(enabled=device.type == "cuda")
    best_val_loss = float("inf")
    patience_counter = 0

    mlflow.set_experiment(experiment_name)
    with mlflow.start_run(run_name=run_name):
        mlflow.log_params({
            "n_epochs": n_epochs,
            "patience": patience,
            "optimizer": type(optimizer).__name__,
            "lr": optimizer.param_groups[0]["lr"],
            "grad_clip": grad_clip,
            "device": str(device),
            "n_params": sum(p.numel() for p in model.parameters() if p.requires_grad),
        })

        for epoch in range(1, n_epochs + 1):
            t0 = time.time()

            train_loss, train_acc = train_epoch(
                model, train_loader, optimizer, criterion, scaler, device, grad_clip,
                scheduler=scheduler if isinstance(
                    scheduler, torch.optim.lr_scheduler.OneCycleLR
                ) else None,
            )
            val_loss, val_acc = evaluate(model, val_loader, criterion, device)

            # Step epoch-level schedulers
            if scheduler is not None and not isinstance(
                scheduler, torch.optim.lr_scheduler.OneCycleLR
            ):
                if isinstance(scheduler, torch.optim.lr_scheduler.ReduceLROnPlateau):
                    scheduler.step(val_loss)
                else:
                    scheduler.step()

            current_lr = optimizer.param_groups[0]["lr"]
            epoch_time = time.time() - t0

            if epoch % log_interval == 0:
                logger.info(
                    f"Epoch {epoch:03d}/{n_epochs} | "
                    f"Train Loss: {train_loss:.4f} Acc: {train_acc:.4f} | "
                    f"Val Loss: {val_loss:.4f} Acc: {val_acc:.4f} | "
                    f"LR: {current_lr:.2e} | {epoch_time:.1f}s"
                )

            mlflow.log_metrics({
                "train_loss": train_loss, "train_acc": train_acc,
                "val_loss": val_loss, "val_acc": val_acc,
                "lr": current_lr, "epoch_time_s": epoch_time,
            }, step=epoch)

            # Save best checkpoint
            if val_loss < best_val_loss:
                best_val_loss = val_loss
                patience_counter = 0
                torch.save({
                    "epoch": epoch,
                    "model_state_dict": model.state_dict(),
                    "optimizer_state_dict": optimizer.state_dict(),
                    "val_loss": val_loss,
                    "val_acc": val_acc,
                }, checkpoint_path)
                logger.info(f"  ✓ New best val_loss: {val_loss:.4f}")
            else:
                patience_counter += 1
                if patience_counter >= patience:
                    logger.info(f"Early stopping triggered at epoch {epoch}")
                    break

        # Load best model and log it
        ckpt = torch.load(checkpoint_path, map_location=device)
        model.load_state_dict(ckpt["model_state_dict"])
        logger.info(f"Best model: epoch {ckpt['epoch']}, val_loss={ckpt['val_loss']:.4f}")

        mlflow.pytorch.log_model(model, artifact_path="model")
        mlflow.log_artifact(checkpoint_path)

    return model


# ──────────────────────────────────────────────
# Transformer Fine-Tuning (Hugging Face)
# ──────────────────────────────────────────────

def finetune_transformer(
    model_name: str,
    train_df,
    val_df,
    text_col: str = "text",
    label_col: str = "label",
    num_labels: int = 2,
    num_epochs: int = 3,
    batch_size: int = 32,
    learning_rate: float = 2e-5,
    output_dir: str = "./transformer-output",
    use_lora: bool = False,
    lora_r: int = 16,
):
    """Fine-tune a BERT-family model for sequence classification."""
    from transformers import (
        AutoModelForSequenceClassification, AutoTokenizer,
        TrainingArguments, Trainer,
    )
    from datasets import Dataset
    import evaluate

    logger.info(f"Loading tokenizer and model: {model_name}")
    tokenizer = AutoTokenizer.from_pretrained(model_name)

    def tokenize_batch(batch):
        return tokenizer(
            batch[text_col],
            truncation=True,
            padding="max_length",
            max_length=256,
        )

    train_hf = Dataset.from_pandas(train_df[[text_col, label_col]])
    val_hf = Dataset.from_pandas(val_df[[text_col, label_col]])
    train_tok = train_hf.map(tokenize_batch, batched=True, remove_columns=[text_col])
    val_tok = val_hf.map(tokenize_batch, batched=True, remove_columns=[text_col])
    train_tok = train_tok.rename_column(label_col, "labels")
    val_tok = val_tok.rename_column(label_col, "labels")

    model = AutoModelForSequenceClassification.from_pretrained(
        model_name, num_labels=num_labels
    )

    if use_lora:
        from peft import LoraConfig, get_peft_model, TaskType
        lora_config = LoraConfig(
            task_type=TaskType.SEQ_CLS,
            r=lora_r,
            lora_alpha=lora_r * 2,
            target_modules=["query", "value"],
            lora_dropout=0.1,
            bias="none",
        )
        model = get_peft_model(model, lora_config)
        model.print_trainable_parameters()

    accuracy = evaluate.load("accuracy")
    f1 = evaluate.load("f1")

    def compute_metrics(eval_pred):
        logits, labels = eval_pred
        preds = logits.argmax(axis=-1)
        return {
            "accuracy": accuracy.compute(predictions=preds, references=labels)["accuracy"],
            "f1": f1.compute(predictions=preds, references=labels, average="weighted")["f1"],
        }

    training_args = TrainingArguments(
        output_dir=output_dir,
        num_train_epochs=num_epochs,
        per_device_train_batch_size=batch_size,
        per_device_eval_batch_size=batch_size * 2,
        learning_rate=learning_rate,
        warmup_ratio=0.06,
        weight_decay=0.01,
        fp16=torch.cuda.is_available(),
        eval_strategy="epoch",
        save_strategy="epoch",
        load_best_model_at_end=True,
        metric_for_best_model="f1",
        report_to="mlflow",
        logging_steps=50,
        dataloader_num_workers=4,
    )

    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=train_tok,
        eval_dataset=val_tok,
        compute_metrics=compute_metrics,
    )

    logger.info("Starting fine-tuning...")
    trainer.train()
    trainer.save_model(f"{output_dir}/final")
    tokenizer.save_pretrained(f"{output_dir}/final")
    logger.info(f"Model saved to {output_dir}/final")
    return model, tokenizer


# ──────────────────────────────────────────────
# QLoRA LLM Fine-Tuning
# ──────────────────────────────────────────────

def finetune_qlora(
    model_name: str,
    dataset_path: str,
    output_dir: str = "./qlora-output",
    lora_r: int = 16,
    lora_alpha: int = 16,
    num_epochs: int = 1,
    per_device_batch_size: int = 4,
    gradient_accumulation_steps: int = 8,
    max_seq_length: int = 1024,
    learning_rate: float = 2e-4,
):
    """
    QLoRA fine-tuning for large language models.
    Runs on a single consumer GPU (e.g., RTX 3090 24GB) for 7–13B models.
    """
    try:
        import bitsandbytes  # noqa
        from transformers import (
            AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig,
        )
        from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training
        from trl import SFTTrainer, SFTConfig
        from datasets import load_dataset
    except ImportError as e:
        raise ImportError(
            f"Missing dependency: {e}\n"
            "Run: pip install transformers peft trl bitsandbytes datasets"
        )

    logger.info(f"Loading {model_name} in 4-bit QLoRA mode...")

    bnb_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=torch.bfloat16,
        bnb_4bit_use_double_quant=True,
    )

    model = AutoModelForCausalLM.from_pretrained(
        model_name,
        quantization_config=bnb_config,
        device_map="auto",
        torch_dtype=torch.bfloat16,
    )
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    tokenizer.pad_token = tokenizer.eos_token
    tokenizer.padding_side = "right"   # Important: pad on right for causal LMs

    model = prepare_model_for_kbit_training(model)

    lora_config = LoraConfig(
        r=lora_r,
        lora_alpha=lora_alpha,
        target_modules="all-linear",   # Target all linear layers
        lora_dropout=0.05,
        bias="none",
        task_type="CAUSAL_LM",
        use_rslora=True,               # Rank-Stabilized LoRA
    )
    model = get_peft_model(model, lora_config)

    n_trainable = sum(p.numel() for p in model.parameters() if p.requires_grad)
    n_total = sum(p.numel() for p in model.parameters())
    logger.info(f"Trainable: {n_trainable:,} / {n_total:,} ({100*n_trainable/n_total:.2f}%)")

    dataset = load_dataset("json", data_files=dataset_path, split="train")

    training_args = SFTConfig(
        output_dir=output_dir,
        num_train_epochs=num_epochs,
        per_device_train_batch_size=per_device_batch_size,
        gradient_accumulation_steps=gradient_accumulation_steps,
        gradient_checkpointing=True,
        gradient_checkpointing_kwargs={"use_reentrant": False},
        learning_rate=learning_rate,
        lr_scheduler_type="cosine",
        warmup_ratio=0.1,
        bf16=True,
        logging_steps=10,
        save_steps=100,
        max_seq_length=max_seq_length,
        packing=True,
        report_to="mlflow",
        optim="paged_adamw_32bit",     # Memory-efficient optimizer for QLoRA
    )

    trainer = SFTTrainer(
        model=model,
        args=training_args,
        train_dataset=dataset,
        dataset_text_field="text",
        peft_config=lora_config,
    )

    logger.info("Starting QLoRA fine-tuning...")
    trainer.train()
    trainer.save_model(output_dir)

    logger.info("Merging LoRA adapter with base model...")
    merged = model.merge_and_unload()
    merged.save_pretrained(f"{output_dir}/merged")
    tokenizer.save_pretrained(f"{output_dir}/merged")
    logger.info(f"Merged model saved to {output_dir}/merged")

    return model, tokenizer


# ──────────────────────────────────────────────
# Tabular MLP Example
# ──────────────────────────────────────────────

def run_tabular_example():
    """Demo: Train an MLP on synthetic tabular data."""
    from torch.utils.data import TensorDataset, DataLoader
    from sklearn.datasets import make_classification
    from sklearn.model_selection import train_test_split
    from sklearn.preprocessing import StandardScaler

    seed_everything(42)
    device = get_device()

    # Generate synthetic data
    X, y = make_classification(n_samples=20000, n_features=50, n_informative=30,
                                 n_redundant=10, random_state=42)
    X_train, X_val, y_train, y_val = train_test_split(X, y, test_size=0.2,
                                                        random_state=42, stratify=y)

    scaler = StandardScaler()
    X_train = scaler.fit_transform(X_train)
    X_val = scaler.transform(X_val)

    train_ds = TensorDataset(torch.FloatTensor(X_train), torch.LongTensor(y_train))
    val_ds = TensorDataset(torch.FloatTensor(X_val), torch.LongTensor(y_val))

    train_loader = DataLoader(train_ds, batch_size=512, shuffle=True,
                               num_workers=2, pin_memory=device.type == "cuda")
    val_loader = DataLoader(val_ds, batch_size=1024, shuffle=False,
                             num_workers=2, pin_memory=device.type == "cuda")

    model = MLP(input_dim=50, hidden_dims=[256, 256, 128], output_dim=2).to(device)
    logger.info(f"Model parameters: {sum(p.numel() for p in model.parameters()):,}")

    optimizer = torch.optim.AdamW(model.parameters(), lr=1e-3, weight_decay=0.01)
    criterion = nn.CrossEntropyLoss(label_smoothing=0.1)
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=50, eta_min=1e-5)

    model = run_training(
        model=model,
        train_loader=train_loader,
        val_loader=val_loader,
        optimizer=optimizer,
        criterion=criterion,
        device=device,
        n_epochs=100,
        patience=15,
        scheduler=scheduler,
        experiment_name="tabular-mlp-demo",
        run_name="mlp-synthetic-v1",
    )

    logger.info("Training complete!")
    return model


# ──────────────────────────────────────────────
# CLI Entry Point
# ──────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Neural Network Training")
    parser.add_argument("--mode", choices=["tabular", "transformer", "qlora"],
                        default="tabular", help="Training mode")
    parser.add_argument("--model", default=None, help="Model name (for transformer/qlora)")
    parser.add_argument("--data", default=None, help="Path to data directory or file")
    parser.add_argument("--output", default="./output", help="Output directory")
    parser.add_argument("--epochs", type=int, default=None)
    parser.add_argument("--lr", type=float, default=None)
    parser.add_argument("--batch-size", type=int, default=None)
    parser.add_argument("--tracking-uri", default="http://localhost:5000")
    parser.add_argument("--lora", action="store_true", help="Use LoRA (transformer mode)")
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    seed_everything(args.seed)
    mlflow.set_tracking_uri(args.tracking_uri)

    if args.mode == "tabular":
        logger.info("Running tabular MLP demo...")
        run_tabular_example()

    elif args.mode == "transformer":
        import pandas as pd
        model_name = args.model or "distilbert-base-uncased"
        # Load your own data here
        # train_df = pd.read_csv(f"{args.data}/train.csv")
        # val_df = pd.read_csv(f"{args.data}/val.csv")
        logger.info(f"Transformer fine-tuning mode: {model_name}")
        logger.info("Supply train_df and val_df with 'text' and 'label' columns.")

    elif args.mode == "qlora":
        model_name = args.model or "meta-llama/Meta-Llama-3.1-8B"
        data_path = args.data or "data/train.jsonl"
        finetune_qlora(
            model_name=model_name,
            dataset_path=data_path,
            output_dir=args.output,
            num_epochs=args.epochs or 1,
            learning_rate=args.lr or 2e-4,
            per_device_batch_size=args.batch_size or 4,
        )


if __name__ == "__main__":
    main()
