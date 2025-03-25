#!/bin/bash

# save_map.sh - Script to save maps easily
# Usage: ./save_map.sh [map_name]

# Display header
echo "====================================="
echo "  Robot Killer - Map Saving Tool     "
echo "====================================="
echo ""

# Get map name from argument or prompt
MAP_NAME=${1:-""}
if [ -z "$MAP_NAME" ]; then
    echo "Enter map name (default: my_map):"
    read -r MAP_NAME
    MAP_NAME=${MAP_NAME:-"my_map"}
fi

# Create maps directory if it doesn't exist
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
MAPS_DIR="$SCRIPT_DIR/maps"
mkdir -p "$MAPS_DIR"
echo "🗂️  Maps directory: $MAPS_DIR"

# Check if map with this name already exists
if [ -f "$MAPS_DIR/$MAP_NAME.pgm" ] || [ -f "$MAPS_DIR/$MAP_NAME.yaml" ]; then
    echo ""
    echo "⚠️  Warning: Map files with name '$MAP_NAME' already exist!"
    echo "   Do you want to overwrite? (y/n)"
    read -r overwrite
    
    if [[ $overwrite != "y" && $overwrite != "Y" ]]; then
        echo "Enter a new map name:"
        read -r MAP_NAME
        
        if [ -z "$MAP_NAME" ]; then
            echo "❌ No map name provided. Exiting."
            exit 1
        fi
    fi
fi

# Save the map
echo ""
echo "💾 Saving map as '$MAP_NAME'..."
ros2 launch robot_killer save_map.launch.py map_name:=$MAP_NAME

# Check if saved successfully
if [ -f "$MAPS_DIR/$MAP_NAME.pgm" ] && [ -f "$MAPS_DIR/$MAP_NAME.yaml" ]; then
    echo ""
    echo "✅ Map saved successfully!"
    echo "   • Image file: $MAPS_DIR/$MAP_NAME.pgm"
    echo "   • Config file: $MAPS_DIR/$MAP_NAME.yaml"
    
    # List available maps
    echo ""
    echo "📋 Available maps:"
    ls -l "$MAPS_DIR"/*.yaml 2>/dev/null | awk '{print $9}' | xargs -n1 basename 2>/dev/null
    
    # Suggest next steps
    echo ""
    echo "🔍 To use this map for navigation, run:"
    echo "   ros2 launch robot_killer main.launch.py mode:=nav map_file:=$MAPS_DIR/$MAP_NAME.yaml"
else
    echo ""
    echo "❌ Failed to save map. Check that:"
    echo "   • The map server is running properly"
    echo "   • You have write permissions to $MAPS_DIR"
    echo "   • ROS2 environment is properly set up"
fi

echo ""
echo "=====================================" 