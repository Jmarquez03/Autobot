#!/bin/bash

# Get the map name from arguments or use default
MAP_NAME="${1:-my_map}"

# Get the path to the all_nodes package
ALL_NODES_PATH=$(ros2 pkg prefix all_nodes)
MAPS_DIR="${ALL_NODES_PATH}/share/all_nodes/maps"

# Create maps directory if it doesn't exist
mkdir -p "${MAPS_DIR}"

echo "Saving map with name: ${MAP_NAME}"
echo "Maps will be saved to: ${MAPS_DIR}"

# Save the map
ros2 run nav2_map_server map_saver_cli -f "${MAPS_DIR}/${MAP_NAME}"

echo "Map saved to: ${MAPS_DIR}/${MAP_NAME}.pgm and ${MAPS_DIR}/${MAP_NAME}.yaml"
echo "To use this map for navigation, run:"
echo "ros2 launch all_nodes all_nodes.launch.py mode:=nav map_file:=${MAPS_DIR}/${MAP_NAME}.yaml" 