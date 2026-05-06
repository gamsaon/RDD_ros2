#!/usr/bin/env python3

import math

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import JointState


class RddJointStateFilter(Node):
    def __init__(self):
        super().__init__('rdd_joint_state_filter')
        self.publisher = self.create_publisher(JointState, '/joint_states_filtered', 10)
        self.subscription = self.create_subscription(
            JointState,
            '/joint_states',
            self.on_joint_state,
            10,
        )
        self.last_position = {}
        self.last_velocity = {}
        self.last_effort = {}

    def sanitize_value(self, cache: dict, name: str, value: float) -> float:
        if math.isfinite(value):
            cache[name] = value
            return value
        return cache.get(name, 0.0)

    def on_joint_state(self, msg: JointState) -> None:
        out = JointState()
        out.header = msg.header
        out.name = list(msg.name)

        if msg.position:
            out.position = [
                self.sanitize_value(self.last_position, name, msg.position[idx])
                for idx, name in enumerate(msg.name[:len(msg.position)])
            ]
            if len(out.position) < len(out.name):
                out.position.extend(self.last_position.get(name, 0.0) for name in out.name[len(out.position):])

        if msg.velocity:
            out.velocity = [
                self.sanitize_value(self.last_velocity, name, msg.velocity[idx])
                for idx, name in enumerate(msg.name[:len(msg.velocity)])
            ]
            if len(out.velocity) < len(out.name):
                out.velocity.extend(self.last_velocity.get(name, 0.0) for name in out.name[len(out.velocity):])

        if msg.effort:
            out.effort = [
                self.sanitize_value(self.last_effort, name, msg.effort[idx])
                for idx, name in enumerate(msg.name[:len(msg.effort)])
            ]
            if len(out.effort) < len(out.name):
                out.effort.extend(self.last_effort.get(name, 0.0) for name in out.name[len(out.effort):])

        self.publisher.publish(out)


def main():
    rclpy.init()
    node = RddJointStateFilter()
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
