#!/usr/bin/env python3
"""
Camera Node for Inventory Management System
Captures images from camera and publishes to ROS2 topic

Subscribes: None
Publishes: /camera/image_raw (sensor_msgs/Image)
"""

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from cv_bridge import CvBridge
import cv2
import numpy as np
from rclpy.qos import QoSProfile, QoSReliabilityPolicy, QoSHistoryPolicy


class CameraNode(Node):
    """Camera driver node"""
    
    def __init__(self):
        super().__init__('camera_node')
        
        # Declare parameters
        self.declare_parameter('camera_id', 0)
        self.declare_parameter('width', 640)
        self.declare_parameter('height', 480)
        self.declare_parameter('fps', 30)
        self.declare_parameter('frame_id', 'camera_frame')
        self.declare_parameter('topic_name', 'camera/image_raw')
        
        # Get parameters
        self.camera_id = self.get_parameter('camera_id').get_parameter_value().integer_value
        self.width = self.get_parameter('width').get_parameter_value().integer_value
        self.height = self.get_parameter('height').get_parameter_value().integer_value
        self.fps = self.get_parameter('fps').get_parameter_value().integer_value
        self.frame_id = self.get_parameter('frame_id').get_parameter_value().string_value
        topic_name = self.get_parameter('topic_name').get_parameter_value().string_value
        
        # Initialize camera
        self.get_logger().info(f'Initializing camera {self.camera_id}...')
        self.cap = cv2.VideoCapture(int(self.camera_id))
        
        if not self.cap.isOpened():
            self.get_logger().error(f'Cannot open camera {self.camera_id}')
            raise RuntimeError(f'Cannot open camera {self.camera_id}')
        
        # Configure camera
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
        self.cap.set(cv2.CAP_PROP_FPS, self.fps)
        
        # Get actual camera properties
        actual_width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        actual_height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        actual_fps = self.cap.get(cv2.CAP_PROP_FPS)
        
        self.get_logger().info(f'Camera configured: {actual_width}x{actual_height} @ {actual_fps:.1f} FPS')
        
        # Initialize CV bridge
        self.bridge = CvBridge()
        
        # Create publisher with QoS for best effort (video streaming)
        qos_profile = QoSProfile(
            reliability=QoSReliabilityPolicy.BEST_EFFORT,
            history=QoSHistoryPolicy.KEEP_LAST,
            depth=5
        )
        
        self.publisher = self.create_publisher(
            Image,
            topic_name,
            qos_profile
        )
        
        # Create timer
        timer_period = 1.0 / self.fps
        self.timer = self.create_timer(timer_period, self.timer_callback)
        
        # Statistics
        self.frame_count = 0
        self.get_logger().info(f'Camera node initialized. Publishing to {topic_name}')
    
    def timer_callback(self):
        """Capture and publish frame"""
        ret, frame = self.cap.read()
        
        if not ret:
            self.get_logger().warn('Failed to capture frame')
            return
        
        # Convert BGR to RGB for ROS2
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # Convert to ROS2 Image message
        try:
            msg = self.bridge.cv2_to_imgmsg(frame_rgb, encoding='rgb8')
            msg.header.stamp = self.get_clock().now().to_msg()
            msg.header.frame_id = self.frame_id
            
            # Publish
            self.publisher.publish(msg)
            
            # Update statistics
            self.frame_count += 1
            if self.frame_count % 30 == 0:
                self.get_logger().info(f'Published {self.frame_count} frames')
        
        except Exception as e:
            self.get_logger().error(f'Error converting frame: {str(e)}')
    
    def destroy_node(self):
        """Cleanup"""
        self.get_logger().info('Shutting down camera node...')
        if hasattr(self, 'cap'):
            self.cap.release()
        super().destroy_node()


def main(args=None):
    """Main entry point"""
    rclpy.init(args=args)
    
    try:
        node = CameraNode()
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    except Exception as e:
        print(f'Error: {str(e)}')
    finally:
        if 'node' in locals():
            node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
