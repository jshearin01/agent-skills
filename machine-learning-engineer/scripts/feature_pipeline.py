#!/usr/bin/env python3
"""
Feature Engineering Pipeline
==============================
Production-ready feature pipeline using scikit-learn that prevents train-serving skew.

This pipeline:
  - Handles numeric and categorical features
  - Supports missing value imputation with missingness indicators
  - Applies scaling and encoding correctly
  - Serializes the fitted pipeline for use in production serving

Usage:
    python feature_pipeline.py \
        --train data/raw/train.csv \
        --val   data/raw/val.csv \
        --output data/features/ \
        --pipeline-out models/preprocessor.pkl

Requirements:
    pip install scikit-learn pandas numpy category-encoders joblib
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
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler, OneHotEncoder, FunctionTransformer

warnings.filterwarnings("ignore")
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


# ──────────────────────────────────────────────
# Custom Transformers
# ──────────────────────────────────────────────

class MissingIndicatorTransformer(BaseEstimator, TransformerMixin):
    """
    Add binary missingness indicator columns alongside imputed values.
    Useful when missingness itself is informative (MNAR data).
    """
    def __init__(self, columns: Optional[list] = None, threshold: float = 0.01):
        self.columns = columns  # If None, auto-detect columns with any missing values
        self.threshold = threshold  # Only add indicator if null rate > threshold

    def fit(self, X: pd.DataFrame, y=None):
        if self.columns is None:
            null_rates = X.isnull().mean()
            self.indicator_cols_ = null_rates[null_rates > self.threshold].index.tolist()
        else:
            self.indicator_cols_ = self.columns
        return self

    def transform(self, X: pd.DataFrame) -> pd.DataFrame:
        X = X.copy()
        for col in self.indicator_cols_:
            if col in X.columns:
                X[f"{col}_is_missing"] = X[col].isnull().astype(int)
        return X


class DatetimeFeatureExtractor(BaseEstimator, TransformerMixin):
    """
    Extract standard features from datetime columns with cyclical encoding.
    """
    def __init__(self, datetime_columns: list[str]):
        self.datetime_columns = datetime_columns

    def fit(self, X: pd.DataFrame, y=None):
        return self

    def transform(self, X: pd.DataFrame) -> pd.DataFrame:
        X = X.copy()
        for col in self.datetime_columns:
            if col not in X.columns:
                continue
            dt = pd.to_datetime(X[col], errors="coerce")

            X[f"{col}_year"] = dt.dt.year
            X[f"{col}_month"] = dt.dt.month
            X[f"{col}_day"] = dt.dt.day
            X[f"{col}_dayofweek"] = dt.dt.dayofweek
            X[f"{col}_hour"] = dt.dt.hour.fillna(0).astype(int)
            X[f"{col}_is_weekend"] = (dt.dt.dayofweek >= 5).astype(int)
            X[f"{col}_quarter"] = dt.dt.quarter

            # Cyclical encoding (prevents discontinuity)
            X[f"{col}_hour_sin"] = np.sin(2 * np.pi * dt.dt.hour / 24)
            X[f"{col}_hour_cos"] = np.cos(2 * np.pi * dt.dt.hour / 24)
            X[f"{col}_month_sin"] = np.sin(2 * np.pi * dt.dt.month / 12)
            X[f"{col}_month_cos"] = np.cos(2 * np.pi * dt.dt.month / 12)

            X = X.drop(columns=[col])
        return X


class RareValueEncoder(BaseEstimator, TransformerMixin):
    """
    Replace rare categorical values with 'OTHER' to reduce cardinality.
    Fit on training data; apply consistently at serve time.
    """
    def __init__(self, min_frequency: float = 0.01, fill_value: str = "OTHER"):
        self.min_frequency = min_frequency
        self.fill_value = fill_value

    def fit(self, X: pd.DataFrame, y=None):
        self.frequent_values_ = {}
        for col in X.select_dtypes(include=["object", "category"]).columns:
            freqs = X[col].value_counts(normalize=True)
            self.frequent_values_[col] = set(freqs[freqs >= self.min_frequency].index)
        return self

    def transform(self, X: pd.DataFrame) -> pd.DataFrame:
        X = X.copy()
        for col, frequent in self.frequent_values_.items():
            if col in X.columns:
                X[col] = X[col].apply(
                    lambda v: v if v in frequent else self.fill_value
                )
        return X


# ──────────────────────────────────────────────
# Pipeline Builder
# ──────────────────────────────────────────────

def detect_column_types(df: pd.DataFrame, target_col: str = "target",
                         datetime_cols: Optional[list] = None
                         ) -> tuple[list, list, list]:
    """Auto-detect column types from a DataFrame."""
    exclude = {target_col}
    if datetime_cols:
        exclude.update(datetime_cols)

    numeric_cols = [
        c for c in df.select_dtypes(include=[np.number]).columns
        if c not in exclude
    ]
    categorical_cols = [
        c for c in df.select_dtypes(include=["object", "category"]).columns
        if c not in exclude
    ]

    return numeric_cols, categorical_cols, datetime_cols or []


def build_preprocessing_pipeline(
    numeric_cols: list[str],
    categorical_cols: list[str],
    numeric_impute_strategy: str = "median",
    scale_numerics: bool = True,
    ohe_max_categories: int = 50,
    rare_value_threshold: float = 0.01,
) -> Pipeline:
    """
    Build a complete preprocessing pipeline.

    This is the canonical way to avoid train-serving skew:
    fit this pipeline on training data, then use it for both
    training and production inference.
    """
    # Numeric pipeline: impute → (optionally) scale
    numeric_steps = [
        ("imputer", SimpleImputer(strategy=numeric_impute_strategy)),
    ]
    if scale_numerics:
        numeric_steps.append(("scaler", StandardScaler()))
    numeric_pipeline = Pipeline(numeric_steps)

    # Categorical pipeline: rare value encoding → impute → one-hot
    categorical_pipeline = Pipeline([
        ("rare_encoder", RareValueEncoder(min_frequency=rare_value_threshold)),
        ("imputer", SimpleImputer(strategy="constant", fill_value="UNKNOWN")),
        ("ohe", OneHotEncoder(
            handle_unknown="ignore",
            sparse_output=False,
            max_categories=ohe_max_categories,
        )),
    ])

    # Combine into a single ColumnTransformer
    preprocessor = ColumnTransformer(
        transformers=[
            ("numeric", numeric_pipeline, numeric_cols),
            ("categorical", categorical_pipeline, categorical_cols),
        ],
        remainder="drop",  # Drop columns not listed above
        verbose_feature_names_out=True,
    )

    return preprocessor


def get_feature_names(preprocessor: ColumnTransformer,
                       numeric_cols: list, categorical_cols: list) -> list[str]:
    """Extract feature names after transformation (for interpretability)."""
    try:
        return list(preprocessor.get_feature_names_out())
    except Exception:
        # Fallback for older sklearn versions
        names = list(numeric_cols)
        try:
            ohe = preprocessor.named_transformers_["categorical"].named_steps["ohe"]
            names += list(ohe.get_feature_names_out(categorical_cols))
        except Exception:
            pass
        return names


# ──────────────────────────────────────────────
# Main Pipeline Logic
# ──────────────────────────────────────────────

def build_and_fit_pipeline(
    train_path: str,
    val_path: str,
    output_dir: str,
    pipeline_out: str,
    target_col: str = "target",
    datetime_cols: Optional[list] = None,
) -> dict:
    """
    Full pipeline: load data → detect columns → fit pipeline → transform and save.

    Returns a dict with feature names and basic statistics for logging.
    """
    logger.info("Loading data...")
    train_df = pd.read_csv(train_path)
    val_df = pd.read_csv(val_path)

    logger.info(f"Train shape: {train_df.shape}, Val shape: {val_df.shape}")

    # Separate features and target
    y_train = train_df[target_col]
    y_val = val_df[target_col]
    X_train = train_df.drop(columns=[target_col])
    X_val = val_df.drop(columns=[target_col])

    # Add missingness indicators BEFORE imputation (preserves information)
    logger.info("Adding missingness indicators...")
    miss_transformer = MissingIndicatorTransformer(threshold=0.01)
    X_train = miss_transformer.fit_transform(X_train)
    X_val = miss_transformer.transform(X_val)

    # Extract datetime features
    if datetime_cols:
        logger.info(f"Extracting datetime features from: {datetime_cols}")
        dt_transformer = DatetimeFeatureExtractor(datetime_cols)
        X_train = dt_transformer.fit_transform(X_train)
        X_val = dt_transformer.transform(X_val)

    # Detect column types on the modified DataFrame
    numeric_cols, categorical_cols, _ = detect_column_types(
        X_train, target_col="",  # target already removed
    )
    logger.info(f"Numeric features: {len(numeric_cols)}, "
                f"Categorical features: {len(categorical_cols)}")

    # Build and fit the preprocessing pipeline
    logger.info("Fitting preprocessing pipeline (on training data only)...")
    preprocessor = build_preprocessing_pipeline(
        numeric_cols=numeric_cols,
        categorical_cols=categorical_cols,
    )

    # !! Critical: fit ONLY on training data, transform all splits
    X_train_transformed = preprocessor.fit_transform(X_train, y_train)
    X_val_transformed = preprocessor.transform(X_val)

    # Get feature names
    feature_names = get_feature_names(preprocessor, numeric_cols, categorical_cols)
    logger.info(f"Total features after transformation: {len(feature_names)}")

    # Save transformed datasets
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    train_out = pd.DataFrame(X_train_transformed, columns=feature_names)
    train_out[target_col] = y_train.values
    train_out.to_csv(output_path / "train_features.csv", index=False)

    val_out = pd.DataFrame(X_val_transformed, columns=feature_names)
    val_out[target_col] = y_val.values
    val_out.to_csv(output_path / "val_features.csv", index=False)

    # Save the pipeline for production serving
    pipeline_path = Path(pipeline_out)
    pipeline_path.parent.mkdir(parents=True, exist_ok=True)

    serving_pipeline = {
        "missing_indicator": miss_transformer,
        "datetime_extractor": DatetimeFeatureExtractor(datetime_cols) if datetime_cols else None,
        "preprocessor": preprocessor,
        "feature_names": feature_names,
        "numeric_cols": numeric_cols,
        "categorical_cols": categorical_cols,
    }
    joblib.dump(serving_pipeline, pipeline_path)
    logger.info(f"Pipeline saved to: {pipeline_path}")

    # Save metadata for MLflow logging
    metadata = {
        "n_train_samples": len(X_train),
        "n_val_samples": len(X_val),
        "n_features_input": X_train.shape[1],
        "n_features_output": len(feature_names),
        "numeric_cols": numeric_cols,
        "categorical_cols": categorical_cols,
        "feature_names": feature_names,
        "null_rates_train": train_df.isnull().mean().to_dict(),
    }

    with open(output_path / "feature_metadata.json", "w") as f:
        json.dump(metadata, f, indent=2, default=str)

    logger.info("Feature pipeline complete!")
    logger.info(f"  Train: {train_out.shape}, Val: {val_out.shape}")

    return metadata


def load_serving_pipeline(pipeline_path: str) -> dict:
    """Load the serialized pipeline for use in production serving."""
    return joblib.load(pipeline_path)


def transform_for_serving(serving_pipeline: dict, raw_input: dict) -> pd.DataFrame:
    """
    Apply the same transformations at serve time as at training time.
    This guarantees zero train-serving skew.
    """
    df = pd.DataFrame([raw_input])

    # Apply missingness indicators
    if serving_pipeline["missing_indicator"]:
        df = serving_pipeline["missing_indicator"].transform(df)

    # Apply datetime extraction
    if serving_pipeline["datetime_extractor"]:
        df = serving_pipeline["datetime_extractor"].transform(df)

    # Apply the main preprocessor
    transformed = serving_pipeline["preprocessor"].transform(df)
    return pd.DataFrame(transformed, columns=serving_pipeline["feature_names"])


# ──────────────────────────────────────────────
# CLI Entry Point
# ──────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Build and fit a feature engineering pipeline")
    parser.add_argument("--train", required=True, help="Path to training CSV")
    parser.add_argument("--val", required=True, help="Path to validation CSV")
    parser.add_argument("--output", default="data/features/", help="Output directory")
    parser.add_argument("--pipeline-out", default="models/preprocessor.pkl",
                        help="Path to save the fitted pipeline")
    parser.add_argument("--target", default="target", help="Target column name")
    parser.add_argument("--datetime-cols", nargs="*", default=None,
                        help="Datetime columns to process")
    args = parser.parse_args()

    metadata = build_and_fit_pipeline(
        train_path=args.train,
        val_path=args.val,
        output_dir=args.output,
        pipeline_out=args.pipeline_out,
        target_col=args.target,
        datetime_cols=args.datetime_cols,
    )

    print(f"\nFeature pipeline summary:")
    print(f"  Input features:  {metadata['n_features_input']}")
    print(f"  Output features: {metadata['n_features_output']}")
    print(f"  Train samples:   {metadata['n_train_samples']}")


if __name__ == "__main__":
    main()
