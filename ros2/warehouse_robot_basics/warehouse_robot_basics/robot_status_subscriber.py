import rclpy
from rclpy.node import Node
from std_msgs.msg import String


class RobotStatusSubscriber(Node):
    def __init__(self):
        super().__init__("robot_status_subscriber")
        self.subscription = self.create_subscription(
            String,
            "/warehouse/robot_status",
            self.receive_status,
            10,
        )

    def receive_status(self, msg):
        self.get_logger().info(f"Received robot telemetry: {msg.data}")


def main(args=None):
    rclpy.init(args=args)
    node = RobotStatusSubscriber()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == "__main__":
    main()
