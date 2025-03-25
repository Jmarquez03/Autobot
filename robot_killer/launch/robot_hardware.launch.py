import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.substitutions import LaunchConfiguration
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node


def generate_launch_description():
    pkg_dir = get_package_share_directory('robot_killer')
    
    use_sim_time = LaunchConfiguration('use_sim_time', default='false')
    
    # Device configurations
    lidar_port = LaunchConfiguration('lidar_port', default='/dev/ttyUSB0')
    imu_port = LaunchConfiguration('imu_port', default='/dev/ttyUSB1')
    esp32_port = LaunchConfiguration('esp32_port', default='/dev/ttyUSB0')
    
    # Include the launch files for each hardware component
    lidar_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(pkg_dir, 'launch', 'lidar.launch.py')
        ),
        launch_arguments={
            'use_sim_time': use_sim_time,
            'serial_port': lidar_port
        }.items()
    )
    
    bno055_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(pkg_dir, 'launch', 'bno055.launch.py')
        ),
        launch_arguments={
            'use_sim_time': use_sim_time,
            'port': imu_port
        }.items()
    )
    
    esp32_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(pkg_dir, 'launch', 'esp32.launch.py')
        ),
        launch_arguments={
            'use_sim_time': use_sim_time,
            'serial_port': esp32_port
        }.items()
    )
    
    # Define the launch description with all components
    return LaunchDescription([
        DeclareLaunchArgument(
            'use_sim_time',
            default_value='false',
            description='Use simulation (Gazebo) clock if true'),
            
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
            default_value='/dev/ttyUSB0',
            description='Serial port for the ESP32 controller'
        ),
            
        # Include all hardware components
        lidar_launch,
        bno055_launch,
        esp32_launch,
    ]) 