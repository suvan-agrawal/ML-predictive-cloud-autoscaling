"""
AI-Driven Cloud Auto-Scaling Dashboard
───────────────────────────────────────
Interactive Streamlit application with:
  - Real-time manual scaling simulator (sliders)
  - Configurable SLA thresholds
  - Step-by-step dataset simulation
  - What-If scenario testing
  - Full historical simulation with charts

Updated: uses datetime timestamps and time-aware ML features
(hour, day_of_week, is_weekend).
"""

import os
import sys
import math
import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib
matplotlib.use("Agg")
from streamlit_autorefresh import st_autorefresh
from datetime import datetime

# ── Ensure project root is on sys.path ───────
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from monitor import WorkloadMonitor
from predictor import train_model, predict_load, load_model, MODEL_PATH
from scaler import decide_scaling, evaluate_sla
from resource_manager import ResourceManager
from utils.preprocessing import get_processed_data
from live_generator import generate_live_metrics

# ──────────────────────────────────────────────
#  Page config
# ──────────────────────────────────────────────
st.set_page_config(
    page_title="AI Cloud Auto-Scaler",
    page_icon="☁️",
    layout="wide",
)

# ──────────────────────────────────────────────
#  Custom CSS
# ──────────────────────────────────────────────
st.markdown("""
<style>
    div[data-testid="stMetricValue"] { font-size: 1.6rem; }
</style>
""", unsafe_allow_html=True)

# ──────────────────────────────────────────────
#  Sidebar — SLA Config & Model Controls
# ──────────────────────────────────────────────
with st.sidebar:
    st.header("Model Controls")
    if st.button("Train / Retrain Model", use_container_width=True):
        with st.spinner("Training model ..."):
            X, y, _ = get_processed_data()
            result = train_model(X, y)
        st.success("Model trained!")
        st.json({"MAE": result["mae"], "R2": result["r2"],
                 "Train": result["train_size"], "Test": result["test_size"]})

    st.divider()
    st.header("SLA Configuration")
    st.caption("Adjust these to see how scaling behavior changes across ALL tabs.")

    sla_max_cpu = st.slider(
        "Max CPU Utilisation (%)", min_value=50, max_value=100,
        value=80, step=5, help="Scale up if CPU exceeds this threshold"
    )
    sla_max_reqs = st.slider(
        "Max Requests per Container", min_value=25, max_value=300,
        value=100, step=25, help="Each container can handle up to this many requests"
    )
    sla_initial_containers = st.slider(
        "Initial Containers", min_value=1, max_value=10,
        value=3, step=1, help="Starting number of containers"
    )

# ──────────────────────────────────────────────
#  Ensure a trained model exists
# ──────────────────────────────────────────────
if not os.path.exists(MODEL_PATH):
    st.info("No trained model found. Training now ...")
    X, y, _ = get_processed_data()
    train_model(X, y)
    st.success("Model trained automatically!")

model = load_model()

# ──────────────────────────────────────────────
#  Header
# ──────────────────────────────────────────────
st.title("AI-Driven Cloud Auto-Scaling Dashboard")
st.markdown(
    "This prototype demonstrates **predictive auto-scaling** using Machine Learning. "
    "The dataset covers **15 days of hourly data** with realistic traffic patterns "
    "(business-hour peaks, night lulls, weekend dips). Use the **sidebar** to adjust "
    "SLA thresholds and the **tabs** below to explore different interactive modes."
)
st.divider()

# ══════════════════════════════════════════════
#  TABS — Main navigation
# ══════════════════════════════════════════════
tab_sim, tab_live, tab_whatif, tab_step, tab_monitor, tab_arch = st.tabs([
    "Full Simulation",
    "Live Control Panel",
    "What-If Scenarios",
    "Step-by-Step",
    "Live Monitor",
    "Architecture",
])

# ══════════════════════════════════════════════
#  TAB 1 — Full Historical Simulation
# ══════════════════════════════════════════════
with tab_sim:
    st.subheader("Full Dataset Simulation (15 Days)")
    st.caption("Runs through all 360 hourly records using the current SLA settings.")

    monitor = WorkloadMonitor()
    rm = ResourceManager(initial_containers=sla_initial_containers)

    datetimes, actual_reqs, pred_reqs = [], [], []
    container_counts, cpu_vals, actions_log = [], [], []

    while True:
        metrics = monitor.get_current_metrics()
        if metrics is None:
            break

        pred = predict_load(metrics, model)
        decision = decide_scaling(
            pred, metrics["cpu_usage"],
            rm.get_current_resources()["containers"],
            max_cpu=sla_max_cpu, max_reqs=sla_max_reqs,
        )
        rm.set_containers(decision["required_containers"])

        datetimes.append(pd.Timestamp(metrics["datetime"]))
        actual_reqs.append(metrics["requests"])
        pred_reqs.append(pred)
        container_counts.append(rm.get_current_resources()["containers"])
        cpu_vals.append(metrics["cpu_usage"])
        actions_log.append({
            "Datetime": metrics["datetime"],
            "Hour": metrics["hour"],
            "Day": ["Sun","Mon","Tue","Wed","Thu","Fri","Sat"][metrics["day_of_week"]],
            "Actual Reqs": metrics["requests"],
            "Predicted": pred,
            "CPU %": metrics["cpu_usage"],
            "Action": decision["action"],
            "Containers": rm.get_current_resources()["containers"],
            "Reason": decision["reason"],
        })

    # ── KPIs ──
    st.markdown("#### Key Performance Indicators")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Peak Actual Load", f"{max(actual_reqs)} reqs")
    c2.metric("Peak Predicted Load", f"{max(pred_reqs)} reqs")
    c3.metric("Max Containers", f"{max(container_counts)}")
    scale_events = sum(1 for a in actions_log if a["Action"] != "no_change")
    c4.metric("Scale Events", f"{scale_events}")

    # ── Charts ──
    st.markdown("---")
    st.markdown("#### Workload vs Predicted Load (15 Days)")

    fig1, ax1 = plt.subplots(figsize=(14, 4))
    ax1.plot(datetimes, actual_reqs, label="Actual Requests", linewidth=1.5, color="#2196F3")
    ax1.plot(datetimes, pred_reqs, label="Predicted Requests", linewidth=1.5, linestyle="--", color="#FF5722")
    ax1.set_xlabel("Date & Time")
    ax1.set_ylabel("Requests / hour")
    ax1.legend()
    ax1.set_title("Actual vs Predicted Workload Over 15 Days")
    ax1.xaxis.set_major_formatter(mdates.DateFormatter("%b %d"))
    ax1.xaxis.set_major_locator(mdates.DayLocator())
    plt.xticks(rotation=45)
    ax1.grid(True, alpha=0.3)
    fig1.tight_layout()
    st.pyplot(fig1)

    col_chart1, col_chart2 = st.columns(2)

    with col_chart1:
        st.markdown("#### Container Allocation")
        fig2, ax2 = plt.subplots(figsize=(7, 3))
        ax2.step(datetimes, container_counts, where="mid", linewidth=1.5, color="#4CAF50")
        ax2.fill_between(datetimes, container_counts, step="mid", alpha=0.2, color="#4CAF50")
        ax2.set_xlabel("Date & Time")
        ax2.set_ylabel("Containers")
        ax2.set_title("Allocated Containers Over Time")
        ax2.xaxis.set_major_formatter(mdates.DateFormatter("%b %d"))
        ax2.xaxis.set_major_locator(mdates.DayLocator(interval=2))
        plt.xticks(rotation=45)
        ax2.grid(True, alpha=0.3)
        fig2.tight_layout()
        st.pyplot(fig2)

    with col_chart2:
        st.markdown("#### CPU Utilisation")
        fig3, ax3 = plt.subplots(figsize=(7, 3))
        ax3.plot(datetimes, cpu_vals, linewidth=1.5, color="#9C27B0")
        ax3.axhline(y=sla_max_cpu, color="red", linestyle="--", linewidth=1,
                     label=f"SLA Threshold ({sla_max_cpu}%)")
        ax3.set_xlabel("Date & Time")
        ax3.set_ylabel("CPU %")
        ax3.set_title("CPU Usage with SLA Threshold")
        ax3.legend()
        ax3.xaxis.set_major_formatter(mdates.DateFormatter("%b %d"))
        ax3.xaxis.set_major_locator(mdates.DayLocator(interval=2))
        plt.xticks(rotation=45)
        ax3.grid(True, alpha=0.3)
        fig3.tight_layout()
        st.pyplot(fig3)

    # ── Hourly pattern chart ──
    st.markdown("---")
    st.markdown("#### Average Traffic by Hour of Day")
    df_hourly = pd.DataFrame({"hour": [a["Hour"] for a in actions_log],
                               "requests": actual_reqs})
    hourly_avg = df_hourly.groupby("hour")["requests"].mean()

    fig_h, ax_h = plt.subplots(figsize=(10, 3))
    ax_h.bar(hourly_avg.index, hourly_avg.values, color="#FF9800", edgecolor="white")
    ax_h.set_xlabel("Hour of Day")
    ax_h.set_ylabel("Avg Requests")
    ax_h.set_title("Average Hourly Traffic Pattern")
    ax_h.set_xticks(range(24))
    ax_h.set_xticklabels([f"{h:02d}" for h in range(24)])
    ax_h.grid(True, alpha=0.2, axis="y")
    fig_h.tight_layout()
    st.pyplot(fig_h)

    st.markdown("---")
    st.markdown("#### Scaling Actions Log")
    df_log = pd.DataFrame(actions_log)
    st.dataframe(df_log, use_container_width=True, hide_index=True)

# ══════════════════════════════════════════════
#  TAB 2 — Live Control Panel
# ══════════════════════════════════════════════
with tab_live:
    st.subheader("Real-Time Scaling Simulator")
    st.markdown(
        "Drag the sliders to simulate **any workload scenario** and instantly see "
        "the ML prediction, SLA evaluation, and scaling decision."
    )
    st.markdown("---")

    # ── User input sliders ──
    lc1, lc2, lc3 = st.columns(3)

    with lc1:
        live_hour = st.slider(
            "Hour of Day", min_value=0, max_value=23, value=14,
            help="Simulated hour (0=midnight, 12=noon, 18=evening)"
        )
    with lc2:
        live_requests = st.slider(
            "Current Requests / hour", min_value=0, max_value=800, value=250,
            step=10, help="Incoming request rate right now"
        )
    with lc3:
        live_cpu = st.slider(
            "Current CPU Usage (%)", min_value=0.0, max_value=100.0,
            value=65.0, step=1.0, help="Current server CPU utilisation"
        )

    lc4, lc5, lc6 = st.columns(3)

    with lc4:
        live_dow = st.selectbox(
            "Day of Week",
            options=[0, 1, 2, 3, 4, 5, 6],
            format_func=lambda x: ["Sunday","Monday","Tuesday","Wednesday",
                                    "Thursday","Friday","Saturday"][x],
            index=2,  # Tuesday default
            help="Day of the week (affects weekend prediction)"
        )
    with lc5:
        live_is_weekend = 1 if live_dow in (0, 6) else 0
        st.metric("Weekend?", "Yes" if live_is_weekend else "No")
    with lc6:
        live_containers = st.slider(
            "Current Running Containers", min_value=1, max_value=15, value=3,
            help="How many containers are currently active"
        )

    st.markdown("---")

    # ── Run prediction & decision ──
    live_metrics = {
        "hour": live_hour,
        "day_of_week": live_dow,
        "is_weekend": live_is_weekend,
        "requests": live_requests,
        "cpu_usage": live_cpu,
    }
    live_pred = predict_load(live_metrics, model)
    live_sla = evaluate_sla(live_pred, live_cpu, max_cpu=sla_max_cpu, max_reqs=sla_max_reqs)
    live_decision = decide_scaling(
        live_pred, live_cpu, live_containers,
        max_cpu=sla_max_cpu, max_reqs=sla_max_reqs,
    )

    # ── Display results ──
    result_cols = st.columns(4)
    result_cols[0].metric("ML Predicted Load", f"{live_pred} reqs",
                          delta=f"{live_pred - live_requests:+d} from current")
    result_cols[1].metric("Required Containers", f"{live_decision['required_containers']}",
                          delta=f"{live_decision['required_containers'] - live_containers:+d} change")
    result_cols[2].metric("Current Capacity", f"{live_containers * sla_max_reqs} reqs",
                          help=f"{live_containers} containers x {sla_max_reqs} reqs each")

    action_emoji = {"scale_up": "SCALE UP", "scale_down": "SCALE DOWN", "no_change": "NO CHANGE"}
    result_cols[3].metric("Scaling Action", action_emoji.get(live_decision["action"], live_decision["action"]))

    # ── Detailed breakdown ──
    st.markdown("---")
    detail_left, detail_right = st.columns(2)

    with detail_left:
        st.markdown("#### Decision Breakdown")
        day_name = ["Sunday","Monday","Tuesday","Wednesday","Thursday","Friday","Saturday"][live_dow]
        st.markdown(f"- **Time:** {live_hour:02d}:00 on {day_name} {'(Weekend)' if live_is_weekend else '(Weekday)'}")
        st.markdown(f"- **Prediction:** {live_pred} requests expected at next time step")
        st.markdown(f"- **Containers needed:** ceil({live_pred} / {sla_max_reqs}) = "
                    f"**{math.ceil(live_pred / sla_max_reqs)}**")
        if live_cpu > sla_max_cpu:
            st.warning(f"CPU {live_cpu}% exceeds SLA threshold of {sla_max_cpu}% -- adding safety buffer!")
        else:
            st.success(f"CPU {live_cpu}% is within SLA threshold of {sla_max_cpu}%")
        st.info(f"**Reason:** {live_decision['reason']}")

    with detail_right:
        st.markdown("#### Visual Capacity Check")

        capacity = live_containers * sla_max_reqs
        new_capacity = live_decision["required_containers"] * sla_max_reqs

        fig_cap, ax_cap = plt.subplots(figsize=(5, 3))
        bars = ax_cap.bar(
            ["Current\nCapacity", "Predicted\nDemand", "New\nCapacity"],
            [capacity, live_pred, new_capacity],
            color=["#2196F3", "#FF5722", "#4CAF50"],
            edgecolor="white", linewidth=2,
        )
        for bar, val in zip(bars, [capacity, live_pred, new_capacity]):
            ax_cap.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 5,
                        str(val), ha="center", va="bottom", fontweight="bold")
        ax_cap.set_ylabel("Requests")
        ax_cap.set_title("Capacity vs Demand")
        ax_cap.grid(True, alpha=0.2, axis="y")
        fig_cap.tight_layout()
        st.pyplot(fig_cap)


# ══════════════════════════════════════════════
#  TAB 3 — What-If Scenarios
# ══════════════════════════════════════════════
with tab_whatif:
    st.subheader("What-If Scenario Comparison")
    st.markdown(
        "Compare how the system responds to **different traffic scenarios** side by side. "
        "Adjust each scenario's parameters independently."
    )
    st.markdown("---")

    scenario_cols = st.columns(3)
    scenarios = []

    labels = ["Scenario A (Night - Low)", "Scenario B (Afternoon - Med)", "Scenario C (Peak Hour)"]
    defaults_reqs = [60, 250, 450]
    defaults_cpu = [15.0, 60.0, 92.0]
    defaults_hour = [3, 14, 11]
    defaults_dow = [2, 2, 1]  # Tuesday, Tuesday, Monday

    for i, (col, label, def_req, def_cpu, def_hr, def_dw) in enumerate(
        zip(scenario_cols, labels, defaults_reqs, defaults_cpu, defaults_hour, defaults_dow)
    ):
        with col:
            st.markdown(f"**{label}**")
            s_hour = st.number_input(
                "Hour (0-23)", min_value=0, max_value=23,
                value=def_hr, step=1, key=f"scenario_hour_{i}"
            )
            s_reqs = st.number_input(
                "Requests/hour", min_value=0, max_value=1000,
                value=def_req, step=10, key=f"scenario_reqs_{i}"
            )
            s_cpu = st.number_input(
                "CPU Usage (%)", min_value=0.0, max_value=100.0,
                value=def_cpu, step=5.0, key=f"scenario_cpu_{i}"
            )
            s_dow = st.selectbox(
                "Day", options=[0,1,2,3,4,5,6],
                format_func=lambda x: ["Sun","Mon","Tue","Wed","Thu","Fri","Sat"][x],
                index=def_dw, key=f"scenario_dow_{i}"
            )
            s_containers = st.number_input(
                "Current Containers", min_value=1, max_value=15,
                value=3, step=1, key=f"scenario_cont_{i}"
            )
            scenarios.append({
                "label": label, "hour": s_hour,
                "requests": s_reqs, "cpu": s_cpu,
                "dow": s_dow, "is_weekend": 1 if s_dow in (0,6) else 0,
                "containers": s_containers,
            })

    st.markdown("---")
    st.markdown("#### Comparison Results")

    # Compute predictions for each scenario
    scenario_results = []
    for s in scenarios:
        metrics = {"hour": s["hour"], "day_of_week": s["dow"],
                   "is_weekend": s["is_weekend"],
                   "requests": s["requests"], "cpu_usage": s["cpu"]}
        pred = predict_load(metrics, model)
        dec = decide_scaling(pred, s["cpu"], s["containers"],
                             max_cpu=sla_max_cpu, max_reqs=sla_max_reqs)
        scenario_results.append({"pred": pred, "decision": dec})

    # Display comparison table
    rows = [
        ("Predicted Load", [f"{r['pred']} reqs" for r in scenario_results]),
        ("Required Containers", [f"{r['decision']['required_containers']}" for r in scenario_results]),
        ("Action", [r["decision"]["action"].replace("_", " ").upper() for r in scenario_results]),
        ("New Capacity", [f"{r['decision']['required_containers'] * sla_max_reqs} reqs" for r in scenario_results]),
    ]

    row_header = st.columns(4)
    row_header[0].markdown("**Metric**")
    for i in range(3):
        row_header[i+1].markdown(f"**{'ABC'[i]}**")

    for row_label, values in rows:
        row_cols = st.columns(4)
        row_cols[0].write(row_label)
        for i, v in enumerate(values):
            row_cols[i + 1].write(v)

    # ── Bar chart comparison ──
    st.markdown("---")
    fig_comp, ax_comp = plt.subplots(figsize=(10, 4))
    x = np.arange(3)
    width = 0.25

    demands = [r["pred"] for r in scenario_results]
    current_caps = [s["containers"] * sla_max_reqs for s in scenarios]
    new_caps = [r["decision"]["required_containers"] * sla_max_reqs for r in scenario_results]

    ax_comp.bar(x - width, current_caps, width, label="Current Capacity", color="#2196F3")
    ax_comp.bar(x, demands, width, label="Predicted Demand", color="#FF5722")
    ax_comp.bar(x + width, new_caps, width, label="Scaled Capacity", color="#4CAF50")
    ax_comp.set_xticks(x)
    ax_comp.set_xticklabels(["Scenario A", "Scenario B", "Scenario C"])
    ax_comp.set_ylabel("Requests")
    ax_comp.set_title("Capacity vs Demand -- Scenario Comparison")
    ax_comp.legend()
    ax_comp.grid(True, alpha=0.2, axis="y")
    fig_comp.tight_layout()
    st.pyplot(fig_comp)


# ══════════════════════════════════════════════
#  TAB 4 — Step-by-Step Simulation
# ══════════════════════════════════════════════
with tab_step:
    st.subheader("Step-by-Step Simulation")
    st.markdown(
        "Walk through the dataset **one record at a time**. Use the slider to pick "
        "any time step and see what the system decides at that exact moment."
    )
    st.markdown("---")

    monitor_step = WorkloadMonitor()
    total_records = monitor_step.total_records()

    step_idx = st.slider("Select Time Step", min_value=1, max_value=total_records, value=1)

    monitor_step.reset()
    rm_step = ResourceManager(initial_containers=sla_initial_containers)

    step_history = []
    for i in range(step_idx):
        m = monitor_step.get_current_metrics()
        if m is None:
            break
        p = predict_load(m, model)
        d = decide_scaling(p, m["cpu_usage"], rm_step.get_current_resources()["containers"],
                           max_cpu=sla_max_cpu, max_reqs=sla_max_reqs)
        rm_step.set_containers(d["required_containers"])
        step_history.append({"metrics": m, "pred": p, "decision": d,
                             "containers": rm_step.get_current_resources()["containers"]})

    current_step = step_history[-1]
    m = current_step["metrics"]
    p = current_step["pred"]
    d = current_step["decision"]

    # ── Current step display ──
    day_name = ["Sun","Mon","Tue","Wed","Thu","Fri","Sat"][m["day_of_week"]]
    st.markdown(f"### Step {step_idx} of {total_records} — {m['datetime']} ({day_name})")

    sc1, sc2, sc3, sc4 = st.columns(4)
    sc1.metric("Requests", f"{m['requests']} /hour")
    sc2.metric("CPU Usage", f"{m['cpu_usage']}%",
               delta="OVER SLA" if m["cpu_usage"] > sla_max_cpu else "OK",
               delta_color="inverse" if m["cpu_usage"] > sla_max_cpu else "normal")
    sc3.metric("Memory Usage", f"{m['memory_usage']}%")
    sc4.metric("Predicted Next Load", f"{p} reqs")

    st.markdown("---")

    sc5, sc6, sc7 = st.columns(3)
    sc5.metric("Scaling Action", d["action"].replace("_"," ").upper())
    sc6.metric("Containers After", f"{d['required_containers']}")
    sc7.metric("New Capacity", f"{d['required_containers'] * sla_max_reqs} reqs")

    st.info(f"**Reason:** {d['reason']}")

    # ── Step history mini chart ──
    if len(step_history) > 1:
        st.markdown("#### History up to this step")

        step_dts = [pd.Timestamp(h["metrics"]["datetime"]) for h in step_history]
        step_actual = [h["metrics"]["requests"] for h in step_history]
        step_preds = [h["pred"] for h in step_history]
        step_conts = [h["containers"] for h in step_history]

        fig_step, (ax_s1, ax_s2) = plt.subplots(1, 2, figsize=(14, 3))

        ax_s1.plot(step_dts, step_actual, label="Actual", linewidth=1.5, color="#2196F3")
        ax_s1.plot(step_dts, step_preds, label="Predicted", linewidth=1.5,
                   linestyle="--", color="#FF5722")
        ax_s1.set_xlabel("Date & Time")
        ax_s1.set_ylabel("Requests")
        ax_s1.set_title("Workload History")
        ax_s1.legend(fontsize=8)
        ax_s1.xaxis.set_major_formatter(mdates.DateFormatter("%b %d"))
        ax_s1.grid(True, alpha=0.3)

        ax_s2.step(step_dts, step_conts, where="mid", linewidth=1.5, color="#4CAF50")
        ax_s2.fill_between(step_dts, step_conts, step="mid", alpha=0.2, color="#4CAF50")
        ax_s2.set_xlabel("Date & Time")
        ax_s2.set_ylabel("Containers")
        ax_s2.set_title("Container History")
        ax_s2.xaxis.set_major_formatter(mdates.DateFormatter("%b %d"))
        ax_s2.grid(True, alpha=0.3)

        fig_step.tight_layout()
        st.pyplot(fig_step)


# ══════════════════════════════════════════════
#  TAB 5 — Architecture
# ══════════════════════════════════════════════
with tab_arch:
    st.subheader("System Architecture")
    st.markdown("""
    ```
    Client Requests
         |
         v
    Monitoring Module  -->  Metrics Collector (datetime, hour, day, requests, cpu, mem)
         |
         v
    Data Preprocessing  -->  Feature Engineering (hour, day_of_week, is_weekend)
         |
         v
    ML Prediction Engine  -->  Predicted Workload (next hour)
         |
         v
    SLA Evaluation Engine
         |
         v
    Scaling Decision Module
         |
         v
    Resource Manager  -->  Allocated Containers
         |
         +------------ feedback loop -----> Monitoring
    ```
    """)

    st.markdown("---")
    st.markdown("#### Module Map")

    module_data = {
        "Module": ["Monitoring", "Preprocessing", "ML Prediction", "SLA + Scaling",
                    "Resource Manager", "Dashboard"],
        "File": ["monitor.py", "utils/preprocessing.py", "predictor.py",
                 "scaler.py", "resource_manager.py", "app.py"],
        "Key Functions": [
            "get_current_metrics() -> datetime, hour, dow, requests, cpu, mem",
            "load_dataset(), prepare_features() -> [hour, dow, is_weekend, reqs, cpu]",
            "train_model(), predict_load() using 5 time-aware features",
            "evaluate_sla(), decide_scaling() with configurable thresholds",
            "scale_up(), scale_down(), set_containers()",
            "Streamlit UI with 5 interactive tabs",
        ],
    }
    st.table(pd.DataFrame(module_data))

    st.markdown("---")
    st.markdown("#### ML Features")
    feature_data = {
        "Feature": ["hour", "day_of_week", "is_weekend", "requests", "cpu_usage"],
        "Type": ["Time", "Time", "Time", "Workload", "Workload"],
        "Description": [
            "Hour of day (0-23) — captures daily traffic cycle",
            "Day of week (0=Sun, 6=Sat) — captures weekly patterns",
            "Binary flag (1=weekend, 0=weekday) — weekend traffic is lower",
            "Current requests per hour",
            "Current CPU utilisation %",
        ],
    }
    st.table(pd.DataFrame(feature_data))

    st.markdown("---")
    st.markdown("#### Current SLA Configuration")
    st.markdown(f"- **Max CPU Utilisation:** {sla_max_cpu}%")
    st.markdown(f"- **Max Requests per Container:** {sla_max_reqs}")
    st.markdown(f"- **Initial Containers:** {sla_initial_containers}")

st.divider()
st.caption("AI-Driven Cloud Auto-Scaling Prototype  |  Built with Streamlit & Scikit-learn  |  Live + Historical Modes")

# ══════════════════════════════════════════════
#  TAB 6 — Live Monitor (auto-refreshing)
# ══════════════════════════════════════════════
with tab_monitor:
    st.subheader("Live Workload Monitor")
    st.markdown(
        "This tab generates **real-time workload data** based on the **actual current time** "
        "on your machine. Every 3 seconds, a new data point is generated, the ML model predicts "
        "the next hour's load, and a scaling decision is made — all live."
    )

    # ── Auto-refresh every 3 seconds ──
    refresh_count = st_autorefresh(interval=3000, limit=None, key="live_monitor_refresh")

    # ── Session state for live history ──
    if "live_history" not in st.session_state:
        st.session_state.live_history = []
    if "live_containers" not in st.session_state:
        st.session_state.live_containers = sla_initial_containers

    # ── Generate new live data point ──
    live_metrics = generate_live_metrics()
    live_pred = predict_load(live_metrics, model)
    live_decision = decide_scaling(
        live_pred, live_metrics["cpu_usage"],
        st.session_state.live_containers,
        max_cpu=sla_max_cpu, max_reqs=sla_max_reqs,
    )

    # Update container count
    st.session_state.live_containers = live_decision["required_containers"]

    # Scaling direction indicator
    action = live_decision["action"]
    if action == "scale_up":
        direction = "▲"
        action_color = "red"
        action_label = "SCALE UP ▲"
    elif action == "scale_down":
        direction = "▼"
        action_color = "green"
        action_label = "SCALE DOWN ▼"
    else:
        direction = "−"
        action_color = "gray"
        action_label = "NO CHANGE −"

    # Append to history
    day_names = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]
    st.session_state.live_history.append({
        "Time": live_metrics["datetime"],
        "Day": day_names[live_metrics["day_of_week"]],
        "Requests": live_metrics["requests"],
        "CPU %": live_metrics["cpu_usage"],
        "Memory %": live_metrics["memory_usage"],
        "Predicted": live_pred,
        "Containers": st.session_state.live_containers,
        "Action": action_label,
        "Direction": direction,
    })

    # Keep last 200 records max
    if len(st.session_state.live_history) > 200:
        st.session_state.live_history = st.session_state.live_history[-200:]

    st.markdown("---")

    # ── Current Status Cards ──
    day_name = day_names[live_metrics["day_of_week"]]
    weekend_tag = " (Weekend)" if live_metrics["is_weekend"] else ""
    st.markdown(f"### Now: {live_metrics['datetime']}  —  {day_name}{weekend_tag}")

    m1, m2, m3, m4, m5 = st.columns(5)
    m1.metric("Requests/hr", f"{live_metrics['requests']}")
    m2.metric("CPU", f"{live_metrics['cpu_usage']}%",
             delta="OVER SLA" if live_metrics['cpu_usage'] > sla_max_cpu else "OK",
             delta_color="inverse" if live_metrics['cpu_usage'] > sla_max_cpu else "normal")
    m3.metric("Predicted Next", f"{live_pred} reqs")
    m4.metric("Containers", f"{st.session_state.live_containers} {direction}")
    m5.metric("Capacity", f"{st.session_state.live_containers * sla_max_reqs} reqs")

    # ── Action banner ──
    if action == "scale_up":
        st.error(f"**{action_label}**  —  {live_decision['reason']}")
    elif action == "scale_down":
        st.success(f"**{action_label}**  —  {live_decision['reason']}")
    else:
        st.info(f"**{action_label}**  —  {live_decision['reason']}")

    st.markdown("---")

    # ── Live Charts ──
    if len(st.session_state.live_history) >= 2:
        hist_df = pd.DataFrame(st.session_state.live_history)
        hist_df["Time_dt"] = pd.to_datetime(hist_df["Time"])

        chart_col1, chart_col2 = st.columns(2)

        with chart_col1:
            st.markdown("#### Live Workload")
            fig_lw, ax_lw = plt.subplots(figsize=(7, 3))
            ax_lw.plot(hist_df["Time_dt"], hist_df["Requests"],
                       linewidth=1.5, color="#2196F3", label="Actual")
            ax_lw.plot(hist_df["Time_dt"], hist_df["Predicted"],
                       linewidth=1.5, linestyle="--", color="#FF5722", label="Predicted")
            ax_lw.set_xlabel("Time")
            ax_lw.set_ylabel("Requests")
            ax_lw.legend(fontsize=8)
            ax_lw.grid(True, alpha=0.3)
            ax_lw.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M:%S"))
            plt.xticks(rotation=45)
            fig_lw.tight_layout()
            st.pyplot(fig_lw)

        with chart_col2:
            st.markdown("#### Containers")
            fig_lc, ax_lc = plt.subplots(figsize=(7, 3))
            ax_lc.step(hist_df["Time_dt"], hist_df["Containers"],
                       where="mid", linewidth=2, color="#4CAF50")
            ax_lc.fill_between(hist_df["Time_dt"], hist_df["Containers"],
                               step="mid", alpha=0.2, color="#4CAF50")

            # Add direction markers
            for idx, row in hist_df.iterrows():
                if row["Direction"] == "▲":
                    ax_lc.annotate("▲", (row["Time_dt"], row["Containers"]),
                                  fontsize=10, color="red", ha="center", va="bottom")
                elif row["Direction"] == "▼":
                    ax_lc.annotate("▼", (row["Time_dt"], row["Containers"]),
                                  fontsize=10, color="green", ha="center", va="top")

            ax_lc.set_xlabel("Time")
            ax_lc.set_ylabel("Containers")
            ax_lc.grid(True, alpha=0.3)
            ax_lc.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M:%S"))
            plt.xticks(rotation=45)
            fig_lc.tight_layout()
            st.pyplot(fig_lc)

        # CPU chart
        st.markdown("#### CPU Usage")
        fig_cpu, ax_cpu = plt.subplots(figsize=(14, 2.5))
        ax_cpu.plot(hist_df["Time_dt"], hist_df["CPU %"],
                    linewidth=1.5, color="#9C27B0")
        ax_cpu.axhline(y=sla_max_cpu, color="red", linestyle="--",
                       linewidth=1, label=f"SLA Threshold ({sla_max_cpu}%)")
        ax_cpu.set_xlabel("Time")
        ax_cpu.set_ylabel("CPU %")
        ax_cpu.legend(fontsize=8)
        ax_cpu.grid(True, alpha=0.3)
        ax_cpu.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M:%S"))
        plt.xticks(rotation=45)
        fig_cpu.tight_layout()
        st.pyplot(fig_cpu)

    st.markdown("---")

    # ── Live Data Table ──
    st.markdown("#### Live Data Feed")
    st.caption(f"{len(st.session_state.live_history)} records collected  |  Auto-refreshes every 3 seconds")

    if st.session_state.live_history:
        display_df = pd.DataFrame(st.session_state.live_history[::-1])  # newest first
        display_df = display_df[["Time", "Day", "Requests", "CPU %", "Memory %",
                                  "Predicted", "Containers", "Action"]]
        st.dataframe(display_df, use_container_width=True, hide_index=True,
                     height=400)

    # ── Clear history button ──
    if st.button("Clear Live History", key="clear_live"):
        st.session_state.live_history = []
        st.session_state.live_containers = sla_initial_containers
        st.rerun()
