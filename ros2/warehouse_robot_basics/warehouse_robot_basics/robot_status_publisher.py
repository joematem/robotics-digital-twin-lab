import os
import random

import rclpy
from rclpy.node import Node
from std_msgs.msg import String


class MultiRobotStatusPublisher(Node):
    def __init__(self):
        super().__init__("multi_robot_status_publisher")
        self.publisher = self.create_publisher(String, "/warehouse/robot_status", 10)
        self.timer = self.create_timer(1.0, self.publish_status)
        self.counter = 0

        self.scenario_name = os.getenv("SCENARIO_NAME", "baseline")
        self.blocked_zone = os.getenv("BLOCKED_ZONE", "A3")

        self.robots = [
            {"robot_id": "AMR_001", "battery": 100, "task": "inventory_scan", "status": "active"},
            {"robot_id": "AMR_002", "battery": 85, "task": "pallet_transfer", "status": "active"},
            {"robot_id": "AMR_003", "battery": 70, "task": "replenishment", "status": "active"},
        ]

        self.tasks = ["inventory_scan", "pallet_transfer", "replenishment", "idle"]

        self.get_logger().info(
            f"Publisher started with scenario={self.scenario_name}, blocked_zone={self.blocked_zone}"
        )

    def update_robot(self, robot, index):
        if robot["status"] == "waiting_for_charger":
            robot["battery"] = max(0, robot["battery"] - 1)
            robot["task"] = "charger_unavailable"

            if robot["battery"] == 0:
                robot["status"] = "stalled"

            return

        if robot["status"] == "stalled":
            robot["battery"] = 0
            robot["task"] = "stalled_no_battery"
            return

        if robot["status"] == "charging":
            robot["battery"] = min(100, robot["battery"] + 8)
            robot["task"] = "charging"

            if robot["battery"] >= 80:
                robot["status"] = "active"
                robot["task"] = random.choice(self.tasks[:-1])

        elif robot["battery"] <= 15:
            if self.scenario_name == "charging_station_failure":
                robot["status"] = "waiting_for_charger"
                robot["task"] = "charger_unavailable"
                robot["battery"] = max(0, robot["battery"] - 1)
            else:
                robot["status"] = "needs_charging"
                robot["task"] = "return_to_charger"
                robot["battery"] = max(0, robot["battery"] - 1)

                if robot["battery"] <= 5:
                    robot["status"] = "charging"
                    robot["task"] = "charging"

        else:
            robot["status"] = "active"
            robot["battery"] = max(0, robot["battery"] - (index + 1))

            if self.counter % 8 == 0:
                robot["task"] = random.choice(self.tasks)

    def apply_scenario(self, robot, zone):
        if self.scenario_name == "blocked_zone_A3" and zone == self.blocked_zone:
            return "A4", "reroute_from_blocked_zone", "delayed"

        return zone, robot["task"], robot["status"]

    def publish_status(self):
        self.counter += 1

        for index, robot in enumerate(self.robots):
            self.update_robot(robot, index)

            planned_zone = f"A{(self.counter + index) % 5}"
            zone, task, status = self.apply_scenario(robot, planned_zone)

            msg = String()
            msg.data = (
                f"robot_id={robot['robot_id']}; "
                f"zone={zone}; "
                f"task={task}; "
                f"battery={robot['battery']}; "
                f"status={status}"
            )

            self.publisher.publish(msg)
            self.get_logger().info(f"Published: {msg.data}")


def main(args=None):
    rclpy.init(args=args)
    node = MultiRobotStatusPublisher()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == "__main__":
    main()
