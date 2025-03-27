from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    return LaunchDescription([
        Node(
            package='autobot_core',  # Changed from all_nodes
            executable='esp32_odometry_node',
            name='esp32_odometry_node',
            output='screen',
            parameters=[
                {'serial_port': '/dev/ttyUSB0'},
                {'baud_rate': 115200},
                {'odom_frame': 'odom'},
                {'base_frame': 'base_footprint'},
            ]
        ),
    ])
