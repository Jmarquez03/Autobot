import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node

def generate_launch_description():
    use_sim_time = LaunchConfiguration('use_sim_time', default='false')
    
    # Get the URDF file path
    urdf_file_name = 'robot.urdf.xml'
    urdf = os.path.join(
        get_package_share_directory('autobot_core'),
        'urdf',
        urdf_file_name)
    
    # Create a LaunchDescription with the necessary nodes
    return LaunchDescription([
        DeclareLaunchArgument(
            'use_sim_time',
            default_value='false',
            description='Use simulation (Gazebo) clock if true'),
            
        # Robot state publisher to publish the robot description
        Node(
            package='robot_state_publisher',
            executable='robot_state_publisher',
            name='robot_state_publisher',
            output='screen',
            parameters=[{'use_sim_time': use_sim_time}],
            arguments=[urdf]),
            
        # Custom joint state publisher that combines steering and wheel rotation
        Node(
            package='autobot_core',
            executable='joint_state_publisher',
            name='joint_state_publisher',
            output='screen'),
            
        # RViz2 for visualization
        Node(
            package='rviz2',
            executable='rviz2',
            name='rviz2',
            output='screen'),
    ])
