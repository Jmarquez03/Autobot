from launch import LaunchDescription
from launch_ros.actions import Node
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from ament_index_python.packages import get_package_share_directory
import os
from launch.substitutions import LaunchConfiguration
from launch.conditions import IfCondition

def generate_launch_description():
    # Launch arguments
    lidar_port = LaunchConfiguration('lidar_port', default='/dev/ttyUSB1')
    esp32_port = LaunchConfiguration('esp32_port', default='/dev/ttyUSB0')
    use_rviz = LaunchConfiguration('use_rviz', default='true')

    # Get package directories
    all_nodes_dir = get_package_share_directory('all_nodes')
    
    # Set up RViz configuration path
    rviz_config_file = os.path.join(all_nodes_dir, 'config', 'robot_rviz.rviz')

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
            parameters=[{'use_sim_time': False, 'serial_port': lidar_port}],
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
            launch_arguments={'serial_port': esp32_port}.items()
        ),

        # SLAM Toolbox launch
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource([
                get_package_share_directory('slam_toolbox'),
                '/launch/online_async_launch.py'
            ]),
            launch_arguments={
                'params_file': os.path.join(all_nodes_dir, 'config', 'slam_toolbox_params.yaml'),
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
                'params_file': os.path.join(all_nodes_dir, 'config', 'robot_local_params.yaml')
            }.items()
        ),
        
        # RViz with custom configuration
        Node(
            package='rviz2',
            executable='rviz2',
            name='rviz2',
            arguments=['-d', rviz_config_file],
            output='screen',
            condition=IfCondition(use_rviz)
        )
    ])

