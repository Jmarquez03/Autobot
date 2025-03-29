from launch import LaunchDescription
from launch_ros.actions import Node
from launch.substitutions import LaunchConfiguration

def generate_launch_description():
    serial_port = LaunchConfiguration('serial_port', default='/dev/ttyUSB0')
    
    return LaunchDescription([
        Node(
            package='autobot_core',
            executable='esp32_odometry_node',
            name='esp32_odometry_node',
            output='screen',
            parameters=[
                {'serial_port': serial_port},
                {'baud_rate': 115200},
                {'odom_frame_id': 'odom'},
                {'base_frame_id': 'base_footprint'},
            ]
        ),
    ])
