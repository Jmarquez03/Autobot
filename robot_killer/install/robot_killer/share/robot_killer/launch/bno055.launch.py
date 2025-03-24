import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    use_sim_time = LaunchConfiguration('use_sim_time', default='false')
    
    # Parameters for the BNO055 IMU
    port = LaunchConfiguration('port', default='/dev/ttyUSB1')  # Change to match your system
    frame_id = LaunchConfiguration('frame_id', default='imu_link')
    
    return LaunchDescription([
        DeclareLaunchArgument(
            'use_sim_time',
            default_value='false',
            description='Use simulation (Gazebo) clock if true'),
        
        DeclareLaunchArgument(
            'port',
            default_value='/dev/ttyUSB1',
            description='Serial port for the IMU'),
            
        DeclareLaunchArgument(
            'frame_id',
            default_value='imu_link',
            description='Frame ID for the IMU messages'),
            
        # BNO055 node
        Node(
            package='bno055',
            executable='bno055_node',
            name='bno055_node',
            output='screen',
            parameters=[{
                'use_sim_time': use_sim_time,
                'port': port,
                'frame_id': frame_id,
                'operation_mode': 8,  # OPERATION_MODE_IMUPLUS
                'oscillator': False,
                'reset_orientation': True,
                'frequency': 100.0,
                'use_magnetometer': True,
                'use_temperature': True
            }],
        ),
        
        # Static transform publisher from IMU to base_link
        Node(
            package='tf2_ros',
            executable='static_transform_publisher',
            name='static_tf_imu_base',
            arguments=['0', '0', '0.03', '0', '0', '0', 'base_link', 'imu_link'],
            output='screen',
        ),
    ]) 