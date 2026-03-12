# PROJECT SPECIFICATION
## AI-Driven Cloud Auto-Scaling Prototype

---

### 1. Goal

Build a prototype that demonstrates **predictive cloud resource auto-scaling** using machine learning, replacing reactive threshold-based scaling with proactive forecasting.

### 2. Core Feedback Loop

```
Workload → Monitoring → ML Prediction → SLA Evaluation → Scaling Decision → Resource Allocation → Monitoring
```

### 3. Modules

| Module               | File                     | Key Functions                         |
| -------------------- | ------------------------ | ------------------------------------ |
| Monitoring           | `monitor.py`             | `get_current_metrics()`               |
| Preprocessing        | `utils/preprocessing.py` | `load_dataset()`, `prepare_features()`|
| ML Prediction        | `predictor.py`           | `train_model()`, `predict_load()`     |
| SLA + Scaling        | `scaler.py`              | `evaluate_sla()`, `decide_scaling()`  |
| Resource Manager     | `resource_manager.py`    | `scale_up()`, `scale_down()`          |
| Dashboard            | `app.py`                 | Streamlit UI                          |

### 4. SLA Constraints

- Max CPU utilisation: **80 %**
- Capacity per container: **100 requests**

### 5. ML Approach

- **Model:** Linear Regression (scikit-learn)
- **Features:** timestamp, requests, cpu_usage
- **Target:** next-step request count
- **Persistence:** joblib → `models/trained_model.pkl`

### 6. Dataset

- File: `dataset/workload_dataset.csv`
- 100 records with columns: `timestamp, requests, cpu_usage, memory_usage`
- Pattern: ramp-up → peak → cooldown → second wave

### 7. Success Criteria

- ✅ Workload monitoring simulation
- ✅ ML-based demand prediction
- ✅ SLA-aware scaling decisions
- ✅ Container allocation simulation
- ✅ Interactive Streamlit dashboard with charts & metrics
