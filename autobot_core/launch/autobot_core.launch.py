from launch import LaunchDescription
from launch_ros.actions import Node
from launch.actions import IncludeLaunchDescription, DeclareLaunchArgument, ExecuteProcess
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PythonExpression
from launch.conditions import IfCondition, UnlessCondition
from ament_index_python.packages import get_package_share_directory
import os

def generate_launch_description():
    # Launch arguments
    esp_port = LaunchConfiguration('esp_port', default='/dev/ttyUSB0')
    lidar_port = LaunchConfiguration('lidar_port', default='/dev/ttyUSB1')
    nano_port = LaunchConfiguration('nano_port', default='/dev/ttyUSB2')
    use_rviz = LaunchConfiguration('use_rviz', default='true')

    # Add launch arguments
    use_thermocouple = LaunchConfiguration('use_thermocouple', default='true')
    use_fire_detection = LaunchConfiguration('use_fire_detection', default='true')
    use_diagnostics = LaunchConfiguration('use_diagnostics', default='true')
    use_mission_controller = LaunchConfiguration('use_mission_controller', default='true')
    
    # NEW: Mode selection (slam or navigation)
    mode = LaunchConfiguration('mode', default='slam')
    slam_mode_condition = IfCondition(PythonExpression(['\'', mode, '\' == \'slam\'']))
    nav_mode_condition = IfCondition(PythonExpression(['\'', mode, '\' == \'nav\'']))
    
    # NEW: Autonomous mode
    autonomous = LaunchConfiguration('autonomous', default='false')
    autonomous_condition = IfCondition(autonomous)
    manual_condition = UnlessCondition(autonomous)
    
    # NEW: Map parameters
    map_dir = LaunchConfiguration('map_dir', default=os.path.join(get_package_share_directory('autobot_core'), 'maps'))
    map_file = LaunchConfiguration('map_file', default=os.path.join(map_dir, 'map.yaml'))
    save_map = LaunchConfiguration('save_map', default='false')
    map_name = LaunchConfiguration('map_name', default='my_map')

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
            'esp_port',
            default_value='/dev/ttyUSB0',
           description='Serial port for ESP32'
        ),
        DeclareLaunchArgument(
            'nano_port',
            default_value='/dev/ttyUSB2',
            description='Serial port for Ackermann controller'
        ),
        DeclareLaunchArgument(
            'use_rviz',
            default_value='true',
            description='Launch RViz if true'
        ),
        # Added
        DeclareLaunchArgument(
            'use_thermocouple',
            default_value='true',
            description='Enable thermocouple if true'
        ),
        DeclareLaunchArgument(
            'use_fire_detection',
            default_value='true',
            description='Enable fire detection if true'
        ),
        DeclareLaunchArgument(
            'use_diagnostics',
            default_value='true',
            description='Launch hardware diagnostics'
        ),
        DeclareLaunchArgument(
            'use_mission_controller',
            default_value='true',
            description='Launch mission controller'
        ),
        # NEW: Mode selection arguments
        DeclareLaunchArgument(
            'mode',
            default_value='slam',
            description='Operating mode: slam or nav'
        ),
        DeclareLaunchArgument(
            'autonomous',
            default_value='false',
            description='Enable autonomous operation if true'
        ),
        # NEW: Map arguments
        DeclareLaunchArgument(
            'map_dir',
            default_value=os.path.join(autobot_core_dir, 'maps'),
            description='Directory for map files'
        ),
        DeclareLaunchArgument(
            'map_file',
            default_value=os.path.join(map_dir, 'map.yaml'),
            description='Full path to map yaml file to load'
        ),
        DeclareLaunchArgument(
            'save_map',
            default_value='false',
            description='Save map on shutdown'
        ),
        DeclareLaunchArgument(
            'map_name',
            default_value='my_map',
            description='Name for saved map'
        ),
        # Remaining original arguments
        
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
            launch_arguments={'serial_port': esp_port}.items()
        ),

        # Ackermann converter node
        Node(
            package='autobot_core',
            executable='twist_to_ackermann_converter',
            output='screen',
            parameters=[{'serial_port': nano_port}]  # Added parameter for serial port
        ),

        # SLAM Toolbox launch - Only when in SLAM mode
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource([
                get_package_share_directory('slam_toolbox'),
                '/launch/online_async_launch.py'
            ]),
            launch_arguments={
                'params_file': os.path.join(autobot_core_dir, 'config', 'slam_toolbox_params.yaml'),
                'use_sim_time': 'false'
            }.items(),
            condition=slam_mode_condition
        ),

        # Nav2 launch with custom parameters
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource([
                get_package_share_directory('nav2_bringup'),
                '/launch/bringup_launch.py'
            ]),
            launch_arguments={
                'params_file': os.path.join(autobot_core_dir, 'config', 'nav2_params.yaml'),
                'use_sim_time': 'false',
                'map_subscribe_transient_local': 'true',
                'default_bt_xml_filename': 'nav2_bt_navigator/navigate_w_replanning_and_recovery.xml',
                'autostart': 'true',
                'map': map_file
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
        ),

        # Add thermocouple node
        Node(
            package='autobot_core',
            executable='thermocouple_node',
            parameters=[{'serial_port': '/dev/ttyUSB3'}],
            condition=IfCondition(use_thermocouple)
        ),

        # Add fire detector node - only active in autonomous mode
        Node(
            package='autobot_core',
            executable='fire_detector',
            parameters=[
                {'temperature_threshold': 100.0},
                {'confidence_threshold': 0.7},
                {'window_size': 10},
                {'thermocouple_topic': '/thermocouple/temperature'},
                {'thermocouple_message_type': 'float32'}
            ],
            condition=IfCondition(PythonExpression([use_fire_detection, ' and ', autonomous]))
        ),

        # Add hardware diagnostics node
        Node(
            package='autobot_core',
            executable='hardware_diagnostics',
            condition=IfCondition(use_diagnostics)
        ),

        # Add mission controller - only active in autonomous mode
        Node(
            package='autobot_core',
            executable='mission_controller',
            parameters=[
                {'exploration_radius': 3.0},
                {'use_frontier_exploration': True}
            ],
            condition=IfCondition(PythonExpression([use_mission_controller, ' and ', autonomous]))
        ),
        
        # NEW: Map saving action
        ExecuteProcess(
            cmd=[
                'ros2', 'launch', 'autobot_core', 'save_map.launch.py', 
                'map_name:=', map_name
            ],
            output='screen',
            condition=IfCondition(PythonExpression([save_map, ' and \'', mode, '\' == \'slam\'']))
        )
    ])

