import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    # Get the config directory
    robot_killer_dir = get_package_share_directory('robot_killer')
    slam_params_file = os.path.join(robot_killer_dir, 'config', 'slam_params.yaml')
    
    use_sim_time = LaunchConfiguration('use_sim_time', default='false')
    
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
    
    return LaunchDescription([
        DeclareLaunchArgument(
            'use_sim_time',
            default_value='false',
            description='Use simulation (Gazebo) clock if true'),
            
        # Include the robot description launch file
        robot_state_publisher_launch,
        
        # Include the lidar launch file
        lidar_launch,
        
        # Include the IMU launch file
        imu_launch,
        
        # Include the twist_to_ackermann launch file
        twist_to_ackermann_launch,
        
        # SLAM Toolbox node
        Node(
            package='slam_toolbox',
            executable='async_slam_toolbox_node',
            name='slam_toolbox',
            output='screen',
            parameters=[
                slam_params_file,
                {'use_sim_time': use_sim_time}
            ],
        ),
    ]) 