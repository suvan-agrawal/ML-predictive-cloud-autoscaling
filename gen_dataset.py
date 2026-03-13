"""Generate a realistic 15-day hourly workload dataset."""
import csv, random, os

random.seed(42)

rows = []

for day in range(15):
    for hour in range(24):
        day_num = day + 1
        datetime_str = f"2026-02-{day_num:02d} {hour:02d}:00"
        
        day_of_week = day % 7  # 0=Sun, 1=Mon, ..., 6=Sat (Feb 1 is Sunday)
        is_weekend = 1 if day_of_week in (0, 6) else 0
        
        # Base traffic by hour
        if 0 <= hour <= 5:
            base = 60 + hour * 5
        elif 6 <= hour <= 9:
            base = 100 + (hour - 6) * 50
        elif 10 <= hour <= 13:
            base = 300 + (hour - 10) * 40
        elif 14 <= hour <= 17:
            base = 400 - (hour - 14) * 25
        elif 18 <= hour <= 21:
            base = 280 - (hour - 18) * 40
        else:
            base = 140 - (hour - 22) * 30

        if is_weekend:
            base = int(base * 0.7)
        
        growth = 1.0 + (day * 0.015)
        base = int(base * growth)
        
        noise = random.uniform(-0.10, 0.10)
        requests = max(30, int(base * (1 + noise)))
        
        cpu_base = (requests / 500) * 100
        cpu_usage = round(min(99.0, max(8.0, cpu_base + random.uniform(-5, 5))), 1)
        
        mem_base = (requests / 500) * 85 + 15
        memory_usage = round(min(98.0, max(15.0, mem_base + random.uniform(-3, 3))), 1)
        
        rows.append([datetime_str, hour, day_of_week, is_weekend,
                      requests, cpu_usage, memory_usage])

out_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                         "dataset", "workload_dataset.csv")
with open(out_path, "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(["datetime", "hour", "day_of_week", "is_weekend",
                      "requests", "cpu_usage", "memory_usage"])
    writer.writerows(rows)

print(f"Generated {len(rows)} records -> {out_path}")
