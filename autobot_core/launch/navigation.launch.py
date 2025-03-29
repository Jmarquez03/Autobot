import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, GroupAction
from launch.substitutions import LaunchConfiguration, PythonExpression
from launch.conditions import IfCondition
from launch_ros.actions import Node
from nav2_common.launch import RewrittenYaml

def generate_launch_description():
    # Get the package directory
    all_nodes_dir = get_package_share_directory('all_nodes')
    
    # Calculate workspace root (go up one level from all_nodes)
    workspace_root = os.path.dirname(os.path.dirname(all_nodes_dir))
    
    # Launch arguments
    use_sim_time = LaunchConfiguration('use_sim_time', default='false')
    map_dir = LaunchConfiguration('map_dir', default=os.path.join(all_nodes_dir, 'maps'))
    map_file = LaunchConfiguration('map_file', default=os.path.join(map_dir, 'map.yaml'))
    
    # Nav2 params file - directly point to the file in nav2 folder
    nav_params_file = os.path.join(workspace_root, 'nav2', 'nav2_params.yaml')
    
    # Fallback to robot_local_params if the nav2_params.yaml doesn't exist
    if not os.path.exists(nav_params_file):
        # Log a warning
        print("WARNING: Could not find nav2_params.yaml at", nav_params_file)
        print("Falling back to robot_local_params.yaml")
        nav_params_file = os.path.join(all_nodes_dir, 'config', 'robot_local_params.yaml')
    else:
        print("Using navigation parameters from:", nav_params_file)
    
    # Create parameter map for substitutions
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
    
    return LaunchDescription([
        # Launch arguments
        DeclareLaunchArgument(
            'use_sim_time',
            default_value='false',
            description='Use simulation (Gazebo) clock if true'
        ),
        
        DeclareLaunchArgument(
            'map_dir',
            default_value=os.path.join(all_nodes_dir, 'maps'),
            description='Directory for map files'
        ),
        
        DeclareLaunchArgument(
            'map_file',
            default_value=os.path.join(map_dir, 'map.yaml'),
            description='Full path to map yaml file to load'
        ),
        
        # Map server
        Node(
            package='nav2_map_server',
            executable='map_server',
            name='map_server',
            output='screen',
            parameters=[configured_params]
        ),
        
        # AMCL
        Node(
            package='nav2_amcl',
            executable='amcl',
            name='amcl',
            output='screen',
            parameters=[configured_params],
            remappings=[('scan', 'scan')]
        ),
        
        # Controller server
        Node(
            package='nav2_controller',
            executable='controller_server',
            name='controller_server',
            output='screen',
            parameters=[configured_params]
        ),
        
        # Planner server
        Node(
            package='nav2_planner',
            executable='planner_server',
            name='planner_server',
            output='screen',
            parameters=[configured_params]
        ),
        
        # Recoveries server
        Node(
            package='nav2_recoveries',
            executable='recoveries_server',
            name='recoveries_server',
            output='screen',
            parameters=[configured_params]
        ),
        
        # BT navigator
        Node(
            package='nav2_bt_navigator',
            executable='bt_navigator',
            name='bt_navigator',
            output='screen',
            parameters=[configured_params]
        ),
        
        # Waypoint follower
        Node(
            package='nav2_waypoint_follower',
            executable='waypoint_follower',
            name='waypoint_follower',
            output='screen',
            parameters=[configured_params]
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
                                      'waypoint_follower']}]
        )
    ]) 