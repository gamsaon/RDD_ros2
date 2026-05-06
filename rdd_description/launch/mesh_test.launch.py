import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, SetEnvironmentVariable
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import Command, LaunchConfiguration
from launch_ros.actions import Node


def append_env_path(current_value, *paths):
    merged = [path for path in paths if path]
    if current_value:
        merged.append(current_value)
    return os.pathsep.join(merged)


def generate_launch_description():
    package_name = 'rdd_description'
    pkg_share = get_package_share_directory(package_name)
    pkg_parent = os.path.dirname(pkg_share)
    xacro_file = os.path.join(pkg_share, 'urdf', 'mesh_test.urdf.xacro')
    gazebo_launch = os.path.join(
        get_package_share_directory('gazebo_ros'),
        'launch',
        'gazebo.launch.py',
    )

    mesh_file = LaunchConfiguration('mesh_file')
    scale_x = LaunchConfiguration('scale_x')
    scale_y = LaunchConfiguration('scale_y')
    scale_z = LaunchConfiguration('scale_z')
    spawn_z = LaunchConfiguration('spawn_z')
    use_sim_time = LaunchConfiguration('use_sim_time')
    gazebo_model_path = append_env_path(
        os.environ.get('GAZEBO_MODEL_PATH'),
        pkg_parent,
        pkg_share,
    )
    gazebo_resource_path = append_env_path(
        os.environ.get('GAZEBO_RESOURCE_PATH'),
        pkg_parent,
        pkg_share,
        os.path.join(pkg_share, 'meshes'),
    )

    robot_description = Command([
        'xacro', ' ', xacro_file, ' ',
        'mesh_file:=', mesh_file, ' ',
        'scale_x:=', scale_x, ' ',
        'scale_y:=', scale_y, ' ',
        'scale_z:=', scale_z,
    ])

    rsp_node = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        output='screen',
        parameters=[{
            'robot_description': robot_description,
            'use_sim_time': use_sim_time,
        }],
    )

    spawn_entity = Node(
        package='gazebo_ros',
        executable='spawn_entity.py',
        output='screen',
        arguments=[
            '-entity', 'mesh_test_robot',
            '-topic', 'robot_description',
            '-x', '0.0',
            '-y', '0.0',
            '-z', spawn_z,
        ],
    )

    return LaunchDescription([
        DeclareLaunchArgument(
            'mesh_file',
            default_value='package://rdd_description/meshes/RDD_entity.stl',
        ),
        DeclareLaunchArgument('scale_x', default_value='1.0'),
        DeclareLaunchArgument('scale_y', default_value='1.0'),
        DeclareLaunchArgument('scale_z', default_value='1.0'),
        DeclareLaunchArgument('spawn_z', default_value='0.2'),
        DeclareLaunchArgument('use_sim_time', default_value='true'),
        SetEnvironmentVariable('GAZEBO_MODEL_PATH', gazebo_model_path),
        SetEnvironmentVariable('GAZEBO_RESOURCE_PATH', gazebo_resource_path),
        IncludeLaunchDescription(PythonLaunchDescriptionSource(gazebo_launch)),
        rsp_node,
        spawn_entity,
    ])
