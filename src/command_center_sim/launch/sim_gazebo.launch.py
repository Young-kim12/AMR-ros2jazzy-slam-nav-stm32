import os
import xacro
from launch import LaunchDescription
from launch_ros.actions import Node
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from ament_index_python.packages import get_package_share_directory
from launch.actions import TimerAction




def generate_launch_description():
    sim_dir = get_package_share_directory('command_center_sim')

    xacro_path = os.path.join(sim_dir, 'urdf', 'command_center_sim.urdf.xacro')
    robot_description = xacro.process_file(xacro_path).toxml()

    world_path = os.path.join(sim_dir, 'worlds', 'robot_world.sdf')
    bridge_params = os.path.join(sim_dir, 'config', 'gz_bridge.yaml')

    # Gazebo 서버
    gazebo_server = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(
                get_package_share_directory('ros_gz_sim'),
                'launch', 'gz_sim.launch.py'
            )
        ),
        launch_arguments={
            'gz_args': '-r -s -v1 ' + world_path,
        }.items()
    )

    # Gazebo 클라이언트
    gazebo_client = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(
                get_package_share_directory('ros_gz_sim'),
                'launch', 'gz_sim.launch.py'
            )
        ),
        launch_arguments={'gz_args': '-g'}.items()
    )

    robot_state_publisher = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        name='robot_state_publisher',
        output='screen',
        parameters=[{
            'robot_description': robot_description,
            'use_sim_time': True,
        }]
    )

    spawn_robot = Node(
        package='ros_gz_sim',
        executable='create',
        name='spawn_robot',
        output='screen',
        arguments=[
            '-topic', 'robot_description',
            '-name', 'command_center',
            '-z', '0.2',
        ]
    )


    # spawn_robot 이후 10초 대기 후 브릿지 실행
    bridge = TimerAction(
        period=10.0,
        actions=[Node(
            package='ros_gz_bridge',
            executable='parameter_bridge',
            name='ros_gz_bridge',
            output='screen',
            arguments=[
                '--ros-args', '-p',
                f'config_file:={bridge_params}',
            ]
        )]
    )




    bridge = Node(
        package='ros_gz_bridge',
        executable='parameter_bridge',
        name='ros_gz_bridge',
        output='screen',
        arguments=[
            '--ros-args', '-p',
            f'config_file:={bridge_params}',
        ]
    )

    rviz_node = Node(
        package='rviz2',
        executable='rviz2',
        name='rviz2',
        output='screen',
        parameters=[{'use_sim_time': True}]
    )

    return LaunchDescription([
        gazebo_server,
        gazebo_client,
        robot_state_publisher,
        spawn_robot,
        bridge,
        rviz_node,
    ])