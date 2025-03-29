from launch import LaunchDescription
from launch_ros.actions import Node
from launch.substitutions import Command, FindPackageShare, LaunchConfiguration
from launch.actions import DeclareLaunchArgument
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
    
    ld = LaunchDescription([
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
        
        # ESP32 odometry node
        Node(
            package='autobot_core',
            executable='esp32_odometry_node',
            name='esp32_odometry_node',
            parameters=[{
                'serial_port': esp_port,
                'odom_frame_id': 'odom',
                'base_frame_id': 'base_footprint'
            }],
            output='screen'
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
                'frame_id': 'lidar_link'
            }],
            output='screen'
        ),
        
        # Nav2 bringup
        Node(
            package='nav2_bringup',
            executable='bringup_launch.py',
            name='nav2_bringup',
            output='screen',
            parameters=[{
                'use_sim_time': use_sim_time,
                'params_file': nav2_params_path
            }]
        )
    ])
    
    # Add required transforms
    ld.add_action(Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        name='robot_state_publisher',
        output='screen',
        parameters=[{
            'robot_description': Command(['xacro ', FindPackageShare('autobot_core'), '/urdf/robot.urdf.xacro'])
        }]
    ))
    
    # Static transform for LIDAR
    ld.add_action(Node(
        package='tf2_ros',
        executable='static_transform_publisher',
        name='lidar_link_broadcaster',
        arguments=['0', '0', '0.2', '0', '0', '0', 'base_link', 'lidar_link']
    ))
    
    # Base footprint to base_link transform
    ld.add_action(Node(
        package='tf2_ros',
        executable='static_transform_publisher',
        name='base_footprint_broadcaster',
        arguments=['0', '0', '0.1', '0', '0', '0', 'base_footprint', 'base_link']
    ))
    
    return ld