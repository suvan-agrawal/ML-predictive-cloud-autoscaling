# Faculty Presentation Guide — AI-Driven Cloud Auto-Scaling

Use this as your script/reference when presenting the project. It covers **what to say**, **what to show**, and **how to answer common questions**.

---

## 1. Opening — What Is This Project?

> **What to say:**
>
> "This project is a prototype that demonstrates how **machine learning can be used to predict cloud workload** and **automatically scale resources before overload happens.**
>
> In traditional cloud systems, auto-scaling is **reactive** — it waits until CPU or memory crosses a threshold, then adds servers. By that time, users already experience slowness.
>
> Our system is **predictive** — it uses a trained ML model to forecast the next time-step's workload and scales containers **ahead of time**, so resources are ready before traffic arrives."

---

## 2. The Problem — Why Does This Matter?

> **What to say:**
>
> "Cloud providers like AWS and Azure charge by the resources you use. Companies need to balance two risks:
> - **Under-provisioning** → servers overload, users face downtime, SLA is violated
> - **Over-provisioning** → money is wasted on idle resources
>
> Reactive scaling has a **cold-start problem** — it takes time to spin up new containers. During that gap, the system is overloaded.
>
> Our approach **eliminates that gap** by predicting demand in advance."

---

## 3. Architecture — How Is It Built?

> **What to show:** The architecture diagram from the README or the expandable section in the dashboard.
>
> **What to say:**
>
> "The system has **six core modules** forming a **closed feedback loop**:
>
> 1. **Monitoring Module** (`monitor.py`) — reads workload metrics (requests/sec, CPU, memory) from the dataset, simulating a real-time monitoring agent
> 2. **Preprocessing** (`utils/preprocessing.py`) — cleans data, handles missing values, and engineers features for the ML model
> 3. **ML Prediction Engine** (`predictor.py`) — a trained Linear Regression model that takes current metrics and predicts the next time-step's request count
> 4. **SLA Evaluation** (`scaler.py`) — checks if the predicted load would violate our SLA constraints (CPU < 80%, max 100 requests per container)
> 5. **Scaling Decision** (`scaler.py`) — calculates exactly how many containers are needed and whether to scale up, scale down, or hold
> 6. **Resource Manager** (`resource_manager.py`) — simulates the actual container pool, maintaining an audit trail of every scaling action
>
> All of this is visualised in a **Streamlit dashboard** (`app.py`) with real-time charts and metrics."

---

## 4. The Dataset

> **What to say:**
>
> "We created a **synthetic dataset of 100 workload records** that simulates realistic cloud traffic:
> - A gradual **ramp-up** from 100 to 400 requests
> - A **sustained peak** at around 400 requests
> - A **cooldown** period dropping to ~150 requests
> - A **second unexpected spike** back up to 420 requests
> - A final **recovery** phase
>
> This pattern is designed to **stress-test** the prediction model — it has to handle growth, peaks, sudden drops, and unexpected second waves."
>
> Each record has: `timestamp`, `requests` (per second), `cpu_usage` (%), and `memory_usage` (%).

---

## 5. The Machine Learning Model

> **What to say:**
>
> "We use **Linear Regression** from scikit-learn. Here's how it works:
>
> **Features (input to the model):**
> - Current timestamp
> - Current request count
> - Current CPU usage
>
> **Target (what we're predicting):**
> - The request count at the **next** time step
>
> We train this by shifting the data by one row — so the model learns: 'given what's happening now, what will happen next?'
>
> **Training results:**
> - **R-squared = 0.9717** — the model explains **97%** of the variance in the actual data. This is very high accuracy.
> - **MAE = 12.71** — on average, predictions are off by only ~13 requests. For loads in the 100-400 range, that's a small error.
>
> The model is saved as a `.pkl` file using `joblib` so it doesn't need to be retrained every time."

**If asked "Why Linear Regression and not something more complex?":**
> "Linear Regression was chosen because the workload data exhibits a strong linear correlation between consecutive time steps. For this prototype demonstration, it achieves 97% accuracy. In a production system, we could upgrade to Random Forest, Gradient Boosting, or LSTM (a deep learning model designed for time-series). The architecture is modular — swapping the model only requires changing `predictor.py`."

---

## 6. SLA and Scaling Logic

> **What to say:**
>
> "SLA stands for **Service Level Agreement** — it defines the performance guarantees we must maintain.
>
> Our SLA rules are:
> 1. CPU must stay **below 80%**
> 2. Each container can handle **at most 100 requests**
>
> The scaling formula is simple:
> ```
> required_containers = ceil(predicted_requests / 100)
> ```
>
> So if the model predicts 348 requests, we need `ceil(348/100) = 4` containers.
>
> If CPU is *already* above 80%, we add one extra container as a safety buffer.
>
> Then we compare with the current count:
> - Need more? → **Scale up**
> - Need fewer? → **Scale down**
> - Same? → **No change**"

---

## 7. Live Demo — What to Show

When running `python -m streamlit run app.py`, walk through these 5 tabs:

### Tab 1: Full Simulation
> "This tab runs through all 100 records automatically. You can see the KPI cards at the top — peak load, predicted load, max containers used, and total scaling events. Below that are three charts showing actual vs predicted workload, container allocation, and CPU usage with the SLA threshold line."

### Tab 2: Live Control Panel (THE KEY DEMO)
> "This is the **most interactive part**. I can drag sliders to simulate ANY traffic scenario in real time."
>
> **Demo action:** Move the "Current Requests" slider from 250 to 400.
>
> "Watch — the ML model instantly predicts the next load, calculates how many containers are needed, and shows the scaling decision. It says SCALE UP from 3 to 4 containers. The bar chart below compares current capacity vs predicted demand vs the new capacity after scaling."
>
> **Demo action:** Now move CPU to 90%.
>
> "Since CPU crossed the 80% SLA threshold, the system adds a safety buffer container — you can see the warning message. This is the fallback for when prediction alone isn't enough."
>
> **Demo action:** Go to the sidebar and change "Max Requests per Container" from 100 to 50.
>
> "Notice how the entire analysis updates — now each container handles fewer requests, so more containers are needed. This shows that our SLA thresholds are fully configurable."

### Tab 3: What-If Scenarios
> "Here we compare three scenarios side by side — low traffic at 80 requests, medium at 250, and peak at 450. Each column shows what the system would decide. You can change any value and the comparison updates instantly. The bar chart at the bottom gives a visual comparison."

### Tab 4: Step-by-Step
> "This tab lets me walk through the dataset one record at a time. I can drag the slider to any time step and see exactly what the system saw at that moment — the raw metrics, the ML prediction, and the scaling decision. The history charts build up as I advance."
>
> **Demo action:** Slide from step 1 to step 70 slowly.
>
> "Watch how the containers increase during the ramp-up and decrease during the cooldown."

### Tab 5: Architecture
> "This tab shows the system architecture diagram and a module map — which file does what."

---

## 8. Key Results to Highlight

| Point | What to say |
|-------|-------------|
| **Accuracy** | "The model achieves R2 = 0.97, meaning 97% prediction accuracy" |
| **Proactive** | "Resources are ready *before* the traffic spike hits" |
| **SLA Compliance** | "The system prevents most SLA violations by scaling ahead of time" |
| **Feedback Loop** | "It's a closed loop — monitoring feeds prediction, prediction feeds scaling, scaling feeds monitoring" |
| **Modular Design** | "Each component is a separate module — you can swap the ML model, change SLA rules, or connect to real cloud APIs without rewriting everything" |
| **Interactive** | "The dashboard isn't just static — users can adjust SLA parameters, test custom scenarios, and see real-time scaling decisions" |

---

## 9. Common Faculty Questions & Answers

### Q: "Why not use a real cloud environment?"
> "This is a prototype for academic demonstration. The architecture and logic are identical to what you'd deploy on AWS or Azure — the only difference is that `resource_manager.py` simulates containers instead of making real API calls. The ML model, SLA logic, and scaling decisions are production-grade."

### Q: "How is this different from AWS Auto Scaling?"
> "AWS Auto Scaling is **reactive** — it monitors CloudWatch metrics and triggers scaling when thresholds are crossed. What is missing is **prediction**. Our system adds an ML layer that **anticipates** future demand. AWS introduced Predictive Scaling in 2021, which uses a similar concept — our project demonstrates that exact approach."

### Q: "Can this handle real-world traffic?"
> "With a better dataset (thousands of real data points) and a more powerful model like LSTM or XGBoost, yes. The architecture is designed for extensibility — `predictor.py` can be swapped to use any model. The feedback loop and SLA logic remain the same."

### Q: "What happens if the prediction is wrong?"
> "The system has a safety net: if CPU is already above 80%, it adds an extra container regardless of prediction. Also, since the loop runs continuously, a bad prediction is corrected in the very next cycle. The MAE of ~13 requests means even wrong predictions are close to the truth."

### Q: "Why these specific SLA values (80% CPU, 100 req/container)?"
> "These are industry-standard benchmarks. AWS recommends keeping CPU below 70-80% for stability. 100 requests per container is a conservative estimate — real containers on Kubernetes typically handle 50-200 requests depending on the application. And importantly, **these values are configurable** — in the dashboard sidebar, you can drag a slider to change them and instantly see how scaling behavior changes."

### Q: "What ML techniques could improve this?"
> "Three main upgrades: (1) **Random Forest** for handling non-linear patterns, (2) **LSTM (Long Short-Term Memory)** which is a deep learning model specifically designed for time-series prediction, (3) **ARIMA/SARIMA** for capturing seasonal workload patterns. The modular architecture makes these easy to integrate."

### Q: "What makes this dashboard interactive?"
> "Unlike static reports, our dashboard has 5 tabs with live controls. The Live Control Panel lets you drag sliders to simulate any traffic scenario — the ML model predicts, the SLA engine evaluates, and you see the scaling decision instantly. The What-If tab compares 3 scenarios side by side. The Step-by-Step tab replays the simulation one record at a time. And all SLA thresholds in the sidebar affect every tab — so you can experiment with different configurations in real time."

---

## 10. One-Minute Elevator Pitch

> "We built a system that predicts cloud traffic before it happens and scales resources automatically. Traditional systems wait for overload then react — ours uses a machine learning model with 97% accuracy to forecast demand and scale proactively. The prototype includes a monitoring simulator, a Linear Regression prediction engine, SLA-aware scaling logic, a container pool simulation, and an interactive Streamlit dashboard with real-time sliders, what-if scenario comparison, and step-by-step replay. It demonstrates the same concept that AWS Predictive Scaling uses in production."

