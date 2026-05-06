import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, ExecuteProcess, IncludeLaunchDescription, RegisterEventHandler, SetEnvironmentVariable, TimerAction
from launch.event_handlers import OnProcessExit
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
    xacro_file = os.path.join(pkg_share, 'urdf', 'rdd.urdf.xacro')
    default_world = os.path.join(pkg_share, 'worlds', 'apartment_test.world')
    gazebo_launch = os.path.join(
        get_package_share_directory('gazebo_ros'),
        'launch',
        'gazebo.launch.py',
    )

    use_sim_time = LaunchConfiguration('use_sim_time')
    spawn_z = LaunchConfiguration('spawn_z')
    world = LaunchConfiguration('world')
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
        'use_gazebo_control:=true', ' ',
        'use_mesh_visual:=true', ' ',
        'use_casters:=true',
    ])

    rsp_node = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        output='screen',
        parameters=[{
            'robot_description': robot_description,
            'use_sim_time': use_sim_time,
        }],
        remappings=[
            ('/joint_states', '/joint_states_filtered'),
        ],
    )

    spawn_entity = Node(
        package='gazebo_ros',
        executable='spawn_entity.py',
        output='screen',
        arguments=[
            '-entity', 'rdd_robot',
            '-topic', 'robot_description',
            '-x', '0.0',
            '-y', '0.0',
            '-z', spawn_z,
        ],
    )

    joint_state_broadcaster = Node(
        package='controller_manager',
        executable='spawner',
        output='screen',
        arguments=['joint_state_broadcaster', '--controller-manager', '/controller_manager'],
    )

    diff_drive_controller = Node(
        package='controller_manager',
        executable='spawner',
        output='screen',
        arguments=['diff_drive_base_controller', '--controller-manager', '/controller_manager'],
    )

    linear_controller = Node(
        package='controller_manager',
        executable='spawner',
        output='screen',
        arguments=['linear_position_controller', '--controller-manager', '/controller_manager'],
    )

    load_controller = Node(
        package='controller_manager',
        executable='spawner',
        output='screen',
        arguments=['load_position_controller', '--controller-manager', '/controller_manager'],
    )

    caster_controller = Node(
        package='controller_manager',
        executable='spawner',
        output='screen',
        arguments=['caster_position_controller', '--controller-manager', '/controller_manager'],
    )

    joint_state_filter_node = Node(
        package='rdd_description',
        executable='rdd_joint_state_filter.py',
        output='screen',
    )

    load_sync_node = Node(
        package='rdd_description',
        executable='rdd_load_sync.py',
        output='screen',
    )

    caster_sync_node = Node(
        package='rdd_description',
        executable='rdd_caster_sync.py',
        output='screen',
    )

    set_linear_joint = ExecuteProcess(
        cmd=[
            'ros2', 'topic', 'pub', '--rate', '5', '--times', '10',
            '/linear_position_controller/commands',
            'std_msgs/msg/Float64MultiArray',
            '{data: [0.245]}',
        ],
        output='screen',
    )

    set_load_joint = ExecuteProcess(
        cmd=[
            'ros2', 'topic', 'pub', '--rate', '5', '--times', '10',
            '/load_position_controller/commands',
            'std_msgs/msg/Float64MultiArray',
            '{data: [0.042]}',
        ],
        output='screen',
    )

    return LaunchDescription([
        DeclareLaunchArgument('use_sim_time', default_value='true'),
        DeclareLaunchArgument('spawn_z', default_value='0.12'),
        DeclareLaunchArgument('world', default_value=default_world),
        SetEnvironmentVariable('GAZEBO_MODEL_PATH', gazebo_model_path),
        SetEnvironmentVariable('GAZEBO_RESOURCE_PATH', gazebo_resource_path),
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(gazebo_launch),
            launch_arguments={'world': world}.items(),
        ),
        rsp_node,
        joint_state_filter_node,
        load_sync_node,
        spawn_entity,
        RegisterEventHandler(
            OnProcessExit(
                target_action=spawn_entity,
                on_exit=[
                    joint_state_broadcaster,
                    diff_drive_controller,
                    linear_controller,
                    load_controller,
                    caster_controller,
                ],
            )
        ),
        RegisterEventHandler(
            OnProcessExit(
                target_action=caster_controller,
                on_exit=[
                    TimerAction(
                        period=4.0,
                        actions=[
                            set_linear_joint,
                            set_load_joint,
                            caster_sync_node,
                        ],
                    ),
                ],
            )
        ),
    ])
