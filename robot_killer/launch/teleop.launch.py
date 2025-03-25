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
    
    # Include hardware components only
    robot_state_publisher_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([os.path.join(robot_killer_dir, 'launch', 'robot_state_publisher.launch.py')]),
        launch_arguments={'use_sim_time': use_sim_time}.items()
    )
    
    lidar_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([os.path.join(robot_killer_dir, 'launch', 'lidar.launch.py')]),
        launch_arguments={
            'use_sim_time': use_sim_time,
            'serial_port': lidar_port
        }.items()
    )
    
    imu_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([os.path.join(robot_killer_dir, 'launch', 'bno055.launch.py')]),
        launch_arguments={
            'use_sim_time': use_sim_time,
            'port': imu_port
        }.items()
    )
    
    esp32_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([os.path.join(robot_killer_dir, 'launch', 'esp32.launch.py')]),
        launch_arguments={
            'use_sim_time': use_sim_time,
            'serial_port': esp32_port
        }.items()
    )
    
    twist_to_ackermann_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([os.path.join(robot_killer_dir, 'launch', 'twist_to_ackermann.launch.py')]),
        launch_arguments={'use_sim_time': use_sim_time}.items()
    )
    
    rviz_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([os.path.join(robot_killer_dir, 'launch', 'rviz.launch.py')]),
        launch_arguments={'use_sim_time': use_sim_time}.items()
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
        
        # Hardware components
        robot_state_publisher_launch,
        lidar_launch,
        imu_launch,
        esp32_launch,
        twist_to_ackermann_launch,
        
        # Visualization
        rviz_launch,
        
        # Teleop keyboard
        teleop_node
    ]) 