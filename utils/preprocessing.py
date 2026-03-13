"""
Data Preprocessing Module
─────────────────────────
Loads the workload dataset, cleans missing values,
normalises numeric columns, and prepares feature / target
arrays for the ML prediction engine.

Features now include time-of-day and day-of-week signals
so the model can learn hourly and weekly traffic patterns.
"""

import os
import pandas as pd
import numpy as np
from sklearn.preprocessing import MinMaxScaler

# ──────────────────────────────────────────────
#  Constants
# ──────────────────────────────────────────────
DATASET_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "dataset",
    "workload_dataset.csv",
)

FEATURE_COLUMNS = ["hour", "day_of_week", "is_weekend", "requests", "cpu_usage"]
TARGET_COLUMN = "requests"


# ──────────────────────────────────────────────
#  Public helpers
# ──────────────────────────────────────────────
def load_dataset(path: str = DATASET_PATH) -> pd.DataFrame:
    """Load the CSV workload dataset and return a DataFrame."""
    df = pd.read_csv(path)
    # Ensure datetime column is parsed
    if "datetime" in df.columns:
        df["datetime"] = pd.to_datetime(df["datetime"])
    return df


def clean_data(df: pd.DataFrame) -> pd.DataFrame:
    """Handle missing values by forward-fill then drop any remaining NaNs."""
    df = df.ffill()          # forward-fill gaps
    df = df.dropna()         # drop if any still remain
    df = df.reset_index(drop=True)
    return df


def normalise_data(df: pd.DataFrame, columns: list | None = None) -> tuple[pd.DataFrame, MinMaxScaler]:
    """
    Apply Min-Max normalisation to the specified numeric columns.

    Returns
    -------
    df_normalised : DataFrame with normalised values
    scaler        : fitted MinMaxScaler (for inverse transforms later)
    """
    if columns is None:
        columns = FEATURE_COLUMNS
    scaler = MinMaxScaler()
    df_normalised = df.copy()
    df_normalised[columns] = scaler.fit_transform(df[columns])
    return df_normalised, scaler


def prepare_features(df: pd.DataFrame) -> tuple[np.ndarray, np.ndarray]:
    """
    Build feature matrix X and target vector y for the ML model.

    Features : [hour, day_of_week, is_weekend, requests, cpu_usage]
    Target   : next-row value of requests  (i.e. shift(-1))

    The last row is dropped because it has no "next" target.
    """
    df = df.copy()
    df["target"] = df[TARGET_COLUMN].shift(-1)
    df = df.dropna(subset=["target"])

    X = df[FEATURE_COLUMNS].values
    y = df["target"].values
    return X, y


def get_processed_data(path: str = DATASET_PATH):
    """
    One-call convenience function:
    load -> clean -> prepare features.

    Returns
    -------
    X, y, df_clean
    """
    df = load_dataset(path)
    df_clean = clean_data(df)
    X, y = prepare_features(df_clean)
    return X, y, df_clean
