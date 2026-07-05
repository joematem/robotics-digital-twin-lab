import pandas as pd
import plotly.express as px
import streamlit as st
from sqlalchemy import create_engine, text

DATABASE_URL = "postgresql+psycopg://robotics:robotics_password@localhost:5433/robotics_lab"

st.set_page_config(page_title="Warehouse Robot Digital Twin", layout="wide")

st.title("Warehouse Robot Digital Twin")
st.caption("Fleet monitoring dashboard for ROS 2 warehouse robot telemetry")

engine = create_engine(DATABASE_URL)


@st.cache_data(ttl=3)
def load_recent_records(limit=2000):
    query = text("""
        SELECT robot_id, zone, task, battery, status, created_at
        FROM ros_robot_telemetry
        ORDER BY created_at DESC
        LIMIT :limit;
    """)
    return pd.read_sql(query, engine, params={"limit": limit})


recent_df = load_recent_records()

if recent_df.empty:
    st.warning("No robot telemetry found yet.")
    st.stop()

recent_df["created_at"] = pd.to_datetime(recent_df["created_at"])

st.sidebar.header("Filters")

robots = sorted(recent_df["robot_id"].unique())
statuses = sorted(recent_df["status"].unique())

selected_robots = st.sidebar.multiselect(
    "Robots",
    robots,
    default=robots,
)

selected_statuses = st.sidebar.multiselect(
    "Statuses",
    statuses,
    default=statuses,
)

record_limit = st.sidebar.slider(
    "Records to display",
    min_value=100,
    max_value=2000,
    value=500,
    step=100,
)

filtered_df = recent_df[
    recent_df["robot_id"].isin(selected_robots)
    & recent_df["status"].isin(selected_statuses)
].head(record_limit)

latest_df = (
    filtered_df.sort_values("created_at", ascending=False)
    .drop_duplicates("robot_id")
    .sort_values("robot_id")
)

total_robots = latest_df["robot_id"].nunique()
active_robots = int((latest_df["status"] == "active").sum())
charging_robots = int((latest_df["status"] == "charging").sum())
needs_charging = int((latest_df["status"] == "needs_charging").sum())

avg_battery = 0 if latest_df.empty else round(float(latest_df["battery"].mean()), 1)

col1, col2, col3, col4, col5 = st.columns(5)
col1.metric("Robots", total_robots)
col2.metric("Active", active_robots)
col3.metric("Charging", charging_robots)
col4.metric("Need Charging", needs_charging)
col5.metric("Avg Battery", f"{avg_battery}%")

if needs_charging > 0:
    st.error(f"{needs_charging} robot(s) need charging.")
else:
    st.success("No robot currently needs charging.")

st.subheader("Latest Robot State")
st.dataframe(latest_df, use_container_width=True)

left, right = st.columns(2)

with left:
    st.subheader("Current Battery Levels")
    battery_fig = px.bar(
        latest_df,
        x="robot_id",
        y="battery",
        color="status",
        range_y=[0, 100],
        text="battery",
        title="Battery by Robot",
    )
    st.plotly_chart(battery_fig, use_container_width=True)

with right:
    st.subheader("Robot Zone Map")
    zone_fig = px.scatter(
        latest_df,
        x="zone",
        y="robot_id",
        color="status",
        size="battery",
        hover_data=["task", "created_at"],
        title="Latest Robot Position by Zone",
    )
    st.plotly_chart(zone_fig, use_container_width=True)

st.subheader("Battery Trend")
trend_fig = px.line(
    filtered_df.sort_values("created_at"),
    x="created_at",
    y="battery",
    color="robot_id",
    title="Battery Trend Over Time",
)
st.plotly_chart(trend_fig, use_container_width=True)

left2, right2 = st.columns(2)

with left2:
    st.subheader("Task Distribution")
    task_counts = filtered_df.groupby("task").size().reset_index(name="records")
    task_fig = px.pie(task_counts, names="task", values="records")
    st.plotly_chart(task_fig, use_container_width=True)

with right2:
    st.subheader("Status Distribution")
    status_counts = filtered_df.groupby("status").size().reset_index(name="records")
    status_fig = px.bar(status_counts, x="status", y="records", color="status")
    st.plotly_chart(status_fig, use_container_width=True)

st.subheader("Zone Activity")
zone_counts = filtered_df.groupby("zone").size().reset_index(name="visits")
zone_fig = px.bar(zone_counts, x="zone", y="visits", title="Zone Visit Counts")
st.plotly_chart(zone_fig, use_container_width=True)

st.subheader("Robots Needing Attention")
attention_df = latest_df[latest_df["status"].isin(["needs_charging"]) | (latest_df["battery"] <= 20)]
st.dataframe(attention_df, use_container_width=True)

st.subheader("Recent Telemetry")
st.dataframe(filtered_df, use_container_width=True)

st.caption("Dashboard refreshes cached database queries every 3 seconds.")
st.divider()
st.header("Scenario Comparison")

@st.cache_data(ttl=5)
def load_scenario_runs():
    query = """
        SELECT run_id, scenario_name, started_at
        FROM simulation_runs
        ORDER BY started_at DESC;
    """
    return pd.read_sql(query, engine)


@st.cache_data(ttl=5)
def load_scenario_records(run_ids):
    if not run_ids:
        return pd.DataFrame()

    query = text("""
        SELECT
            r.scenario_name,
            t.run_id,
            t.robot_id,
            t.zone,
            t.task,
            t.battery,
            t.status,
            t.created_at
        FROM ros_robot_telemetry t
        JOIN simulation_runs r ON t.run_id = r.run_id
        WHERE t.run_id = ANY(:run_ids)
        ORDER BY t.created_at DESC;
    """)
    return pd.read_sql(query, engine, params={"run_ids": run_ids})


runs_df = load_scenario_runs()

if runs_df.empty:
    st.info("No named simulation runs found yet.")
else:
    run_labels = {
        f"{row.scenario_name} | {row.run_id}": row.run_id
        for row in runs_df.itertuples()
    }

    selected_labels = st.multiselect(
        "Select runs to compare",
        options=list(run_labels.keys()),
        default=list(run_labels.keys())[:2],
    )

    selected_run_ids = [run_labels[label] for label in selected_labels]
    scenario_df = load_scenario_records(selected_run_ids)

    if scenario_df.empty:
        st.warning("No telemetry found for selected runs.")
    else:
        kpi_df = (
            scenario_df.groupby("scenario_name")
            .agg(
                total_records=("robot_id", "count"),
                delayed_records=("status", lambda x: int((x == "delayed").sum())),
                charging_need_records=("status", lambda x: int((x == "needs_charging").sum())),
                waiting_for_charger_records=(
                    "status",
                    lambda x: int((x == "waiting_for_charger").sum()),
                ),
                stalled_records=("status", lambda x: int((x == "stalled").sum())),
                avg_battery=("battery", "mean"),
                min_battery=("battery", "min"),
            )
            .reset_index()
        )

        kpi_df["avg_battery"] = kpi_df["avg_battery"].round(2)
        kpi_df["operational_stress_score"] = (
            kpi_df["delayed_records"]
            + kpi_df["charging_need_records"]
            + kpi_df["waiting_for_charger_records"]
            + (2 * kpi_df["stalled_records"])
        )
        st.subheader("Scenario KPI Summary")
        st.dataframe(kpi_df, use_container_width=True)

        left3, right3 = st.columns(2)

        with left3:
            st.subheader("Status Comparison")
            status_compare = (
                scenario_df.groupby(["scenario_name", "status"])
                .size()
                .reset_index(name="records")
            )
            status_fig = px.bar(
                status_compare,
                x="status",
                y="records",
                color="scenario_name",
                barmode="group",
                title="Status Counts by Scenario",
            )
            st.plotly_chart(status_fig, use_container_width=True)

        with right3:
            st.subheader("Task Comparison")
            task_compare = (
                scenario_df.groupby(["scenario_name", "task"])
                .size()
                .reset_index(name="records")
            )
            task_fig = px.bar(
                task_compare,
                x="task",
                y="records",
                color="scenario_name",
                barmode="group",
                title="Task Counts by Scenario",
            )
            st.plotly_chart(task_fig, use_container_width=True)

        st.subheader("Zone Comparison")
        zone_compare = (
            scenario_df.groupby(["scenario_name", "zone"])
            .size()
            .reset_index(name="records")
        )
        zone_fig = px.bar(
            zone_compare,
            x="zone",
            y="records",
            color="scenario_name",
            barmode="group",
            title="Zone Activity by Scenario",
        )
        st.plotly_chart(zone_fig, use_container_width=True)

        st.subheader("Robot Battery Comparison")
        battery_compare = (
            scenario_df.groupby(["scenario_name", "robot_id"])
            .agg(avg_battery=("battery", "mean"))
            .reset_index()
        )
        battery_compare["avg_battery"] = battery_compare["avg_battery"].round(2)

        battery_compare_fig = px.bar(
            battery_compare,
            x="robot_id",
            y="avg_battery",
            color="scenario_name",
            barmode="group",
            range_y=[0, 100],
            title="Average Battery by Robot and Scenario",
        )
        st.plotly_chart(battery_compare_fig, use_container_width=True)
