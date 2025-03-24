import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    use_sim_time = LaunchConfiguration('use_sim_time', default='false')
    
    # Configure the lidar parameters here
    lidar_params = {
        'serial_port': '/dev/ttyUSB0',  # Change this to your lidar's port
        'serial_baudrate': 115200,       # Change based on your lidar model
        'frame_id': 'laser',             # This matches the RViz config
        'inverted': False,
        'angle_compensate': True,
        'scan_mode': 'Standard',
    }
    
    # Try to use the sllidar RViz config if available
    rviz_config_dir = os.path.join(
        get_package_share_directory('sllidar_ros2'),
        'rviz',
        'sllidar_ros2.rviz')
    
    return LaunchDescription([
        DeclareLaunchArgument(
            'use_sim_time',
            default_value='false',
            description='Use simulation clock if true'),
            
        # Add a static transform publisher
        # This connects the "laser" frame to a base frame "base_link"
        # Parameters: x y z qx qy qz qw parent_frame child_frame
        Node(
            package='tf2_ros',
            executable='static_transform_publisher',
            name='static_transform_publisher',
            arguments=['0', '0', '0', '0', '0', '0', '1', 'base_link', 'laser'],
        ),
        
        # The sllidar driver node
        Node(
            package='sllidar_ros2',
            executable='sllidar_node',
            name='sllidar_node',
            parameters=[lidar_params,
                       {'use_sim_time': use_sim_time}],
            output='screen',
        ),
        
        # Launch RViz2 for visualization
        Node(
            package='rviz2',
            executable='rviz2',
            name='rviz2',
            arguments=['-d', rviz_config_dir],
            parameters=[{'use_sim_time': use_sim_time}],
            output='screen',
        ),
    ]) 