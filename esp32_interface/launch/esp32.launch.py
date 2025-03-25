from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    return LaunchDescription([
        Node(
            package='esp32_interface',
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
        # Node(
        #     package='tf2_ros',
        #     executable='static_transform_publisher',
        #     name='base_link_to_laser',
        #     arguments=['0', '0', '0', '0', '0', '0', 'base_link', 'laser'],
        # ),
        # Node(
        #     package='teleop_twist_keyboard',
        #     executable='teleop_twist_keyboard',
        #     name='teleop_twist_keyboard',
        #     output='screen',
        #     #prefix='xterm -e',
        # ),
    ])
