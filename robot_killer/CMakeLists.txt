cmake_minimum_required(VERSION 3.8)
project(robot_killer)

# Find dependencies
find_package(ament_cmake REQUIRED)

# Install launch files
install(DIRECTORY
  launch/
  DESTINATION share/${PROJECT_NAME}/launch
)

# Install config files (if you have any)
install(DIRECTORY
  config/
  DESTINATION share/${PROJECT_NAME}/config
)

ament_package() 