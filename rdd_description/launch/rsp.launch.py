import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration, Command
from launch_ros.actions import Node

def generate_launch_description():
    # 1. 패키지 경로 및 파일 설정
    package_name = 'rdd_description'
    xacro_file = os.path.join(get_package_share_directory(package_name), 'urdf', 'rdd.urdf.xacro')

    # 2. 파라미터 설정 (xacro를 urdf로 변환)
    robot_description_config = Command(['xacro ', xacro_file])
    
    # 3. 노드 설정
    node_robot_state_publisher = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        output='screen',
        parameters=[{
            'robot_description': robot_description_config,
            'use_sim_time': LaunchConfiguration('use_sim_time')
        }]
    )

    return LaunchDescription([
        DeclareLaunchArgument(
            'use_sim_time',
            default_value='false',
            description='Use simulation (Gazebo) clock if true'),
        node_robot_state_publisher
    ])