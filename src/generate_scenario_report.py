from pathlib import Path

import pandas as pd
from sqlalchemy import create_engine

DATABASE_URL = "postgresql+psycopg://robotics:robotics_password@localhost:5433/robotics_lab"
OUTPUT_PATH = Path("outputs/scenario_comparison_report.md")

engine = create_engine(DATABASE_URL)


def load_kpis():
    query = """
        SELECT
            r.scenario_name,
            COUNT(*) AS total_records,
            SUM(CASE WHEN t.status = 'delayed' THEN 1 ELSE 0 END) AS delayed_records,
            SUM(CASE WHEN t.status = 'needs_charging' THEN 1 ELSE 0 END) AS charging_need_records,
            SUM(CASE WHEN t.status = 'waiting_for_charger' THEN 1 ELSE 0 END) AS waiting_for_charger_records,
            SUM(CASE WHEN t.status = 'stalled' THEN 1 ELSE 0 END) AS stalled_records,
            ROUND(AVG(t.battery), 2) AS avg_battery,
            MIN(t.battery) AS min_battery
        FROM ros_robot_telemetry t
        JOIN simulation_runs r ON t.run_id = r.run_id
        WHERE t.run_id IS NOT NULL
        GROUP BY r.scenario_name
        ORDER BY r.scenario_name;
    """
    return pd.read_sql(query, engine)


def load_zone_counts():
    query = """
        SELECT r.scenario_name, t.zone, COUNT(*) AS records
        FROM ros_robot_telemetry t
        JOIN simulation_runs r ON t.run_id = r.run_id
        WHERE t.run_id IS NOT NULL
        GROUP BY r.scenario_name, t.zone
        ORDER BY r.scenario_name, t.zone;
    """
    return pd.read_sql(query, engine)


def load_task_counts():
    query = """
        SELECT r.scenario_name, t.task, COUNT(*) AS records
        FROM ros_robot_telemetry t
        JOIN simulation_runs r ON t.run_id = r.run_id
        WHERE t.run_id IS NOT NULL
        GROUP BY r.scenario_name, t.task
        ORDER BY r.scenario_name, records DESC;
    """
    return pd.read_sql(query, engine)


def interpret(kpis):
    lines = []

    for row in kpis.itertuples(index=False):
        scenario = row.scenario_name

        if scenario == "baseline":
            lines.append("- Baseline shows normal fleet operation and provides the reference condition.")
        elif "blocked_zone" in scenario:
            lines.append(
                f"- {scenario} introduced {row.delayed_records} delayed records, "
                "showing route disruption and local congestion effects."
            )
        elif "charging" in scenario:
            lines.append(
                f"- {scenario} introduced {row.waiting_for_charger_records} waiting-for-charger records, "
                "showing support-infrastructure stress."
            )
        else:
            lines.append(
                f"- {scenario} produced {row.total_records} telemetry records and should be interpreted against baseline."
            )

    return "\n".join(lines)


def main():
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    kpis = load_kpis()
    zone_counts = load_zone_counts()
    task_counts = load_task_counts()

    report = f"""# Warehouse Robot Digital Twin Scenario Report

## Purpose

This report summarises ROS 2 warehouse robot telemetry stored in PostgreSQL and compares baseline operation against disruption scenarios.

## Scenario KPI Summary

{kpis.to_markdown(index=False)}

## Zone Activity

{zone_counts.to_markdown(index=False)}

## Task Distribution

{task_counts.to_markdown(index=False)}

## Interpretation

{interpret(kpis)}

## Research Notes

- The baseline scenario provides a reference for normal robot behaviour.
- The blocked-zone scenario tests adaptive rerouting and congestion effects.
- The charging-station-failure scenario tests support-resource vulnerability.
- These scenarios support digital twin research into resilience, disruption response, and operational stress.

## Next Experiments

1. Extend each scenario to equal run lengths for fair comparison.
2. Add task completion metrics and delay duration.
3. Add robot utilisation and idle-time metrics.
4. Simulate multiple blocked zones.
5. Connect ROS 2 telemetry to Gazebo or Isaac Sim.
"""

    OUTPUT_PATH.write_text(report, encoding="utf-8")
    print(f"Report written to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
