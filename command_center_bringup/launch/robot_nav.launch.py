import os
import xacro
from launch import LaunchDescription
from launch_ros.actions import Node
from launch.actions import ExecuteProcess, IncludeLaunchDescription, TimerAction
from launch.launch_description_sources import PythonLaunchDescriptionSource
from ament_index_python.packages import get_package_share_directory

def generate_launch_description():
    bringup_dir     = get_package_share_directory('command_center_bringup')
    description_dir = get_package_share_directory('command_center_description')
    #lidar_dir       = get_package_share_directory('ydlidar_ros2_driver')

    xacro_path   = os.path.join(description_dir, 'urdf', 'command_center.urdf.xacro')
    params_path  = os.path.join(bringup_dir, 'config', 'params.yaml')
    nav2_params  = os.path.join(bringup_dir, 'config', 'nav2_params.yaml')
    #lidar_params = os.path.join(lidar_dir, 'params', 'ydlidar.yaml')
    map_file     = os.path.join(bringup_dir, 'maps', 'my_map.yaml')

    robot_description = xacro.process_file(xacro_path).toxml()

    #micro_ros_agent = ExecuteProcess(
    #    cmd=['ros2', 'run', 'micro_ros_agent', 'micro_ros_agent',
    #         'serial', '--dev', '/dev/ttyACM0', '-b', '115200'],
    #    output='screen'
    #)

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

    #robot_node = Node(
    #    package='command_center_hal',
    #    executable='robot_node',
    #    name='robot_node',
    #    output='screen',
    #    parameters=[params_path],
    #    remappings=[('/cmd_vel', '/cmd_vel_nav')]
    #)

    
    odometry_node = Node(
        package='command_center_hal',
        executable='odometry_node',
        name='odometry_node',
        output='screen',
        parameters=[params_path]
    )

    #lidar_node = Node(
    #    package='ydlidar_ros2_driver',
    #    executable='ydlidar_ros2_driver_node',
    #    name='ydlidar_ros2_driver_node',
    #    output='screen',
    #    emulate_tty=True,
    #    parameters=[lidar_params],
    #)

    #lidar_tf = Node(
    #    package='tf2_ros',
    #    executable='static_transform_publisher',
    #    name='static_tf_pub_laser',
    #    arguments=['0', '0', '0.02', '0', '0', '0', '1',
    #               'base_link', 'laser_frame'],
    #)

    # Nav2 bringup (저장된 맵 + AMCL)
    nav2 = TimerAction(
        period=3.0,
        actions=[IncludeLaunchDescription(
            PythonLaunchDescriptionSource(
                os.path.join(
                    get_package_share_directory('nav2_bringup'),
                    'launch', 'bringup_launch.py'
                )
            ),
            launch_arguments={
                'map': map_file,
                'params_file': nav2_params,
                'use_sim_time': 'false'
            }.items()
        )]
    )

    nav2_activate = TimerAction(
        period=15.0,
        actions=[ExecuteProcess(
            cmd=['bash', '-c',
                 'ros2 lifecycle set /bt_navigator configure && '
                 'ros2 lifecycle set /bt_navigator activate && '
                 'ros2 lifecycle set /planner_server activate && '
                 'ros2 lifecycle set /controller_server activate && '
                 'ros2 lifecycle set /behavior_server activate && '
                 'ros2 lifecycle set /smoother_server activate'],
            output='screen'
        )]
    )

    return LaunchDescription([
        #micro_ros_agent,
        robot_state_publisher,
        #robot_node,
        odometry_node,
        #lidar_node,
        #lidar_tf,
        nav2,
        nav2_activate,
    ])