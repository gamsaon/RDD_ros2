import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.conditions import IfCondition, UnlessCondition
from launch.substitutions import LaunchConfiguration
from launch.substitutions import Command
from launch_ros.actions import Node

def generate_launch_description():

    # 패키지 경로 설정
    pkg_description = get_package_share_directory('rdd_description')

    # Xacro 파일 경로 설정
    xacro_file = os.path.join(pkg_description, 'urdf', 'rdd.urdf.xacro')
    rviz_config_file = os.path.join(pkg_description, 'rviz', 'rdd_gazebo.rviz')

    # Robot State Publisher 노드 설정 (Xacro를 URDF로 변환하여 읽음)
    robot_description_config = Command(['xacro ', xacro_file, ' ', 'use_casters:=true'])
    
    params = {'robot_description': robot_description_config}
    node_robot_state_publisher = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        output='screen',
        parameters=[params],
        remappings=[
            ('/joint_states', '/joint_states_filtered')
        ]
    )

    node_joint_state_filter = Node(
        package='rdd_description',
        executable='rdd_joint_state_filter.py',
        name='rdd_joint_state_filter',
        output='screen'
    )

    node_joint_state_publisher_gui = Node(
        package='joint_state_publisher_gui',
        executable='joint_state_publisher_gui',
        name='joint_state_publisher_gui',
        condition=IfCondition(LaunchConfiguration('use_joint_state_gui'))
    )

    node_joint_state_publisher = Node(
        package='joint_state_publisher',
        executable='joint_state_publisher',
        name='joint_state_publisher',
        condition=UnlessCondition(LaunchConfiguration('use_joint_state_gui'))
    )

    # RViz2 실행
    node_rviz = Node(
        package='rviz2',
        executable='rviz2',
        name='rviz2',
        output='screen',
        arguments=['-d', rviz_config_file],
    )

    return LaunchDescription([
        DeclareLaunchArgument(
            'use_joint_state_gui',
            default_value='true',
            description='Run joint_state_publisher_gui for manual joint sliders'
        ),
        node_joint_state_filter,
        node_robot_state_publisher,
        node_joint_state_publisher,
        node_joint_state_publisher_gui,
        node_rviz
    ])
