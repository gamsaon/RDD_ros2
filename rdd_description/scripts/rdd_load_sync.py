#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import JointState
from std_msgs.msg import Float64MultiArray


class RddLoadSync(Node):
    def __init__(self):
        super().__init__('rdd_load_sync')
        self.linear_joint_name = 'linear_joint'
        self.load_pub = self.create_publisher(
            Float64MultiArray,
            '/load_position_controller/commands',
            10,
        )
        self.create_subscription(JointState, '/joint_states', self.on_joint_state, 10)

        self.linear_trigger_on = 0.045
        self.linear_trigger_off = 0.055
        self.linear_bottom = 0.0
        self.load_top = 0.042
        self.load_bottom = -0.18
        self.last_target = None
        self.load_sync_active = False

    def on_joint_state(self, msg: JointState) -> None:
        if self.linear_joint_name not in msg.name:
            return

        idx = msg.name.index(self.linear_joint_name)
        linear_pos = msg.position[idx]
        self.update_sync_state(linear_pos)
        target = self.compute_load_target(linear_pos)

        if self.last_target is not None and abs(target - self.last_target) < 1e-4:
            return

        out = Float64MultiArray()
        out.data = [target]
        self.load_pub.publish(out)
        self.last_target = target

    def update_sync_state(self, linear_pos: float) -> None:
        if self.load_sync_active:
            if linear_pos >= self.linear_trigger_off:
                self.load_sync_active = False
        else:
            if linear_pos <= self.linear_trigger_on:
                self.load_sync_active = True

    def compute_load_target(self, linear_pos: float) -> float:
        if not self.load_sync_active:
            return self.load_top
        if linear_pos <= self.linear_bottom:
            return self.load_bottom

        ratio = (self.linear_trigger_on - linear_pos) / (self.linear_trigger_on - self.linear_bottom)
        ratio = max(0.0, min(1.0, ratio))
        return self.load_top + ratio * (self.load_bottom - self.load_top)


def main():
    rclpy.init()
    node = RddLoadSync()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
