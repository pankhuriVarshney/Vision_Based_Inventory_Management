cmake_minimum_required(VERSION 3.8)
project(ros2_inventory)

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

# Find dependencies
find_package(ament_cmake REQUIRED)
find_package(ament_cmake_python REQUIRED)
find_package(rclpy REQUIRED)
find_package(std_msgs REQUIRED)
find_package(sensor_msgs REQUIRED)
find_package(vision_msgs REQUIRED)
find_package(cv_bridge REQUIRED)

# Include Python package
ament_python_install_package(${PROJECT_NAME})

# Install Python executables
install(PROGRAMS
  ros2_inventory/camera_node.py
  ros2_inventory/detection_node.py
  ros2_inventory/inventory_node.py
  ros2_inventory/api_bridge_node.py
  DESTINATION lib/${PROJECT_NAME}
)

# Install launch and config files
install(DIRECTORY
  launch
  config
  DESTINATION share/${PROJECT_NAME}/
)

# Install message files
install(FILES
  msg/Detection.msg
  msg/DetectionArray.msg
  msg/InventoryCount.msg
  DESTINATION share/${PROJECT_NAME}/msg
)

# Build message generation
find_package(rosidl_default_generators REQUIRED)
rosidl_generate_interfaces(${PROJECT_NAME}
  "msg/Detection.msg"
  "msg/DetectionArray.msg"
  "msg/InventoryCount.msg"
  DEPENDENCIES builtin_interfaces
)

if(BUILD_TESTING)
  find_package(ament_lint_auto REQUIRED)
  ament_lint_auto_find_test_dependencies()
endif()

ament_package()
