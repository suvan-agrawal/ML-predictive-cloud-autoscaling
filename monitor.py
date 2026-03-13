"""
Monitoring Module
─────────────────
Simulates real-time monitoring of cloud workload metrics.
Loads recorded metrics from the dataset and serves them
sequentially, mimicking a live monitoring feed.

Now returns datetime strings and time-of-day features.
"""

import os
import pandas as pd

# ──────────────────────────────────────────────
#  Constants
# ──────────────────────────────────────────────
DATASET_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "dataset",
    "workload_dataset.csv",
)


class WorkloadMonitor:
    """Iterate over historical workload records one-by-one."""

    def __init__(self, dataset_path: str = DATASET_PATH):
        self.data = pd.read_csv(dataset_path)
        if "datetime" in self.data.columns:
            self.data["datetime"] = pd.to_datetime(self.data["datetime"])
        self._index = 0

    # ── public API ────────────────────────────
    def get_current_metrics(self) -> dict | None:
        """
        Return the next set of metrics as a dictionary.

        Returns
        -------
        dict  –  {"datetime": str, "hour": int, "day_of_week": int,
                   "is_weekend": int, "requests": int,
                   "cpu_usage": float, "memory_usage": float}
        None  –  when all records have been consumed.
        """
        if self._index >= len(self.data):
            return None

        row = self.data.iloc[self._index]
        self._index += 1

        return {
            "datetime": str(row["datetime"]),
            "hour": int(row["hour"]),
            "day_of_week": int(row["day_of_week"]),
            "is_weekend": int(row["is_weekend"]),
            "requests": int(row["requests"]),
            "cpu_usage": float(row["cpu_usage"]),
            "memory_usage": float(row["memory_usage"]),
        }

    def reset(self):
        """Reset the monitor to the beginning of the dataset."""
        self._index = 0

    def total_records(self) -> int:
        """Total number of records in the dataset."""
        return len(self.data)

    def remaining_records(self) -> int:
        """How many records are left to read."""
        return len(self.data) - self._index


# ── convenience function (matches spec) ──────
_default_monitor: WorkloadMonitor | None = None


def get_current_metrics() -> dict | None:
    """Module-level helper that auto-creates a monitor instance."""
    global _default_monitor
    if _default_monitor is None:
        _default_monitor = WorkloadMonitor()
    return _default_monitor.get_current_metrics()
