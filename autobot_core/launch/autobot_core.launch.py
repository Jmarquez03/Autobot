from launch import LaunchDescription
from launch_ros.actions import Node
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from ament_index_python.packages import get_package_share_directory
import os
from launch.substitutions import LaunchConfiguration
from launch.conditions import IfCondition
from launch.actions import DeclareLaunchArgument

def generate_launch_description():
    # Launch arguments
    lidar_port = LaunchConfiguration('lidar_port', default='/dev/ttyUSB1')
    esp32_port = LaunchConfiguration('esp32_port', default='/dev/ttyUSB0')
    ackermann_port = LaunchConfiguration('ackermann_port', default='/dev/ttyUSB2')
    use_rviz = LaunchConfiguration('use_rviz', default='true')

    # Get package directories
    autobot_core_dir = get_package_share_directory('autobot_core')
    
    # Set up RViz configuration path
    rviz_config_file = os.path.join(autobot_core_dir, 'config', 'robot_rviz.rviz')

    return LaunchDescription([
        # Declare launch arguments
        DeclareLaunchArgument(
            'lidar_port',
            default_value='/dev/ttyUSB1',
            description='Serial port for LIDAR'
        ),
        DeclareLaunchArgument(
            'esp32_port',
            default_value='/dev/ttyUSB0',
            description='Serial port for ESP32'
        ),
        DeclareLaunchArgument(
            'ackermann_port',
            default_value='/dev/ttyUSB2',
            description='Serial port for Ackermann controller'
        ),
        DeclareLaunchArgument(
            'use_rviz',
            default_value='true',
            description='Launch RViz if true'
        ),
        
        # Visualize the robot
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource([
                get_package_share_directory('autobot_core'),
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

        # ESP32 odometry interface
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource([
                get_package_share_directory('autobot_core'),
                '/launch/esp32_interface.launch.py'
            ]),
            launch_arguments={'serial_port': esp32_port}.items()
        ),

        # Ackermann converter node
        Node(
            package='autobot_core',
            executable='twist_to_ackermann_converter',
            output='screen',
            parameters=[{'serial_port': ackermann_port}]  # Added parameter for serial port
        ),

        # SLAM Toolbox launch
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource([
                get_package_share_directory('slam_toolbox'),
                '/launch/online_async_launch.py'
            ]),
            launch_arguments={
                'params_file': os.path.join(autobot_core_dir, 'config', 'slam_toolbox_params.yaml'),
                'use_sim_time': 'false'
            }.items()
        ),

        # Robot localization EKF
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource([
                get_package_share_directory('robot_localization'),
                '/launch/ekf.launch.py'
            ]),
            launch_arguments={
                'params_file': os.path.join(autobot_core_dir, 'config', 'robot_local_params.yaml')
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

