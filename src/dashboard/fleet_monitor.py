import pandas as pd
import plotly.express as px
import streamlit as st
from sqlalchemy import create_engine, text

DATABASE_URL = "postgresql+psycopg://robotics:robotics_password@localhost:5433/robotics_lab"

st.set_page_config(
    page_title="Warehouse Robot Digital Twin",
    layout="wide",
)

st.title("Warehouse Robot Digital Twin")
st.caption("Live monitoring dashboard for ROS 2 warehouse robot telemetry")

engine = create_engine(DATABASE_URL)


@st.cache_data(ttl=3)
def load_latest_state():
    query = """
        SELECT DISTINCT ON (robot_id)
            robot_id, zone, task, battery, status, created_at
        FROM ros_robot_telemetry
        ORDER BY robot_id, created_at DESC;
    """
    return pd.read_sql(query, engine)


@st.cache_data(ttl=3)
def load_recent_records(limit=300):
    query = text("""
        SELECT robot_id, zone, task, battery, status, created_at
        FROM ros_robot_telemetry
        ORDER BY created_at DESC
        LIMIT :limit;
    """)
    return pd.read_sql(query, engine, params={"limit": limit})


@st.cache_data(ttl=3)
def load_fleet_summary():
    query = """
        SELECT
            robot_id,
            MIN(battery) AS min_battery,
            MAX(battery) AS max_battery,
            COUNT(*) AS telemetry_records
        FROM ros_robot_telemetry
        GROUP BY robot_id
        ORDER BY robot_id;
    """
    return pd.read_sql(query, engine)


latest_df = load_latest_state()
recent_df = load_recent_records()
summary_df = load_fleet_summary()

if latest_df.empty:
    st.warning("No robot telemetry found yet.")
    st.stop()

total_robots = latest_df["robot_id"].nunique()
needs_charging = int((latest_df["status"] == "needs_charging").sum())
active_robots = int((latest_df["status"] == "active").sum())
avg_battery = round(float(latest_df["battery"].mean()), 1)

col1, col2, col3, col4 = st.columns(4)
col1.metric("Robots", total_robots)
col2.metric("Active", active_robots)
col3.metric("Need Charging", needs_charging)
col4.metric("Average Battery", f"{avg_battery}%")

st.subheader("Latest Robot State")
st.dataframe(latest_df, use_container_width=True)

left, right = st.columns(2)

with left:
    st.subheader("Battery By Robot")
    battery_fig = px.bar(
        latest_df,
        x="robot_id",
        y="battery",
        color="status",
        range_y=[0, 100],
        text="battery",
        title="Current Battery Levels",
    )
    st.plotly_chart(battery_fig, use_container_width=True)

with right:
    st.subheader("Current Robot Zones")
    zone_fig = px.scatter(
        latest_df,
        x="zone",
        y="robot_id",
        color="status",
        size="battery",
        hover_data=["task", "created_at"],
        title="Latest Robot Location By Zone",
    )
    st.plotly_chart(zone_fig, use_container_width=True)

st.subheader("Task Distribution")
task_counts = recent_df.groupby("task").size().reset_index(name="records")
task_fig = px.pie(task_counts, names="task", values="records", title="Recent Task Mix")
st.plotly_chart(task_fig, use_container_width=True)

st.subheader("Zone Activity")
zone_counts = recent_df.groupby("zone").size().reset_index(name="visits")
zone_fig = px.bar(zone_counts, x="zone", y="visits", title="Recent Zone Visits")
st.plotly_chart(zone_fig, use_container_width=True)

st.subheader("Fleet Summary")
st.dataframe(summary_df, use_container_width=True)

st.subheader("Recent Telemetry")
st.dataframe(recent_df, use_container_width=True)

st.caption("Refreshes cached database queries every 3 seconds.")
