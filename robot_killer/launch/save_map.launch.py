#!/usr/bin/env python3

import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration, TextSubstitution
from launch_ros.actions import Node
from launch.conditions import IfCondition
import subprocess

def generate_launch_description():
    # Create maps directory if it doesn't exist
    pkg_dir = get_package_share_directory('robot_killer')
    maps_dir = os.path.join(pkg_dir, 'maps')
    os.makedirs(maps_dir, exist_ok=True)
    
    # Launch arguments
    map_name = LaunchConfiguration('map_name', default='my_map')
    map_path = LaunchConfiguration('map_path', 
                                  default=os.path.join(maps_dir, TextSubstitution(text='${map_name}')))
    
    return LaunchDescription([
        # Declare arguments
        DeclareLaunchArgument(
            'map_name',
            default_value='my_map',
            description='Name of the map to save'
        ),
        
        DeclareLaunchArgument(
            'map_path',
            default_value=os.path.join(maps_dir, '${map_name}'),
            description='Full path to save the map (without file extension)'
        ),
        
        # Map saver node
        Node(
            package='nav2_map_server',
            executable='map_saver_cli',
            name='map_saver',
            output='screen',
            arguments=['-f', map_path],
            parameters=[
                {'save_map_timeout': 5.0},
                {'free_thresh_default': 0.25},
                {'occupied_thresh_default': 0.65}
            ]
        ),
    ]) 