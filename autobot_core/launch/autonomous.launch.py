from launch import LaunchDescription
from launch_ros.actions import Node
from launch.substitutions import LaunchConfiguration, Command
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
    controller_params_path = os.path.join(autobot_core_dir, 'config', 'ackermann_controller.yaml')
    
    # Get URDF via xacro
    robot_description_content = Command(
        ['xacro ', os.path.join(autobot_core_dir, 'urdf', 'robot.urdf.xml')]
    )
    robot_description = {'robot_description': robot_description_content}
    
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
        
        # Robot state publisher
        Node(
            package='robot_state_publisher',
            executable='robot_state_publisher',
            name='robot_state_publisher',
            output='screen',
            parameters=[robot_description]
        ),
        
        # ESP32 odometry interface
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource([
                get_package_share_directory('autobot_core'),
                '/launch/esp32_interface.launch.py'
            ]),
            launch_arguments={'serial_port': esp_port}.items()
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
        
        # Controller Manager
        Node(
            package='controller_manager',
            executable='ros2_control_node',
            parameters=[robot_description, controller_params_path],
            output='screen',
        ),
        
        # Joint State Broadcaster
        Node(
            package='controller_manager',
            executable='spawner',
            arguments=['joint_state_broadcaster', '--controller-manager', '/controller_manager'],
            output='screen',
        ),
        
        # Ackermann Controller
        Node(
            package='controller_manager',
            executable='spawner',
            arguments=['ackermann_controller', '--controller-manager', '/controller_manager'],
            output='screen',
        ),
        
        # Twist to Ackermann converter (for compatibility)
        Node(
            package='autobot_core',
            executable='twist_to_ackermann_converter',
            output='screen',
            parameters=[{
                'serial_port': nano_port,
                'wheelbase': 0.3,
                'max_steering_angle': 0.6,
                'use_ros2_control': True
            }]
        ),
        
        # Nav2 launch
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource([
                get_package_share_directory('nav2_bringup'),
                '/launch/navigation_launch.py'
            ]),
            launch_arguments={
                'params_file': nav2_params_path,
                'use_sim_time': use_sim_time
            }.items()
        ),
        
        # SLAM Toolbox
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource([
                get_package_share_directory('slam_toolbox'),
                '/launch/online_async_launch.py'
            ]),
            launch_arguments={
                'params_file': os.path.join(autobot_core_dir, 'config', 'slam_toolbox_params.yaml'),
                'use_sim_time': use_sim_time
            }.items()
        ),
        
        # Autonomous navigation node
        Node(
            package='autobot_core',
            executable='autonomous_nav',
            name='autonomous_nav',
            output='screen'
        ),
    ])