# AI-Driven Cloud Resource Auto-Scaling Using Machine Learning

A prototype system that demonstrates **intelligent, predictive cloud resource auto-scaling** using machine learning. Instead of reacting to overload after it happens, this system **forecasts future workload demand** and scales cloud resources **proactively** — before performance degrades.

---

## Table of Contents

- [Introduction](#introduction)
- [Problem Statement](#problem-statement)
- [Proposed Solution](#proposed-solution)
- [System Architecture](#system-architecture)
- [Technology Stack](#technology-stack)
- [Project Structure](#project-structure)
- [Module Descriptions](#module-descriptions)
- [Dataset Design](#dataset-design)
- [Machine Learning Model](#machine-learning-model)
- [SLA Constraints & Scaling Logic](#sla-constraints--scaling-logic)
- [Dashboard Features](#dashboard-features)
- [Installation & Setup](#installation--setup)
- [How to Run](#how-to-run)
- [Demo Walkthrough](#demo-walkthrough)
- [Results & Observations](#results--observations)
- [Future Enhancements](#future-enhancements)

---

## Introduction

Cloud computing platforms like AWS, Azure, and Google Cloud allow applications to dynamically add or remove compute resources (containers, virtual machines) based on demand. This process is called **auto-scaling**.

Most production systems today use **reactive auto-scaling** — they wait for a metric (like CPU usage) to cross a threshold and only *then* add more resources. This introduces a **lag**: by the time new resources are provisioned, users may have already experienced slowness or downtime.

This project demonstrates a **predictive (proactive) approach** where a machine learning model anticipates future workload and triggers scaling *before* the overload occurs.

---

## Problem Statement

Traditional cloud auto-scaling systems are **reactive in nature**:

1. They monitor system metrics (CPU, memory, request count).
2. When a metric crosses a predefined threshold (e.g., CPU > 80%), they trigger scaling.
3. New resources take time to provision (cold-start delay).
4. During this delay, **performance degrades** and **SLA violations** may occur.

**Key issues with reactive scaling:**

| Problem | Impact |
|---------|--------|
| Cold-start latency | Users experience slowness during provisioning |
| Threshold-based triggers | Cannot handle sudden traffic spikes gracefully |
| No foresight | System has no awareness of upcoming demand patterns |
| Over-provisioning risk | Static thresholds often lead to wasted resources |

---

## Proposed Solution

This project implements a **closed-loop predictive scaling system**:

```
Workload  -->  Monitor  -->  ML Prediction  -->  SLA Check  -->  Scale Decision  -->  Resource Allocation
   ^                                                                                         |
   |___________________________ feedback loop _______________________________________________|
```

**How it works:**

1. **Monitor** current workload metrics (requests/sec, CPU usage, memory usage).
2. **Predict** the next time-step's workload using a trained ML model.
3. **Evaluate** whether the predicted load violates SLA constraints.
4. **Decide** how many containers are needed to handle the predicted load.
5. **Allocate** resources proactively — *before* the demand actually arrives.
6. **Repeat** — the system continuously monitors and adjusts in a feedback loop.

**Key advantage:** Resources are ready *before* the traffic spike, eliminating cold-start delays and SLA violations.

---

## System Architecture

```
                    +---------------------+
                    |   Client Requests   |
                    +----------+----------+
                               |
                               v
                    +----------+----------+
                    |  Monitoring Module  |  <-- monitor.py
                    |  (Metrics Collector)|
                    +----------+----------+
                               |
                               v
                    +----------+----------+
                    | Data Preprocessing  |  <-- utils/preprocessing.py
                    |  (Clean & Prepare)  |
                    +----------+----------+
                               |
                               v
                    +----------+----------+
                    |  ML Prediction      |  <-- predictor.py
                    |  Engine             |
                    |  (Linear Regression)|
                    +----------+----------+
                               |
                               v
                    +----------+----------+
                    |  SLA Evaluation     |  <-- scaler.py
                    |  Engine             |
                    +----------+----------+
                               |
                               v
                    +----------+----------+
                    |  Scaling Decision   |  <-- scaler.py
                    |  Module             |
                    +----------+----------+
                               |
                               v
                    +----------+----------+
                    |  Resource Manager   |  <-- resource_manager.py
                    |  (Container Pool)   |
                    +----------+----------+
                               |
                               v
                    +----------+----------+
                    | Allocated Resources |
                    +----------+----------+
                               |
                               +--------> Feedback to Monitoring Module
```

---

## Technology Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| Programming Language | Python 3.10+ | Core development language |
| Data Processing | Pandas, NumPy | Data loading, cleaning, feature engineering |
| Machine Learning | Scikit-learn | Linear Regression model for workload prediction |
| Model Persistence | Joblib | Save/load trained models to/from disk |
| Dashboard Framework | Streamlit | Interactive web-based UI for visualization |
| Charting Library | Matplotlib | Custom charts (line, step, area plots) |
| Dataset Format | CSV | Simple, portable data storage |

---

## Project Structure

```
Cloud Recourses Auto Scaling using ML/
|
+-- app.py                        # Streamlit dashboard (main entry point)
+-- monitor.py                    # Workload monitoring simulation module
+-- predictor.py                  # ML model training & prediction engine
+-- scaler.py                     # SLA evaluation & scaling decision logic
+-- resource_manager.py           # Simulated cloud container manager
|
+-- dataset/
|   +-- workload_dataset.csv      # Synthetic workload data (100 records)
|
+-- models/
|   +-- trained_model.pkl         # Persisted trained ML model
|
+-- utils/
|   +-- preprocessing.py          # Data cleaning, normalization, feature prep
|
+-- requirements.txt              # Python dependencies
+-- README.md                     # This file
+-- PROJECT_SPEC.md               # Technical specification document
```

---

## Module Descriptions

### 1. Monitoring Module (`monitor.py`)

**Purpose:** Simulates a real-time cloud monitoring agent.

- Loads the historical workload dataset and serves records one-by-one, mimicking a live monitoring feed.
- Each call to `get_current_metrics()` returns the next data point:

```python
{
    "timestamp": 5,
    "requests": 240,
    "cpu_usage": 60.0,
    "memory_usage": 65.0
}
```

- Uses a `WorkloadMonitor` class with an internal index pointer to iterate sequentially.

---

### 2. Data Preprocessing (`utils/preprocessing.py`)

**Purpose:** Prepares raw data for training and prediction.

| Function | What it does |
|----------|-------------|
| `load_dataset()` | Reads CSV file into a Pandas DataFrame |
| `clean_data()` | Forward-fills missing values, drops remaining NaNs |
| `normalise_data()` | Applies Min-Max scaling (0 to 1 range) |
| `prepare_features()` | Creates feature matrix X and target vector y using a shift-by-1 approach |
| `get_processed_data()` | One-call pipeline: load -> clean -> prepare |

**Feature engineering approach:**
- **Features (X):** `[timestamp, requests, cpu_usage]` of the current row
- **Target (y):** `requests` of the *next* row (shift by -1)
- This teaches the model to predict "what will the request count be in the next time step?"

---

### 3. ML Prediction Engine (`predictor.py`)

**Purpose:** Trains and uses a Linear Regression model to forecast future workload.

| Function | What it does |
|----------|-------------|
| `train_model(X, y)` | Trains LinearRegression, evaluates on test split, saves model to disk |
| `load_model()` | Loads a previously saved model from `models/trained_model.pkl` |
| `predict_load(metrics)` | Takes current metrics dict, returns predicted next-step request count |

**Why Linear Regression?**
- Simple, interpretable, and fast to train
- Works well for linearly correlated workload patterns
- Ideal for academic demonstration of the concept
- Can be upgraded to Random Forest, LSTM, etc. in production

---

### 4. SLA Evaluation & Scaling Decision (`scaler.py`)

**Purpose:** Applies business rules (SLA constraints) to the ML prediction and decides how many containers are needed.

**SLA Constraints:**
```
Max CPU Utilisation   = 80%
Max Load/Container    = 100 requests
```

| Function | What it does |
|----------|-------------|
| `evaluate_sla()` | Checks if predicted workload violates SLA limits |
| `decide_scaling()` | Calculates required containers and returns scale_up / scale_down / no_change |

**Scaling formula:**
```
required_containers = ceil(predicted_requests / 100)
```

If CPU is already above 80%, one extra container is added as a safety buffer.

---

### 5. Resource Manager (`resource_manager.py`)

**Purpose:** Simulates a cloud container pool (like Docker / Kubernetes).

| Function | What it does |
|----------|-------------|
| `scale_up(n)` | Add n containers to the pool |
| `scale_down(n)` | Remove n containers (minimum 1 kept) |
| `set_containers(n)` | Directly set container count to n |
| `get_current_resources()` | Returns current container count and total capacity |
| `get_history()` | Returns audit trail of all scaling actions |

- Starts with **3 containers** (capacity = 300 requests)
- Maintains a complete **action history** for analysis

---

### 6. Dashboard (`app.py`)

**Purpose:** Ties everything together in an interactive Streamlit web application.

See [Dashboard Features](#dashboard-features) section below for details.## Dataset Design

**File:** `dataset/workload_dataset.csv`

**Size:** 360 records (15 days × 24 hours)

| Column | Type | Description |
|--------|------|-------------|
| `datetime` | string | Real timestamp (e.g., "2026-02-01 14:00") |
| `hour` | int | Hour of day (0-23) |
| `day_of_week` | int | Day of week (0=Sunday, 6=Saturday) |
| `is_weekend` | int | Binary flag (1=weekend, 0=weekday) |
| `requests` | int | Incoming requests per hour |
| `cpu_usage` | float | Server CPU utilisation percentage |
| `memory_usage` | float | Server memory utilisation percentage |

**Traffic patterns (realistic daily and weekly cycles):**

```
Hourly Pattern:
  00:00 - 05:00  →  Low traffic (60-85 reqs)     — Night lull
  06:00 - 09:00  →  Morning ramp (100-250 reqs)   — Users waking up
  10:00 - 13:00  →  Peak hours (300-420 reqs)      — Business hours
  14:00 - 17:00  →  Afternoon (325-400 reqs)       — Still busy
  18:00 - 21:00  →  Evening decline (160-280 reqs) — Winding down
  22:00 - 23:00  →  Late night (110-140 reqs)      — Approaching night

Weekly Pattern:
  Weekdays (Mon-Fri) → Full traffic
  Weekends (Sat-Sun) → 30% reduction in traffic

Growth Trend:
  Day 1 → baseline
  Day 15 → ~21% higher (gradual daily growth)
```

This pattern enables the model to learn **when** traffic is high (not just *how much*), making predictions time-aware.

---

## Machine Learning Model

### Model Type
**Linear Regression** (from scikit-learn)

### Features — Time-Aware

| Feature | Type | Why it matters |
|---------|------|---------------|
| `hour` | Time | Captures daily traffic cycle (peaks at 10-14, dips at 0-5) |
| `day_of_week` | Time | Captures weekly patterns |
| `is_weekend` | Time | Weekend traffic is ~30% lower than weekday |
| `requests` | Workload | Current request rate (strongest predictor) |
| `cpu_usage` | Workload | Current CPU utilisation |

### Training Details

| Parameter | Value |
|-----------|-------|
| Algorithm | `LinearRegression` |
| Train/Test Split | 80% / 20% (random_state=42) |
| Features | hour, day_of_week, is_weekend, requests, cpu_usage |
| Target | Next hour's request count |
| Training Samples | 287 |
| Test Samples | 72 |

### Performance Metrics

| Metric | Value | Meaning |
|--------|-------|---------|
| **R-squared (R²)** | **0.90** | Model explains 90% of variance in actual data |
| **MAE** | **29.52** | On average, predictions are off by ~30 requests |

R² = 0.90 is strong for a dataset with daily cycles and random noise. The model correctly captures the hourly and weekly traffic patterns.

### How Prediction Works

```
Input:  current metrics  {hour: 12, day_of_week: 3, is_weekend: 0,
                          requests: 400, cpu_usage: 85.0}
                               |
                               v
                      Linear Regression Model
                               |
                               v
Output: predicted_requests = 395
```

The model learns:
> "Given the current hour of day, day of week, whether it's a weekend, current request count, and CPU usage — what will the request count be in the next hour?"

---

## SLA Constraints & Scaling Logic

### What is an SLA?

A **Service Level Agreement (SLA)** defines the minimum performance standards a cloud service must maintain. Common SLA metrics include response time, uptime, and throughput.

### Our SLA Rules

| Constraint | Threshold | Consequence |
|------------|-----------|-------------|
| CPU Utilisation | Must stay below **80%** | If exceeded, add extra container |
| Load per Container | Max **100 requests** per container | Determines minimum container count |

### Scaling Decision Flow

```
Predicted Requests = 350
                |
                v
   containers_needed = ceil(350 / 100) = 4
                |
                v
   CPU > 80%?  --YES-->  containers_needed = max(4, current + 1)
       |
       NO
       |
       v
   Compare with current containers
                |
       +--------+--------+
       |        |        |
   needed >  needed <  needed ==
   current   current   current
       |        |        |
   SCALE UP  SCALE DOWN  NO CHANGE
```

---

## Dashboard Features

The Streamlit dashboard is an **interactive, multi-tab application** with real-time controls:

### Sidebar — Configurable SLA & Model Controls

The sidebar is always visible and contains:
- **Train / Retrain Model** button — retrain the ML model on demand
- **Max CPU Utilisation (%)** slider — adjust the SLA CPU threshold (50%-100%, default 80%)
- **Max Requests per Container** slider — adjust per-container capacity (25-300, default 100)
- **Initial Containers** slider — set the starting container count (1-10, default 3)

Changing any slider **instantly updates** all tabs with the new SLA configuration.

---

### Tab 1: Full Simulation

Runs through all 100 workload records using the current SLA settings.

- **KPI Cards** — Peak Actual Load, Peak Predicted Load, Max Containers, Scale Events
- **Workload Chart** — Actual (blue) vs Predicted (orange dashed) requests
- **Container Chart** — Green step chart of allocated containers over time
- **CPU Chart** — Purple line with red SLA threshold (adjusts to sidebar value)
- **Scaling Log** — Full decision table with timestamps, actions, and reasons

---

### Tab 2: Live Control Panel (Real-Time Simulator)

Users can **drag sliders to simulate any workload scenario** and see instant results:

| Slider | Range | What it controls |
|--------|-------|-----------------|
| Timestamp | 1–200 | Simulated time step |
| Current Requests/sec | 0–800 | Incoming request rate |
| Current CPU Usage (%) | 0–100 | Server CPU load |
| Current Running Containers | 1–15 | Active containers |

**Instant output:**
- ML predicted next-step load (with delta from current)
- Required containers (with +/- change indicator)
- Current capacity display
- Scaling action: SCALE UP (red), SCALE DOWN (green), or NO CHANGE
- Decision breakdown with formula and SLA status
- **Bar chart** comparing Current Capacity vs Predicted Demand vs New Capacity

---

### Tab 3: What-If Scenarios

Compare **three traffic scenarios side by side**:

| Scenario | Default Values |
|----------|---------------|
| A (Low Traffic) | 80 reqs, 25% CPU |
| B (Medium Traffic) | 250 reqs, 60% CPU |
| C (Peak Traffic) | 450 reqs, 92% CPU |

Each scenario has independently adjustable:
- Requests/sec (number input)
- CPU Usage (number input)
- Current Containers (number input)

**Output:** Comparison table and grouped bar chart showing how each scenario triggers different scaling decisions.

---

### Tab 4: Step-by-Step Simulation

Walk through the dataset **one record at a time** using a slider:

- Select any time step (1 to 100)
- See exact metrics at that moment: requests, CPU, memory
- See ML prediction and scaling decision for that step
- SLA violation warnings highlight in real-time
- **History charts** show workload and container trends up to the selected step

---

### Tab 5: Architecture

- System architecture diagram
- Module map table (file → function mapping)
- Current SLA configuration display

---

## Installation & Setup

### Prerequisites
- Python 3.10 or higher installed on your system
- pip (Python package manager)

### Step 1: Navigate to the project directory

```bash
cd "D:\STUDENT X\ML PROJECTS\Cloud Recourses Auto Scaling using ML"
```

### Step 2: Install dependencies

```bash
pip install -r requirements.txt
```

This installs: pandas, numpy, scikit-learn, streamlit, matplotlib, joblib

### Step 3 (Optional): Train the model manually

```bash
python predictor.py
```

> **Note:** The dashboard will auto-train the model on first launch if no saved model exists.

---

## How to Run

### Launch the Dashboard

```bash
python -m streamlit run app.py
```

### Access in Browser

Open the URL shown in the terminal (typically):
```
http://localhost:8501
```

### Stop the Dashboard

Press `Ctrl + C` in the terminal.

---

## Demo Walkthrough

Here is what happens when you run the dashboard:

**Step 1 — Model Loads:**
The system loads the pre-trained Linear Regression model from `models/trained_model.pkl`.

**Step 2 — Simulation Starts:**
The monitoring module reads all 100 workload records from the dataset sequentially.

**Step 3 — For Each Record:**

| Action | What Happens |
|--------|-------------|
| Monitor | Reads timestamp, requests, cpu_usage, memory_usage |
| Predict | ML model forecasts next-step request count |
| Evaluate | SLA engine checks if predicted load exceeds capacity |
| Decide | Scaler calculates required containers |
| Allocate | Resource manager adjusts container count |
| Log | Decision is recorded for the audit trail |

**Step 4 — Results Display:**
After processing all 100 records, the dashboard renders all KPI cards, charts, and the scaling log.

### Example Decision (from the simulation):

```
Current State:
  - Timestamp:  66
  - Requests:   330 reqs/sec
  - CPU:        85.0%
  - Containers: 3

ML Prediction:  348 requests in next step

SLA Check:
  - CPU 85% > 80% threshold     --> VIOLATION
  - 348 reqs needs ceil(348/100) = 4 containers

Decision:  SCALE UP  from 3 --> 4 containers
Reason:    Predicted 348 reqs, need 4 containers (currently 3)
```

---

## Results & Observations

| Observation | Detail |
|-------------|--------|
| Model Accuracy | R2 = 0.9717 — model explains 97% of workload variance |
| Prediction Error | MAE = 12.71 — average error of ~13 requests (acceptable) |
| Scaling Responsiveness | System scales *before* overload, not after |
| Peak Containers | Up to 5 containers allocated during peak traffic |
| Total Scaling Events | 48 scaling actions across 100 time steps |
| SLA Compliance | Proactive scaling prevents most SLA violations |

**Key Insight:** The system successfully demonstrates that ML-based prediction enables **proactive scaling**, reducing the risk of SLA violations compared to traditional reactive approaches.

---

## Future Enhancements

| Enhancement | Description |
|-------------|-------------|
| LSTM Model | Use Long Short-Term Memory neural network for better time-series prediction |
| Real-time Data | Connect to actual cloud monitoring APIs (AWS CloudWatch, Prometheus) |
| Docker Integration | Deploy each "container" as an actual Docker container |
| Kubernetes Simulation | Simulate Kubernetes HPA (Horizontal Pod Autoscaler) behavior |
| Grafana Dashboard | Use Grafana for production-grade monitoring visualization |
| Multi-metric Prediction | Predict CPU and memory alongside request count |
| Anomaly Detection | Detect unusual traffic patterns (DDoS, flash crowds) |
| Cost Optimization | Factor in cloud pricing to minimize scaling costs |

---



---

*Built with Python, Scikit-learn, Streamlit, and Matplotlib*
