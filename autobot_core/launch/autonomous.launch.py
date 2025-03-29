from launch import LaunchDescription
from launch_ros.actions import Node
from launch.substitutions import LaunchConfiguration
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from ament_index_python.packages import get_package_share_directory
import os

def generate_launch_description():
    # Launch arguments
    use_sim_time = LaunchConfiguration('use_sim_time', default='false')
    esp_port = LaunchConfiguration('esp_port', default='/dev/ttyUSB0')
    lidar_port = LaunchConfiguration('lidar_port', default='/dev/ttyUSB1')
    nano_port = LaunchConfiguration('nano_port', default='/dev/ttyUSB2')
    
    autobot_core_dir = get_package_share_directory('autobot_core')
    nav2_params_path = os.path.join(autobot_core_dir, 'config', 'nav2_ackermann_params.yaml')
    
    return LaunchDescription([
        # Declare launch arguments
        DeclareLaunchArgument(
            'use_sim_time',
            default_value='false',
            description='Use simulation time'
        ),
        DeclareLaunchArgument(
            'esp_port',
            default_value='/dev/ttyUSB0',
            description='ESP32 serial port'
        ),
        DeclareLaunchArgument(
            'lidar_port',
            default_value='/dev/ttyUSB1',
            description='LIDAR serial port'
        ),
        DeclareLaunchArgument(
            'nano_port',
            default_value='/dev/ttyUSB2',
            description='Nano serial port'
        ),
        
        # Visualize the robot
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource([
                get_package_share_directory('autobot_core'),
                '/launch/robot_visualization.launch.py'
            ])
        ),
        
        # ESP32 odometry interface
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource([
                get_package_share_directory('autobot_core'),
                '/launch/esp32_interface.launch.py'
            ]),
            launch_arguments={'serial_port': esp_port}.items()
        ),
        
        # Twist to Ackermann converter
        Node(
            package='autobot_core',
            executable='twist_to_ackermann_converter',
            name='twist_to_ackermann_converter',
            parameters=[{
                'serial_port': nano_port,
                'wheelbase': 0.3,
                'max_steering_angle': 0.6
            }],
            output='screen'
        ),
        
        # LIDAR node
        Node(
            package='sllidar_ros2',
            executable='sllidar_node',
            name='sllidar_node',
            parameters=[{
                'serial_port': lidar_port,
                'frame_id': 'laser'
            }],
            output='screen'
        ),
        
        # Nav2 bringup
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource([
                get_package_share_directory('nav2_bringup'),
                '/launch/bringup_launch.py'
            ]),
            launch_arguments={
                'params_file': nav2_params_path,
                'use_sim_time': 'false',
                'map_subscribe_transient_local': 'true',
                'default_bt_xml_filename': 'nav2_bt_navigator/navigate_w_replanning_and_recovery.xml',
                'autostart': 'true'
            }.items()
        )
    ])