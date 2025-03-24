import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    use_sim_time = LaunchConfiguration('use_sim_time', default='false')
    
    # Parameters for the lidar
    serial_port = LaunchConfiguration('serial_port', default='/dev/ttyUSB0')
    serial_baudrate = LaunchConfiguration('serial_baudrate', default='115200')
    frame_id = LaunchConfiguration('frame_id', default='laser')
    scan_frequency = LaunchConfiguration('scan_frequency', default='10.0')
    
    return LaunchDescription([
        DeclareLaunchArgument(
            'use_sim_time',
            default_value='false',
            description='Use simulation (Gazebo) clock if true'),
        
        DeclareLaunchArgument(
            'serial_port',
            default_value='/dev/ttyUSB0',
            description='Serial port for the lidar'),
            
        DeclareLaunchArgument(
            'serial_baudrate',
            default_value='115200',
            description='Serial baudrate for the lidar'),
            
        DeclareLaunchArgument(
            'frame_id',
            default_value='laser',
            description='Frame ID for the laser scan messages'),
            
        DeclareLaunchArgument(
            'scan_frequency',
            default_value='10.0',
            description='Scan frequency (Hz)'),
            
        # SLlidar node
        Node(
            package='sllidar_ros2',
            executable='sllidar_node',
            name='sllidar_node',
            output='screen',
            parameters=[{
                'use_sim_time': use_sim_time,
                'serial_port': serial_port,
                'serial_baudrate': serial_baudrate,
                'frame_id': frame_id,
                'scan_frequency': scan_frequency,
                'angle_compensate': True,
                'inverted': False,
                'angle_min': -3.14159265359,
                'angle_max': 3.14159265359,
            }],
        ),
        
        # Static transform publisher from lidar to base_link
        Node(
            package='tf2_ros',
            executable='static_transform_publisher',
            name='static_tf_lidar_base',
            arguments=['0', '0', '0.05', '0', '0', '0', 'base_link', 'laser'],
            output='screen',
        ),
    ]) 