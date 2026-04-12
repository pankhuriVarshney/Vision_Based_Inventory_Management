#!/usr/bin/env python3
"""
Launch file for Inventory Management System with Pan-Tilt Support
"""

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, LogInfo
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    # Launch arguments
    camera_id_arg = DeclareLaunchArgument('camera_id', default_value='0')
    model_path_arg = DeclareLaunchArgument('model_path', default_value='yolov8n.pt')
    conf_threshold_arg = DeclareLaunchArgument('conf_threshold', default_value='0.25')
    device_arg = DeclareLaunchArgument('device', default_value='cpu')
    api_host_arg = DeclareLaunchArgument('api_host', default_value='0.0.0.0')
    api_port_arg = DeclareLaunchArgument('api_port', default_value='8000')
    enable_pan_tilt_arg = DeclareLaunchArgument('enable_pan_tilt', default_value='true')
    auto_scan_arg = DeclareLaunchArgument('auto_scan', default_value='false')
    
    config_file = PathJoinSubstitution([
        FindPackageShare('ros2_inventory'),
        'config',
        'params.yaml'
    ])
    
    # Pan-Tilt Controller Node
    pan_tilt_node = Node(
        package='ros2_inventory',
        executable='pan_tilt_controller',
        name='pan_tilt_controller',
        output='screen',
        parameters=[{
            'pan_pin': 14,
            'tilt_pin': 15,
            'pan_min': 0,
            'pan_max': 180,
            'tilt_min': 0,
            'tilt_max': 90,
            'smooth_motion': True,
            'auto_scan': LaunchConfiguration('auto_scan'),
            'scan_interval': 10.0
        }]
    )
    
    # Camera Node (with pan-tilt tracking)
    camera_node = Node(
        package='ros2_inventory',
        executable='camera_node',
        name='camera_node',
        output='screen',
        parameters=[{
            'width': 640,
            'height': 480,
            'fps': 30,
            'use_picamera2': True,
            'use_libcamera': False,
            'enable_pan_tilt_tracking': LaunchConfiguration('enable_pan_tilt'),
            'topic_name': 'camera/image_raw'
        }]
    )
    
    # Detection Node
    detection_node = Node(
        package='ros2_inventory',
        executable='detection_node',
        name='detection_node',
        output='screen',
        parameters=[{
            'model_path': LaunchConfiguration('model_path'),
            'conf_threshold': LaunchConfiguration('conf_threshold'),
            'device': LaunchConfiguration('device'),
            'enable_tracking': LaunchConfiguration('enable_pan_tilt'),
            'tracking_threshold': 0.7
        }]
    )
    
    # Inventory Node
    inventory_node = Node(
        package='ros2_inventory',
        executable='inventory_node',
        name='inventory_node',
        output='screen',
        parameters=[config_file]
    )
    
    # API Bridge Node
    api_bridge_node = Node(
        package='ros2_inventory',
        executable='api_bridge_node',
        name='api_bridge_node',
        output='screen',
        parameters=[{
            'api_host': LaunchConfiguration('api_host'),
            'api_port': LaunchConfiguration('api_port'),
            'api_base_url': 'http://localhost:8000'
        }]
    )
    
    # Info message
    info_msg = LogInfo(msg=[
        '\n',
        '╔═══════════════════════════════════════════════════════════╗\n',
        '║  ROS2 Inventory Management System with Pan-Tilt           ║\n',
        '╠═══════════════════════════════════════════════════════════╣\n',
        '║  Nodes:                                                   ║\n',
        '║    • pan_tilt_controller - Servo control (GPIO 14/15)     ║\n',
        '║    • camera_node - Pi Camera with tracking                ║\n',
        '║    • detection_node - YOLOv8 inference                    ║\n',
        '║    • inventory_node - Count & analysis                    ║\n',
        '║    • api_bridge_node - API integration                    ║\n',
        '║                                                           ║\n',
        '║  Hardware:                                                ║\n',
        '║    • Pan Servo: GPIO 14 (Pin 8)                           ║\n',
        '║    • Tilt Servo: GPIO 15 (Pin 10)                         ║\n',
        '║    • Power: External 5V (Do NOT power from Pi!)           ║\n',
        '╚═══════════════════════════════════════════════════════════╝'
    ])
    
    return LaunchDescription([
        camera_id_arg, model_path_arg, conf_threshold_arg,
        device_arg, api_host_arg, api_port_arg,
        enable_pan_tilt_arg, auto_scan_arg,
        info_msg,
        pan_tilt_node,
        camera_node,
        detection_node,
        inventory_node,
        api_bridge_node
    ])


if __name__ == '__main__':
    generate_launch_description()