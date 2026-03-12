# Complete Project Explanation — Step by Step

Everything you need to understand about how this project works, how features connect, and what happens when you change values.

---

## Part 1: The Big Picture (What Problem Are We Solving?)

### Imagine This Scenario:

You run an online food delivery app. On normal days, you get **100 orders per minute**. Your servers can handle that fine with **1 server**.

But on **Friday night at 8 PM**, suddenly **500 orders per minute** start pouring in.

**What happens with a TRADITIONAL system?**
```
8:00 PM  →  100 orders  →  1 server  →  Everything fine
8:05 PM  →  200 orders  →  1 server  →  Getting slow...
8:10 PM  →  400 orders  →  1 server  →  OVERLOAD! Users see errors!
8:11 PM  →  System detects: "CPU is at 95%!" → Triggers new servers
8:15 PM  →  New servers are ready (took 4 minutes to boot up)
```

**Users had a BAD experience for 5-10 minutes.** That's reactive scaling.

**What happens with OUR system?**
```
8:00 PM  →  100 orders  →  ML model predicts: "500 orders coming at 8:10 PM"
8:01 PM  →  System scales UP to 5 servers IMMEDIATELY
8:10 PM  →  500 orders arrive  →  5 servers ready  →  Everything runs smooth!
```

**That's what this project demonstrates — predicting workload BEFORE it happens and scaling AHEAD of time.**

---

## Part 2: How the System Works (The Feedback Loop)

The system has 6 steps that repeat in a loop:

```
STEP 1: MONITOR      →  "What's happening right now?" (read current metrics)
STEP 2: PREPROCESS   →  "Clean and prepare the data for ML"
STEP 3: PREDICT      →  "What will happen NEXT?" (ML model forecasts)
STEP 4: EVALUATE SLA →  "Does the prediction violate our rules?"
STEP 5: DECIDE       →  "How many containers do we need?"
STEP 6: SCALE        →  "Add or remove containers"
         ↓
    Loop back to STEP 1 with the new state
```

Let me explain each step with a concrete example:

---

### STEP 1: Monitor (`monitor.py`)

**What it does:** Reads the current workload metrics from the dataset.

Think of it like a health monitor on a server. Every second, it checks:
- How many requests are coming in?
- How much CPU is being used?
- How much memory is being used?

**Example output:**
```
{
    "timestamp": 30,
    "requests": 300,        ← 300 requests per second right now
    "cpu_usage": 80.0,      ← CPU is at 80%
    "memory_usage": 90.0    ← Memory at 90%
}
```

In our project, we don't have a real server. So `monitor.py` reads from the CSV file row by row, pretending each row is a "new second" of data.

---

### STEP 2: Preprocess (`utils/preprocessing.py`)

**What it does:** Cleans the data and prepares it for the ML model.

The ML model can't directly understand raw data. We need to:
1. Fill in any missing values
2. Extract the right columns (timestamp, requests, cpu_usage)
3. Create the "target" — what we want to predict

**The key trick — how we create training data:**

```
Row 1:  timestamp=1,  requests=100,  cpu=30   →  Target: 110 (next row's requests)
Row 2:  timestamp=2,  requests=110,  cpu=32   →  Target: 120 (next row's requests)
Row 3:  timestamp=3,  requests=120,  cpu=35   →  Target: 115 (next row's requests)
...
```

We shift the data by one row. The model learns: "Given current values → predict the NEXT request count."

---

### STEP 3: Predict (`predictor.py`)

**What it does:** Uses the trained ML model to predict future workload.

**How Linear Regression works (simplified):**

The model learns a formula like:
```
predicted_requests = (a × timestamp) + (b × current_requests) + (c × cpu_usage) + d
```

During training, scikit-learn finds the best values for a, b, c, d that minimize prediction errors.

**Example:**
```
Input:   timestamp=30, requests=300, cpu=80
Model:   predicted_requests = (0.1 × 30) + (0.95 × 300) + (0.2 × 80) + 5
Output:  predicted_requests ≈ 307
```

The model is 97% accurate (R² = 0.9717), meaning its predictions are very close to the actual values.

---

### STEP 4: Evaluate SLA (`scaler.py` → `evaluate_sla()`)

**What it does:** Checks if the predicted workload violates our "rules."

**SLA = Service Level Agreement.** Think of it as a contract:
- "We promise CPU will stay below 80%"
- "Each container can handle at most 100 requests"

**Example check:**
```
Predicted requests = 307
Current CPU = 80%

Check 1: Is CPU > 80%?  →  80% equals 80%, so borderline (not violated)
Check 2: Does 307 need more than 1 container?
         307 / 100 = 3.07 → ceil(3.07) = 4 containers needed
         Yes, SLA requires scaling!
```

---

### STEP 5: Decide Scaling (`scaler.py` → `decide_scaling()`)

**What it does:** Calculates exactly how many containers we need and whether to scale up, down, or hold.

**The Formula:**
```
required_containers = ceil(predicted_requests / max_requests_per_container)
```

**Decision logic:**
```
IF required > current_containers  →  SCALE UP
IF required < current_containers  →  SCALE DOWN
IF required == current_containers →  NO CHANGE
```

**Extra safety rule:** If CPU is already above the threshold, add one extra container as a buffer.

---

### STEP 6: Scale (`resource_manager.py`)

**What it does:** Adjusts the container count.

```
Before: 3 containers (capacity = 300 requests)
Decision: Need 4 containers
Action: SCALE UP → add 1 container
After: 4 containers (capacity = 400 requests)
```

Then the loop starts again from Step 1 with the new state.

---

## Part 3: How the Dashboard Connects Everything

### Sidebar (Always Visible)

The sidebar has **3 sliders** that control the SLA rules:

| Slider | What it changes | Default |
|--------|----------------|---------|
| Max CPU Utilisation | The CPU threshold above which extra scaling kicks in | 80% |
| Max Requests per Container | How many requests one container can handle | 100 |
| Initial Containers | How many containers you start with | 3 |

**IMPORTANT:** When you change ANY sidebar slider, ALL tabs recalculate with the new values. This is how you experiment with different configurations.

---

### Tab 1: Full Simulation

**What happens:** The system runs through all 100 dataset records automatically using the current SLA settings.

**Connection to modules:**
```
For each of the 100 rows:
    monitor.py       → reads the row
    predictor.py     → predicts next request count
    scaler.py        → decides scaling action
    resource_manager → adjusts containers
    
Results → displayed as KPI cards, charts, and a log table
```

**What to look at:**
- KPI cards show summary stats
- Blue line = actual traffic, Orange line = ML prediction (they should track closely)
- Green step chart = how containers change over time
- Purple line = CPU usage, Red dashed line = SLA threshold

---

### Tab 2: Live Control Panel

**What happens:** YOU manually set the values with sliders, and the system runs ONE prediction cycle.

**Connection to modules:**
```
YOUR slider values
    ↓
predictor.py  → predict_load(your_values)  → predicted requests
    ↓
scaler.py     → decide_scaling(prediction, your_cpu, your_containers)
    ↓
Display: predicted load, required containers, scaling action, bar chart
```

This is the most interactive tab — you can see EXACTLY what the ML model predicts for any combination of values, and what scaling decision results.

---

### Tab 3: What-If Scenarios

**What happens:** Three scenarios run simultaneously with different input values.

**Connection:** Each scenario independently calls `predict_load()` and `decide_scaling()`, then results are shown side-by-side.

This lets you compare: "What would happen with low traffic vs medium vs peak?"

---

### Tab 4: Step-by-Step

**What happens:** You walk through the dataset ONE ROW AT A TIME using a slider.

**Connection:** At each step, it runs the full pipeline (monitor → predict → decide → scale) and shows you exactly what happened at that moment. The charts build up as you advance.

---

## Part 4: Dry Run Examples

### Dry Run 1: Normal Traffic

```
YOU SET (Live Control Panel):
    Timestamp:          50
    Current Requests:   150 reqs/sec
    Current CPU:        45%
    Current Containers: 3

WHAT HAPPENS:

Step 1 → ML Model receives: {timestamp:50, requests:150, cpu:45}
Step 2 → ML Model predicts:  ~157 requests in next time step
Step 3 → SLA Check:
         - CPU 45% < 80% threshold?     YES, safe ✓
         - Containers needed: ceil(157/100) = 2
Step 4 → Decision:
         - Required: 2 containers
         - Currently: 3 containers
         - 2 < 3 → SCALE DOWN
Step 5 → Result: Remove 1 container (3 → 2)
         New capacity: 2 × 100 = 200 reqs (enough for 157)

DISPLAY:
    ML Predicted Load:     157 reqs (+7 from current)
    Required Containers:   2 (-1 change)
    Scaling Action:        🟢 SCALE DOWN
    Reason:                "Predicted 157 reqs → only 2 containers needed (currently 3)"
```

---

### Dry Run 2: High Traffic

```
YOU SET:
    Timestamp:          70
    Current Requests:   400 reqs/sec
    Current CPU:        65%
    Current Containers: 3

WHAT HAPPENS:

Step 1 → ML Model receives: {timestamp:70, requests:400, cpu:65}
Step 2 → ML Model predicts:  ~410 requests
Step 3 → SLA Check:
         - CPU 65% < 80%?     YES, safe ✓
         - Containers needed: ceil(410/100) = 5
Step 4 → Decision:
         - Required: 5 containers
         - Currently: 3 containers
         - 5 > 3 → SCALE UP
Step 5 → Result: Add 2 containers (3 → 5)
         New capacity: 5 × 100 = 500 reqs (enough for 410)

DISPLAY:
    ML Predicted Load:     410 reqs (+10 from current)
    Required Containers:   5 (+2 change)
    Scaling Action:        🔴 SCALE UP
```

---

### Dry Run 3: High Traffic + Hot CPU (Safety Buffer)

```
YOU SET:
    Timestamp:          70
    Current Requests:   350 reqs/sec
    Current CPU:        92%          ← ABOVE 80% THRESHOLD!
    Current Containers: 3

WHAT HAPPENS:

Step 1 → ML Model receives: {timestamp:70, requests:350, cpu:92}
Step 2 → ML Model predicts:  ~365 requests
Step 3 → SLA Check:
         - CPU 92% > 80%?     ⚠️ VIOLATION!
         - Containers needed: ceil(365/100) = 4
Step 4 → Safety buffer activates:
         - Normal calculation: 4 containers
         - But CPU is over threshold → required = max(4, current+1) = max(4, 4) = 4
Step 5 → Decision:
         - Required: 4 containers
         - Currently: 3
         - 4 > 3 → SCALE UP
Step 6 → Result: Add 1 container (3 → 4)

DISPLAY:
    ⚠️ WARNING: "CPU 92.0% exceeds SLA threshold of 80%"
    Scaling Action: 🔴 SCALE UP
```

---

### Dry Run 4: Changing SLA Thresholds (Sidebar Effect)

**Scenario A — Default SLA (100 reqs/container):**
```
Predicted requests: 250
Containers needed: ceil(250/100) = 3
Current containers: 3
Action: NO CHANGE ⚪
```

**Scenario B — You change sidebar to 50 reqs/container:**
```
Predicted requests: 250    (same prediction!)
Containers needed: ceil(250/50) = 5     ← MORE containers needed!
Current containers: 3
Action: SCALE UP 🔴  (3 → 5)
```

**Scenario C — You change sidebar to 200 reqs/container:**
```
Predicted requests: 250    (same prediction!)
Containers needed: ceil(250/200) = 2    ← FEWER containers needed
Current containers: 3
Action: SCALE DOWN 🟢  (3 → 2)
```

**Key insight:** The same traffic prediction leads to DIFFERENT scaling decisions depending on your SLA configuration. This is why the sidebar sliders matter — they let you tune the system's sensitivity.

---

### Dry Run 5: Step-by-Step Progression

```
STEP 1:   requests=100, cpu=30  → predict=110  → need 2 → have 3 → SCALE DOWN to 2
STEP 5:   requests=130, cpu=37  → predict=140  → need 2 → have 2 → NO CHANGE
STEP 15:  requests=200, cpu=55  → predict=210  → need 3 → have 2 → SCALE UP to 3
STEP 30:  requests=300, cpu=80  → predict=310  → need 4 → have 3 → SCALE UP to 4
STEP 44:  requests=400, cpu=95  → predict=395  → need 4 → cpu>80 → SCALE UP to 5
STEP 55:  requests=200, cpu=60  → predict=190  → need 2 → have 5 → SCALE DOWN to 2
STEP 70:  requests=400, cpu=95  → predict=410  → need 5 → have 2 → SCALE UP to 5
STEP 88:  requests=150, cpu=50  → predict=160  → need 2 → have 5 → SCALE DOWN to 2
```

Notice the pattern:
- Traffic rises → containers scale UP
- Traffic drops → containers scale DOWN
- CPU above 80% → extra safety container added

---

## Part 5: How Everything Connects (One Diagram)

```
dataset/workload_dataset.csv
        |
        |  (read by)
        v
    monitor.py ─── get_current_metrics() ──→ {timestamp, requests, cpu, memory}
        |
        |  (fed to)
        v
    predictor.py ─── predict_load() ──→ predicted_requests (integer)
        |
        |  (checked by)
        v
    scaler.py ─── evaluate_sla() ──→ is SLA violated? (yes/no)
        |          decide_scaling() ──→ {action, required_containers, reason}
        |
        |  (executed by)
        v
    resource_manager.py ─── set_containers() ──→ new container count
        |
        |  (displayed by)
        v
    app.py ─── Streamlit Dashboard
        |       Tab 1: Full auto-run of all 100 rows
        |       Tab 2: YOU control the inputs with sliders
        |       Tab 3: Compare 3 scenarios side by side
        |       Tab 4: Walk through data one row at a time
        |       Tab 5: View architecture
        |
        |  (configured by)
        v
    Sidebar Sliders ── max_cpu, max_reqs_per_container, initial_containers
                       (these values are passed to scaler.py functions)
```

---

## Part 6: Quick Reference Card

| Question | Answer |
|----------|--------|
| What model does it use? | Linear Regression (scikit-learn) |
| What does it predict? | Next time-step's request count |
| How accurate is it? | R² = 0.9717 (97% accuracy) |
| What features go into the model? | timestamp, current requests, current CPU |
| What is the scaling formula? | `containers = ceil(predicted_requests / max_reqs_per_container)` |
| When does scale UP happen? | When predicted load needs more containers than currently running |
| When does scale DOWN happen? | When predicted load needs fewer containers |
| What is the safety buffer? | If CPU > threshold, add 1 extra container |
| What are the default SLA values? | CPU < 80%, 100 requests per container |
| Can SLA be changed live? | Yes, sidebar sliders change it across all tabs |
| Where is the model saved? | `models/trained_model.pkl` |
| What library saves the model? | Joblib |
