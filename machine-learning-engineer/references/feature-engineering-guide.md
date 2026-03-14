# Feature Engineering Guide

## Table of Contents
1. [Core Principles](#core-principles)
2. [Numeric Features](#numeric-features)
3. [Categorical Features](#categorical-features)
4. [Text Features](#text-features)
5. [Datetime Features](#datetime-features)
6. [Missing Value Handling](#missing-value-handling)
7. [Outlier Treatment](#outlier-treatment)
8. [Feature Selection](#feature-selection)
9. [Feature Stores](#feature-stores)
10. [Anti-Patterns](#anti-patterns)

---

## Core Principles

1. **Fit on train, transform all** — Never let information from validation/test data influence your feature transformers.
2. **Encapsulate in Pipelines** — Use scikit-learn `Pipeline` so the exact same transformations run in production.
3. **Document every feature** — Name, definition, data type, source table, and known quirks.
4. **Log feature statistics** — After engineering, log distribution summaries to detect future drift.
5. **Version your features** — Treat feature definitions like code; use DVC or a feature store.

---

## Numeric Features

### Scaling

```python
from sklearn.preprocessing import StandardScaler, MinMaxScaler, RobustScaler

# StandardScaler: zero mean, unit variance — good for most linear models and neural nets
# MinMaxScaler: [0, 1] range — good for neural nets with bounded activation functions
# RobustScaler: uses median/IQR — best when data has significant outliers

# Rule of thumb:
# - Tree-based models (XGBoost, RandomForest): scaling NOT required
# - Linear models, SVMs, KNNs, neural nets: scaling REQUIRED

scaler = RobustScaler()
X_train_scaled = scaler.fit_transform(X_train[numeric_cols])
X_val_scaled = scaler.transform(X_val[numeric_cols])   # Use fitted scaler!
```

### Transformations for Skewed Distributions

```python
import numpy as np
from sklearn.preprocessing import PowerTransformer, QuantileTransformer

# Log transform: effective for right-skewed positive data (prices, counts)
X["log_price"] = np.log1p(X["price"])  # log1p handles zeros

# Box-Cox: requires strictly positive values; finds optimal lambda
# Yeo-Johnson: works on any real value; generalizes Box-Cox
pt = PowerTransformer(method="yeo-johnson")
X_transformed = pt.fit_transform(X[["skewed_feature"]])

# Quantile transform: maps to uniform or normal distribution
qt = QuantileTransformer(output_distribution="normal", n_quantiles=1000)
X_transformed = qt.fit_transform(X[["heavy_tailed"]])
```

### Binning / Discretization

```python
from sklearn.preprocessing import KBinsDiscretizer

# Equal-width bins: fast but sensitive to outliers
# Equal-frequency (quantile) bins: more robust, better for imbalanced distributions
# Decision-tree-based bins: supervised, optimal boundaries

kbd = KBinsDiscretizer(n_bins=10, encode="onehot-dense", strategy="quantile")
X_binned = kbd.fit_transform(X[["age"]])

# Manual business-logic bins (often best for interpretability)
X["age_group"] = pd.cut(X["age"],
    bins=[0, 18, 35, 55, 100],
    labels=["under_18", "18_35", "35_55", "over_55"])
```

### Interaction Features

```python
# Polynomial features (use cautiously — exponential feature growth)
from sklearn.preprocessing import PolynomialFeatures
poly = PolynomialFeatures(degree=2, interaction_only=True, include_bias=False)
X_interactions = poly.fit_transform(X[key_features])

# Manual interactions (preferred — domain knowledge guided)
X["price_per_sqft"] = X["price"] / (X["sqft"] + 1e-9)
X["age_income_interaction"] = X["age"] * X["income"]
```

---

## Categorical Features

### When to Use Each Encoding

| Encoding | Use Case | Cardinality |
|---|---|---|
| One-Hot Encoding | Linear models, neural nets | Low (< 15 categories) |
| Ordinal Encoding | Tree models, ordered categories | Any |
| Target Encoding | Tree models, high-cardinality | High (> 50 categories) |
| Binary Encoding | Balanced size/performance | Medium-High |
| Hashing Trick | Online learning, very high cardinality | Very High |

```python
from sklearn.preprocessing import OneHotEncoder, OrdinalEncoder
from category_encoders import TargetEncoder, BinaryEncoder

# One-Hot Encoding
ohe = OneHotEncoder(handle_unknown="ignore", sparse_output=False)

# Target Encoding (mean target per category — add smoothing to prevent overfitting)
te = TargetEncoder(smoothing=10)  # Higher smoothing = less overfitting
X_train["color_encoded"] = te.fit_transform(X_train["color"], y_train)
X_val["color_encoded"] = te.transform(X_val["color"])

# Ordinal encoding for ordered categories
size_order = ["XS", "S", "M", "L", "XL"]
oe = OrdinalEncoder(categories=[size_order])
X["size_ordinal"] = oe.fit_transform(X[["size"]])
```

### Handling High Cardinality

```python
# Frequency-based capping: replace rare categories with "OTHER"
def cap_rare_categories(series, min_freq=0.01):
    freq = series.value_counts(normalize=True)
    rare = freq[freq < min_freq].index
    return series.replace(rare, "OTHER")

# Feature hashing (sklearn HashingEncoder or FeatureHasher)
from sklearn.feature_extraction import FeatureHasher
fh = FeatureHasher(n_features=64, input_type="string")
X_hashed = fh.transform(X["city"].values)
```

---

## Text Features

```python
from sklearn.feature_extraction.text import TfidfVectorizer, CountVectorizer

# Bag of Words — simple baseline
cv = CountVectorizer(max_features=10000, ngram_range=(1, 2), min_df=5)
X_bow = cv.fit_transform(X_train["text"])

# TF-IDF — better default for most text classification tasks
tfidf = TfidfVectorizer(
    max_features=50000,
    ngram_range=(1, 2),
    sublinear_tf=True,      # Apply log to TF
    strip_accents="unicode",
    analyzer="word",
    token_pattern=r"\w{1,}",
    min_df=3,
    max_df=0.9,
)
X_tfidf = tfidf.fit_transform(X_train["text"])

# Sentence Embeddings (modern approach with Hugging Face)
from sentence_transformers import SentenceTransformer
encoder = SentenceTransformer("all-MiniLM-L6-v2")
embeddings = encoder.encode(X["text"].tolist(), batch_size=64)
```

---

## Datetime Features

```python
def extract_datetime_features(df, col):
    """Extract standard datetime components."""
    dt = pd.to_datetime(df[col])
    df[f"{col}_year"] = dt.dt.year
    df[f"{col}_month"] = dt.dt.month
    df[f"{col}_day"] = dt.dt.day
    df[f"{col}_dayofweek"] = dt.dt.dayofweek       # 0=Monday
    df[f"{col}_hour"] = dt.dt.hour
    df[f"{col}_is_weekend"] = (dt.dt.dayofweek >= 5).astype(int)
    df[f"{col}_quarter"] = dt.dt.quarter

    # Cyclical encoding for periodic features (avoids discontinuity at midnight, Jan 1)
    df[f"{col}_hour_sin"] = np.sin(2 * np.pi * dt.dt.hour / 24)
    df[f"{col}_hour_cos"] = np.cos(2 * np.pi * dt.dt.hour / 24)
    df[f"{col}_month_sin"] = np.sin(2 * np.pi * dt.dt.month / 12)
    df[f"{col}_month_cos"] = np.cos(2 * np.pi * dt.dt.month / 12)

    # Time since reference (age/recency features)
    reference_date = pd.Timestamp("2024-01-01")
    df[f"{col}_days_since_ref"] = (dt - reference_date).dt.days

    return df

# Lag features for time series
def add_lag_features(df, target_col, lags=[1, 7, 14, 30], group_col=None):
    for lag in lags:
        if group_col:
            df[f"{target_col}_lag_{lag}"] = (
                df.groupby(group_col)[target_col].shift(lag)
            )
        else:
            df[f"{target_col}_lag_{lag}"] = df[target_col].shift(lag)
    return df

# Rolling window aggregations
def add_rolling_features(df, target_col, windows=[7, 30], group_col=None):
    for window in windows:
        if group_col:
            rolled = df.groupby(group_col)[target_col].transform(
                lambda x: x.shift(1).rolling(window).mean()
            )
        else:
            rolled = df[target_col].shift(1).rolling(window).mean()
        df[f"{target_col}_rolling_mean_{window}"] = rolled
    return df
```

---

## Missing Value Handling

```python
from sklearn.impute import SimpleImputer, KNNImputer
from sklearn.experimental import enable_iterative_imputer  # noqa
from sklearn.impute import IterativeImputer

# Simple imputation
num_imputer = SimpleImputer(strategy="median")   # robust to outliers
cat_imputer = SimpleImputer(strategy="most_frequent")

# KNN imputation: better for correlated features, expensive at scale
knn_imputer = KNNImputer(n_neighbors=5, weights="distance")

# Multivariate (MICE): best for MAR (missing at random) data
mice_imputer = IterativeImputer(random_state=42, max_iter=10)

# Always add a missingness indicator for informative missingness
X["feature_is_null"] = X["feature"].isnull().astype(int)

# Decision by missing mechanism:
# MCAR (missing completely at random): any imputer works
# MAR (missing at random): KNN or MICE preferred
# MNAR (missing not at random): domain-specific handling; imputation biases results
```

---

## Outlier Treatment

```python
# Detection methods
from sklearn.ensemble import IsolationForest
from sklearn.neighbors import LocalOutlierFactor

# IQR-based capping (Winsorization)
def winsorize(series, lower=0.01, upper=0.99):
    low, high = series.quantile([lower, upper])
    return series.clip(low, high)

X["clipped_income"] = winsorize(X["income"])

# Z-score based filtering (use only for normally distributed features)
from scipy import stats
z_scores = np.abs(stats.zscore(X[numeric_cols]))
X_filtered = X[(z_scores < 3).all(axis=1)]

# Isolation Forest for multivariate outliers
iso = IsolationForest(contamination=0.01, random_state=42)
X["is_outlier"] = iso.fit_predict(X[numeric_cols])  # -1 = outlier
```

---

## Feature Selection

```python
from sklearn.feature_selection import (
    SelectKBest, f_classif, mutual_info_classif,
    RFE, SelectFromModel, VarianceThreshold
)
from sklearn.ensemble import RandomForestClassifier

# Remove near-zero variance features (no predictive power)
vt = VarianceThreshold(threshold=0.01)
X_filtered = vt.fit_transform(X)

# Univariate selection
selector = SelectKBest(mutual_info_classif, k=50)
X_selected = selector.fit_transform(X_train, y_train)

# Model-based selection (L1 or tree importance)
lasso = SelectFromModel(LogisticRegression(penalty="l1", C=0.1, solver="saga"))
rf_selector = SelectFromModel(RandomForestClassifier(n_estimators=100), threshold="median")

# Recursive Feature Elimination (slow but thorough)
rfe = RFE(estimator=RandomForestClassifier(), n_features_to_select=30)
X_rfe = rfe.fit_transform(X_train, y_train)

# SHAP-based feature importance (most interpretable)
import shap
explainer = shap.TreeExplainer(model)
shap_values = explainer.shap_values(X_val)
feature_importance = np.abs(shap_values).mean(axis=0)
top_features = X.columns[np.argsort(-feature_importance)[:50]]
```

---

## Feature Stores

For teams with multiple models using the same features, use a feature store to:
- Eliminate train-serve skew by using the same computation for training and production
- Share features across teams and models
- Version feature definitions and backfill historical data

**Popular options:**
- **Feast** (open source): Git-versioned feature definitions, works with any data warehouse
- **Tecton**: Managed, enterprise-grade, real-time + batch
- **Vertex AI Feature Store**: Native GCP integration
- **AWS SageMaker Feature Store**: Native AWS integration

```python
# Feast example: define features once, use in training and serving
from feast import FeatureStore

store = FeatureStore(repo_path="feature_repo/")

# Training data retrieval
training_df = store.get_historical_features(
    entity_df=entity_df,
    features=["driver_stats:conv_rate", "driver_stats:acc_rate"],
).to_df()

# Online serving (low-latency)
online_features = store.get_online_features(
    features=["driver_stats:conv_rate"],
    entity_rows=[{"driver_id": 1001}],
).to_dict()
```

---

## Anti-Patterns

| Anti-Pattern | Problem | Fix |
|---|---|---|
| Fitting scaler on all data | Data leakage | Fit only on train split |
| Dropping rows with nulls indiscriminately | Loses data; biases model | Impute with indicator |
| One-hot encoding high-cardinality features | Dimensionality explosion | Use target encoding or hashing |
| Not documenting feature definitions | Features become unmaintainable | Maintain a feature catalog |
| Hardcoding preprocessing in notebooks | Won't work in production | Use scikit-learn Pipelines |
| Creating features after the train/test split | Potential leakage if features use test data | Always split first, then engineer |
| Using future information in lag features | Target leakage | Shift by at least 1 time period |
