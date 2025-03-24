import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from nav2_common.launch import RewrittenYaml


def generate_launch_description():
    # Get the config directory
    robot_killer_dir = get_package_share_directory('robot_killer')
    nav2_params_file = os.path.join(robot_killer_dir, 'config', 'nav2_params.yaml')
    
    use_sim_time = LaunchConfiguration('use_sim_time', default='false')
    map_file = LaunchConfiguration('map_file')
    autostart = LaunchConfiguration('autostart', default='true')
    
    # Include the robot description launch file
    robot_state_publisher_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([os.path.join(
            robot_killer_dir, 'launch', 'robot_state_publisher.launch.py')]),
        launch_arguments={'use_sim_time': use_sim_time}.items(),
    )
    
    # Include the lidar launch file
    lidar_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([os.path.join(
            robot_killer_dir, 'launch', 'lidar.launch.py')]),
        launch_arguments={'use_sim_time': use_sim_time}.items(),
    )
    
    # Include the IMU launch file
    imu_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([os.path.join(
            robot_killer_dir, 'launch', 'bno055.launch.py')]),
        launch_arguments={'use_sim_time': use_sim_time}.items(),
    )
    
    # Include the twist_to_ackermann launch file
    twist_to_ackermann_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([os.path.join(
            robot_killer_dir, 'launch', 'twist_to_ackermann.launch.py')]),
        launch_arguments={'use_sim_time': use_sim_time}.items(),
    )
    
    # Create our own temporary YAML files that include substitutions
    param_substitutions = {
        'use_sim_time': use_sim_time,
        'yaml_filename': map_file
    }
    
    configured_params = RewrittenYaml(
        source_file=nav2_params_file,
        root_key='',
        param_rewrites=param_substitutions,
        convert_types=True)
    
    return LaunchDescription([
        DeclareLaunchArgument(
            'map_file',
            default_value=os.path.join(robot_killer_dir, 'maps', 'map.yaml'),
            description='Full path to map file to load'),
            
        DeclareLaunchArgument(
            'use_sim_time',
            default_value='false',
            description='Use simulation (Gazebo) clock if true'),
            
        DeclareLaunchArgument(
            'autostart',
            default_value='true',
            description='Automatically startup the nav2 stack'),
            
        # Include the robot description launch file
        robot_state_publisher_launch,
        
        # Include the lidar launch file
        lidar_launch,
        
        # Include the IMU launch file
        imu_launch,
        
        # Include the twist_to_ackermann launch file
        twist_to_ackermann_launch,
        
        # Map server
        Node(
            package='nav2_map_server',
            executable='map_server',
            name='map_server',
            output='screen',
            parameters=[configured_params]),
            
        # AMCL
        Node(
            package='nav2_amcl',
            executable='amcl',
            name='amcl',
            output='screen',
            parameters=[configured_params],
            remappings=[('scan', 'scan')]),
            
        # Controller server
        Node(
            package='nav2_controller',
            executable='controller_server',
            name='controller_server',
            output='screen',
            parameters=[configured_params]),
            
        # Planner server
        Node(
            package='nav2_planner',
            executable='planner_server',
            name='planner_server',
            output='screen',
            parameters=[configured_params]),
            
        # Recoveries server
        Node(
            package='nav2_recoveries',
            executable='recoveries_server',
            name='recoveries_server',
            output='screen',
            parameters=[configured_params]),
            
        # BT navigator
        Node(
            package='nav2_bt_navigator',
            executable='bt_navigator',
            name='bt_navigator',
            output='screen',
            parameters=[configured_params]),
            
        # Waypoint follower
        Node(
            package='nav2_waypoint_follower',
            executable='waypoint_follower',
            name='waypoint_follower',
            output='screen',
            parameters=[configured_params]),
            
        # Lifecycle manager
        Node(
            package='nav2_lifecycle_manager',
            executable='lifecycle_manager',
            name='lifecycle_manager_navigation',
            output='screen',
            parameters=[{'use_sim_time': use_sim_time},
                        {'autostart': autostart},
                        {'node_names': ['map_server',
                                        'amcl',
                                        'controller_server',
                                        'planner_server',
                                        'recoveries_server',
                                        'bt_navigator',
                                        'waypoint_follower']}])
    ]) 