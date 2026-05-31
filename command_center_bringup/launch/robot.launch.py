import os
import xacro
from launch import LaunchDescription
from launch_ros.actions import Node
from launch.actions import ExecuteProcess, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from ament_index_python.packages import get_package_share_directory

def generate_launch_description():
    bringup_dir     = get_package_share_directory('command_center_bringup')
    description_dir = get_package_share_directory('command_center_description')
    lidar_dir       = get_package_share_directory('ydlidar_ros2_driver')

    xacro_path  = os.path.join(description_dir, 'urdf', 'command_center.urdf.xacro')
    params_path = os.path.join(bringup_dir, 'config', 'params.yaml')

    robot_description = xacro.process_file(xacro_path).toxml()

    # micro-ROS 에이전트 (Docker)
    micro_ros_agent = ExecuteProcess(
        cmd=['docker', 'run', '-it', '--rm',
             '-v', '/dev:/dev',
             '--privileged',
             '--net=host',
             'microros/micro-ros-agent:jazzy',
             'serial', '--dev', '/dev/ttyACM0', '-b', '115200'],
        output='screen'
    )

    robot_state_publisher = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        name='robot_state_publisher',
        output='screen',
        parameters=[{
            'robot_description': robot_description,
            'use_sim_time': False,
        }],
        remappings=[('/joint_states', '/joint_states/filtered')]
    )

    robot_node = Node(
        package='command_center_hal',
        executable='robot_node',
        name='robot_node',
        output='screen',
        parameters=[params_path],
        remappings=[('/cmd_vel', '/cmd_vel_nav')]
    )

    odometry_node = Node(
        package='command_center_hal',
        executable='odometry_node',
        name='odometry_node',
        output='screen',
        parameters=[params_path]
    )

    lidar_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(lidar_dir, 'launch', 'ydlidar_launch.py')
        )
    )

    return LaunchDescription([
        micro_ros_agent,
        robot_state_publisher,
        robot_node,
        odometry_node,
        lidar_launch,
    ])
