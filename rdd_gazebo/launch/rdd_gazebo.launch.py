import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, TimerAction
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node
import xacro


def generate_launch_description():

    pkg_description = get_package_share_directory('rdd_description')

    xacro_file = os.path.join(pkg_description, 'urdf', 'rdd.urdf.xacro')
    robot_description = xacro.process_file(xacro_file).toxml()

    rsp = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        parameters=[{
            'robot_description': robot_description,
            'use_sim_time': True
        }]
    )

    gazebo = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(
                get_package_share_directory('gazebo_ros'),
                'launch',
                'gazebo.launch.py'
            )
        )
    )

    spawn_entity = Node(
        package='gazebo_ros',
        executable='spawn_entity.py',
        arguments=[
            '-topic', 'robot_description',
            '-entity', 'rdd_robot',
            '-z', '0.3'
        ],
        output='screen'
    )

    joint_state_broadcaster = Node(
        package="controller_manager",
        executable="spawner",
        arguments=["joint_state_broadcaster"],
    )

    diff_drive_controller = Node(
        package="controller_manager",
        executable="spawner",
        arguments=["diff_drive_controller"],
    )

    # 🔥 핵심: 타이머로 순서 제어
    delayed_spawn = TimerAction(
        period=3.0,
        actions=[spawn_entity]
    )

    delayed_controller = TimerAction(
        period=5.0,
        actions=[joint_state_broadcaster, diff_drive_controller]
    )

    return LaunchDescription([
        rsp,
        gazebo,
        delayed_spawn,
        delayed_controller
    ])
