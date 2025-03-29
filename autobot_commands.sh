#!/bin/bash
# Autobot Commands Script
# This script provides a menu of common commands for the Autobot project

#make file executable
#chmod +x autobot_commands.sh

#run file
#./autobot_commands.sh

# Function to display the menu
show_menu() {
    clear
    echo "===== AUTOBOT COMMAND CENTER ====="
    echo "1. Launch Complete Robot"
    echo "2. Hardware Setup"
    echo "3. Debugging Tools"
    echo "4. Manual Control"
    echo "5. Individual Component Launch"
    echo "0. Exit"
    echo "=================================="
    echo "Enter your choice: "
}

# Function for hardware setup
hardware_setup() {
    echo "===== HARDWARE SETUP ====="
    echo "1. Check USB devices"
    echo "2. Set USB permissions"
    echo "0. Back to main menu"
    echo "=========================="
    
    read -p "Enter your choice: " choice
    case $choice in
        1)
            echo "Checking USB devices..."
            ls -la /dev | grep USB
            read -p "Press Enter to continue..."
            hardware_setup
            ;;
        2)
            echo "Setting USB permissions..."
            sudo chmod 777 /dev/ttyUSB0
            sudo chmod 777 /dev/ttyUSB1
            sudo chmod 777 /dev/ttyUSB2
            echo "Permissions set!"
            read -p "Press Enter to continue..."
            hardware_setup
            ;;  # <-- This semicolon was missing
        0)
            show_menu
            ;;
        *)
            echo "Invalid option"
            read -p "Press Enter to continue..."
            hardware_setup
            ;;
    esac
}

# Function for debugging tools
debugging_tools() {
    echo "===== DEBUGGING TOOLS ====="
    echo "1. View TF tree"
    echo "2. List all topics"
    echo "3. Echo a specific topic"
    echo "0. Back to main menu"
    echo "==========================="
    
    read -p "Enter your choice: " choice
    case $choice in
        1)
            echo "Generating TF tree..."
            ros2 run tf2_tools view_frames
            echo "TF tree generated!"
            read -p "Press Enter to continue..."
            debugging_tools
            ;;
        2)
            echo "Listing all topics..."
            ros2 topic list
            read -p "Press Enter to continue..."
            debugging_tools
            ;;
        3)
            echo "Available topics:"
            ros2 topic list
            echo ""
            read -p "Enter topic name to echo (e.g. /cmd_vel): " topic_name
            echo "Echoing $topic_name (press Ctrl+C to stop)..."
            ros2 topic echo $topic_name
            debugging_tools
            ;;
        0)
            show_menu
            ;;
        *)
            echo "Invalid option"
            read -p "Press Enter to continue..."
            debugging_tools
            ;;
    esac
}

# Function for manual control
manual_control() {
    echo "Starting teleop keyboard control..."
    echo "Use arrow keys to control the robot. Press Ctrl+C to exit."
    ros2 run teleop_twist_keyboard teleop_twist_keyboard
    read -p "Press Enter to continue..."
    show_menu
}

# Function for individual component launch
individual_components() {
    echo "===== INDIVIDUAL COMPONENTS ====="
    echo "1. Robot Visualization"
    echo "2. LIDAR"
    echo "3. IMU"
    echo "4. ESP32 Odometry"
    echo "0. Back to main menu"
    echo "================================="
    
    read -p "Enter your choice: " choice
    case $choice in
        1)
            echo "Launching Robot Visualization..."
            ros2 launch autobot_core robot_visualization.launch.py
            individual_components
            ;;
        2)
            echo "Launching LIDAR..."
            ros2 launch sllidar_ros2 sllidar_a1_launch.py use_sim_time:=false serial_port:=/dev/ttyUSB1
            individual_components
            ;;
        3)
            echo "Launching IMU..."
            ros2 run bno055 bno055 --ros-args --params-file /Users/ajrivera/code/Autobot/bno055/bno055/params/bno055_params_i2c.yaml
            individual_components
            ;;
        4)
            echo "Launching ESP32 Odometry..."
            ros2 launch autobot_core esp32_interface.launch.py serial_port:=/dev/ttyUSB0
            individual_components
            ;;
        0)
            show_menu
            ;;
        *)
            echo "Invalid option"
            read -p "Press Enter to continue..."
            individual_components
            ;;
    esac
}

# Main menu logic
main_menu() {
    show_menu
    read -p "Enter your choice: " choice
    case $choice in
        1)
            echo "Launching complete robot..."
            ros2 launch autobot_core autobot_core.launch.py
            read -p "Press Enter to continue..."
            main_menu
            ;;
        2)
            hardware_setup
            ;;
        3)
            debugging_tools
            ;;
        4)
            manual_control
            ;;
        5)
            individual_components
            ;;
        0)
            echo "Exiting Autobot Command Center. Goodbye!"
            exit 0
            ;;
        *)
            echo "Invalid option"
            read -p "Press Enter to continue..."
            main_menu
            ;;
    esac
}

# Source ROS workspace before starting
echo "Sourcing ROS workspace..."
source /Users/ajrivera/code/Autobot/install/setup.bash

# Start the menu
main_menu