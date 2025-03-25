import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, GroupAction
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PythonExpression
from launch.conditions import IfCondition, UnlessCondition
from launch_ros.actions import Node
from nav2_common.launch import RewrittenYaml


def generate_launch_description():
    # Get the package directory
    robot_killer_dir = get_package_share_directory('robot_killer')
    
    # Launch configurations
    use_sim_time = LaunchConfiguration('use_sim_time', default='false')
    map_dir = LaunchConfiguration('map_dir', default=os.path.join(robot_killer_dir, 'maps'))
    map_file = LaunchConfiguration('map_file', default=os.path.join(map_dir, 'map.yaml'))
    use_rviz = LaunchConfiguration('use_rviz', default='true')
    rviz_config_file = LaunchConfiguration('rviz_config_file', default=os.path.join(robot_killer_dir, 'config', 'rviz_config.rviz'))
    
    # Device configurations
    lidar_port = LaunchConfiguration('lidar_port', default='/dev/ttyUSB0')
    imu_port = LaunchConfiguration('imu_port', default='/dev/ttyUSB1')
    esp32_port = LaunchConfiguration('esp32_port', default='/dev/ttyUSB0')
    
    # Mode selection parameter (slam or navigation)
    mode = LaunchConfiguration('mode', default='slam')
    slam_mode_condition = IfCondition(PythonExpression(['\'', mode, '\' == \'slam\'']))
    nav_mode_condition = IfCondition(PythonExpression(['\'', mode, '\' == \'nav\'']))
    
    # Autonomous mode (true for fully autonomous operation)
    autonomous = LaunchConfiguration('autonomous', default='false')
    autonomous_condition = IfCondition(autonomous)
    
    # Include individual launch files
    robot_state_publisher_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([os.path.join(robot_killer_dir, 'launch', 'robot_state_publisher.launch.py')]),
        launch_arguments={'use_sim_time': use_sim_time}.items()
    )
    
    lidar_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([os.path.join(robot_killer_dir, 'launch', 'lidar.launch.py')]),
        launch_arguments={
            'use_sim_time': use_sim_time,
            'serial_port': lidar_port
        }.items()
    )
    
    imu_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([os.path.join(robot_killer_dir, 'launch', 'bno055.launch.py')]),
        launch_arguments={
            'use_sim_time': use_sim_time,
            'port': imu_port
        }.items()
    )
    
    esp32_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([os.path.join(robot_killer_dir, 'launch', 'esp32.launch.py')]),
        launch_arguments={
            'use_sim_time': use_sim_time,
            'serial_port': esp32_port
        }.items()
    )
    
    twist_to_ackermann_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([os.path.join(robot_killer_dir, 'launch', 'twist_to_ackermann.launch.py')]),
        launch_arguments={'use_sim_time': use_sim_time}.items()
    )
    
    slam_launch = GroupAction([
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource([os.path.join(robot_killer_dir, 'launch', 'slam.launch.py')]),
            launch_arguments={
                'use_sim_time': use_sim_time,
                'lidar_port': lidar_port,
                'imu_port': imu_port,
                'controller_port': esp32_port,
                'slam_mode': 'mapping',
                'use_rviz': use_rviz,
                'rviz_config': rviz_config_file
            }.items()
        )
    ], condition=slam_mode_condition)
    
    nav_params_file = os.path.join(robot_killer_dir, 'config', 'nav2_params.yaml')
    
    # Create our own temporary YAML files that include substitutions
    param_substitutions = {
        'use_sim_time': use_sim_time,
        'yaml_filename': map_file
    }
    
    configured_params = RewrittenYaml(
        source_file=nav_params_file,
        root_key='',
        param_rewrites=param_substitutions,
        convert_types=True
    )
    
    navigation_launch = GroupAction([
        # Map server
        Node(
            package='nav2_map_server',
            executable='map_server',
            name='map_server',
            output='screen',
            parameters=[configured_params],
            condition=nav_mode_condition
        ),
            
        # AMCL
        Node(
            package='nav2_amcl',
            executable='amcl',
            name='amcl',
            output='screen',
            parameters=[configured_params],
            remappings=[('scan', 'scan')],
            condition=nav_mode_condition
        ),
            
        # Controller server
        Node(
            package='nav2_controller',
            executable='controller_server',
            name='controller_server',
            output='screen',
            parameters=[configured_params],
            condition=nav_mode_condition
        ),
            
        # Planner server
        Node(
            package='nav2_planner',
            executable='planner_server',
            name='planner_server',
            output='screen',
            parameters=[configured_params],
            condition=nav_mode_condition
        ),
            
        # Recoveries server
        Node(
            package='nav2_recoveries',
            executable='recoveries_server',
            name='recoveries_server',
            output='screen',
            parameters=[configured_params],
            condition=nav_mode_condition
        ),
            
        # BT navigator
        Node(
            package='nav2_bt_navigator',
            executable='bt_navigator',
            name='bt_navigator',
            output='screen',
            parameters=[configured_params],
            condition=nav_mode_condition
        ),
            
        # Waypoint follower
        Node(
            package='nav2_waypoint_follower',
            executable='waypoint_follower',
            name='waypoint_follower',
            output='screen',
            parameters=[configured_params],
            condition=nav_mode_condition
        ),
            
        # Lifecycle manager
        Node(
            package='nav2_lifecycle_manager',
            executable='lifecycle_manager',
            name='lifecycle_manager_navigation',
            output='screen',
            parameters=[{'use_sim_time': use_sim_time},
                        {'autostart': True},
                        {'node_names': ['map_server',
                                        'amcl',
                                        'controller_server',
                                        'planner_server',
                                        'recoveries_server',
                                        'bt_navigator',
                                        'waypoint_follower']}],
            condition=nav_mode_condition
        )
    ])
    
    # NEW: Add autonomous nodes
    autonomous_nodes = GroupAction([
        # Fire detector node
        Node(
            package='robot_killer',
            executable='fire_detector_node',
            name='fire_detector',
            output='screen',
            parameters=[{
                'use_sim_time': use_sim_time,
                'temperature_threshold': 50.0,
                'confidence_threshold': 0.7,
                'window_size': 10
            }],
            condition=autonomous_condition
        ),
        
        # Hose controller node
        # Node(
        #     package='robot_killer',
        #     executable='hose_controller',
        #     name='hose_controller',
        #     output='screen',
        #     parameters=[{'use_sim_time': use_sim_time}],
        #     condition=autonomous_condition
        # ),
        
        # Mission controller node
        Node(
            package='robot_killer',
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
    ])
    
    rviz_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([os.path.join(robot_killer_dir, 'launch', 'rviz.launch.py')]),
        launch_arguments={
            'use_sim_time': use_sim_time,
            'rviz_config': rviz_config_file
        }.items(),
        condition=IfCondition(use_rviz)
    )
    
    return LaunchDescription([
        # Launch arguments
        DeclareLaunchArgument(
            'use_sim_time',
            default_value='false',
            description='Use simulation (Gazebo) clock if true'
        ),
        
        DeclareLaunchArgument(
            'map_dir',
            default_value=os.path.join(robot_killer_dir, 'maps'),
            description='Directory for map files'
        ),
        
        DeclareLaunchArgument(
            'map_file',
            default_value=os.path.join(map_dir, 'map.yaml'),
            description='Full path to map yaml file to load'
        ),
        
        DeclareLaunchArgument(
            'use_rviz',
            default_value='true',
            description='Whether to launch RViz'
        ),
        
        DeclareLaunchArgument(
            'rviz_config_file',
            default_value=os.path.join(robot_killer_dir, 'config', 'rviz_config.rviz'),
            description='Full path to RViz config file'
        ),
        
        DeclareLaunchArgument(
            'mode',
            default_value='slam',
            description='Operating mode: slam or nav'
        ),
        
        # NEW: Add autonomous mode parameter
        DeclareLaunchArgument(
            'autonomous',
            default_value='false',
            description='Enable autonomous operation if true'
        ),
        
        # Device port arguments
        DeclareLaunchArgument(
            'lidar_port',
            default_value='/dev/ttyUSB0',
            description='Serial port for the LIDAR'
        ),
        
        DeclareLaunchArgument(
            'imu_port',
            default_value='/dev/ttyUSB1',
            description='Serial port for the BNO055 IMU'
        ),
        
        DeclareLaunchArgument(
            'esp32_port',
            default_value='/dev/ttyUSB0',
            description='Serial port for the ESP32 controller'
        ),
        
        # Common components
        robot_state_publisher_launch,
        lidar_launch,
        imu_launch,
        esp32_launch,
        twist_to_ackermann_launch,
        
        # Mode-dependent components
        slam_launch,
        navigation_launch,
        
        # Autonomous components
        autonomous_nodes,
        
        # Visualization
        rviz_launch
    ]) 