# Autonomous Fire Detection Robot - Competition System

## Overview

This repository contains the code for an autonomous robot designed to compete in fire detection challenges. The system implements a complete autonomous navigation, exploration, fire detection, and mapping solution using ROS2.

## Key Capabilities

- Autonomous exploration using frontier-based detection
- Fire detection using thermocouple sensor
- Marking and saving fire locations for multi-round competitions
- Complete mapping and navigation stack
- Learning across competition rounds

## System Architecture

The `all_nodes` package serves as the central integration point for all robot functionality:

### Hardware Integration
- **LiDAR** (RPLIDAR): Provides laser scan data for mapping and obstacle detection
- **IMU** (BNO055): Provides orientation data for accurate positioning
- **ESP32**: Controls motors and provides odometry data
- **Thermocouple**: Detects temperature for fire identification

### Software Components
- **Navigation System**: Based on Nav2 stack
- **Mapping**: SLAM Toolbox for building maps
- **Exploration**: Wavefront Frontier Detection for efficient exploration
- **Mission Control**: State machine managing the robot's behavior

## Core Components Explained

### Mission Controller

The heart of the system is the `mission_controller.py` file, which implements a state machine with these states:

1. **INIT**: Initializes the mission and generates exploration waypoints
2. **EXPLORING**: Autonomously explores the environment using frontier detection
3. **APPROACHING_FIRE**: Navigates to detected fire location
4. **AT_FIRE**: Marks and saves the fire location
5. **RETURNING**: Returns to starting position
6. **COMPLETED**: Completes the mission and records statistics
7. **IDLE**: Waits for new commands

### Frontier Exploration

Instead of using predefined waypoints, the robot identifies "frontiers" - boundaries between known and unknown space. This results in more efficient exploration as the robot always moves toward unexplored areas.

### Fire Detection and Recording

When a fire is detected:
1. The robot navigates to the fire location
2. Creates a visual marker (cylinder) at the fire's position
3. Saves the coordinates to YAML files for future reference
4. Returns to the starting position

### Multi-Round Learning

A key competitive advantage: the robot remembers fire locations from previous rounds, prioritizing these locations in subsequent competition runs.

## Competition Workflow

### Mapping Phase (Before Competition)
1. Create a detailed map of the environment
2. Save the map for navigation

### Competition Round
1. Load the pre-built map
2. Robot autonomously explores using frontier detection
3. When a fire is detected, robot approaches, marks and saves the location
4. Robot returns to starting point

### Subsequent Rounds
1. Robot loads previous fire locations
2. Checks these locations first before continuing exploration
3. Updates its knowledge with any new fire detections

## Setup Instructions for Raspberry Pi 5

### 1. Basic Setup

```bash
# Update the system first
sudo apt update
sudo apt upgrade -y

# Install required dependencies
sudo apt install -y python3-pip python3-yaml
pip3 install transforms3d
```

### 2. ROS2 Environment Setup

```bash
# Source ROS2 environment (assuming ROS2 Humble is installed)
source /opt/ros/jazzy/setup.bash

# Navigate to your workspace
cd ~/Desktop/robot/Autobot-esp-branch

# Build the workspace
colcon build --symlink-install
```

### 3. Hardware Connection

Ensure all devices are properly connected:

```bash
# Check connected USB devices
ls -l /dev/ttyUSB*

# Make USB ports accessible (if needed)
sudo chmod 666 /dev/ttyUSB0  # For LiDAR
sudo chmod 666 /dev/ttyUSB1  # For IMU
sudo chmod 666 /dev/ttyUSB2  # For ESP32
sudo chmod 666 /dev/ttyUSB3  # For Thermocouple
```

## Running the Robot

### Step 1: Mapping (Before Competition)

```bash
# Source your workspace
source ~/Desktop/robot/Autobot-esp-branch/install/setup.bash

# Start the robot in SLAM mode
ros2 launch all_nodes all_nodes.launch.py mode:=slam use_rviz:=true lidar_port:=/dev/ttyUSB0 imu_port:=/dev/ttyUSB1 esp32_port:=/dev/ttyUSB2 arduino_port:=/dev/ttyUSB3

# In a new terminal, send movement commands to map the area
source ~/Desktop/robot/Autobot-esp-branch/install/setup.bash
ros2 run teleop_twist_keyboard teleop_twist_keyboard

# Once mapping is complete, save the map
ros2 launch all_nodes all_nodes.launch.py mode:=slam save_map:=true map_name:=competition_map use_rviz:=true
```

### Step 2: Competition Run

```bash
# Source your workspace
source ~/Desktop/robot/Autobot-esp-branch/install/setup.bash

# Start navigation with the saved map and autonomous mode enabled
ros2 launch all_nodes all_nodes.launch.py mode:=nav autonomous:=true map_file:=/Users/estebanzavala/Desktop/robot/Autobot-esp-branch/all_nodes/maps/competition_map.yaml lidar_port:=/dev/ttyUSB0 imu_port:=/dev/ttyUSB1 esp32_port:=/dev/ttyUSB2 arduino_port:=/dev/ttyUSB3

# In a new terminal, monitor mission status
source ~/Desktop/robot/Autobot-esp-branch/install/setup.bash
ros2 topic echo /mission_status
```

### Step 3: View Results

```bash
# Check the saved fire location file
cat ~/Desktop/robot/Autobot-esp-branch/all_nodes/maps/latest_fire_location.yaml
```

## Important Launch Parameters

| Parameter | Description | Default |
|-----------|-------------|---------|
| `mode` | Operating mode: `slam` or `nav` | `slam` |
| `autonomous` | Enable autonomous operation | `false` |
| `use_rviz` | Start RViz visualization | `true` |
| `map_file` | Path to map file for navigation | `[package_dir]/maps/map.yaml` |
| `save_map` | Save map on shutdown | `false` |
| `map_name` | Name for saved map | `my_map` |
| `lidar_port` | Serial port for LIDAR | `/dev/ttyUSB0` |
| `imu_port` | Serial port for IMU | `/dev/ttyUSB1` |
| `esp32_port` | Serial port for ESP32 | `/dev/ttyUSB2` |
| `arduino_port` | Serial port for Thermocouple | `/dev/ttyUSB3` |

## Mission Controller Parameters (Tunable)

| Parameter | Description | Default |
|-----------|-------------|---------|
| `exploration_radius` | Radius for circular exploration pattern (meters) | `3.0` |
| `exploration_points` | Number of waypoints in exploration pattern | `8` |
| `fire_approach_distance` | How close to approach detected fires (meters) | `0.5` |
| `return_timeout` | Max time before returning to start (seconds) | `180.0` |
| `use_frontier_exploration` | Use frontier exploration instead of fixed pattern | `true` |

## Troubleshooting

### Common Issues

1. **Robot not moving:**
   - Check ESP32 connection
   - Verify motor power
   - Ensure the navigation server is running

2. **Poor localization:**
   - Improve map quality through slower mapping
   - Check IMU connection
   - Verify LiDAR data quality

3. **Fire detection not working:**
   - Check thermocouple connection
   - Verify that the temperature threshold is appropriate
   - Check topics with `ros2 topic echo /fire_detection`

4. **USB port issues:**
   - Ports might change between reboots; verify with `ls -l /dev/ttyUSB*`
   - If access issues: `sudo chmod 666 /dev/ttyUSB*`

### Emergency Recovery

If the robot gets stuck during a competition run:

```bash
# Stop the current process
Ctrl+C

# Restart with the same parameters
ros2 launch all_nodes all_nodes.launch.py mode:=nav autonomous:=true map_file:=/Users/estebanzavala/Desktop/robot/Autobot-esp-branch/all_nodes/maps/competition_map.yaml
```

## Team Roles During Competition

### Recommended Division of Responsibilities

1. **Hardware Specialist:**
   - Manages power and connections
   - Monitors hardware status
   - Handles physical robot positioning

2. **Navigation Specialist:**
   - Runs mapping process
   - Ensures map quality
   - Monitors localization in RViz

3. **Mission Specialist:**
   - Launches autonomous mission
   - Monitors mission status
   - Records and verifies fire detections

## Visualization

The system provides rich visualization in RViz:

- Robot model and sensor data
- Map and costmaps
- Planned and executed paths
- Frontier markers (blue spheres)
- Fire markers (red cylinders)
- Previous fire markers (blue cylinders)

To customize the RViz display, save your configuration file to `all_nodes/config/competition.rviz` and load it in subsequent runs.

## Data Management

Fire location data is stored in:
- Timestamped files: `fire_location_[TIMESTAMP].yaml`
- Latest detection: `latest_fire_location.yaml`

These files contain the X/Y coordinates of detected fires and can be used to analyze performance or prepare for subsequent competition rounds.

## Advanced Usage

### Custom Exploration Parameters

You can tune exploration parameters at launch time:

```bash
ros2 launch all_nodes all_nodes.launch.py mode:=nav autonomous:=true exploration_radius:=5.0 exploration_points:=12
```

### Disabling Frontier Exploration

If you prefer a simple circular pattern instead:

```bash
ros2 launch all_nodes all_nodes.launch.py mode:=nav autonomous:=true use_frontier_exploration:=false
```

## Credits

This project integrates several open-source components:
- Navigation2 (Nav2) stack
- SLAM Toolbox
- Robot Localization package
- Various sensor drivers 