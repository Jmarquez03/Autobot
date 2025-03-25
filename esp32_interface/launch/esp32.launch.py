#!/usr/bin/env python3

import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node

def generate_launch_description():
    # Get the package directory
    pkg_dir = get_package_share_directory('esp32_interface')
    
    # Define launch arguments
    serial_port = LaunchConfiguration('serial_port')
    baud_rate = LaunchConfiguration('baud_rate')
    frame_id = LaunchConfiguration('frame_id')
    child_frame_id = LaunchConfiguration('child_frame_id')
    publish_rate = LaunchConfiguration('publish_rate')
    
    # ESP32 odometry node
    esp32_node = Node(
        package='esp32_interface',
        executable='esp32_odometry_node',
        name='esp32_odometry_node',
        output='screen',
        parameters=[{
            'serial_port': serial_port,
            'baud_rate': baud_rate,
            'frame_id': frame_id,
            'child_frame_id': child_frame_id,
            'publish_rate': publish_rate
        }]
    )
    
    return LaunchDescription([
        # Declare all launch arguments
        DeclareLaunchArgument(
            'serial_port',
            default_value='/dev/ttyUSB0',
            description='Serial port connected to ESP32'
        ),
        
        DeclareLaunchArgument(
            'baud_rate',
            default_value='115200',
            description='Baud rate for serial communication'
        ),
        
        DeclareLaunchArgument(
            'frame_id',
            default_value='odom',
            description='Frame ID for odometry messages'
        ),
        
        DeclareLaunchArgument(
            'child_frame_id',
            default_value='base_link',
            description='Child frame ID for odometry messages'
        ),
        
        DeclareLaunchArgument(
            'publish_rate',
            default_value='20.0',
            description='Rate at which to publish odometry (Hz)'
        ),
        
        # Add the node to the launch description
        esp32_node
    ]) 