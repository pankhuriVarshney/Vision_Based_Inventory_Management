#!/home/sonik/Vision_Based_Inventory_Management/venv/bin/python
"""
Real-time Detection Node for Raspberry Pi 5
Optimized for 5-10 FPS using TFLite INT8
"""

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from cv_bridge import CvBridge
import sys
from pathlib import Path
import cv2
import time
import numpy as np
import threading

sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'src'))

from ros2_inventory.msg import Detection as ROS2Detection, DetectionArray

class RealTimeDetectionNode(Node):
    """Real-time detection node using optimized TFLite model"""
    
    def __init__(self):
        super().__init__('detection_node_realtime')
        
        # Parameters
        self.declare_parameter('model_path', '/home/sonik/Vision_Based_Inventory_Management/models/rpc_real_labels/weights/best_int8.tflite')
        self.declare_parameter('conf_threshold', 0.25)
        self.declare_parameter('input_topic', 'camera/image_raw')
        self.declare_parameter('output_topic', 'detections')
        self.declare_parameter('annotated_topic', 'annotated_image')
        
        model_path = self.get_parameter('model_path').get_parameter_value().string_value
        self.conf_threshold = self.get_parameter('conf_threshold').get_parameter_value().double_value
        input_topic = self.get_parameter('input_topic').get_parameter_value().string_value
        output_topic = self.get_parameter('output_topic').get_parameter_value().string_value
        annotated_topic = self.get_parameter('annotated_topic').get_parameter_value().string_value
        
        # Load TFLite model
        self.get_logger().info(f'Loading TFLite model: {model_path}')
        try:
            import tflite_runtime.interpreter as tflite
            self.interpreter = tflite.Interpreter(model_path=model_path)
            self.interpreter.allocate_tensors()
            
            # Get input/output details
            self.input_details = self.interpreter.get_input_details()
            self.output_details = self.interpreter.get_output_details()
            self.input_shape = self.input_details[0]['shape']
            self.input_height = self.input_shape[1]
            self.input_width = self.input_shape[2]
            
            self.get_logger().info(f'Model loaded - Input size: {self.input_width}x{self.input_height}')
        except Exception as e:
            self.get_logger().error(f'Failed to load TFLite model: {e}')
            self.get_logger().info('Falling back to PyTorch model...')
            from ultralytics import YOLO
            self.model = YOLO('/home/sonik/Vision_Based_Inventory_Management/models/rpc_real_labels/weights/best.pt')
            self.use_tflite = False
        else:
            self.use_tflite = True
        
        self.bridge = CvBridge()
        self.frame_count = 0
        self.fps = 0
        self.last_fps_time = time.time()
        
        # Class names mapping
        self.class_names = {
            0: 'chips_snacks', 1: 'chocolate', 2: 'candy', 3: 'desserts',
            4: 'soft_drink', 5: 'juice', 6: 'milk_dairy', 7: 'dried_food',
            8: 'canned_food', 9: 'seasoning', 10: 'tissue_paper', 11: 'stationary'
        }
        
        # QoS for low latency
        from rclpy.qos import QoSProfile, QoSReliabilityPolicy, QoSHistoryPolicy
        qos_profile = QoSProfile(
            reliability=QoSReliabilityPolicy.BEST_EFFORT,
            history=QoSHistoryPolicy.KEEP_LAST,
            depth=1
        )
        
        # Subscriber
        self.subscription = self.create_subscription(
            Image, input_topic, self.image_callback, qos_profile)
        
        # Publishers
        self.detection_pub = self.create_publisher(DetectionArray, output_topic, 10)
        self.annotated_pub = self.create_publisher(Image, annotated_topic, 10)
        
        self.get_logger().info('Real-time detection node ready!')
    
    def preprocess_tflite(self, frame):
        """Preprocess frame for TFLite model"""
        # Resize to model input size
        resized = cv2.resize(frame, (self.input_width, self.input_height))
        
        # Convert BGR to RGB if needed
        if self.input_details[0]['dtype'] == np.uint8:
            input_data = resized
        else:
            input_data = resized.astype(np.float32) / 255.0
        
        return np.expand_dims(input_data, axis=0)
    
    def parse_yolo_output(self, output, frame_shape):
        """Parse YOLO output to detections"""
        detections = []
        h, w = frame_shape[:2]
        
        # Simplified parsing - adjust based on your model's output format
        # This is a placeholder - you'll need to implement based on your model
        return detections
    
    def image_callback(self, msg):
        try:
            start_time = time.time()
            
            # Convert to OpenCV
            frame = self.bridge.imgmsg_to_cv2(msg, desired_encoding='bgr8')
            orig_h, orig_w = frame.shape[:2]
            
            if self.use_tflite:
                # TFLite inference
                input_data = self.preprocess_tflite(frame)
                self.interpreter.set_tensor(self.input_details[0]['index'], input_data)
                self.interpreter.invoke()
                output = self.interpreter.get_tensor(self.output_details[0]['index'])
                detections = self.parse_yolo_output(output, frame.shape)
            else:
                # PyTorch fallback
                small_frame = cv2.resize(frame, (320, 240))
                results = self.model(small_frame, conf=self.conf_threshold, verbose=False)[0]
                detections = []
                
                if results.boxes is not None:
                    boxes = results.boxes.xyxy.cpu().numpy()
                    confs = results.boxes.conf.cpu().numpy()
                    classes = results.boxes.cls.cpu().numpy().astype(int)
                    
                    scale_x = orig_w / 320
                    scale_y = orig_h / 240
                    
                    for box, conf, cls in zip(boxes, confs, classes):
                        if conf >= self.conf_threshold:
                            detections.append({
                                'bbox': [box[0]*scale_x, box[1]*scale_y, box[2]*scale_x, box[3]*scale_y],
                                'confidence': float(conf),
                                'class_id': int(cls),
                                'class_name': self.class_names.get(int(cls), f'class_{cls}'),
                                'center': [((box[0]+box[2])/2)*scale_x, ((box[1]+box[3])/2)*scale_y]
                            })
            
            # Draw detections on frame
            annotated = frame.copy()
            for det in detections:
                x1, y1, x2, y2 = [int(v) for v in det['bbox']]
                cv2.rectangle(annotated, (x1, y1), (x2, y2), (0, 255, 0), 2)
                label = f"{det['class_name']}: {det['confidence']:.2f}"
                cv2.putText(annotated, label, (x1, y1-5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
            
            # Calculate FPS
            inference_time = (time.time() - start_time) * 1000
            current_fps = 1000 / inference_time if inference_time > 0 else 0
            self.fps = self.fps * 0.9 + current_fps * 0.1
            
            self.frame_count += 1
            if self.frame_count % 30 == 0:
                self.get_logger().info(f'FPS: {self.fps:.1f}, Detections: {len(detections)}')
            
            # Publish
            self.publish_detections(detections, inference_time, msg.header.stamp)
            self.publish_annotated(annotated, msg.header.stamp)
            
        except Exception as e:
            self.get_logger().error(f'Error: {str(e)}')
    
    def publish_detections(self, detections, inference_time, stamp):
        """Publish detection results"""
        msg = DetectionArray()
        msg.stamp = stamp
        msg.inference_time_ms = float(inference_time)
        msg.frame_count = self.frame_count
        
        for det in detections:
            ros_det = ROS2Detection()
            ros_det.class_id = int(det['class_id'])
            ros_det.class_name = det['class_name']
            ros_det.confidence = float(det['confidence'])
            ros_det.x1 = float(det['bbox'][0])
            ros_det.y1 = float(det['bbox'][1])
            ros_det.x2 = float(det['bbox'][2])
            ros_det.y2 = float(det['bbox'][3])
            ros_det.center_x = float(det['center'][0])
            ros_det.center_y = float(det['center'][1])
            msg.detections.append(ros_det)
        
        self.detection_pub.publish(msg)
    
    def publish_annotated(self, frame, stamp):
        """Publish annotated image"""
        msg = self.bridge.cv2_to_imgmsg(frame, encoding='bgr8')
        msg.header.stamp = stamp
        self.annotated_pub.publish(msg)

def main(args=None):
    rclpy.init(args=args)
    node = RealTimeDetectionNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()