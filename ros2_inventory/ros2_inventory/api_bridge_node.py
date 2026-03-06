#!/usr/bin/env python3
"""
API Bridge Node for Inventory Management System
Bridges ROS2 topics with FastAPI backend via HTTP/WebSocket

Subscribes: 
  - /inventory_status (ros2_inventory/msg/InventoryCount)
  - /annotated_image (sensor_msgs/Image)
  - /detections (ros2_inventory/msg/DetectionArray)

Publishes: None (sends data to API via HTTP/WebSocket)
"""

import rclpy
from rclpy.node import Node
from ros2_inventory.msg import InventoryCount, DetectionArray
from sensor_msgs.msg import Image
from cv_bridge import CvBridge
import threading
import time
import json
import base64
import numpy as np

# Try to import httpx for async HTTP, fall back to requests
try:
    import httpx
    HAS_HTTPX = True
except ImportError:
    HAS_HTTPXX = False
    import requests


class APIBridgeNode(Node):
    """Bridge between ROS2 and FastAPI"""
    
    def __init__(self):
        super().__init__('api_bridge_node')
        
        # Declare parameters
        self.declare_parameter('api_host', '0.0.0.0')
        self.declare_parameter('api_port', 8000)
        self.declare_parameter('inventory_topic', 'inventory_status')
        self.declare_parameter('image_topic', 'annotated_image')
        self.declare_parameter('detection_topic', 'detections')
        self.declare_parameter('enable_cors', True)
        self.declare_parameter('api_base_url', 'http://localhost:8000')
        
        # Get parameters
        self.api_host = self.get_parameter('api_host').get_parameter_value().string_value
        self.api_port = self.get_parameter('api_port').get_parameter_value().integer_value
        inventory_topic = self.get_parameter('inventory_topic').get_parameter_value().string_value
        image_topic = self.get_parameter('image_topic').get_parameter_value().string_value
        detection_topic = self.get_parameter('detection_topic').get_parameter_value().string_value
        self.api_base_url = self.get_parameter('api_base_url').get_parameter_value().string_value
        
        # Initialize CV bridge
        self.bridge = CvBridge()
        
        # State
        self.latest_inventory = None
        self.latest_image = None
        self.latest_detections = None
        self.last_publish_time = 0
        
        # Create subscriptions
        self.create_subscription(
            InventoryCount,
            inventory_topic,
            self.inventory_callback,
            10
        )
        
        self.create_subscription(
            Image,
            image_topic,
            self.image_callback,
            5  # Lower QoS for images
        )
        
        self.create_subscription(
            DetectionArray,
            detection_topic,
            self.detection_callback,
            10
        )
        
        # Timer for periodic API updates (every 2 seconds)
        self.timer = self.create_timer(2.0, self.publish_to_api)
        
        # WebSocket thread
        self.ws_thread = None
        self.ws_running = False
        
        self.get_logger().info(f'API Bridge initialized. Publishing to {self.api_base_url}')
    
    def inventory_callback(self, msg: InventoryCount):
        """Store latest inventory data"""
        self.latest_inventory = {
            'total_objects': msg.total_objects,
            'class_names': msg.class_names,
            'class_counts': msg.class_counts,
            'density_score': msg.density_score,
            'shelf_capacity_percent': msg.shelf_capacity_percent,
            'status': msg.status,
            'timestamp': time.time()
        }
    
    def image_callback(self, msg: Image):
        """Store latest image"""
        try:
            # Convert to base64 for API
            frame = self.bridge.imgmsg_to_cv2(msg, desired_encoding='rgb8')
            _, buffer = cv2.imencode('.jpg', frame)
            image_base64 = base64.b64encode(buffer).decode('utf-8')
            
            self.latest_image = {
                'image_base64': image_base64,
                'timestamp': time.time(),
                'width': msg.width,
                'height': msg.height
            }
        except Exception as e:
            self.get_logger().error(f'Error processing image: {str(e)}')
    
    def detection_callback(self, msg: DetectionArray):
        """Store latest detections"""
        detections_list = []
        for det in msg.detections:
            detections_list.append({
                'class_id': det.class_id,
                'class_name': det.class_name,
                'confidence': det.confidence,
                'bbox': [det.x1, det.y1, det.x2, det.y2],
                'center': [det.center_x, det.center_y]
            })
        
        self.latest_detections = {
            'detections': detections_list,
            'inference_time_ms': msg.inference_time_ms,
            'frame_count': msg.frame_count,
            'timestamp': time.time()
        }
    
    def publish_to_api(self):
        """Publish latest data to FastAPI"""
        try:
            # Only publish if we have new data
            current_time = time.time()
            if current_time - self.last_publish_time < 1.0:
                return
            
            # Prepare payload
            payload = {
                'inventory': self.latest_inventory,
                'detections': self.latest_detections,
                'image': self.latest_image,
                'timestamp': current_time
            }
            
            # Send to API (using requests for simplicity)
            # In production, use async HTTP client
            api_url = f'{self.api_base_url}/api/ros2/data'
            
            # Note: This is a placeholder - actual implementation would need
            # the API endpoint to be created, or use WebSocket
            # For now, we'll just log the data
            if self.latest_inventory:
                self.get_logger().info(
                    f"Inventory: {self.latest_inventory['total_objects']} items, "
                    f"status: {self.latest_inventory['status']}"
                )
            
            self.last_publish_time = current_time
        
        except Exception as e:
            self.get_logger().error(f'Error publishing to API: {str(e)}')
    
    def start_websocket_client(self):
        """Start WebSocket client thread for real-time updates"""
        self.ws_running = True
        self.ws_thread = threading.Thread(target=self._websocket_loop, daemon=True)
        self.ws_thread.start()
    
    def _websocket_loop(self):
        """WebSocket client loop"""
        import websocket  # Requires websocket-client package
        
        ws_url = f"ws://{self.api_host}:{self.api_port}/ws/ros2"
        
        def on_message(ws, message):
            try:
                data = json.loads(message)
                self.get_logger().info(f"Received from API: {data.get('type', 'unknown')}")
            except Exception as e:
                self.get_logger().error(f"WebSocket message error: {str(e)}")
        
        def on_error(ws, error):
            self.get_logger().error(f"WebSocket error: {str(error)}")
        
        def on_close(ws, close_status_code, close_msg):
            self.get_logger().info("WebSocket connection closed")
        
        def on_open(ws):
            self.get_logger().info("WebSocket connection opened")
            
            def run():
                while self.ws_running:
                    # Send latest inventory data
                    if self.latest_inventory:
                        ws.send(json.dumps({
                            'type': 'inventory_update',
                            'data': self.latest_inventory
                        }))
                    time.sleep(1.0)
            
            thread = threading.Thread(target=run)
            thread.start()
        
        try:
            ws = websocket.WebSocketApp(
                ws_url,
                on_open=on_open,
                on_message=on_message,
                on_error=on_error,
                on_close=on_close
            )
            ws.run_forever()
        except Exception as e:
            self.get_logger().error(f"WebSocket error: {str(e)}")
    
    def destroy_node(self):
        """Cleanup"""
        self.get_logger().info('Shutting down API bridge node...')
        self.ws_running = False
        super().destroy_node()


def main(args=None):
    """Main entry point"""
    rclpy.init(args=args)
    
    try:
        node = APIBridgeNode()
        
        # Start WebSocket client in background
        # node.start_websocket_client()
        
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
