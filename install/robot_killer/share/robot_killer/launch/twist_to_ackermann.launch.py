import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    # Get the config directory
    robot_killer_dir = get_package_share_directory('robot_killer')
    params_file = os.path.join(robot_killer_dir, 'config', 'twist_to_ackermann_params.yaml')
    
    use_sim_time = LaunchConfiguration('use_sim_time', default='false')
    
    return LaunchDescription([
        DeclareLaunchArgument(
            'use_sim_time',
            default_value='false',
            description='Use simulation (Gazebo) clock if true'),
            
        # Twist to Ackermann converter node
        Node(
            package='twist_to_ackermann',
            executable='twist_to_ackermann_node',
            name='twist_to_ackermann',
            output='screen',
            parameters=[
                params_file,
                {'use_sim_time': use_sim_time}
            ],
        ),
    ]) 