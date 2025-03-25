import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    use_sim_time = LaunchConfiguration('use_sim_time', default='false')
    
    # Parameters for the ESP32 interface
    serial_port = LaunchConfiguration('serial_port', default='/dev/ttyUSB0')
    baud_rate = LaunchConfiguration('baud_rate', default='115200')
    odom_frame = LaunchConfiguration('odom_frame', default='odom')
    base_frame = LaunchConfiguration('base_frame', default='base_footprint')  # Matches URDF
    
    return LaunchDescription([
        DeclareLaunchArgument(
            'use_sim_time',
            default_value='false',
            description='Use simulation (Gazebo) clock if true'),
        
        DeclareLaunchArgument(
            'serial_port',
            default_value='/dev/ttyUSB0',
            description='Serial port for the ESP32'),
            
        DeclareLaunchArgument(
            'baud_rate',
            default_value='115200',
            description='Baud rate for the ESP32 serial connection'),
            
        DeclareLaunchArgument(
            'odom_frame',
            default_value='odom',
            description='Frame ID for odometry messages'),
            
        DeclareLaunchArgument(
            'base_frame',
            default_value='base_footprint',
            description='Base frame ID for the robot - matches URDF'),
            
        # ESP32 Odometry Node
        Node(
            package='esp32_interface',
            executable='esp32_odometry_node',
            name='esp32_odometry_node',
            output='screen',
            parameters=[{
                'use_sim_time': use_sim_time,
                'serial_port': serial_port,
                'baud_rate': baud_rate,
                'odom_frame': odom_frame,
                'base_frame': base_frame,
            }],
        ),
    ]) 