import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, ExecuteProcess
from launch.substitutions import LaunchConfiguration, PythonExpression
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.conditions import IfCondition


def generate_launch_description():
    # Get the package directory
    robot_killer_dir = get_package_share_directory('robot_killer')
    
    # Launch configurations
    use_sim_time = LaunchConfiguration('use_sim_time', default='false')
    mode = LaunchConfiguration('mode', default='slam')
    autonomous = LaunchConfiguration('autonomous', default='false')
    use_rviz = LaunchConfiguration('use_rviz', default='true')
    
    # Device configurations
    lidar_port = LaunchConfiguration('lidar_port', default='/dev/ttyUSB0')
    imu_port = LaunchConfiguration('imu_port', default='/dev/ttyUSB1')
    esp32_port = LaunchConfiguration('esp32_port', default='/dev/ttyUSB2')
    
    # Map saving (new)
    save_map = LaunchConfiguration('save_map', default='false')
    map_name = LaunchConfiguration('map_name', default='my_map')
    
    # Include the main round1 launch file which includes all components
    round1_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([os.path.join(robot_killer_dir, 'launch', 'round1.launch.py')]),
        launch_arguments={
            'use_sim_time': use_sim_time,
            'mode': mode,
            'autonomous': autonomous,
            'use_rviz': use_rviz,
            'lidar_port': lidar_port,
            'imu_port': imu_port,
            'esp32_port': esp32_port
        }.items()
    )
    
    # Map saving action - only triggered if save_map is true
    save_map_action = ExecuteProcess(
        cmd=[
            'ros2', 'launch', 'robot_killer', 'save_map.launch.py', 
            'map_name:=', map_name
        ],
        name='map_saver',
        output='screen',
        condition=IfCondition(save_map)
    )
    
    return LaunchDescription([
        # Launch arguments
        DeclareLaunchArgument(
            'use_sim_time',
            default_value='false',
            description='Use simulation (Gazebo) clock if true'
        ),
        
        DeclareLaunchArgument(
            'mode',
            default_value='slam',
            description='Operating mode: slam or nav'
        ),
        
        DeclareLaunchArgument(
            'autonomous',
            default_value='false',
            description='Enable autonomous operation if true'
        ),
        
        DeclareLaunchArgument(
            'use_rviz',
            default_value='true',
            description='Whether to launch RViz'
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
            default_value='/dev/ttyUSB2',
            description='Serial port for the ESP32 controller'
        ),
        
        # Map saving arguments (new)
        DeclareLaunchArgument(
            'save_map',
            default_value='false',
            description='Whether to save the map when shutting down (only works in slam mode)'
        ),
        
        DeclareLaunchArgument(
            'map_name',
            default_value='my_map',
            description='Name of the map to save'
        ),
        
        # Main launch file that includes all components
        round1_launch,
        
        # Save map action
        save_map_action
    ]) 