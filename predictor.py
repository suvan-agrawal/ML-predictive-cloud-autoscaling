"""
ML Prediction Engine
────────────────────
Trains a Linear Regression model on historical workload data
and predicts future request load given current metrics.
The trained model is persisted to disk with joblib.

Features: [hour, day_of_week, is_weekend, requests, cpu_usage]
Target:   next-step request count
"""

import os
import numpy as np
import joblib
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, r2_score

# ──────────────────────────────────────────────
#  Paths
# ──────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_DIR = os.path.join(BASE_DIR, "models")
MODEL_PATH = os.path.join(MODEL_DIR, "trained_model.pkl")


# ──────────────────────────────────────────────
#  Training
# ──────────────────────────────────────────────
def train_model(X: np.ndarray, y: np.ndarray, test_size: float = 0.2) -> dict:
    """
    Train a LinearRegression model and save it to disk.

    Parameters
    ----------
    X : feature matrix  [hour, day_of_week, is_weekend, requests, cpu_usage]
    y : target vector   [next-step requests]
    test_size : fraction held out for evaluation

    Returns
    -------
    dict with keys: model, mae, r2, train_size, test_size
    """
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, random_state=42
    )

    model = LinearRegression()
    model.fit(X_train, y_train)

    y_pred = model.predict(X_test)
    mae = mean_absolute_error(y_test, y_pred)
    r2 = r2_score(y_test, y_pred)

    # Persist model
    os.makedirs(MODEL_DIR, exist_ok=True)
    joblib.dump(model, MODEL_PATH)

    return {
        "model": model,
        "mae": round(mae, 4),
        "r2": round(r2, 4),
        "train_size": len(X_train),
        "test_size": len(X_test),
    }


# ──────────────────────────────────────────────
#  Loading
# ──────────────────────────────────────────────
def load_model(path: str = MODEL_PATH) -> LinearRegression:
    """Load a previously trained model from disk."""
    if not os.path.exists(path):
        raise FileNotFoundError(
            f"No trained model found at {path}. Run train_model() first."
        )
    return joblib.load(path)


# ──────────────────────────────────────────────
#  Prediction
# ──────────────────────────────────────────────
def predict_load(current_metrics: dict, model: LinearRegression | None = None) -> int:
    """
    Predict the next-step request load.

    Parameters
    ----------
    current_metrics : dict with keys hour, day_of_week, is_weekend,
                      requests, cpu_usage
    model           : sklearn model (loaded from disk if not supplied)

    Returns
    -------
    predicted_requests : int
    """
    if model is None:
        model = load_model()

    features = np.array(
        [[current_metrics["hour"],
          current_metrics["day_of_week"],
          current_metrics["is_weekend"],
          current_metrics["requests"],
          current_metrics["cpu_usage"]]]
    )
    prediction = model.predict(features)[0]
    return max(0, int(round(prediction)))


# ──────────────────────────────────────────────
#  CLI helper
# ──────────────────────────────────────────────
if __name__ == "__main__":
    from utils.preprocessing import get_processed_data

    print("[*] Loading & preprocessing dataset ...")
    X, y, _ = get_processed_data()

    print("[*] Training Linear Regression model ...")
    result = train_model(X, y)

    print(f"[OK] Model trained and saved to {MODEL_PATH}")
    print(f"     MAE  = {result['mae']}")
    print(f"     R2   = {result['r2']}")
    print(f"     Train / Test = {result['train_size']} / {result['test_size']}")
