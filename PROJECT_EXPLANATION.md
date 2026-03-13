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

Think of it like a health monitor on a server. Every hour, it checks:
- What time is it? (hour, day of week)
- How many requests are coming in?
- How much CPU is being used?
- How much memory is being used?

**Example output:**
```
{
    "datetime": "2026-02-05 14:00",
    "hour": 14,                ← 2 PM
    "day_of_week": 4,          ← Thursday
    "is_weekend": 0,           ← Weekday
    "requests": 380,           ← 380 requests per hour right now
    "cpu_usage": 80.0,         ← CPU is at 80%
    "memory_usage": 82.0       ← Memory at 82%
}
```

In our project, we don't have a real server. So `monitor.py` reads from the CSV file row by row, pretending each row is a "new hour" of data.

---

### STEP 2: Preprocess (`utils/preprocessing.py`)

**What it does:** Cleans the data and prepares it for the ML model.

The ML model can't directly understand raw data. We need to:
1. Fill in any missing values
2. Extract time-aware features: `hour`, `day_of_week`, `is_weekend`, `requests`, `cpu_usage`
3. Create the "target" — what we want to predict

**The key trick — how we create training data:**

```
Row 1:  hour=0,  dow=0, wknd=1, reqs=42,  cpu=12  →  Target: 44 (next row's requests)
Row 2:  hour=1,  dow=0, wknd=1, reqs=44,  cpu=13  →  Target: 46 (next row's requests)
Row 3:  hour=2,  dow=0, wknd=1, reqs=46,  cpu=14  →  Target: 50 (next row's requests)
...
```

We shift the data by one row. The model learns: "Given the current hour, day, and workload → predict the NEXT hour's request count."

---

### STEP 3: Predict (`predictor.py`)

**What it does:** Uses the trained ML model to predict future workload.

**How Linear Regression works (simplified):**

The model learns a formula like:
```
predicted_requests = (a × hour) + (b × day_of_week) + (c × is_weekend) + (d × current_requests) + (e × cpu_usage) + f
```

During training, scikit-learn finds the best values for a, b, c, d, e, f that minimize prediction errors.

**Example:**
```
Input:   hour=12, day_of_week=3, is_weekend=0, requests=400, cpu=85
Output:  predicted_requests ≈ 395
```

The model is 90% accurate (R² = 0.90), meaning its predictions closely track the actual values even with daily cycles and noise.

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

**What happens:** The system runs through all 360 hourly records (15 days) automatically using the current SLA settings.

**Connection to modules:**
```
For each of the 360 rows:
    monitor.py       → reads the row (datetime, hour, day, requests, cpu)
    predictor.py     → predicts next hour's request count
    scaler.py        → decides scaling action
    resource_manager → adjusts containers
    
Results → displayed as KPI cards, charts, and a log table
```

**What to look at:**
- KPI cards show summary stats
- Blue line = actual traffic, Orange line = ML prediction (they should track closely)
- Green step chart = how containers change over time (shows daily cycles!)
- Purple line = CPU usage, Red dashed line = SLA threshold
- Orange bar chart = Average Traffic by Hour of Day (shows the daily pattern)

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
    Hour of Day:        3 (3 AM — night)
    Day of Week:        Tuesday (weekday)
    Current Requests:   65 reqs/hour
    Current CPU:        15%
    Current Containers: 3

WHAT HAPPENS:

Step 1 → ML Model receives: {hour:3, dow:2, wknd:0, requests:65, cpu:15}
Step 2 → ML Model predicts:  ~70 requests in next hour
Step 3 → SLA Check:
         - CPU 15% < 80% threshold?     YES, safe ✓
         - Containers needed: ceil(70/100) = 1
Step 4 → Decision:
         - Required: 1 container
         - Currently: 3 containers
         - 1 < 3 → SCALE DOWN
Step 5 → Result: Remove 2 containers (3 → 1)
         New capacity: 1 × 100 = 100 reqs (enough for 70)

DISPLAY:
    ML Predicted Load:     70 reqs (+5 from current)
    Required Containers:   1 (-2 change)
    Scaling Action:        🟢 SCALE DOWN
    Reason:                "Predicted 70 reqs → only 1 container needed (currently 3)"
```

---

### Dry Run 2: High Traffic

```
YOU SET:
    Hour of Day:        12 (noon — peak)
    Day of Week:        Wednesday (weekday)
    Current Requests:   400 reqs/hour
    Current CPU:        85%
    Current Containers: 3

WHAT HAPPENS:

Step 1 → ML Model receives: {hour:12, dow:3, wknd:0, requests:400, cpu:85}
Step 2 → ML Model predicts:  ~395 requests
Step 3 → SLA Check:
         - CPU 85% > 80%?     ⚠️ VIOLATION!
         - Containers needed: ceil(395/100) = 4
Step 4 → Safety buffer activates → max(4, current+1) = max(4, 4) = 4
Step 5 → Decision:
         - Required: 4 containers
         - Currently: 3 containers
         - 4 > 3 → SCALE UP
Step 6 → Result: Add 1 container (3 → 4)
         New capacity: 4 × 100 = 400 reqs (enough for 395)

DISPLAY:
    ML Predicted Load:     395 reqs (-5 from current)
    Required Containers:   4 (+1 change)
    Scaling Action:        🔴 SCALE UP
```

---

### Dry Run 3: High Traffic + Hot CPU (Safety Buffer)

```
YOU SET:
    Hour of Day:        12 (noon)
    Day of Week:        Saturday (weekend!)
    Current Requests:   280 reqs/hour     ← lower because weekend
    Current CPU:        60%
    Current Containers: 3

WHAT HAPPENS:

Step 1 → ML Model receives: {hour:12, dow:6, wknd:1, requests:280, cpu:60}
Step 2 → ML Model predicts:  ~270 requests (weekend → model predicts lower)
Step 3 → SLA Check:
         - CPU 60% < 80%?     YES, safe ✓
         - Containers needed: ceil(270/100) = 3
Step 4 → Decision:
         - Required: 3 containers
         - Currently: 3
         - 3 == 3 → NO CHANGE
Step 5 → Result: Keep 3 containers

DISPLAY:
    ML Predicted Load:     270 reqs (-10 from current)
    Scaling Action:        ⚪ NO CHANGE
    Note: Weekend traffic is lower, so fewer containers needed
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
Feb 01 03:00 (Sun)  reqs=50,  cpu=12  → predict=55   → need 1 → have 3 → SCALE DOWN to 1
Feb 01 09:00 (Sun)  reqs=145, cpu=32  → predict=150  → need 2 → have 1 → SCALE UP to 2
Feb 02 12:00 (Mon)  reqs=380, cpu=78  → predict=370  → need 4 → have 2 → SCALE UP to 4
Feb 02 22:00 (Mon)  reqs=120, cpu=28  → predict=65   → need 1 → have 4 → SCALE DOWN to 1
Feb 07 11:00 (Sat)  reqs=260, cpu=55  → predict=270  → need 3 → have 1 → SCALE UP to 3
Feb 10 13:00 (Tue)  reqs=440, cpu=90  → predict=420  → need 5 → cpu>80 → SCALE UP to 5
Feb 15 03:00 (Sun)  reqs=55,  cpu=15  → predict=60   → need 1 → have 5 → SCALE DOWN to 1
```

Notice the patterns:
- **Daily cycle:** containers scale UP during business hours, DOWN at night
- **Weekend dip:** weekend peaks are lower than weekday peaks
- **CPU above 80%** → extra safety container added
- **Day-over-day growth** → later days need slightly more containers

---

## Part 5: How Everything Connects (One Diagram)

```
dataset/workload_dataset.csv
        |
        |  (read by)
        v
    monitor.py ─── get_current_metrics() ──→ {datetime, hour, dow, wknd, requests, cpu, mem}
        |
        |  (fed to)
        v
    predictor.py ─── predict_load() ──→ predicted_requests (integer)
        |             Uses 5 features: hour, day_of_week, is_weekend, requests, cpu_usage
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
        |       Tab 1: Full auto-run of all 360 hourly rows
        |       Tab 2: YOU control hour, day, requests, CPU with sliders
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
| What does it predict? | Next hour's request count |
| How accurate is it? | R² = 0.90 (90% accuracy) |
| How many data points? | 360 records (15 days × 24 hours) |
| What features go into the model? | hour, day_of_week, is_weekend, requests, cpu_usage |
| What is the scaling formula? | `containers = ceil(predicted_requests / max_reqs_per_container)` |
| When does scale UP happen? | When predicted load needs more containers than currently running |
| When does scale DOWN happen? | When predicted load needs fewer containers |
| What is the safety buffer? | If CPU > threshold, add 1 extra container |
| What are the default SLA values? | CPU < 80%, 100 requests per container |
| Can SLA be changed live? | Yes, sidebar sliders change it across all tabs |
| Where is the model saved? | `models/trained_model.pkl` |
| What library saves the model? | Joblib |
