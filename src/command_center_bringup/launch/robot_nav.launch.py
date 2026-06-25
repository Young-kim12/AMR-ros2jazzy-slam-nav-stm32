import os
import xacro
from launch import LaunchDescription
from launch_ros.actions import Node
from launch.actions import ExecuteProcess, IncludeLaunchDescription, TimerAction
from launch.launch_description_sources import PythonLaunchDescriptionSource
from ament_index_python.packages import get_package_share_directory

def generate_launch_description():
    bringup_dir     = get_package_share_directory('command_center_bringup')
    nav2_params     = os.path.join(bringup_dir, 'config', 'nav2_params.yaml')
    map_file        = os.path.join(bringup_dir, 'maps', 'my_map.yaml')

    localization = TimerAction(
        period=2.0,
        actions=[IncludeLaunchDescription(
            PythonLaunchDescriptionSource(
                os.path.join(
                    get_package_share_directory('nav2_bringup'),
                    'launch', 'localization_launch.py'
                )
            ),
            launch_arguments={
                'map': map_file,
                'params_file': nav2_params,
                'use_sim_time': 'false'
            }.items()
        )]
    )

    nav2 = TimerAction(
        period=5.0,
        actions=[IncludeLaunchDescription(
            PythonLaunchDescriptionSource(
                os.path.join(
                    get_package_share_directory('nav2_bringup'),
                    'launch', 'navigation_launch.py'
                )
            ),
            launch_arguments={
                'params_file': nav2_params,
                'use_sim_time': 'false'
            }.items()
        )]
    )

    return LaunchDescription([
        localization,
        nav2,
    ])