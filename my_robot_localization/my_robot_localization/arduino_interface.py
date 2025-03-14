from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    return LaunchDescription([
        Node(
            package='my_robot_localization',
            executable='arduino_interface',
            name='arduino_interface',
            output='screen',
            parameters=[{
                'serial_port': '/dev/ttyUSB0',
                'baud_rate': 115200,
                'wheel_radius': 0.033,
                'wheel_separation': 0.17,
                'encoder_resolution': 360,
                'update_rate': 20.0
            }]
        )
    ])
