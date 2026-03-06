#!/usr/bin/env python3
"""
Detection Node for Inventory Management System
Runs YOLOv8 inference on camera images

Subscribes: /camera/image_raw (sensor_msgs/Image)
Publishes: 
  - /detections (ros2_inventory/msg/DetectionArray)
  - /annotated_image (sensor_msgs/Image)
"""

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from cv_bridge import CvBridge
import sys
from pathlib import Path

# Add parent directory to path to import inference module
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'src'))

from inference import InventoryDetector, Detection
from ros2_inventory.msg import Detection as ROS2Detection
from ros2_inventory.msg import DetectionArray
from rclpy.qos import QoSProfile, QoSReliabilityPolicy, QoSHistoryPolicy
import numpy as np
import time


class DetectionNode(Node):
    """YOLO detection node"""
    
    def __init__(self):
        super().__init__('detection_node')
        
        # Declare parameters
        self.declare_parameter('model_path', 'yolov8n.pt')
        self.declare_parameter('conf_threshold', 0.25)
        self.declare_parameter('iou_threshold', 0.45)
        self.declare_parameter('device', 'cpu')
        self.declare_parameter('input_topic', 'camera/image_raw')
        self.declare_parameter('output_topic', 'detections')
        self.declare_parameter('annotated_topic', 'annotated_image')
        self.declare_parameter('max_detections', 1000)
        
        # Get parameters
        model_path = self.get_parameter('model_path').get_parameter_value().string_value
        conf_threshold = self.get_parameter('conf_threshold').get_parameter_value().double_value
        iou_threshold = self.get_parameter('iou_threshold').get_parameter_value().double_value
        device = self.get_parameter('device').get_parameter_value().string_value
        input_topic = self.get_parameter('input_topic').get_parameter_value().string_value
        output_topic = self.get_parameter('output_topic').get_parameter_value().string_value
        annotated_topic = self.get_parameter('annotated_topic').get_parameter_value().string_value
        max_detections = self.get_parameter('max_detections').get_parameter_value().integer_value
        
        # Initialize detector
        self.get_logger().info(f'Loading YOLO model: {model_path}')
        try:
            self.detector = InventoryDetector(
                model_path=model_path,
                conf_threshold=conf_threshold,
                iou_threshold=iou_threshold,
                max_detections=max_detections,
                device=device
            )
            self.get_logger().info(f'Model loaded successfully on {device}')
        except Exception as e:
            self.get_logger().error(f'Failed to load model: {str(e)}')
            raise
        
        # Initialize CV bridge
        self.bridge = CvBridge()
        
        # Create subscriptions
        qos_profile = QoSProfile(
            reliability=QoSReliabilityPolicy.BEST_EFFORT,
            history=QoSHistoryPolicy.KEEP_LAST,
            depth=5
        )
        
        self.subscription = self.create_subscription(
            Image,
            input_topic,
            self.image_callback,
            qos_profile
        )
        
        # Create publishers
        self.detection_publisher = self.create_publisher(
            DetectionArray,
            output_topic,
            10
        )
        
        self.annotated_publisher = self.create_publisher(
            Image,
            annotated_topic,
            10
        )
        
        # Statistics
        self.frame_count = 0
        self.total_inference_time = 0.0
        self.get_logger().info(f'Detection node initialized. Subscribed to {input_topic}')
    
    def image_callback(self, msg: Image):
        """Process incoming image"""
        try:
            # Convert ROS2 Image to OpenCV format
            frame = self.bridge.imgmsg_to_cv2(msg, desired_encoding='rgb8')
            
            # Convert RGB to BGR for YOLO
            frame_bgr = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
            
            # Run detection
            start_time = time.time()
            detections, annotated_frame = self.detector.detect(frame_bgr)
            inference_time = (time.time() - start_time) * 1000  # ms
            
            # Update statistics
            self.frame_count += 1
            self.total_inference_time += inference_time
            
            if self.frame_count % 30 == 0:
                avg_time = self.total_inference_time / self.frame_count
                self.get_logger().info(
                    f'Processed {self.frame_count} frames, avg inference: {avg_time:.1f}ms '
                    f'({1000/avg_time:.1f} FPS)'
                )
            
            # Publish detections
            self.publish_detections(detections, inference_time, msg.header.stamp)
            
            # Publish annotated image
            self.publish_annotated_image(annotated_frame, msg.header.stamp)
        
        except Exception as e:
            self.get_logger().error(f'Error processing image: {str(e)}')
    
    def publish_detections(self, detections: list, inference_time: float, stamp):
        """Publish detection results"""
        try:
            msg = DetectionArray()
            msg.stamp = stamp
            msg.inference_time_ms = float(inference_time)
            msg.frame_count = self.frame_count
            
            for det in detections:
                ros_det = ROS2Detection()
                ros_det.class_id = int(det.class_id)
                ros_det.class_name = det.class_name
                ros_det.confidence = float(det.confidence)
                ros_det.x1 = float(det.bbox[0])
                ros_det.y1 = float(det.bbox[1])
                ros_det.x2 = float(det.bbox[2])
                ros_det.y2 = float(det.bbox[3])
                ros_det.center_x = float(det.center[0])
                ros_det.center_y = float(det.center[1])
                
                msg.detections.append(ros_det)
            
            self.detection_publisher.publish(msg)
        
        except Exception as e:
            self.get_logger().error(f'Error publishing detections: {str(e)}')
    
    def publish_annotated_image(self, frame: np.ndarray, stamp):
        """Publish annotated image"""
        try:
            # Convert BGR to RGB for ROS2
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # Convert to ROS2 Image message
            msg = self.bridge.cv2_to_imgmsg(frame_rgb, encoding='rgb8')
            msg.header.stamp = stamp
            msg.header.frame_id = 'detection_frame'
            
            self.annotated_publisher.publish(msg)
        
        except Exception as e:
            self.get_logger().error(f'Error publishing annotated image: {str(e)}')
    
    def destroy_node(self):
        """Cleanup"""
        self.get_logger().info('Shutting down detection node...')
        super().destroy_node()


def main(args=None):
    """Main entry point"""
    rclpy.init(args=args)
    
    try:
        node = DetectionNode()
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
