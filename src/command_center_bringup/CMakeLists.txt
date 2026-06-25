cmake_minimum_required(VERSION 3.8)
project(command_center_bringup)
find_package(ament_cmake REQUIRED)
install(DIRECTORY launch config maps
  DESTINATION share/${PROJECT_NAME}
)
ament_package()