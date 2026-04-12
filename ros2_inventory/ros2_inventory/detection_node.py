#!/usr/bin/env python3
"""
Detection Node with Pan-Tilt Tracking Support
Publishes detection centers for camera tracking
"""

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from cv_bridge import CvBridge
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'src'))

from inference import InventoryDetector
from ros2_inventory.msg import Detection as ROS2Detection, DetectionArray
from geometry_msgs.msg import Point
from rclpy.qos import QoSProfile, QoSReliabilityPolicy, QoSHistoryPolicy
import numpy as np
import time


class DetectionNode(Node):
    """YOLO detection node with tracking support"""
    
    def __init__(self):
        super().__init__('detection_node')
        
        # Parameters
        self.declare_parameter('model_path', 'yolov8n.pt')
        self.declare_parameter('conf_threshold', 0.25)
        self.declare_parameter('iou_threshold', 0.45)
        self.declare_parameter('device', 'cpu')
        self.declare_parameter('input_topic', 'camera/image_raw')
        self.declare_parameter('output_topic', 'detections')
        self.declare_parameter('annotated_topic', 'annotated_image')
        self.declare_parameter('center_topic', 'detection_center')
        self.declare_parameter('enable_tracking', True)
        self.declare_parameter('tracking_threshold', 0.7)
        
        model_path = self.get_parameter('model_path').get_parameter_value().string_value
        conf_threshold = self.get_parameter('conf_threshold').get_parameter_value().double_value
        iou_threshold = self.get_parameter('iou_threshold').get_parameter_value().double_value
        device = self.get_parameter('device').get_parameter_value().string_value
        input_topic = self.get_parameter('input_topic').get_parameter_value().string_value
        output_topic = self.get_parameter('output_topic').get_parameter_value().string_value
        annotated_topic = self.get_parameter('annotated_topic').get_parameter_value().string_value
        center_topic = self.get_parameter('center_topic').get_parameter_value().string_value
        self.enable_tracking = self.get_parameter('enable_tracking').get_parameter_value().bool_value
        self.tracking_threshold = self.get_parameter('tracking_threshold').get_parameter_value().double_value
        
        # Initialize detector
        self.get_logger().info(f'Loading YOLO model: {model_path}')
        try:
            self.detector = InventoryDetector(
                model_path=model_path,
                conf_threshold=conf_threshold,
                iou_threshold=iou_threshold,
                device=device
            )
            self.get_logger().info(f'Model loaded on {device}')
        except Exception as e:
            self.get_logger().error(f'Failed to load model: {str(e)}')
            raise
        
        self.bridge = CvBridge()
        
        # QoS
        qos_profile = QoSProfile(
            reliability=QoSReliabilityPolicy.BEST_EFFORT,
            history=QoSHistoryPolicy.KEEP_LAST,
            depth=5
        )
        
        # Subscribers and Publishers
        self.create_subscription(Image, input_topic, self.image_callback, qos_profile)
        self.detection_pub = self.create_publisher(DetectionArray, output_topic, 10)
        self.annotated_pub = self.create_publisher(Image, annotated_topic, 10)
        self.center_pub = self.create_publisher(Point, center_topic, 10)
        
        # Statistics
        self.frame_count = 0
        self.total_inference_time = 0.0
        
        self.get_logger().info('Detection node initialized')
    
    def image_callback(self, msg: Image):
        try:
            frame = self.bridge.imgmsg_to_cv2(msg, desired_encoding='rgb8')
            frame_bgr = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
            
            start_time = time.time()
            detections, annotated_frame = self.detector.detect(frame_bgr)
            inference_time = (time.time() - start_time) * 1000
            
            self.frame_count += 1
            self.total_inference_time += inference_time
            
            # Calculate center of all detections for tracking
            if self.enable_tracking and detections:
                self.publish_tracking_center(detections, frame.shape[1], frame.shape[0])
            
            # Publish results
            self.publish_detections(detections, inference_time, msg.header.stamp)
            self.publish_annotated_image(annotated_frame, msg.header.stamp)
            
            # Log stats
            if self.frame_count % 30 == 0:
                avg_time = self.total_inference_time / self.frame_count
                self.get_logger().info(
                    f'Processed {self.frame_count} frames, '
                    f'avg inference: {avg_time:.1f}ms ({1000/avg_time:.1f} FPS)'
                )
                
        except Exception as e:
            self.get_logger().error(f'Error processing image: {str(e)}')
    
    def publish_tracking_center(self, detections, frame_width, frame_height):
        """Calculate and publish center point for pan-tilt tracking"""
        if not detections:
            return
        
        # Use highest confidence detection or average of all
        best_det = max(detections, key=lambda d: d.confidence)
        
        if best_det.confidence < self.tracking_threshold:
            return
        
        # Get center in normalized coordinates (0-1)
        center_x = best_det.center[0] / frame_width
        center_y = best_det.center[1] / frame_height
        
        msg = Point()
        msg.x = center_x
        msg.y = center_y
        msg.z = best_det.confidence  # Use z for confidence
        
        self.center_pub.publish(msg)
    
    def publish_detections(self, detections, inference_time, stamp):
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
            
            self.detection_pub.publish(msg)
        except Exception as e:
            self.get_logger().error(f'Error publishing detections: {str(e)}')
    
    def publish_annotated_image(self, frame, stamp):
        try:
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            msg = self.bridge.cv2_to_imgmsg(frame_rgb, encoding='rgb8')
            msg.header.stamp = stamp
            msg.header.frame_id = 'detection_frame'
            self.annotated_pub.publish(msg)
        except Exception as e:
            self.get_logger().error(f'Error publishing image: {str(e)}')
    
    def destroy_node(self):
        self.get_logger().info('Shutting down detection node...')
        super().destroy_node()


def main(args=None):
    rclpy.init(args=args)
    node = DetectionNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()