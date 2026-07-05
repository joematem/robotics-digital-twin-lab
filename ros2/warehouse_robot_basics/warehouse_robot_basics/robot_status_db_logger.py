import rclpy
from rclpy.node import Node
from std_msgs.msg import String
import psycopg2


class RobotStatusDbLogger(Node):
    def __init__(self):
        super().__init__("robot_status_db_logger")

        self.conn = psycopg2.connect(
            host="localhost",
            port=5433,
            database="robotics_lab",
            user="robotics",
            password="robotics_password",
        )
        self.conn.autocommit = True

        self.subscription = self.create_subscription(
            String,
            "/warehouse/robot_status",
            self.receive_status,
            10,
        )

        self.get_logger().info("Robot status database logger started")

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
                (robot_id, zone, task, battery, status, raw_message)
                VALUES (%s, %s, %s, %s, %s, %s)
                """,
                (robot_id, zone, task, battery, status, raw_message),
            )

        self.get_logger().info(f"Logged telemetry to PostgreSQL: {raw_message}")


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
