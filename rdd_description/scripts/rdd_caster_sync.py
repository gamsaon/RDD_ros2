#!/usr/bin/env python3

import math

import rclpy
from geometry_msgs.msg import Twist
from rclpy.node import Node
from sensor_msgs.msg import JointState
from std_msgs.msg import Float64MultiArray


def wrap_to_pi(angle: float) -> float:
    while angle > math.pi:
        angle -= 2.0 * math.pi
    while angle < -math.pi:
        angle += 2.0 * math.pi
    return angle


class RddCasterSync(Node):
    def __init__(self):
        super().__init__('rdd_caster_sync')
        self.publisher = self.create_publisher(
            Float64MultiArray,
            '/caster_position_controller/commands',
            10,
        )
        self.create_subscription(
            Twist,
            '/diff_drive_base_controller/cmd_vel_unstamped',
            self.on_cmd_vel,
            10,
        )
        self.create_subscription(JointState, '/joint_states', self.on_joint_state, 10)
        self.timer = self.create_timer(0.05, self.on_timer)

        self.cmd_linear_x = 0.0
        self.cmd_angular_z = 0.0
        self.cmd_timeout = 0.3
        self.last_cmd_time = self.get_clock().now()
        self.wheel_radius = 0.016
        self.left_caster_xy = (-0.33, 0.2135)
        self.right_caster_xy = (-0.33, -0.2135)
        self.current_positions = {
            'rear_left_caster_swivel_joint': 0.0,
            'rear_left_caster_wheel_joint': 0.0,
            'rear_right_caster_swivel_joint': 0.0,
            'rear_right_caster_wheel_joint': 0.0,
        }
        self.last_time = self.get_clock().now()

    def on_cmd_vel(self, msg: Twist) -> None:
        self.cmd_linear_x = msg.linear.x
        self.cmd_angular_z = msg.angular.z
        self.last_cmd_time = self.get_clock().now()

    def on_joint_state(self, msg: JointState) -> None:
        for name in self.current_positions:
            if name in msg.name:
                idx = msg.name.index(name)
                if idx < len(msg.position) and math.isfinite(msg.position[idx]):
                    self.current_positions[name] = msg.position[idx]

    def caster_state_for_point(self, point_xy):
        x, y = point_xy
        vx = self.cmd_linear_x - self.cmd_angular_z * y
        vy = self.cmd_angular_z * x
        speed = math.hypot(vx, vy)
        if speed < 1e-4:
            return None, 0.0
        swivel = math.atan2(vy, vx)
        return swivel, speed / self.wheel_radius

    def on_timer(self) -> None:
        now = self.get_clock().now()
        dt = (now - self.last_time).nanoseconds / 1e9
        self.last_time = now
        if dt <= 0.0:
            return

        cmd_age = (now - self.last_cmd_time).nanoseconds / 1e9
        if cmd_age > self.cmd_timeout:
            self.cmd_linear_x = 0.0
            self.cmd_angular_z = 0.0

        left_swivel, left_wheel_rate = self.caster_state_for_point(self.left_caster_xy)
        right_swivel, right_wheel_rate = self.caster_state_for_point(self.right_caster_xy)

        if left_swivel is None or right_swivel is None:
            msg = Float64MultiArray()
            msg.data = [
                self.current_positions['rear_left_caster_swivel_joint'],
                self.current_positions['rear_left_caster_wheel_joint'],
                self.current_positions['rear_right_caster_swivel_joint'],
                self.current_positions['rear_right_caster_wheel_joint'],
            ]
            self.publisher.publish(msg)
            return

        left_wheel = self.current_positions['rear_left_caster_wheel_joint'] + left_wheel_rate * dt
        right_wheel = self.current_positions['rear_right_caster_wheel_joint'] + right_wheel_rate * dt

        msg = Float64MultiArray()
        msg.data = [
            wrap_to_pi(left_swivel),
            left_wheel,
            wrap_to_pi(right_swivel),
            right_wheel,
        ]
        self.publisher.publish(msg)


def main():
    rclpy.init()
    node = RddCasterSync()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
