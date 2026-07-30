from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    return LaunchDescription([
        Node(
            package='usb_relay_controller',
            executable='usb_relay_controller',
            name='usb_relay_controller',
            output='screen',
            parameters=[{
                'module_count': 2,
                'default_target': 'all',
                'reset_on_start': False,
                'command_delay_sec': 0.0,
                'retry_count': 2,
                'relay_test_path': '',
            }],
        ),
    ])
