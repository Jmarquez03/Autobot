import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    # Get the config directory
    robot_killer_dir = get_package_share_directory('robot_killer')
    
    use_sim_time = LaunchConfiguration('use_sim_time', default='false')
    rviz_config_file = LaunchConfiguration('rviz_config')
    
    return LaunchDescription([
        DeclareLaunchArgument(
            'use_sim_time',
            default_value='false',
            description='Use simulation (Gazebo) clock if true'),
            
        DeclareLaunchArgument(
            'rviz_config',
            default_value=os.path.join(robot_killer_dir, 'config', 'rviz_config.rviz'),
            description='Full path to the RViz config file to use'),
            
        # RViz2
        Node(
            package='rviz2',
            executable='rviz2',
            name='rviz2',
            output='screen',
            parameters=[{'use_sim_time': use_sim_time}],
            arguments=['-d', rviz_config_file],
        ),
    ]) 