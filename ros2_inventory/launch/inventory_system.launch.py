#!/usr/bin/env python3
"""
Launch file for Inventory Management System
Starts all ROS2 nodes: camera, detection, inventory, and API bridge

Usage:
    ros2 launch ros2_inventory inventory_system.launch.py
"""

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, LogInfo
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    """Generate launch description"""
    
    # Launch arguments
    camera_id_arg = DeclareLaunchArgument(
        'camera_id',
        default_value='0',
        description='Camera device ID'
    )
    
    model_path_arg = DeclareLaunchArgument(
        'model_path',
        default_value='yolov8n.pt',
        description='Path to YOLO model'
    )
    
    conf_threshold_arg = DeclareLaunchArgument(
        'conf_threshold',
        default_value='0.25',
        description='Detection confidence threshold'
    )
    
    device_arg = DeclareLaunchArgument(
        'device',
        default_value='cpu',
        description='Device for inference (cpu or cuda)'
    )
    
    api_host_arg = DeclareLaunchArgument(
        'api_host',
        default_value='0.0.0.0',
        description='API host'
    )
    
    api_port_arg = DeclareLaunchArgument(
        'api_port',
        default_value='8000',
        description='API port'
    )
    
    # Configuration file
    config_file = PathJoinSubstitution([
        FindPackageShare('ros2_inventory'),
        'config',
        'params.yaml'
    ])
    
    # Camera node
    camera_node = Node(
        package='ros2_inventory',
        executable='camera_node',
        name='camera_node',
        output='screen',
        parameters=[{
            'camera_id': LaunchConfiguration('camera_id'),
            'width': 640,
            'height': 480,
            'fps': 30,
            'frame_id': 'camera_frame',
            'topic_name': 'camera/image_raw'
        }],
        remappings=[
            ('/camera/image_raw', 'camera/image_raw')
        ]
    )
    
    # Detection node
    detection_node = Node(
        package='ros2_inventory',
        executable='detection_node',
        name='detection_node',
        output='screen',
        parameters=[{
            'model_path': LaunchConfiguration('model_path'),
            'conf_threshold': LaunchConfiguration('conf_threshold'),
            'iou_threshold': 0.45,
            'device': LaunchConfiguration('device'),
            'input_topic': 'camera/image_raw',
            'output_topic': 'detections',
            'annotated_topic': 'annotated_image',
            'max_detections': 1000
        }],
        remappings=[
            ('/detections', 'detections'),
            ('/annotated_image', 'annotated_image')
        ]
    )
    
    # Inventory node
    inventory_node = Node(
        package='ros2_inventory',
        executable='inventory_node',
        name='inventory_node',
        output='screen',
        parameters=[{
            'input_topic': 'detections',
            'output_topic': 'inventory_status',
            'grid_rows': 3,
            'grid_cols': 3,
            'low_stock_threshold': 5,
            'out_of_stock_threshold': 0
        }],
        remappings=[
            ('/inventory_status', 'inventory_status')
        ]
    )
    
    # API bridge node
    api_bridge_node = Node(
        package='ros2_inventory',
        executable='api_bridge_node',
        name='api_bridge_node',
        output='screen',
        parameters=[{
            'api_host': LaunchConfiguration('api_host'),
            'api_port': LaunchConfiguration('api_port'),
            'inventory_topic': 'inventory_status',
            'image_topic': 'annotated_image',
            'detection_topic': 'detections',
            'api_base_url': 'http://localhost:8000'
        }]
    )
    
    # Info message
    info_msg = LogInfo(
        msg=[
            '\n',
            '╔═══════════════════════════════════════════════════════════╗\n',
            '║   ROS2 Inventory Management System                        ║\n',
            '╠═══════════════════════════════════════════════════════════╣\n',
            '║  Nodes:                                                   ║\n',
            '║  • camera_node       - Camera driver                     ║\n',
            '║  • detection_node    - YOLO inference                    ║\n',
            '║  • inventory_node    - Count & analysis                  ║\n',
            '║  • api_bridge_node   - API integration                   ║\n',
            '║                                                           ║\n',
            '║  Topics:                                                  ║\n',
            '║  • /camera/image_raw     - Raw camera feed               ║\n',
            '║  • /detections           - Detection results             ║\n',
            '║  • /annotated_image      - Annotated video               ║\n',
            '║  • /inventory_status     - Inventory counts              ║\n',
            '╚═══════════════════════════════════════════════════════════╝'
        ]
    )
    
    # Create launch description
    ld = LaunchDescription([
        # Arguments
        camera_id_arg,
        model_path_arg,
        conf_threshold_arg,
        device_arg,
        api_host_arg,
        api_port_arg,
        
        # Info message
        info_msg,
        
        # Nodes
        camera_node,
        detection_node,
        inventory_node,
        api_bridge_node
    ])
    
    return ld


# For running directly: python3 inventory_system.launch.py
if __name__ == '__main__':
    generate_launch_description()
