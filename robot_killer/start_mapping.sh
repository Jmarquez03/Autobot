#!/bin/bash

# start_mapping.sh - Script to automate mapping setup with the physical robot
# Usage: ./start_mapping.sh [lidar_port] [imu_port] [controller_port]

# Set defaults
LIDAR_PORT=${1:-"/dev/ttyUSB0"}
IMU_PORT=${2:-"/dev/ttyUSB1"}
CONTROLLER_PORT=${3:-"/dev/ttyUSB2"}

# Display header
echo "====================================="
echo "  Robot Killer - Mapping Setup Tool  "
echo "====================================="
echo ""

# Check if ports exist
check_port() {
    if [ ! -e "$1" ]; then
        echo "⚠️  Warning: Port $1 does not exist"
        return 1
    else
        return 0
    fi
}

# Give permissions to all ttyUSB devices
echo "🔍 Setting permissions for USB devices..."
sudo chmod 666 /dev/ttyUSB* 2>/dev/null
if [ $? -eq 0 ]; then
    echo "✅ Permissions set successfully"
else
    echo "⚠️  Could not set permissions. You may need sudo privileges."
fi

# Check device ports
echo ""
echo "🔍 Checking device ports..."
echo "  LiDAR port:      $LIDAR_PORT"
check_port "$LIDAR_PORT"
echo "  IMU port:        $IMU_PORT"
check_port "$IMU_PORT"
echo "  Controller port: $CONTROLLER_PORT"
check_port "$CONTROLLER_PORT"

# List all available ports for reference
echo ""
echo "📋 Available ports:"
ls -l /dev/ttyUSB* 2>/dev/null
if [ $? -ne 0 ]; then
    echo "  No USB devices found. Please connect your devices."
fi

# Check for potential port conflicts
if [ "$LIDAR_PORT" = "$IMU_PORT" ] || [ "$LIDAR_PORT" = "$CONTROLLER_PORT" ] || [ "$IMU_PORT" = "$CONTROLLER_PORT" ]; then
    echo ""
    echo "⚠️  WARNING: Port conflict detected! Two or more devices are assigned to the same port."
    echo "   Please specify different ports using:"
    echo "   ./start_mapping.sh [lidar_port] [imu_port] [controller_port]"
    echo ""
fi

# Create maps directory if it doesn't exist
echo ""
echo "🗂️  Ensuring maps directory exists..."
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
MAPS_DIR="$SCRIPT_DIR/maps"
mkdir -p "$MAPS_DIR"
echo "✅ Maps will be saved to: $MAPS_DIR"

# Prepare to launch
echo ""
echo "🚀 Starting mapping with the following configuration:"
echo "  • LiDAR:      $LIDAR_PORT"
echo "  • IMU:        $IMU_PORT"
echo "  • Controller: $CONTROLLER_PORT"
echo ""
echo "⌛ Launching SLAM... (Press Ctrl+C to stop)"
echo ""

# Launch SLAM with specified ports
ros2 launch robot_killer slam.launch.py \
    lidar_port:=$LIDAR_PORT \
    imu_port:=$IMU_PORT \
    controller_port:=$CONTROLLER_PORT \
    use_rviz:=true

# This part will execute after SLAM is stopped
echo ""
echo "💾 Would you like to save the map now? (y/n)"
read -r save_map

if [[ $save_map == "y" || $save_map == "Y" ]]; then
    echo "Enter map name (default: my_map):"
    read -r map_name
    map_name=${map_name:-"my_map"}
    
    echo "💾 Saving map as '$map_name'..."
    ros2 launch robot_killer save_map.launch.py map_name:=$map_name
    
    echo "✅ Map saved as: $MAPS_DIR/$map_name"
    echo "   • Image file: $map_name.pgm"
    echo "   • Config file: $map_name.yaml"
fi

echo ""
echo "✅ Mapping session completed!"
echo "=====================================" 