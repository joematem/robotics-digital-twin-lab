import rclpy
from rclpy.node import Node
from std_msgs.msg import String


class MultiRobotStatusPublisher(Node):
    def __init__(self):
        super().__init__("multi_robot_status_publisher")
        self.publisher = self.create_publisher(String, "/warehouse/robot_status", 10)
        self.timer = self.create_timer(1.0, self.publish_status)
        self.counter = 0

        self.robots = [
            {"robot_id": "AMR_001", "battery": 100, "task": "inventory_scan"},
            {"robot_id": "AMR_002", "battery": 85, "task": "pallet_transfer"},
            {"robot_id": "AMR_003", "battery": 70, "task": "replenishment"},
        ]

    def publish_status(self):
        self.counter += 1

        for index, robot in enumerate(self.robots):
            robot["battery"] = max(0, robot["battery"] - (index + 1))

            if robot["battery"] <= 15:
                status = "needs_charging"
                task = "return_to_charger"
            else:
                status = "active"
                task = robot["task"]

            zone = f"A{(self.counter + index) % 5}"

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
