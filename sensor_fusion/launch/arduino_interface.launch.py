from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    return LaunchDescription([
        Node(
            package="sensor_fusion",
            executable="arduino_interface",  # Remove the .py extension
            name="arduino_serial_node",
            output="screen"
        )
    ])
