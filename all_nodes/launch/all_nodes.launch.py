from launch import LaunchDescription
from launch_ros.actions import Node
from launch.actions import IncludeLaunchDescription, DeclareLaunchArgument, ExecuteProcess, GroupAction
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PythonExpression
from launch.conditions import IfCondition, UnlessCondition
from ament_index_python.packages import get_package_share_directory
import os

def generate_launch_description():
    # Get package directories
    all_nodes_dir = get_package_share_directory('all_nodes')
    
    # Launch configurations
    use_sim_time = LaunchConfiguration('use_sim_time', default='false')
    use_rviz = LaunchConfiguration('use_rviz', default='true')
    
    # Device configurations
    lidar_port = LaunchConfiguration('lidar_port', default='/dev/ttyUSB0')
    imu_port = LaunchConfiguration('imu_port', default='/dev/ttyUSB1')
    esp32_port = LaunchConfiguration('esp32_port', default='/dev/ttyUSB2')
    
    # Mode selection (slam or navigation)
    mode = LaunchConfiguration('mode', default='slam')
    slam_mode_condition = IfCondition(PythonExpression(['\'', mode, '\' == \'slam\'']))
    nav_mode_condition = IfCondition(PythonExpression(['\'', mode, '\' == \'nav\'']))
    
    # Autonomous mode
    autonomous = LaunchConfiguration('autonomous', default='false')
    autonomous_condition = IfCondition(autonomous)
    
    # Map parameters
    map_dir = LaunchConfiguration('map_dir', default=os.path.join(all_nodes_dir, 'maps'))
    map_file = LaunchConfiguration('map_file', default=os.path.join(map_dir, 'map.yaml'))
    save_map = LaunchConfiguration('save_map', default='false')
    map_name = LaunchConfiguration('map_name', default='my_map')
    
    # Base components that are always launched
    base_components = [
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
            parameters=[{'use_sim_time': use_sim_time, 'serial_port': lidar_port}],
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
        
        # Include diagnostics
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource([
                os.path.join(all_nodes_dir, 'launch', 'diagnostics.launch.py')
            ]),
            launch_arguments={
                'use_sim_time': use_sim_time
            }.items()
        )
    ]
    
    # SLAM mode components
    slam_components = GroupAction([
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource([
                get_package_share_directory('slam_toolbox'),
                '/launch/online_async_launch.py'
            ]),
            launch_arguments={
                'params_file': os.path.join(all_nodes_dir, 'config', 'slam_toolbox_params.yaml'),
                'use_sim_time': use_sim_time
            }.items()
        )
    ], condition=slam_mode_condition)
    
    # Navigation mode components
    nav_components = GroupAction([
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource([
                os.path.join(all_nodes_dir, 'launch', 'navigation.launch.py')
            ]),
            launch_arguments={
                'use_sim_time': use_sim_time,
                'map_file': map_file
            }.items()
        )
    ], condition=nav_mode_condition)
    
    # Autonomous components
    autonomous_components = GroupAction([
        # Fire detector node
        Node(
            package='all_nodes',
            executable='fire_detector',
            name='fire_detector',
            output='screen',
            parameters=[{
                'use_sim_time': use_sim_time,
                'temperature_threshold': 50.0,
                'confidence_threshold': 0.7,
                'window_size': 10,
                'thermocouple_topic': '/thermocouple/temperature',
                'thermocouple_message_type': 'float32',
                'temperature_offset': 0.0,
                'temperature_scale': 1.0
            }],
            condition=autonomous_condition
        ),
        
        # Mission controller node
        Node(
            package='all_nodes',
            executable='mission_controller',
            name='mission_controller',
            output='screen',
            parameters=[{
                'use_sim_time': use_sim_time,
                'exploration_radius': 3.0,
                'exploration_points': 8,
                'fire_approach_distance': 0.5,
                'return_timeout': 180.0
            }],
            condition=autonomous_condition
        )
    ], condition=autonomous_condition)
    
    # Map saving action
    save_map_action = ExecuteProcess(
        cmd=[
            'ros2', 'launch', 'all_nodes', 'save_map.launch.py', 
            'map_name:=', map_name
        ],
        name='map_saver',
        output='screen',
        condition=IfCondition(PythonExpression([save_map, ' and \'', mode, '\' == \'slam\'']))
    )
    
    # Assemble launch description
    ld = LaunchDescription()
    
    # Add launch arguments
    ld.add_action(DeclareLaunchArgument(
        'use_sim_time',
        default_value='false',
        description='Use simulation (Gazebo) clock if true'
    ))
    
    ld.add_action(DeclareLaunchArgument(
        'use_rviz',
        default_value='true',
        description='Start RViz if true'
    ))
    
    ld.add_action(DeclareLaunchArgument(
        'lidar_port',
        default_value='/dev/ttyUSB0',
        description='Serial port for the LIDAR'
    ))
    
    ld.add_action(DeclareLaunchArgument(
        'imu_port',
        default_value='/dev/ttyUSB1',
        description='Serial port for the IMU'
    ))
    
    ld.add_action(DeclareLaunchArgument(
        'esp32_port',
        default_value='/dev/ttyUSB2',
        description='Serial port for the ESP32'
    ))
    
    ld.add_action(DeclareLaunchArgument(
        'mode',
        default_value='slam',
        description='Operating mode: slam or nav'
    ))
    
    ld.add_action(DeclareLaunchArgument(
        'autonomous',
        default_value='false',
        description='Enable autonomous operation if true'
    ))
    
    ld.add_action(DeclareLaunchArgument(
        'map_dir',
        default_value=os.path.join(all_nodes_dir, 'maps'),
        description='Directory for map files'
    ))
    
    ld.add_action(DeclareLaunchArgument(
        'map_file',
        default_value=os.path.join(map_dir, 'map.yaml'),
        description='Full path to map yaml file to load'
    ))
    
    ld.add_action(DeclareLaunchArgument(
        'save_map',
        default_value='false',
        description='Save map on shutdown'
    ))
    
    ld.add_action(DeclareLaunchArgument(
        'map_name',
        default_value='my_map',
        description='Name for saved map'
    ))
    
    # Add all components
    for component in base_components:
        ld.add_action(component)
    
    ld.add_action(slam_components)
    ld.add_action(nav_components)
    ld.add_action(autonomous_components)
    ld.add_action(save_map_action)
    
    return ld

