import os
from datetime import datetime, timezone

import psycopg2
import rclpy
from rclpy.node import Node
from std_msgs.msg import String


class RobotStatusDbLogger(Node):
    def __init__(self):
        super().__init__("robot_status_db_logger")

        self.run_id = os.getenv("RUN_ID", datetime.now(timezone.utc).strftime("run_%Y%m%d_%H%M%S"))
        self.scenario_name = os.getenv("SCENARIO_NAME", "baseline")

        self.conn = psycopg2.connect(
            host="localhost",
            port=5433,
            database="robotics_lab",
            user="robotics",
            password="robotics_password",
        )
        self.conn.autocommit = True

        self.ensure_run_exists()

        self.subscription = self.create_subscription(
            String,
            "/warehouse/robot_status",
            self.receive_status,
            10,
        )

        self.get_logger().info(
            f"Database logger started for run_id={self.run_id}, scenario={self.scenario_name}"
        )

    def ensure_run_exists(self):
        with self.conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO simulation_runs (run_id, scenario_name, description)
                VALUES (%s, %s, %s)
                ON CONFLICT (run_id) DO NOTHING
                """,
                (
                    self.run_id,
                    self.scenario_name,
                    "ROS 2 warehouse robot telemetry experiment",
                ),
            )

    def parse_message(self, raw_message):
        data = {}

        for part in raw_message.split(";"):
            if "=" in part:
                key, value = part.strip().split("=", 1)
                data[key.strip()] = value.strip()

        return data

    def receive_status(self, msg):
        raw_message = msg.data
        data = self.parse_message(raw_message)

        robot_id = data.get("robot_id", "unknown")
        zone = data.get("zone", "unknown")
        task = data.get("task", "unknown")
        battery = int(data.get("battery", 0))
        status = data.get("status", "unknown")

        with self.conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO ros_robot_telemetry
                (run_id, robot_id, zone, task, battery, status, raw_message)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                """,
                (self.run_id, robot_id, zone, task, battery, status, raw_message),
            )

        self.get_logger().info(f"Logged telemetry: {robot_id} | {status} | {battery}%")


def main(args=None):
    rclpy.init(args=args)
    node = RobotStatusDbLogger()

    try:
        rclpy.spin(node)
    finally:
        node.conn.close()
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
