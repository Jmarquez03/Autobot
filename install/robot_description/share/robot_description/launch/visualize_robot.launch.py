from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
import os
from ament_index_python.packages import get_package_share_directory

def generate_launch_description():
    # Get the package directory
    pkg_dir = get_package_share_directory('robot_description')
    
    # Path to the URDF file
    urdf_file = os.path.join(pkg_dir, 'urdf', 'robot.urdf')
    
    # Declare arguments
    use_sim_time = LaunchConfiguration('use_sim_time', default='false')
    
    # URDF publisher node
    urdf_publisher = Node(
        package='robot_description',
        executable='urdf_publisher',
        name='urdf_publisher_node',
        output='screen',
        parameters=[{
            'robot_description_file': 'robot.urdf',
            'publish_rate': 50.0,
            'use_sim_time': use_sim_time
        }]
    )
    
    # Robot state publisher node
    robot_state_publisher = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        name='robot_state_publisher',
        output='screen',
        parameters=[{
            'use_sim_time': use_sim_time
        }]
    )
    
    # Joint state publisher GUI (optional - for testing joint movements)
    joint_state_publisher_gui = Node(
        package='joint_state_publisher_gui',
        executable='joint_state_publisher_gui',
        name='joint_state_publisher_gui',
        output='screen',
    )
    
    # RViz2 node
    rviz_node = Node(
        package='rviz2',
        executable='rviz2',
        name='rviz2',
        output='screen',
        arguments=['-d', os.path.join(pkg_dir, 'config', 'robot.rviz')]
    )
    
    return LaunchDescription([
        DeclareLaunchArgument(
            'use_sim_time',
            default_value='false',
            description='Use simulation time if true'
        ),
        urdf_publisher,
        robot_state_publisher,
        joint_state_publisher_gui,
        rviz_node
    ])
