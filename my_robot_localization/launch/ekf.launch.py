from launch import LaunchDescription
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory
import os

def generate_launch_description():
    pkg_dir = get_package_share_directory('my_robot_localization')
    ekf_config_path = os.path.join(pkg_dir, 'config', 'ekf_config.yaml')
    
    return LaunchDescription([
        Node(
            package='robot_localization',
            executable='ekf_node',
            name='ekf_filter_node',
            output='screen',
            parameters=[ekf_config_path],
            remappings=[
                ('odometry/filtered', 'odom/filtered')
            ]
        )
    ])
