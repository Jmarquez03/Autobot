
# Autobot

A ROS 2-based robot control system for autonomous navigation and control.

## Overview

Autobot is a comprehensive robotics platform that integrates various sensors and control systems for autonomous navigation. The system includes odometry from an ESP32 microcontroller, LIDAR-based mapping and localization, and Ackermann steering control.

## Features

- Odometry data processing from ESP32
- LIDAR integration with SLAM for mapping
- Robot state visualization
- Twist to Ackermann command conversion
- Navigation and path planning with Nav2
- Interactive command interface

## Package Structure

- **autobot_core**: Main package containing launch files and nodes
  - ESP32 interface for odometry
  - Twist to Ackermann conversion
  - Robot visualization
  
- **External Dependencies**:
  - sllidar_ros2: LIDAR driver
  - bno055: IMU driver
  - nav2: Navigation stack
  - nav2_wavefront_frontier_exploration: Exploration capabilities

## Hardware Requirements

- ESP32 microcontroller (connected to /dev/ttyUSB0 by default)
- SLAMTEC RPLIDAR (connected to /dev/ttyUSB1 by default)
- Ackermann steering controller (connected to /dev/ttyUSB2 by default)
- BNO055 IMU (optional)

## Installation

1. Clone this repository into your ROS 2 workspace:
   
   ```bash
   cd ~/ros2_ws/src
   git clone https://github.com/yourusername/Autobot.git
   ```

2. Install dependencies:
   
   ```bash
   sudo apt install ros-humble-navigation2 ros-humble-nav2-bringup
   sudo apt install ros-humble-slam-toolbox
   sudo apt install ros-humble-robot-localization
   sudo apt install ros-humble-joint-state-publisher-gui
   ```

3. Build the workspace:
   
   ```bash
   cd ~/ros2_ws
   colcon build --symlink-install
   ```

4. Source the workspace:
   
   ```bash
   source ros2_ws/install/setup.bash
   ```

## Manual Launch

```bash
ros2 launch autobot_core autobot_launch.py
```

### Launch Individual Components

```bash
# Robot visualization
ros2 launch autobot_core robot_visualization.launch.py

# ESP32 odometry
ros2 launch autobot_core esp32_interface.launch.py serial_port:=/dev/ttyUSB0

# LIDAR
ros2 launch sllidar_ros2 sllidar_a1_launch.py serial_port:=/dev/ttyUSB1

# Twist to Ackermann converter
ros2 run autobot_core twist_to_ackermann_converter --ros-args -p serial_port:=/dev/ttyUSB2 -p baud_rate:=115200
```

### Configuration

```bash
ros2 launch autobot_core autobot_core.launch.py esp32_port:=/dev/ttyUSB0 lidar_port:=/dev/ttyUSB1 ackermann_port:=/dev/ttyUSB2
```

## Node Details

### Twist to Ackermann Converter
This node converts standard ROS 2 Twist messages to Ackermann drive commands for steering control:

- **Subscribes to**: `/cmd_vel` (geometry_msgs/Twist)
- **Publishes to**: `/ackermann_cmd` (ackermann_msgs/AckermannDriveStamped)
- **Parameters**:
  - `serial_port`: Serial port for the Ackermann controller (default: `/dev/ttyUSB2`)
  - `baud_rate`: Baud rate for serial communication (default: `115200`)
  - `visualize`: Enable visualization markers (default: `true`)

### ESP32 Odometry Node
This node processes odometry data from an ESP32 microcontroller:

- **Publishes to**: `/odom` (nav_msgs/Odometry)
- **Parameters**:
  - `serial_port`: Serial port for the ESP32 (default: `/dev/ttyUSB0`)
  - `baud_rate`: Baud rate for serial communication (default: `115200`)
  - `odom_frame`: Odometry frame ID (default: `odom`)
  - `base_frame`: Base frame ID (default: `base_footprint`)

## Development

To contribute to this project:

1. Create a new branch:
   
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. Make your changes and commit them:
   
   ```bash
   git add .
   git commit -m "Description of changes"
   ```

3. Push your branch and create a pull request:
   
   ```bash
   git push -u origin feature/your-feature-name
   ```

## Troubleshooting

### Serial Port Issues
If you encounter serial port permission issues:

```bash
sudo chmod 777 /dev/ttyUSB0
sudo chmod 777 /dev/ttyUSB1
sudo chmod 777 /dev/ttyUSB2
```

### Node Communication
To check if nodes are communicating properly:

```bash
ros2 topic list
ros2 topic echo /odom
ros2 topic echo /cmd_vel
ros2 topic echo /ackermann_cmd
```

