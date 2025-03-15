cmake_minimum_required(VERSION 3.8)
project(my_robot_localization)

# Default to C++14
if(NOT CMAKE_CXX_STANDARD)
  set(CMAKE_CXX_STANDARD 14)
endif()

# Find dependencies
find_package(ament_cmake REQUIRED)
find_package(rclcpp REQUIRED)
find_package(robot_localization REQUIRED)
find_package(nav_msgs REQUIRED)
find_package(sensor_msgs REQUIRED)
find_package(geometry_msgs REQUIRED)
find_package(tf2 REQUIRED)
find_package(tf2_ros REQUIRED)

# Create my_robot_localization directory if it doesn't exist
#add_subdirectory(my_robot_localization EXCLUDE_FROM_ALL)

# Add the Arduino interface node
add_executable(arduino_interface src/my_robot_localization/arduino_interface.py)
ament_target_dependencies(arduino_interface
  rclcpp
  nav_msgs
  sensor_msgs
  geometry_msgs
  tf2
  tf2_ros
)

# Install executables
install(TARGETS
  arduino_interface
  DESTINATION lib/${PROJECT_NAME}
)

# Install launch files - make sure this directory exists
install(DIRECTORY
  launch/
  DESTINATION share/${PROJECT_NAME}/launch
)

# Install config files - create this directory if it doesn't exist
install(DIRECTORY
  config/
  DESTINATION share/${PROJECT_NAME}/config
)

# Install Python modules if any
install(DIRECTORY
  my_robot_localization/
  DESTINATION lib/python3.12/site-packages/my_robot_localization
  PATTERN "__pycache__" EXCLUDE
)

# Export dependencies
ament_export_include_directories(include)
ament_export_dependencies(
  rclcpp
  robot_localization
  nav_msgs
  sensor_msgs
  geometry_msgs
  tf2
  tf2_ros
)

ament_package()
