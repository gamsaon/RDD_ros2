#!/usr/bin/env python3

import rclpy
from geometry_msgs.msg import Twist
from rclpy.node import Node


class Nav2CmdVelBridge(Node):
    def __init__(self):
        super().__init__('rdd_nav2_cmd_vel_bridge')
        self.publisher = self.create_publisher(
            Twist,
            '/diff_drive_base_controller/cmd_vel_unstamped',
            10,
        )
        self.subscription = self.create_subscription(
            Twist,
            '/cmd_vel',
            self.cmd_vel_callback,
            10,
        )

    def cmd_vel_callback(self, msg: Twist) -> None:
        self.publisher.publish(msg)


def main() -> None:
    rclpy.init()
    node = Nav2CmdVelBridge()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
