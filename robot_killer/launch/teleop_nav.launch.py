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
    map_dir = LaunchConfiguration('map_dir', default=os.path.join(robot_killer_dir, 'maps'))
    map_file = LaunchConfiguration('map_file', default=os.path.join(map_dir, 'map.yaml'))
    use_rviz = LaunchConfiguration('use_rviz', default='true')
    
    # Device configurations
    lidar_port = LaunchConfiguration('lidar_port', default='/dev/ttyUSB0')
    imu_port = LaunchConfiguration('imu_port', default='/dev/ttyUSB1')
    esp32_port = LaunchConfiguration('esp32_port', default='/dev/ttyUSB2')
    
    # Include round1 launch with navigation mode
    round1_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([os.path.join(robot_killer_dir, 'launch', 'round1.launch.py')]),
        launch_arguments={
            'use_sim_time': use_sim_time,
            'mode': 'nav',
            'autonomous': 'false',
            'use_rviz': use_rviz,
            'lidar_port': lidar_port,
            'imu_port': imu_port,
            'esp32_port': esp32_port,
            'map_file': map_file
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
        
        DeclareLaunchArgument(
            'map_dir',
            default_value=os.path.join(robot_killer_dir, 'maps'),
            description='Directory for map files'
        ),
        
        DeclareLaunchArgument(
            'map_file',
            default_value=os.path.join(map_dir, 'map.yaml'),
            description='Full path to map yaml file to load'
        ),
        
        DeclareLaunchArgument(
            'use_rviz',
            default_value='true',
            description='Whether to launch RViz'
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
        
        # Main components
        round1_launch,
        
        # Teleop keyboard
        teleop_node
    ]) 