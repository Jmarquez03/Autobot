import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, ExecuteProcess
from launch.substitutions import LaunchConfiguration

def generate_launch_description():
    # Get the package directory
    all_nodes_dir = get_package_share_directory('all_nodes')
    
    # Map parameters
    map_name = LaunchConfiguration('map_name', default='my_map')
    map_path = LaunchConfiguration('map_path', default=os.path.join(all_nodes_dir, 'maps'))
    
    return LaunchDescription([
        # Map name and path arguments
        DeclareLaunchArgument(
            'map_name',
            default_value='my_map',
            description='Name of the map file without extension'
        ),
        
        DeclareLaunchArgument(
            'map_path',
            default_value=os.path.join(all_nodes_dir, 'maps'),
            description='Path to save the map files'
        ),
        
        # Run map_saver to save the map
        ExecuteProcess(
            cmd=['bash', '-c', 'mkdir -p ' + LaunchConfiguration('map_path').perform(None)],
            output='screen'
        ),
        
        ExecuteProcess(
            cmd=[
                'ros2', 'run', 'nav2_map_server', 'map_saver_cli', 
                '-f', [LaunchConfiguration('map_path'), '/', LaunchConfiguration('map_name')]
            ],
            output='screen'
        )
    ]) 