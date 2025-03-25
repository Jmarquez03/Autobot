#!/usr/bin/env python3

import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.substitutions import LaunchConfiguration
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node

def generate_launch_description():
    # Get the robot_killer directory
    robot_killer_dir = get_package_share_directory('robot_killer')
    
    # Launch configurations
    use_sim_time = LaunchConfiguration('use_sim_time', default='false')
    
    # Device configurations
    lidar_port = LaunchConfiguration('lidar_port', default='/dev/ttyUSB0')
    imu_port = LaunchConfiguration('imu_port', default='/dev/ttyUSB1')
    esp32_port = LaunchConfiguration('esp32_port', default='/dev/ttyUSB2')
    
    # Include SLAM launch (which includes hardware components)
    slam_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([os.path.join(robot_killer_dir, 'launch', 'slam.launch.py')]),
        launch_arguments={
            'use_sim_time': use_sim_time,
            'lidar_port': lidar_port,
            'imu_port': imu_port,
            'controller_port': esp32_port,
            'use_rviz': 'true'
        }.items()
    )
    
    # Add teleop keyboard node
    teleop_node = Node(
        package='teleop_twist_keyboard',
        executable='teleop_twist_keyboard',
        name='teleop_twist_keyboard',
        prefix='xterm -e', # This opens the teleop in a separate terminal window
        output='screen'
    )
    
    return LaunchDescription([
        # Launch arguments
        DeclareLaunchArgument(
            'use_sim_time',
            default_value='false',
            description='Use simulation (Gazebo) clock if true'
        ),
        
        # Device port arguments
        DeclareLaunchArgument(
            'lidar_port',
            default_value='/dev/ttyUSB0',
            description='Serial port for the LIDAR'
        ),
        
        DeclareLaunchArgument(
            'imu_port',
            default_value='/dev/ttyUSB1',
            description='Serial port for the BNO055 IMU'
        ),
        
        DeclareLaunchArgument(
            'esp32_port',
            default_value='/dev/ttyUSB2',
            description='Serial port for the ESP32 controller'
        ),
        
        # SLAM components
        slam_launch,
        
        # Teleop keyboard
        teleop_node
    ]) 