import os
import xacro
from launch import LaunchDescription
from launch_ros.actions import Node
from launch.actions import ExecuteProcess, IncludeLaunchDescription, TimerAction
#from launch.launch_description_sources import PythonLaunchDescriptionSource
from ament_index_python.packages import get_package_share_directory

#from launch.actions import EmitEvent, RegisterEventHandler
#from launch_ros.event_handlers import OnStateTransition
from launch_ros.actions import LifecycleNode
#from lifecycle_msgs.msg import Transition


def generate_launch_description():
    bringup_dir     = get_package_share_directory('command_center_bringup')
    description_dir = get_package_share_directory('command_center_description')
    #lidar_dir       = get_package_share_directory('ydlidar_ros2_driver')

    xacro_path   = os.path.join(description_dir, 'urdf', 'command_center.urdf.xacro')
    params_path  = os.path.join(bringup_dir, 'config', 'params.yaml')
    slam_params  = os.path.join(bringup_dir, 'config', 'slam_params.yaml')
    #nav2_params  = os.path.join(bringup_dir, 'config', 'nav2_params.yaml')
    #lidar_params = os.path.join(lidar_dir, 'params', 'ydlidar.yaml')

    robot_description = xacro.process_file(xacro_path).toxml()

    # micro-ROS 에이전트 (STM32 ↔ ROS2 브릿지)
    #micro_ros_agent = ExecuteProcess(
    #    cmd=['ros2', 'run', 'micro_ros_agent', 'micro_ros_agent',
    #         'serial', '--dev', '/dev/ttyACM0', '-b', '115200',],   # 시간 동기화 모드 추가
    #    output='screen'
    #)


    # 로봇 상태 퍼블리셔
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

    # HAL 노드들
    #robot_node = Node(
    #    package='command_center_hal',
    #    executable='robot_node',
    #    name='robot_node',
    #    output='screen',
    #    parameters=[params_path],
    #    #remappings=[('/cmd_vel', '/cmd_vel_nav')]
    #)

    odometry_node = Node(
        package='command_center_hal',
        executable='odometry_node',
        name='odometry_node',
        output='screen',
        parameters=[params_path]
    )

    # 라이다 드라이버
    #lidar_node = Node(
    #    package='ydlidar_ros2_driver',
    #    executable='ydlidar_ros2_driver_node',
    #    name='ydlidar_ros2_driver_node',
    #    output='screen',
    #    emulate_tty=True,
    #    parameters=[lidar_params],
    #)

    # 라이다 TF (base_link → laser_frame)
    #lidar_tf = Node(
    #    package='tf2_ros',
    #    executable='static_transform_publisher',
    #    name='static_tf_pub_laser',
    #    arguments=['0', '0', '0.02', '0', '0', '0', '1',
    #               'base_link', 'laser_frame'],
    #)

    # SLAM (라이다 뜨고 3초 후)
    slam_node = TimerAction(
        period=3.0,
        actions=[LifecycleNode(
            package='slam_toolbox',
            executable='async_slam_toolbox_node',
            name='slam_toolbox',
            output='screen',
            parameters=[slam_params],
            namespace='',
        )]
    )

    slam_configure = TimerAction(
        period=5.0,
        actions=[ExecuteProcess(
            cmd=['ros2', 'lifecycle', 'set', '/slam_toolbox', 'configure'],
            output='screen'
        )]
    )

    slam_activate = TimerAction(
        period=7.0,
        actions=[ExecuteProcess(
            cmd=['ros2', 'lifecycle', 'set', '/slam_toolbox', 'activate'],
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
        slam_node,
        slam_configure,
        slam_activate,
    ])