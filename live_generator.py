"""
Live Workload Generator
───────────────────────
Generates realistic workload metrics in real-time based on
the ACTUAL current time. Uses the same traffic patterns as
the training dataset:
  - Daily cycle: low at night, peak during business hours
  - Weekend reduction: ~30% less traffic on Sat/Sun
  - Random noise for realistic variation

This module replaces synthetic data with live-generated data.
"""

import random
import math
from datetime import datetime


def _base_traffic(hour: int) -> int:
    """Return base traffic level for a given hour of day."""
    if 0 <= hour <= 5:
        return 60 + hour * 5           # 60-85   (night lull)
    elif 6 <= hour <= 9:
        return 100 + (hour - 6) * 50   # 100-250 (morning ramp)
    elif 10 <= hour <= 13:
        return 300 + (hour - 10) * 40  # 300-420 (peak hours)
    elif 14 <= hour <= 17:
        return 400 - (hour - 14) * 25  # 325-400 (afternoon)
    elif 18 <= hour <= 21:
        return 280 - (hour - 18) * 40  # 160-280 (evening decline)
    else:
        return 140 - (hour - 22) * 30  # 110-140 (late night)


def generate_live_metrics(timestamp: datetime | None = None) -> dict:
    """
    Generate one set of realistic workload metrics.

    If no timestamp is provided, uses the REAL current time.
    Traffic patterns are based on the actual hour and day.

    Returns
    -------
    dict with keys:
        datetime, hour, day_of_week, is_weekend,
        requests, cpu_usage, memory_usage
    """
    if timestamp is None:
        timestamp = datetime.now()

    hour = timestamp.hour
    # Python weekday: 0=Monday ... 6=Sunday
    # Our dataset: 0=Sunday ... 6=Saturday
    py_dow = timestamp.weekday()
    day_of_week = (py_dow + 1) % 7  # convert to our format (0=Sun)
    is_weekend = 1 if day_of_week in (0, 6) else 0

    # Base traffic
    base = _base_traffic(hour)

    # Weekend reduction
    if is_weekend:
        base = int(base * 0.7)

    # Add minute-level variation within the hour
    minute_factor = math.sin(timestamp.minute / 60 * math.pi)  # 0→1→0 across the hour
    base = int(base * (1 + 0.1 * minute_factor))

    # Random noise (+/- 15%)
    noise = random.uniform(-0.15, 0.15)
    requests = max(20, int(base * (1 + noise)))

    # CPU correlates with requests
    cpu_base = (requests / 500) * 100
    cpu_usage = round(min(99.0, max(5.0, cpu_base + random.uniform(-8, 8))), 1)

    # Memory correlates but more stable
    mem_base = (requests / 500) * 85 + 15
    memory_usage = round(min(98.0, max(10.0, mem_base + random.uniform(-5, 5))), 1)

    return {
        "datetime": timestamp.strftime("%Y-%m-%d %H:%M:%S"),
        "hour": hour,
        "day_of_week": day_of_week,
        "is_weekend": is_weekend,
        "requests": requests,
        "cpu_usage": cpu_usage,
        "memory_usage": memory_usage,
    }


# ── CLI test ──
if __name__ == "__main__":
    print("Generating 5 sample live metrics:")
    for i in range(5):
        m = generate_live_metrics()
        day_names = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]
        print(f"  {m['datetime']}  {day_names[m['day_of_week']]}  "
              f"{'WE' if m['is_weekend'] else 'WD'}  "
              f"reqs={m['requests']:>4}  cpu={m['cpu_usage']:>5.1f}%  "
              f"mem={m['memory_usage']:>5.1f}%")
