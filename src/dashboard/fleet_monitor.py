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
