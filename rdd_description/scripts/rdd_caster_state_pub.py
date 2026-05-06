#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import JointState


class RddCasterStatePublisher(Node):
    def __init__(self):
        super().__init__('rdd_caster_state_publisher')
        self.publisher = self.create_publisher(JointState, '/joint_states', 10)
        self.timer = self.create_timer(0.1, self.publish_joint_state)
        self.joint_names = [
            'rear_left_caster_swivel_joint',
            'rear_left_caster_wheel_joint',
            'rear_right_caster_swivel_joint',
            'rear_right_caster_wheel_joint',
        ]

    def publish_joint_state(self) -> None:
        msg = JointState()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.name = self.joint_names
        msg.position = [0.0, 0.0, 0.0, 0.0]
        msg.velocity = [0.0, 0.0, 0.0, 0.0]
        msg.effort = [0.0, 0.0, 0.0, 0.0]
        self.publisher.publish(msg)


def main():
    rclpy.init()
    node = RddCasterStatePublisher()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
