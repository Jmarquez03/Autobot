import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node

def generate_launch_description():
    # Launch Arguments
    use_sim_time = LaunchConfiguration('use_sim_time', default='false')
    
    return LaunchDescription([
        DeclareLaunchArgument(
            'use_sim_time',
            default_value='false',
            description='Use simulation time if true'
        ),
        
        # Hardware diagnostics node
        Node(
            package='autobot_core',
            executable='hardware_diagnostics',
            name='hardware_diagnostics',
            output='screen',
            parameters=[{
                'use_sim_time': use_sim_time
            }]
        )
    ]) 