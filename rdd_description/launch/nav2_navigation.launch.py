import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, TimerAction
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    pkg_share = get_package_share_directory('rdd_description')
    nav2_bringup_dir = get_package_share_directory('nav2_bringup')

    gazebo_launch = os.path.join(pkg_share, 'launch', 'gazebo.launch.py')
    navigation_launch = os.path.join(nav2_bringup_dir, 'launch', 'bringup_launch.py')
    nav2_params = os.path.join(pkg_share, 'config', 'nav2_params.yaml')
    rviz_config = os.path.join(pkg_share, 'rviz', 'rdd_nav2.rviz')

    default_world = os.path.join(pkg_share, 'worlds', 'apartment_test.world')
    default_map = os.path.expanduser('~/ros2_ws/maps/apartment_map.yaml')

    use_sim_time = LaunchConfiguration('use_sim_time')
    spawn_z = LaunchConfiguration('spawn_z')
    world = LaunchConfiguration('world')
    map_yaml = LaunchConfiguration('map')
    params_file = LaunchConfiguration('params_file')
    use_rviz = LaunchConfiguration('use_rviz')

    rviz_node = Node(
        package='rviz2',
        executable='rviz2',
        name='rviz2_nav2',
        output='screen',
        arguments=['-d', rviz_config],
        parameters=[{'use_sim_time': use_sim_time}],
        condition=IfCondition(use_rviz),
    )

    nav2_cmd_vel_bridge = Node(
        package='rdd_description',
        executable='rdd_nav2_cmd_vel_bridge.py',
        name='rdd_nav2_cmd_vel_bridge',
        output='screen',
    )

    return LaunchDescription([
        DeclareLaunchArgument('use_sim_time', default_value='true'),
        DeclareLaunchArgument('spawn_z', default_value='0.02'),
        DeclareLaunchArgument('world', default_value=default_world),
        DeclareLaunchArgument('map', default_value=default_map),
        DeclareLaunchArgument('params_file', default_value=nav2_params),
        DeclareLaunchArgument('use_rviz', default_value='true'),
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(gazebo_launch),
            launch_arguments={
                'use_sim_time': use_sim_time,
                'spawn_z': spawn_z,
                'world': world,
            }.items(),
        ),
        TimerAction(
            period=5.0,
            actions=[
                IncludeLaunchDescription(
                    PythonLaunchDescriptionSource(navigation_launch),
                    launch_arguments={
                        'use_sim_time': use_sim_time,
                        'map': map_yaml,
                        'params_file': params_file,
                    }.items(),
                ),
            ],
        ),
        nav2_cmd_vel_bridge,
        rviz_node,
    ])
