#!/usr/bin/env python3
"""
Camera Node for Inventory Management System - Raspberry Pi 5 Compatible
Supports: Pi Camera Module 3 + Pan-Tilt Mechanism
OS: Ubuntu 24.04 + ROS2 Jazzy
"""

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image, CameraInfo
from cv_bridge import CvBridge
import cv2
import numpy as np
from rclpy.qos import QoSProfile, QoSReliabilityPolicy, QoSHistoryPolicy
from geometry_msgs.msg import Point
import subprocess
import time
import threading

try:
    from picamera2 import Picamera2
    HAS_PICAMERA2 = True
except ImportError:
    HAS_PICAMERA2 = False

try:
    import RPi.GPIO as GPIO
    HAS_GPIO = True
except ImportError:
    HAS_GPIO = False


class CameraNode(Node):
    """Advanced camera node with pan-tilt tracking and multiple backend support"""
    
    def __init__(self):
        super().__init__('camera_node')
        
        # Declare parameters
        self.declare_parameter('width', 640)
        self.declare_parameter('height', 480)
        self.declare_parameter('fps', 30)
        self.declare_parameter('frame_id', 'camera_frame')
        self.declare_parameter('topic_name', 'camera/image_raw')
        self.declare_parameter('camera_info_topic', 'camera/camera_info')
        self.declare_parameter('use_picamera2', True)
        self.declare_parameter('use_libcamera', False)
        self.declare_parameter('enable_pan_tilt_tracking', True)
        self.declare_parameter('detection_input_topic', '/detections')
        
        # Get parameters
        self.width = self.get_parameter('width').get_parameter_value().integer_value
        self.height = self.get_parameter('height').get_parameter_value().integer_value
        self.fps = self.get_parameter('fps').get_parameter_value().integer_value
        self.frame_id = self.get_parameter('frame_id').get_parameter_value().string_value
        topic_name = self.get_parameter('topic_name').get_parameter_value().string_value
        camera_info_topic = self.get_parameter('camera_info_topic').get_parameter_value().string_value
        self.use_picamera2 = self.get_parameter('use_picamera2').get_parameter_value().bool_value
        self.use_libcamera = self.get_parameter('use_libcamera').get_parameter_value().bool_value
        self.enable_tracking = self.get_parameter('enable_pan_tilt_tracking').get_parameter_value().bool_value
        
        # Initialize camera
        self.picam2 = None
        self.cap = None
        self.bridge = CvBridge()
        
        # Pan-tilt state
        self.current_pan = 90.0
        self.current_tilt = 45.0
        self.target_pan = 90.0
        self.target_tilt = 45.0
        self.tracking_active = False
        self.last_detection_center = None
        
        # Initialize camera
        success = False
        if self.use_picamera2 and HAS_PICAMERA2:
            success = self._init_picamera2()
        elif self.use_libcamera:
            success = self._init_libcamera()
        
        if not success:
            success = self._init_standard_camera()
            
        if not success:
            raise RuntimeError('Failed to initialize any camera backend')
        
        # Publishers
        qos_profile = QoSProfile(
            reliability=QoSReliabilityPolicy.BEST_EFFORT,
            history=QoSHistoryPolicy.KEEP_LAST,
            depth=5
        )
        self.publisher = self.create_publisher(Image, topic_name, qos_profile)
        self.camera_info_pub = self.create_publisher(CameraInfo, camera_info_topic, 10)
        
        # Pan-tilt command publisher
        if self.enable_tracking:
            self.pan_tilt_pub = self.create_publisher(Point, 'pan_tilt/position_cmd', 10)
            # Subscribe to detections for tracking
            self.create_subscription(
                Point,  # Using Point for detection center (x, y in normalized coords)
                'detection_center',
                self.detection_center_callback,
                10
            )
        
        # Timers
        self.timer = self.create_timer(1.0 / self.fps, self.timer_callback)
        self.info_timer = self.create_timer(1.0, self.publish_camera_info)
        
        # Statistics
        self.frame_count = 0
        self.error_count = 0
        self.start_time = time.time()
        
        self.get_logger().info(f'Camera node ready: {self.width}x{self.height} @ {self.fps} FPS')
    
    def _init_picamera2(self) -> bool:
        """Initialize using picamera2 (recommended for Pi Camera on Ubuntu 24.04)"""
        try:
            self.get_logger().info('Initializing Pi Camera with picamera2...')
            self.picam2 = Picamera2()
            
            # Configure for preview with specific resolution
            camera_config = self.picam2.create_preview_configuration(
                main={"size": (self.width, self.height), "format": "RGB888"},
                controls={"FrameRate": self.fps}
            )
            self.picam2.configure(camera_config)
            self.picam2.start()
            
            # Wait for camera to warm up
            time.sleep(0.5)
            
            self.get_logger().info('Picamera2 initialized successfully')
            return True
            
        except Exception as e:
            self.get_logger().error(f'Picamera2 init failed: {str(e)}')
            return False
    
    def _init_libcamera(self) -> bool:
        """Initialize using libcamera via GStreamer"""
        try:
            self.get_logger().info('Initializing with libcamera GStreamer...')
            
            gst_pipeline = (
                f'libcamerasrc '
                f'! video/x-raw, width={self.width}, height={self.height}, format=RGBx '
                f'! videoconvert ! video/x-raw, format=BGR '
                f'! appsink drop=true max-buffers=1'
            )
            
            self.cap = cv2.VideoCapture(gst_pipeline, cv2.CAP_GSTREAMER)
            
            if self.cap.isOpened():
                self.get_logger().info('Libcamera GStreamer pipeline active')
                return True
            return False
            
        except Exception as e:
            self.get_logger().error(f'Libcamera init failed: {str(e)}')
            return False
    
    def _init_standard_camera(self) -> bool:
        """Fallback to standard V4L2"""
        self.get_logger().info('Trying standard V4L2 camera...')
        
        for backend in [cv2.CAP_V4L2, cv2.CAP_ANY]:
            self.cap = cv2.VideoCapture(0, backend)
            if self.cap.isOpened():
                self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
                self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
                self.cap.set(cv2.CAP_PROP_FPS, self.fps)
                self.get_logger().info(f'Standard camera opened with backend {backend}')
                return True
            self.cap.release()
        
        return False
    
    def detection_center_callback(self, msg: Point):
        """Receive detection center and update pan-tilt target for tracking"""
        if not self.enable_tracking:
            return
            
        # msg.x and msg.y are normalized (0-1) coordinates
        # Center is (0.5, 0.5)
        center_x, center_y = msg.x, msg.y
        
        # Calculate offset from center
        pan_error = (center_x - 0.5) * 60  # Scale to degrees
        tilt_error = (center_y - 0.5) * 45  # Scale to degrees
        
        # Update target (current position + error)
        self.target_pan = self.current_pan - pan_error  # Invert: object right -> pan right
        self.target_tilt = self.current_tilt + tilt_error
        
        # Clamp to limits
        self.target_pan = max(0, min(180, self.target_pan))
        self.target_tilt = max(0, min(90, self.target_tilt))
        
        # Publish command
        cmd = Point()
        cmd.x = self.target_pan
        cmd.y = self.target_tilt
        self.pan_tilt_pub.publish(cmd)
        
        self.tracking_active = True
        self.last_detection_center = (center_x, center_y)
    
    def timer_callback(self):
        """Capture and publish frame"""
        frame = None
        
        try:
            if self.picam2 is not None:
                # Picamera2 capture
                frame = self.picam2.capture_array()
                # Convert RGB to BGR for OpenCV consistency
                frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
            elif self.cap is not None:
                ret, frame = self.cap.read()
                if not ret:
                    self.error_count += 1
                    return
            else:
                return
            
            if frame is None:
                return
            
            # Ensure correct size
            if frame.shape[0] != self.height or frame.shape[1] != self.width:
                frame = cv2.resize(frame, (self.width, self.height))
            
            # Convert BGR to RGB for ROS
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # Create and publish Image message
            msg = self.bridge.cv2_to_imgmsg(frame_rgb, encoding='rgb8')
            msg.header.stamp = self.get_clock().now().to_msg()
            msg.header.frame_id = self.frame_id
            
            self.publisher.publish(msg)
            self.frame_count += 1
            
            # Log FPS every 30 frames
            if self.frame_count % 30 == 0:
                elapsed = time.time() - self.start_time
                fps = self.frame_count / elapsed
                self.get_logger().info(f'Published {self.frame_count} frames ({fps:.1f} FPS)')
                
        except Exception as e:
            self.error_count += 1
            if self.error_count % 10 == 0:
                self.get_logger().error(f'Capture error ({self.error_count}): {str(e)}')
    
    def publish_camera_info(self):
        """Publish CameraInfo message for calibration"""
        info = CameraInfo()
        info.header.stamp = self.get_clock().now().to_msg()
        info.header.frame_id = self.frame_id
        info.width = self.width
        info.height = self.height
        
        # Approximate focal length for 6mm lens on OV5647
        # fx = fy = focal_length * width / sensor_width
        # OV5647: 3.67mm x 2.74mm sensor, 6mm lens
        fx = fy = 6.0 * self.width / 3.67  # ~1046 for 640px width
        
        cx = self.width / 2.0
        cy = self.height / 2.0
        
        info.k = [fx, 0.0, cx, 0.0, fy, cy, 0.0, 0.0, 1.0]
        info.p = [fx, 0.0, cx, 0.0, 0.0, fy, cy, 0.0, 0.0, 0.0, 1.0, 0.0]
        info.distortion_model = 'plumb_bob'
        info.d = [0.0, 0.0, 0.0, 0.0, 0.0]  # No distortion assumed
        
        self.camera_info_pub.publish(info)
    
    def destroy_node(self):
        """Cleanup"""
        self.get_logger().info('Shutting down camera node...')
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