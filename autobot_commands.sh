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
    echo "2. Launch Autonomous Navigation"
    echo "3. Hardware Setup"
    echo "4. Debugging Tools"
    echo "5. Manual Control"
    echo "6. Individual Component Launch"
    echo "7. Controller Management"
    echo "0. Exit"
    echo "=================================="
    echo "Enter your choice: "
}

# Function for hardware setup
hardware_setup() {
    echo "===== HARDWARE SETUP ====="
    echo "1. Check USB devices"
    echo "2. Set USB permissions"
    echo "3. Install ROS 2 Jazzy dependencies"
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
            ;;
        3)
            echo "Installing ROS 2 Jazzy dependencies..."
            sudo apt update
            sudo apt install ros-jazzy-ros2-control ros-jazzy-ros2-controllers ros-jazzy-ackermann-steering-controller
            echo "Dependencies installed!"
            read -p "Press Enter to continue..."
            hardware_setup
            ;;
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
    echo "4. Monitor odometry data"
    echo "5. Check Nav2 status"
    echo "6. Check controller status"
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
        4)
            echo "Monitoring odometry data (press Ctrl+C to stop)..."
            ros2 topic echo /odom
            debugging_tools
            ;;
        5)
            echo "Checking Nav2 status (press Ctrl+C to stop)..."
            ros2 topic echo /navigate_to_pose/_action/status
            debugging_tools
            ;;
        6)
            echo "Checking controller status..."
            ros2 control list_controllers
            read -p "Press Enter to continue..."
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

# Function for controller management
controller_management() {
    echo "===== CONTROLLER MANAGEMENT ====="
    echo "1. List controllers"
    echo "2. Start controller"
    echo "3. Stop controller"
    echo "4. Reload controller"
    echo "5. Send test command to Ackermann controller"
    echo "0. Back to main menu"
    echo "================================="
    
    read -p "Enter your choice: " choice
    case $choice in
        1)
            echo "Listing controllers..."
            ros2 control list_controllers
            read -p "Press Enter to continue..."
            controller_management
            ;;
        2)
            echo "Available controllers:"
            ros2 control list_controllers
            read -p "Enter controller name to start: " controller_name
            ros2 control load_controller $controller_name
            read -p "Press Enter to continue..."
            controller_management
            ;;
        3)
            echo "Active controllers:"
            ros2 control list_controllers
            read -p "Enter controller name to stop: " controller_name
            ros2 control unload_controller $controller_name
            read -p "Press Enter to continue..."
            controller_management
            ;;
        4)
            echo "Reloading controllers..."
            ros2 control reload_controller_libraries
            read -p "Press Enter to continue..."
            controller_management
            ;;
        5)
            echo "Sending test command to Ackermann controller..."
            ros2 topic pub /ackermann_controller/cmd_vel geometry_msgs/msg/Twist "{linear: {x: 0.2, y: 0.0, z: 0.0}, angular: {x: 0.0, y: 0.0, z: 0.1}}" -1
            read -p "Press Enter to continue..."
            controller_management
            ;;
        0)
            show_menu
            ;;
        *)
            echo "Invalid option"
            read -p "Press Enter to continue..."
            controller_management
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
            echo "Launching autonomous navigation..."
            ros2 launch autobot_core autonomous.launch.py
            read -p "Press Enter to continue..."
            main_menu
            ;;
        3)
            hardware_setup
            ;;
        4)
            debugging_tools
            ;;
        5)
            echo "Starting teleop keyboard control..."
            echo "Use arrow keys to control the robot. Press Ctrl+C to exit."
            ros2 run teleop_twist_keyboard teleop_twist_keyboard --ros-args -r /cmd_vel:=/ackermann_controller/cmd_vel
            read -p "Press Enter to continue..."
            main_menu
            ;;
        6)
            echo "Individual component launch not implemented yet"
            read -p "Press Enter to continue..."
            main_menu
            ;;
        7)
            controller_management
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