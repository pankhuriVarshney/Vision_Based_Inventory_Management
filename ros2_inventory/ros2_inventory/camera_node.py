#!/usr/bin/env python3
"""
Camera Node for Inventory Management System - Proper ROS Publisher
"""

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image, CameraInfo
from cv_bridge import CvBridge
import cv2
import numpy as np
import time
import sys

try:
    from picamera2 import Picamera2
    HAS_PICAMERA2 = True
except ImportError:
    HAS_PICAMERA2 = False


class CameraNode(Node):
    """Camera node that publishes to ROS topics"""
    
    def __init__(self):
        super().__init__('camera_node')
        
        # Parameters
        self.declare_parameter('width', 640)
        self.declare_parameter('height', 480)
        self.declare_parameter('fps', 30)
        self.declare_parameter('frame_id', 'camera_frame')
        
        self.width = self.get_parameter('width').get_parameter_value().integer_value
        self.height = self.get_parameter('height').get_parameter_value().integer_value
        self.fps = self.get_parameter('fps').get_parameter_value().integer_value
        self.frame_id = self.get_parameter('frame_id').get_parameter_value().string_value
        
        # Initialize camera
        self.picam2 = None
        self.cap = None
        self.bridge = CvBridge()
        
        # Publishers - THIS IS WHAT WAS MISSING!
        self.publisher = self.create_publisher(Image, '/image_raw', 10)
        self.camera_info_pub = self.create_publisher(CameraInfo, '/camera_info', 10)
        
        # Initialize camera
        self._init_camera()
        
        # Timer for capturing
        self.timer = self.create_timer(1.0 / self.fps, self.timer_callback)
        
        self.frame_count = 0
        self.get_logger().info(f'Camera node ready: {self.width}x{self.height} @ {self.fps} FPS')
    
    def _init_camera(self):
        """Initialize camera (supports both Pi Camera and USB)"""
        if HAS_PICAMERA2:
            try:
                self.get_logger().info('Initializing Pi Camera with picamera2...')
                self.picam2 = Picamera2()
                config = self.picam2.create_preview_configuration(
                    main={"size": (self.width, self.height), "format": "RGB888"},
                    controls={"FrameRate": self.fps}
                )
                self.picam2.configure(config)
                self.picam2.start()
                time.sleep(0.5)
                self.get_logger().info('Pi Camera initialized')
                return
            except Exception as e:
                self.get_logger().error(f'Picamera2 failed: {e}')
        
        # Fallback to USB camera
        self.get_logger().info('Trying USB camera...')
        self.cap = cv2.VideoCapture(0)
        if self.cap.isOpened():
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
            self.cap.set(cv2.CAP_PROP_FPS, self.fps)
            self.get_logger().info('USB camera initialized')
        else:
            self.get_logger().error('No camera found!')
    
    def timer_callback(self):
        """Capture and publish frame"""
        frame = None
        
        if self.picam2:
            frame = self.picam2.capture_array()
            frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
        elif self.cap:
            ret, frame = self.cap.read()
            if not ret:
                return
        
        if frame is None:
            return
        
        # Resize if needed
        if frame.shape[1] != self.width or frame.shape[0] != self.height:
            frame = cv2.resize(frame, (self.width, self.height))
        
        # Convert to ROS Image message
        msg = self.bridge.cv2_to_imgmsg(frame, encoding='bgr8')
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.header.frame_id = self.frame_id
        
        # PUBLISH TO ROS TOPIC
        self.publisher.publish(msg)
        
        self.frame_count += 1
        if self.frame_count % 30 == 0:
            self.get_logger().info(f'Published {self.frame_count} frames')
    
    def destroy_node(self):
        if self.picam2:
            self.picam2.stop()
        if self.cap:
            self.cap.release()
        super().destroy_node()


def main(args=None):
    rclpy.init(args=args)
    node = CameraNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()