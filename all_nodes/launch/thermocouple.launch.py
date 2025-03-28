import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node

def generate_launch_description():
    # Launch arguments
    use_sim_time = LaunchConfiguration('use_sim_time', default='false')
    serial_port = LaunchConfiguration('serial_port', default='/dev/ttyUSB3')
    
    return LaunchDescription([
        DeclareLaunchArgument(
            'use_sim_time',
            default_value='false',
            description='Use simulation time if true'
        ),
        
        DeclareLaunchArgument(
            'serial_port',
            default_value='/dev/ttyUSB3',
            description='Serial port for Arduino with MAX6675'
        ),
        
        # Thermocouple node
        Node(
            package='all_nodes',
            executable='thermocouple_node',
            name='thermocouple_node',
            output='screen',
            parameters=[{
                'use_sim_time': use_sim_time,
                'serial_port': serial_port,
                'baud_rate': 115200,
                'publish_rate': 2.0
            }]
        )
    ])