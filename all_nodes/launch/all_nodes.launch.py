from launch import LaunchDescription
from launch_ros.actions import Node
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from ament_index_python.packages import get_package_share_directory
import os

def generate_launch_description():
    return LaunchDescription([
        # Visualize the robot
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource([
                get_package_share_directory('robot_visualization'),
                '/launch/robot_visualization.launch.py'
            ])
        ),

        # LIDAR launch with USB configuration
        Node(
            package='sllidar_ros2',
            executable='sllidar_node',
            parameters=[{'use_sim_time': False, 'serial_port': '/dev/ttyUSB1'}],
            output='screen'
        ),

        # IMU node with parameters
        Node(
            package='bno055',
            executable='bno055',
            parameters=[os.path.join(
                get_package_share_directory('bno055'),
                'config',
                'bno055_params_i2c.yaml'
            )],
            output='screen'
        ),

        # ESP32 odometry interface
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource([
                get_package_share_directory('esp32_interface'),
                '/launch/esp32_interface.launch.py'
            ]),
            launch_arguments={'serial_port': '/dev/ttyUSB0'}.items()
        ),

        # SLAM Toolbox launch
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource([
                get_package_share_directory('slam_toolbox'),
                '/launch/online_async_launch.py'
            ]),
            launch_arguments={
                'params_file': './robot_ws/src/all_nodes/config/slam_toolbox_params.yaml',
                'use_sim_time': 'false'
            }.items()
        ),

        # Ackermann converter node
        Node(
            package='twist_to_ackermann',
            executable='twist_to_ackermann_converter',
            output='screen'
        ),

        # Robot localization EKF
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource([
                get_package_share_directory('robot_localization'),
                '/launch/ekf.launch.py'
            ]),
            launch_arguments={
                'params_file': '/home/ieee/robot_ws/src/all_nodes/config/robot_local_params.yaml'
            }.items()
        )
    ])

