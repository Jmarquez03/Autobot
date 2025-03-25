import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch.conditions import IfCondition, UnlessCondition


def generate_launch_description():
    # Get the config directory
    robot_killer_dir = get_package_share_directory('robot_killer')
    
    # Launch arguments
    use_sim_time = LaunchConfiguration('use_sim_time', default='false')
    slam_params_file = LaunchConfiguration(
        'slam_params_file',
        default=os.path.join(robot_killer_dir, 'config', 'slam_params.yaml')
    )
    
    # Device port arguments (can be overridden at runtime)
    lidar_port = LaunchConfiguration('lidar_port', default='/dev/ttyUSB0')
    imu_port = LaunchConfiguration('imu_port', default='/dev/ttyUSB1')
    controller_port = LaunchConfiguration('controller_port', default='/dev/ttyUSB2')
    
    # RViz configuration
    rviz_config_file = LaunchConfiguration(
        'rviz_config',
        default=os.path.join(robot_killer_dir, 'config', 'rviz_config.rviz')
    )
    use_rviz = LaunchConfiguration('use_rviz', default='true')
    
    # Mapping mode (mapping or localization)
    slam_mode = LaunchConfiguration('slam_mode', default='mapping')
    
    # Create directory for saved maps if it doesn't exist
    os.makedirs(os.path.join(robot_killer_dir, 'maps'), exist_ok=True)
    
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
        launch_arguments={
            'use_sim_time': use_sim_time,
            'port': lidar_port
        }.items(),
    )
    
    # Include the IMU launch file
    imu_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([os.path.join(
            robot_killer_dir, 'launch', 'bno055.launch.py')]),
        launch_arguments={
            'use_sim_time': use_sim_time,
            'serial_port': imu_port
        }.items(),
    )
    
    # Include the twist_to_ackermann launch file
    twist_to_ackermann_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([os.path.join(
            robot_killer_dir, 'launch', 'twist_to_ackermann.launch.py')]),
        launch_arguments={
            'use_sim_time': use_sim_time,
            'serial_port': controller_port
        }.items(),
    )
    
    return LaunchDescription([
        # Declare all the launch arguments
        DeclareLaunchArgument(
            'use_sim_time',
            default_value='false',
            description='Use simulation (Gazebo) clock if true'),
            
        DeclareLaunchArgument(
            'slam_params_file',
            default_value=os.path.join(robot_killer_dir, 'config', 'slam_params.yaml'),
            description='Full path to the ROS2 parameters file for SLAM'),
            
        DeclareLaunchArgument(
            'lidar_port',
            default_value='/dev/ttyUSB0',
            description='Serial port for LiDAR'),
            
        DeclareLaunchArgument(
            'imu_port',
            default_value='/dev/ttyUSB1',
            description='Serial port for IMU'),
            
        DeclareLaunchArgument(
            'controller_port',
            default_value='/dev/ttyUSB2',
            description='Serial port for controller'),
            
        DeclareLaunchArgument(
            'use_rviz',
            default_value='true',
            description='Whether to start RViz'),
            
        DeclareLaunchArgument(
            'rviz_config',
            default_value=os.path.join(robot_killer_dir, 'config', 'rviz_config.rviz'),
            description='Full path to the RViz config file'),
            
        DeclareLaunchArgument(
            'slam_mode',
            default_value='mapping',
            description='SLAM mode: mapping or localization'),
            
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
                {'use_sim_time': use_sim_time},
                {'slam_params_file': slam_params_file},
                {'slam_mode': slam_mode}
            ],
        ),
        
        # RViz
        Node(
            package='rviz2',
            executable='rviz2',
            name='rviz2',
            output='screen',
            arguments=['-d', rviz_config_file],
            parameters=[{'use_sim_time': use_sim_time}],
            condition=IfCondition(use_rviz),
        ),
    ]) 