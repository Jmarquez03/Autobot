# ESP32 Interface

A ROS 2 package for interfacing with an ESP32 microcontroller that is connected to wheel encoders and motor controllers.

## Overview

This package provides a node that:
1. Receives encoder data from the ESP32 via serial connection
2. Calculates odometry based on encoder ticks
3. Publishes odometry data to the `/odom` topic and TF
4. Subscribes to `/cmd_vel` topic to control the motors
5. Sends motor commands to the ESP32 via serial connection

## ESP32 Communication Protocol

The communication with the ESP32 uses a simple JSON-based protocol:

### Incoming messages from ESP32 (examples):

Encoder data:
```json
{
  "type": "encoder",
  "left_ticks": 123,
  "right_ticks": 456
}
```

Debug messages:
```json
{
  "type": "debug",
  "message": "Some debug information"
}
```

### Outgoing messages to ESP32:

Motor commands:
```json
{
  "type": "motor_cmd",
  "left_vel": 0.5,
  "right_vel": 0.3
}
```

## Parameters

The node accepts the following parameters:

- `port` (default: `/dev/ttyUSB1`): Serial port for ESP32 connection
- `baudrate` (default: `115200`): Baudrate for ESP32 serial connection
- `base_frame_id` (default: `base_link`): Base frame ID for the robot
- `odom_frame_id` (default: `odom`): Odometry frame ID
- `wheel_radius` (default: `0.035`): Wheel radius in meters
- `wheel_separation` (default: `0.16`): Wheel separation in meters
- `encoder_resolution` (default: `20.0`): Encoder resolution in ticks per revolution
- `publish_tf` (default: `true`): Whether to publish TF transforms
- `cmd_vel_timeout` (default: `0.5`): Timeout for cmd_vel messages in seconds

## Usage

To run the ESP32 interface node:

```bash
ros2 launch esp32_interface esp32_interface_launch.py
```

To override default parameters:

```bash
ros2 launch esp32_interface esp32_interface_launch.py port:=/dev/ttyUSB0 baudrate:=9600
```

## Integration with SLAM Toolbox

When using this package with SLAM Toolbox, make sure the `base_frame_id` parameter matches the `base_frame` parameter in the SLAM Toolbox configuration.

## Topics

### Subscribed Topics

- `/cmd_vel` (geometry_msgs/Twist): Velocity commands for the robot

### Published Topics

- `/odom` (nav_msgs/Odometry): Odometry information
- `/esp32_debug` (std_msgs/String): Debug messages from the ESP32

### TF Transforms

- `odom` → `base_link`: Transform from odometry frame to robot base frame 