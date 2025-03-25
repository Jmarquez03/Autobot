# Robot Killer ROS2 Package

## Overview

The Robot Killer package is a comprehensive ROS2 solution that integrates various robotics components for autonomous navigation, mapping, and control. This package provides a unified system for:

- SLAM (Simultaneous Localization and Mapping)
- Autonomous Navigation
- Sensor Integration (LiDAR, IMU, ESP32)
- Motion Control
- Fire Detection and Response
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
│   ├── esp32.launch.py     # ESP32 interface launch
│   ├── lidar.launch.py     # LiDAR sensor launch
│   ├── main.launch.py      # Top-level launch entry point
│   ├── navigation.launch.py # Navigation stack launch
│   ├── robot_hardware.launch.py # Combined hardware launch
│   ├── robot_state_publisher.launch.py # Robot state publishing
│   ├── round1.launch.py    # Comprehensive system launch
│   ├── rviz.launch.py      # Visualization launch
│   ├── slam.launch.py      # SLAM launch
│   └── twist_to_ackermann.launch.py # Motion converter launch
├── maps/                   # Map storage directory
├── robot_killer/           # Python package
│   ├── __init__.py
│   ├── mission_controller.py  # Mission control logic
│   ├── fire_deector_node.py   # Fire detection node
│   ├── temerature_simulator.py # Temperature simulation
│   └── my_node.py          # Example ROS2 node
└── resource/               # Package resources
```

## Hardware Components

This package integrates three key hardware components:

1. **ESP32 Microcontroller**
   - Provides motor control and odometry
   - Communicates over serial port (default: /dev/ttyUSB0)
   - Handles low-level motor control based on ROS commands

2. **BNO055 IMU Sensor**
   - Provides orientation and motion data
   - Attached via serial port (default: /dev/ttyUSB1)
   - Essential for accurate robot orientation

3. **SLLIDAR Laser Scanner**
   - Provides 360° distance measurements
   - Used for obstacle detection and mapping
   - Communicates over serial port (default: /dev/ttyUSB0)

## Launch System Architecture

Our launch system follows a hierarchical structure to organize the various components. Understanding this architecture is **crucial** for effectively working with and extending the system.

### Launch Files Hierarchy

```
main.launch.py
    └── round1.launch.py
        ├── robot_state_publisher.launch.py
        ├── lidar.launch.py
        ├── bno055.launch.py
        ├── esp32.launch.py
        ├── twist_to_ackermann.launch.py
        ├── slam.launch.py (conditional: mode=slam)
        ├── navigation.launch.py (conditional: mode=nav)
        ├── autonomous nodes (conditional: autonomous=true)
        └── rviz.launch.py (conditional: use_rviz=true)
```

### Main Entry Points

1. **main.launch.py**
   - The top-level entry point for running the entire system
   - Provides a simplified interface for common parameters
   - Delegates to round1.launch.py with configured parameters
   - **USE THIS FOR NORMAL OPERATION**

2. **round1.launch.py**
   - The comprehensive "all-in-one" launch file
   - Coordinates ALL components of the robot system
   - Provides fine-grained control over components
   - Includes conditional launching based on mode and flags
   - **USE THIS FOR CUSTOM CONFIGURATIONS**

3. **robot_hardware.launch.py**
   - Launches only the hardware components (LiDAR, IMU, ESP32)
   - Useful for hardware testing without navigation/SLAM
   - **USE THIS FOR HARDWARE TESTING**

### Component-Specific Launch Files

These files handle individual robot components and are included by the higher-level launch files:

4. **robot_state_publisher.launch.py**
   - Publishes the robot's URDF model and joint states
   - Essential for transforms between different robot parts

5. **lidar.launch.py**
   - Launches the SLLIDAR driver
   - Sets up the transformation between lidar frame and robot base
   - Configures the serial port and parameters for the LiDAR

6. **bno055.launch.py**
   - Launches the BNO055 IMU sensor driver
   - Configures IMU parameters and transforms
   - Publishes sensor data on IMU topics

7. **esp32.launch.py**
   - Launches the ESP32 interface node
   - Handles serial communication with ESP32 microcontroller
   - Sets up odometry and motor control

8. **twist_to_ackermann.launch.py**
   - Launches the motion converter for differential/ackermann steering
   - Adapts standard ROS2 velocity commands to the robot's steering mechanism

9. **slam.launch.py**
   - Launches SLAM Toolbox for simultaneous localization and mapping
   - Used in SLAM mode to create maps of the environment

10. **navigation.launch.py**
    - Launches the complete Nav2 navigation stack
    - Includes planner, controller, recovery behaviors, etc.
    - Used in navigation mode to autonomously navigate using existing maps

11. **rviz.launch.py**
    - Launches RViz visualization with custom configuration
    - Provides real-time visualization of robot state and sensor data

## Launch Modes and Parameters

### Core Parameters

- **mode**: `slam` (mapping) or `nav` (navigation using existing map)
- **autonomous**: `false` (manual control) or `true` (autonomous operation)
- **use_rviz**: `true` (show visualization) or `false` (headless operation)
- **use_sim_time**: `false` (real hardware) or `true` (simulation)

### Running the Robot

#### Standard Operation

For typical use with all components, use the main launch file:

```bash
# Default: SLAM mode, manual control, with visualization
ros2 launch robot_killer main.launch.py

# Navigation mode with autonomous operation
ros2 launch robot_killer main.launch.py mode:=nav autonomous:=true

# SLAM without visualization (headless)
ros2 launch robot_killer main.launch.py use_rviz:=false
```

#### Advanced Configuration

For more detailed configuration, use round1.launch.py directly:

```bash
# Navigation with custom map file
ros2 launch robot_killer round1.launch.py mode:=nav map_file:=/path/to/map.yaml

# Full autonomous mission with specific parameters
ros2 launch robot_killer round1.launch.py mode:=nav autonomous:=true
```

#### Testing Individual Components

```bash
# Test just the hardware components
ros2 launch robot_killer robot_hardware.launch.py

# Test individual sensors
ros2 launch robot_killer lidar.launch.py
ros2 launch robot_killer bno055.launch.py
ros2 launch robot_killer esp32.launch.py
```

## Hardware Setup and Configuration

### Serial Port Configuration

**IMPORTANT**: Pay attention to serial port assignments. By default:

- LiDAR: `/dev/ttyUSB0`
- BNO055 IMU: `/dev/ttyUSB1` 
- ESP32: `/dev/ttyUSB0`

Note that both the LiDAR and ESP32 default to the same port (`/dev/ttyUSB0`), which will cause conflicts.

#### Resolving Port Conflicts

You have several options to handle this:

1. **Using command-line overrides**:
```bash
# Launch everything with specific port assignments
ros2 launch robot_killer main.launch.py lidar_port:=/dev/ttyUSB0 imu_port:=/dev/ttyUSB1 esp32_port:=/dev/ttyUSB2
```

2. **Testing individual components**:
```bash
# Launch individual components with specific ports
ros2 launch robot_killer lidar.launch.py serial_port:=/dev/ttyUSB0
ros2 launch robot_killer bno055.launch.py port:=/dev/ttyUSB1
ros2 launch robot_killer esp32.launch.py serial_port:=/dev/ttyUSB2
```

3. **Using udev rules**: For a permanent solution, you can create udev rules to assign consistent device names based on device attributes. For example:
```bash
# Create udev rules (advanced)
sudo nano /etc/udev/rules.d/99-usb-serial.rules

# Add rules like:
SUBSYSTEM=="tty", ATTRS{idVendor}=="1a86", ATTRS{idProduct}=="7523", SYMLINK+="lidar"
SUBSYSTEM=="tty", ATTRS{idVendor}=="10c4", ATTRS{idProduct}=="ea60", SYMLINK+="imu"
SUBSYSTEM=="tty", ATTRS{idVendor}=="10c4", ATTRS{idProduct}=="ea60", ATTRS{serial}=="01234567", SYMLINK+="esp32"

# Then reload rules:
sudo udevadm control --reload-rules
sudo udevadm trigger
```

#### Identifying Your Devices

To identify which device is connected to which port:
```bash
# List USB devices with details
ls -l /dev/ttyUSB*

# Get detailed USB information
udevadm info -a -n /dev/ttyUSB0 | grep '{serial\|idVendor\|idProduct}'
```

This overlap means you need to:
1. Check which device is on which port: `ls -l /dev/ttyUSB*`
2. Update the port assignments when launching: `ros2 launch robot_killer main.launch.py lidar_port:=/dev/ttyUSB0 imu_port:=/dev/ttyUSB1 esp32_port:=/dev/ttyUSB2`
3. Give appropriate permissions: `sudo chmod 666 /dev/ttyUSB*`

### Hardware Connection Instructions

#### SLLIDAR Connection
1. Connect the SLLIDAR to a USB port
2. Verify the port in `launch/lidar.launch.py` (default: `/dev/ttyUSB0`, 115200 baud)
3. Ensure the LIDAR motor is spinning when powered

#### BNO055 IMU Connection
1. Connect the BNO055 to a USB port
2. Verify the port in `launch/bno055.launch.py` (default: `/dev/ttyUSB1`)
3. The IMU should be mounted rigidly on the robot with proper orientation

#### ESP32 Connection
1. Connect the ESP32 to a USB port
2. Verify the port in `launch/esp32.launch.py` (default: `/dev/ttyUSB0`, 115200 baud)
3. Check that the ESP32 firmware matches the expected protocol

## Building the Package

```bash
cd ~/your_ros2_workspace/
colcon build --packages-select robot_killer esp32_interface bno055 sllidar_ros2
source install/setup.bash
```

## Troubleshooting

### Serial Port Issues
- Check device permissions: `sudo chmod 666 /dev/ttyUSB*`
- Verify port assignments in respective launch files
- Use `ls -l /dev/ttyUSB*` to identify connected devices
- Try unplugging and reconnecting devices in a specific order

### Navigation Issues
- Verify that transforms are correctly published
- Check that the map is properly loaded
- Ensure the robot's position is correctly initialized in the map

### Sensor Issues
- Ensure LiDAR motor is spinning (you should hear it)
- Check IMU calibration status
- Verify ESP32 is responding to commands
- Monitor ROS topics for sensor data: `ros2 topic echo /scan` for LiDAR, etc.

### Transform Issues
- If you see `TF_DENORMALIZED_QUATERNION` warnings, check the transforms in the URDF
- TF errors like "No transform from X to Y" usually indicate that a frame ID doesn't match between the URDF and sensor configuration
- Use `ros2 run tf2_tools view_frames` to visualize the TF tree and check for issues

## Development Guidelines

When extending this system:

1. **Add new launch files** for any new components
2. **Update round1.launch.py** to integrate new components
3. **Document parameters** in this README
4. **Test individual components** before integration

## Dependencies

This package relies on several ROS2 packages:
- slam_toolbox
- nav2_bringup and related packages
- sllidar_ros2
- bno055
- esp32_interface
- twist_to_ackermann
- rviz2
- robot_state_publisher

See package.xml for a complete list of dependencies.

## License

[License information TBD]

## Contact

Maintainer: zlove (zavala_esteban4455@yahoo.com) 

## Robot Model

Our robot is described in the URDF file located at `urdf/robot.urdf.xml`. This model defines:

1. **Base structure**:
   - `base_footprint`: The ground projection of the robot (root link)
   - `base_link`: The main body of the robot

2. **Wheel Configuration**:
   - Rear wheels: Fixed orientation, driven wheels
   - Front wheels: Steerable wheels with Ackermann steering geometry

3. **Sensor Frames** - these match the actual sensor components:
   - `laser`: LiDAR sensor frame
   - `imu_link`: IMU sensor frame
   - `ultrasonic_sensor`: Ultrasonic sensor

### Frame Hierarchy

```
base_footprint
    └── base_link
        ├── left_rear_wheel_link
        ├── right_rear_wheel_link
        ├── front_left_pivot
        │   └── front_left_wheel_link
        ├── front_right_pivot
        │   └── front_right_wheel_link
        ├── lidar_base
        │   └── laser
        ├── imu_link
        ├── ultrasonic_sensor
        └── steering_control
```

### Frame ID Configuration

All sensor components are configured to publish data with frame IDs that match the URDF model:

- **LiDAR**: Publishes scan data with frame_id: `laser`
- **IMU**: Publishes IMU data with frame_id: `imu_link`
- **ESP32**: Uses `base_footprint` as the base frame and publishes odometry with frame_id: `odom`

These frames must match between the URDF and launch files for proper operation.

## Understanding the Integration

For team members to understand how everything works together, here's a detailed explanation of the integration between the robot model and sensors:

### Component Integration Flow

1. **URDF Robot Model** defines the physical structure of the robot, including:
   - Frame positions and relationships
   - Sensor mounting locations
   - Joint types and limits

2. **robot_state_publisher** reads the URDF and:
   - Publishes static transforms between links
   - Makes the robot model available for visualization
   - Creates the transform tree for all other components

3. **Sensor Drivers** (lidar, IMU, ESP32) use frame IDs from the URDF:
   - Each publishes data with the correct frame_id
   - Data is properly positioned in the robot's coordinate system
   - Navigation stack can use this data correctly

4. **Navigation/SLAM** components use the integrated data:
   - LiDAR scans are positioned correctly relative to the robot
   - IMU data provides orientation information
   - ESP32 provides odometry for localization

### Key Integration Points

1. **Frame ID Consistency** - All these must match:
   - Link names in URDF
   - frame_id parameters in launch files
   - References in tf2 transformations

2. **Serial Port Assignment** - Make sure each device has a unique port:
   - LiDAR (typically `/dev/ttyUSB0`)
   - BNO055 IMU (typically `/dev/ttyUSB1`)
   - ESP32 (typically needs a different port than LiDAR, e.g., `/dev/ttyUSB2`)

3. **Parameter Passing** - Launch files are structured to pass parameters down:
   - main.launch.py → round1.launch.py → component launch files
   - USB port parameters can be overridden at main launch

### Testing and Verification

To verify the integration is working:

1. Check transforms are properly published:
   ```bash
   ros2 run tf2_tools view_frames
   ```

2. Visualize sensor data in RViz:
   ```bash
   ros2 launch robot_killer rviz.launch.py
   ```

3. Verify topics are publishing:
   ```bash
   # Check LiDAR data
   ros2 topic echo /scan
   
   # Check IMU data
   ros2 topic echo /imu
   
   # Check odometry
   ros2 topic echo /odom
   ```

If all these components are working together, your robot is properly integrated and ready for SLAM or navigation tasks. 

## Mapping with the Physical Robot

You have two options for creating maps with your physical robot:

### Option 1: Mapping through Main Launch Files

Use this approach when you want to integrate mapping with the rest of your robot's functionality and keep everything in one launch command:

```bash
# Basic mapping with default port settings - most common use case
ros2 launch robot_killer main.launch.py mode:=slam

# Mapping with custom port assignments
ros2 launch robot_killer main.launch.py mode:=slam lidar_port:=/dev/ttyUSB0 imu_port:=/dev/ttyUSB1 esp32_port:=/dev/ttyUSB2

# Mapping and automatically save the map when done (press Ctrl+C to stop and save)
ros2 launch robot_killer main.launch.py mode:=slam save_map:=true map_name:=my_kitchen
```

### Option 2: Dedicated Mapping Tools

Use these dedicated tools when you specifically want to focus on mapping without other components:

```bash
# Use the mapping helper script (recommended for pure mapping sessions)
./robot_killer/start_mapping.sh

# Or specify custom ports
./robot_killer/start_mapping.sh /dev/ttyUSB0 /dev/ttyUSB1 /dev/ttyUSB2

# Or use the slam launch file directly for more control
ros2 launch robot_killer slam.launch.py lidar_port:=/dev/ttyUSB0 imu_port:=/dev/ttyUSB1 controller_port:=/dev/ttyUSB2
```

To save a map after mapping:
```bash
# Save the map using the helper script
./robot_killer/save_map.sh my_kitchen

# Or use the launch file directly
ros2 launch robot_killer save_map.launch.py map_name:=my_kitchen
```

### When to Use Each Option

- **Use Option 1 (main.launch.py)** when:
  - You want a single command to run everything
  - You're doing other tasks besides just mapping
  - You're comfortable with the default configuration

- **Use Option 2 (dedicated tools)** when:
  - You're specifically focused on creating a high-quality map
  - You want more control over the mapping process
  - You want a more interactive experience with clear steps
  - You need the helper scripts to manage permissions and port conflicts

### Setting Up SLAM for Mapping

The SLAM Toolbox is configured to create high-quality maps of your environment. To start mapping with your physical robot:

```bash
# Basic mapping command with default settings
ros2 launch robot_killer slam.launch.py

# Mapping with custom port assignments
ros2 launch robot_killer slam.launch.py lidar_port:=/dev/ttyUSB0 imu_port:=/dev/ttyUSB1 controller_port:=/dev/ttyUSB2
```

The SLAM launch file includes:
- Robot state publisher
- LiDAR driver
- IMU driver
- Twist to Ackermann converter
- SLAM Toolbox (in mapping mode)
- RViz with a specialized mapping configuration

### SLAM Configuration for Physical Hardware

The SLAM parameters have been optimized for physical hardware in the `config/slam_params.yaml` file. Key settings include:

- `mode: mapping` - Set to create and update maps
- `map_file_name: robot_killer/maps/auto_saved_map` - Location for periodic auto-saves
- `use_map_saver: true` - Enables automatic saving 
- Hardware-tuned values for:
  - Loop closing
  - Scan matching
  - Map update intervals
  - Search space parameters

### Creating a Good Map

For best results when mapping:

1. **Drive slowly and smoothly** around the environment
2. **Make multiple passes** through the same areas to improve accuracy
3. **Close loops** by returning to previously visited areas
4. **Cover the entire area** systematically rather than randomly

### Saving Maps

You have two ways to save your map:

#### 1. Using the dedicated save_map.launch.py

```bash
# Save with default name (my_map) in the maps directory
ros2 launch robot_killer save_map.launch.py

# Save with custom name
ros2 launch robot_killer save_map.launch.py map_name:=kitchen_map

# Save to a custom location
ros2 launch robot_killer save_map.launch.py map_path:=/home/user/my_maps/kitchen
```

This will save both a `.pgm` image file and a `.yaml` configuration file.

#### 2. Using SLAM Toolbox's interactive mode

The SLAM Toolbox has an interactive mode enabled, which you can use via the RViz SlamToolboxPlugin:

1. In RViz, find the "SlamToolboxPlugin" tab
2. Click "Serialize Map" to save the current map
3. Specify a path in the maps directory (e.g., `robot_killer/maps/my_map`)
4. Click "Save"

### Map Directory Organization

Maps are stored in the `robot_killer/maps/` directory:
- The directory is automatically created if it doesn't exist
- Maps consist of a `.pgm` file (the image) and a `.yaml` file (metadata)
- Use consistent naming for your maps to avoid confusion

### Using Saved Maps for Navigation

Once you have a good map, you can switch to navigation mode:

```bash
# Basic navigation using the most recently saved map
ros2 launch robot_killer main.launch.py mode:=nav

# Navigation with a specific map file
ros2 launch robot_killer main.launch.py mode:=nav map_file:=robot_killer/maps/my_map.yaml
```

### Troubleshooting Mapping Issues

If you encounter issues with mapping:

1. **Poor map quality**: 
   - Ensure the LiDAR is properly mounted and level
   - Check for reflective surfaces that might cause scan problems
   - Drive more slowly over complex areas

2. **Loop closure problems**:
   - Revisit previously mapped areas to create loop closures
   - Adjust loop closure parameters in `slam_params.yaml` if needed

3. **Transformation errors**:
   - Verify that all transforms are properly published
   - Check that frame IDs match between components
   - Run `ros2 run tf2_tools view_frames` to visualize the transform tree

4. **Map saving failures**:
   - Ensure the maps directory exists
   - Check permissions on the directory
   - Try saving to an absolute path if relative paths don't work 

## Teleop Control with Keyboard

For manual control of your robot during testing or map creation, you can use teleop_twist_keyboard. The robot_killer package includes several integrated launch files for this purpose:

### Using Teleop with Navigation

To control your robot manually in a previously created map:

```bash
# Basic teleop navigation with default map
ros2 launch robot_killer teleop_nav.launch.py

# With a specific map
ros2 launch robot_killer teleop_nav.launch.py map_file:=robot_killer/maps/my_map.yaml

# With custom port assignments
ros2 launch robot_killer teleop_nav.launch.py lidar_port:=/dev/ttyUSB0 imu_port:=/dev/ttyUSB1 esp32_port:=/dev/ttyUSB2
```

### Using Teleop with SLAM for Manual Mapping

Create maps manually by driving the robot with keyboard commands:

```bash
# Map creation with teleop
ros2 launch robot_killer teleop_slam.launch.py

# With custom port assignments
ros2 launch robot_killer teleop_slam.launch.py lidar_port:=/dev/ttyUSB0 imu_port:=/dev/ttyUSB1 esp32_port:=/dev/ttyUSB2
```

### Basic Teleop (Hardware Only)

For testing just the robot hardware with teleop:

```bash
# Basic teleop with hardware
ros2 launch robot_killer teleop.launch.py
```

### Keyboard Controls

When the teleop node is running, you can use the following keys:
- **w/x**: Forward/backward
- **a/d**: Left/right
- **q/e**: Rotate left/right
- **s**: Stop movement
- **Space bar**: Emergency stop
- **i/o**: Increase/decrease speed by 10%
- **k/l**: Increase/decrease turn speed by 10%

The teleop control window must be in focus to receive keyboard commands.

### Using Teleop with Autonomous Mode

You can combine teleop with autonomous operation for testing:

```bash
# First terminal: Start navigation with autonomous mode
ros2 launch robot_killer main.launch.py mode:=nav autonomous:=true

# Second terminal: Run teleop to intervene if needed
ros2 run teleop_twist_keyboard teleop_twist_keyboard
```

This allows you to manually control the robot when needed, while the autonomous system is running. 