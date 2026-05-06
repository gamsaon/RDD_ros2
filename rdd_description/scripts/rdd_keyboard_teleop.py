#!/usr/bin/env python3

import select
import sys
import termios
import tty

import rclpy
from geometry_msgs.msg import Twist
from rclpy.node import Node
from sensor_msgs.msg import JointState
from std_msgs.msg import Float64MultiArray


HELP = """
RDD keyboard teleop
------------------
Move:
  i : forward
  , : backward
  j : turn left
  l : turn right
  k : stop

Linear joint:
  h : lower linear joint
  n : raise linear joint

Quit:
  q
"""


class RddKeyboardTeleop(Node):
    def __init__(self):
        super().__init__('rdd_keyboard_teleop')
        self.cmd_pub = self.create_publisher(
            Twist,
            '/diff_drive_base_controller/cmd_vel_unstamped',
            10,
        )
        self.linear_pub = self.create_publisher(
            Float64MultiArray,
            '/linear_position_controller/commands',
            10,
        )
        self.create_subscription(JointState, '/joint_states', self.on_joint_state, 10)

        self.linear_min = 0.0
        self.linear_max = 0.245
        self.linear_step = 0.01
        self.linear_target = 0.245
        self.linear_position = 0.245
        self.safe_drive_linear_min = 0.06
        self.warned_drive_lock = False

        self.linear_speed = 0.25
        self.angular_speed = 0.8

    def on_joint_state(self, msg: JointState) -> None:
        if 'linear_joint' not in msg.name:
            return
        idx = msg.name.index('linear_joint')
        if idx < len(msg.position):
            self.linear_position = msg.position[idx]

    def drive_locked(self) -> bool:
        return self.linear_position <= self.safe_drive_linear_min

    def try_publish_twist(self, linear_x: float, angular_z: float) -> None:
        if (linear_x != 0.0 or angular_z != 0.0) and self.drive_locked():
            if not self.warned_drive_lock:
                self.get_logger().warn(
                    f'linear_joint={self.linear_position:.3f} m: lower position lock, raise linear before driving'
                )
                self.warned_drive_lock = True
            self.publish_twist(0.0, 0.0)
            return
        self.warned_drive_lock = False
        self.publish_twist(linear_x, angular_z)

    def publish_twist(self, linear_x: float, angular_z: float) -> None:
        msg = Twist()
        msg.linear.x = linear_x
        msg.angular.z = angular_z
        self.cmd_pub.publish(msg)

    def publish_linear_target(self) -> None:
        msg = Float64MultiArray()
        msg.data = [self.linear_target]
        self.linear_pub.publish(msg)
        self.get_logger().info(f'linear_joint target: {self.linear_target:.3f}')

    def lower_linear(self) -> None:
        self.linear_target = max(self.linear_min, self.linear_target - self.linear_step)
        self.publish_linear_target()

    def raise_linear(self) -> None:
        self.linear_target = min(self.linear_max, self.linear_target + self.linear_step)
        self.publish_linear_target()


def get_key(settings) -> str:
    tty.setraw(sys.stdin.fileno())
    rlist, _, _ = select.select([sys.stdin], [], [], 0.1)
    key = sys.stdin.read(1) if rlist else ''
    termios.tcsetattr(sys.stdin, termios.TCSADRAIN, settings)
    return key


def main():
    settings = termios.tcgetattr(sys.stdin)
    rclpy.init()
    node = RddKeyboardTeleop()

    print(HELP)
    node.publish_linear_target()

    try:
        while rclpy.ok():
            rclpy.spin_once(node, timeout_sec=0.0)
            key = get_key(settings)

            if key == 'i':
                node.try_publish_twist(node.linear_speed, 0.0)
            elif key == ',':
                node.try_publish_twist(-node.linear_speed, 0.0)
            elif key == 'j':
                node.try_publish_twist(0.0, node.angular_speed)
            elif key == 'l':
                node.try_publish_twist(0.0, -node.angular_speed)
            elif key == 'k':
                node.publish_twist(0.0, 0.0)
            elif key == 'h':
                node.lower_linear()
            elif key == 'n':
                node.raise_linear()
            elif key == 'q':
                node.publish_twist(0.0, 0.0)
                break

    finally:
        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, settings)
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
