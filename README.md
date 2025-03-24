# Robot Killer ROS2 Package

## Overview

The Robot Killer package is a comprehensive ROS2 solution that integrates various robotics components for autonomous navigation, mapping, and control. This package provides a unified system for:

- SLAM (Simultaneous Localization and Mapping)
- Autonomous Navigation
- Sensor Integration (LiDAR, IMU)
- Motion Control
- Visualization

## Project Structure

```
robot_killer/
├── config/                 # Configuration files
│   ├── nav2_params.yaml    # Navigation stack parameters
│   ├── rviz_config.rviz    # RViz configuration 
│   ├── slam_params.yaml    # SLAM parameters
│   └── twist_to_ackermann_params.yaml  # Motion conversion parameters
├── launch/                 # Launch files
│   ├── bno055.launch.py    # IMU sensor launch
│   ├── lidar.launch.py     # LiDAR sensor launch
│   ├── navigation.launch.py # Navigation stack launch
│   ├── robot_state_publisher.launch.py # Robot state publishing
│   ├── round1.launch.py    # Main launch file for Round 1
│   ├── rviz.launch.py      # Visualization launch
│   ├── slam.launch.py      # SLAM launch
│   └── twist_to_ackermann.launch.py # Motion converter launch
├── maps/                   # Map storage directory
├── robot_killer/           # Python package
│   ├── __init__.py
│   └── my_node.py          # Example ROS2 node
└── resource/               # Package resources
```

## Features

### 1. Integrated SLAM and Navigation

The package offers two primary operation modes:
- **SLAM Mode**: For building maps of unknown environments
- **Navigation Mode**: For autonomous navigation in mapped environments

### 2. Sensor Integration

- **LiDAR Integration**: Uses sllidar_ros2 package for obstacle detection and mapping
- **IMU Integration**: Uses bno055 package for orientation and motion sensing

### 3. Motion Control

- **Twist to Ackermann Conversion**: Converts standard ROS2 twist messages to Ackermann steering commands for wheeled robots

### 4. Visualization

- **RViz Integration**: Provides real-time visualization of robot state, sensor data, and navigation planning

## Usage

### Prerequisites

- ROS2 (tested with Humble)
- Required dependencies (listed in package.xml)

### Building the Package

```bash
cd ~/your_ros2_workspace/
colcon build --packages-select robot_killer
source install/setup.bash
```

### Running the Robot

For SLAM (mapping):
```bash
ros2 launch robot_killer round1.launch.py mode:=slam
```

For Navigation (using existing map):
```bash
ros2 launch robot_killer round1.launch.py mode:=nav map_file:=/path/to/your/map.yaml
```

## Configuration

### Customizing Navigation Parameters

Navigation parameters can be adjusted in `config/nav2_params.yaml` to optimize:
- Path planning
- Obstacle avoidance
- Localization accuracy

### Customizing SLAM Parameters

SLAM parameters in `config/slam_params.yaml` control:
- Map resolution
- Loop closure detection
- Scan matching algorithms

## Dependencies

This package relies on several ROS2 packages:
- slam_toolbox
- nav2_bringup and related packages
- sllidar_ros2
- bno055
- twist_to_ackermann
- rviz2
- robot_state_publisher

See package.xml for a complete list of dependencies.

## Development Status

This branch contains all the integrated components necessary for a fully functional autonomous robot system. The integration includes sensor drivers, navigation stack, and visualization tools, providing a complete solution for robotic applications.

## License

[License information TBD]

## Contact

Maintainer: zlove (zavala_esteban4455@yahoo.com) 