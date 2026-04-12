#!/usr/bin/env python3
"""
Inventory Node for Inventory Management System
Maintains inventory counts from detection results

Subscribes: /detections (ros2_inventory/msg/DetectionArray)
Publishes: /inventory_status (ros2_inventory/msg/InventoryCount)
"""

import rclpy
from rclpy.node import Node
from ros2_inventory.msg import DetectionArray, InventoryCount
from collections import defaultdict
import time


class InventoryNode(Node):
    """Inventory counting and analysis node"""
    
    def __init__(self):
        super().__init__('inventory_node')
        
        # Declare parameters
        self.declare_parameter('input_topic', 'detections')
        self.declare_parameter('output_topic', 'inventory_status')
        self.declare_parameter('grid_rows', 3)
        self.declare_parameter('grid_cols', 3)
        self.declare_parameter('low_stock_threshold', 5)
        self.declare_parameter('out_of_stock_threshold', 0)
        
        # Get parameters
        input_topic = self.get_parameter('input_topic').get_parameter_value().string_value
        output_topic = self.get_parameter('output_topic').get_parameter_value().string_value
        self.grid_rows = self.get_parameter('grid_rows').get_parameter_value().integer_value
        self.grid_cols = self.get_parameter('grid_cols').get_parameter_value().integer_value
        self.low_stock_threshold = self.get_parameter('low_stock_threshold').get_parameter_value().integer_value
        self.out_of_stock_threshold = self.get_parameter('out_of_stock_threshold').get_parameter_value().integer_value
        
        # Initialize inventory state
        self.current_count = 0
        self.class_counts = defaultdict(int)
        self.density_score = 0.0
        self.last_update_time = time.time()
        
        # Create subscription
        self.subscription = self.create_subscription(
            DetectionArray,
            input_topic,
            self.detection_callback,
            10
        )
        
        # Create publisher
        self.publisher = self.create_publisher(
            InventoryCount,
            output_topic,
            10
        )
        
        # Timer for periodic publishing (1 Hz)
        self.timer = self.create_timer(1.0, self.timer_callback)
        
        self.get_logger().info(f'Inventory node initialized. Subscribed to {input_topic}')
    
    def detection_callback(self, msg: DetectionArray):
        """Process detection results"""
        try:
            # Count detections by class
            self.class_counts.clear()
            
            for det in msg.detections:
                self.class_counts[det.class_name] += 1
            
            # Update total count
            self.current_count = len(msg.detections)
            
            # Calculate density score (simplified)
            # In a real system, this would use spatial information
            self.density_score = float(self.current_count) / (self.grid_rows * self.grid_cols)
            
            # Update timestamp
            self.last_update_time = time.time()
            
            # Log significant changes
            if self.current_count == 0:
                self.get_logger().warn('No products detected!')
            elif self.current_count < self.low_stock_threshold:
                self.get_logger().warn(f'Low stock alert: {self.current_count} items')
        
        except Exception as e:
            self.get_logger().error(f'Error processing detections: {str(e)}')
    
    def timer_callback(self):
        """Publish inventory status periodically"""
        try:
            # Determine stock status
            if self.current_count <= self.out_of_stock_threshold:
                status = 'out_of_stock'
            elif self.current_count <= self.low_stock_threshold:
                status = 'low_stock'
            else:
                status = 'normal'
            
            # Calculate shelf capacity percentage (assume max 100 items)
            shelf_capacity_percent = min(float(self.current_count) / 100.0 * 100.0, 100.0)
            
            # Create inventory message
            msg = InventoryCount()
            msg.total_objects = self.current_count
            msg.class_names = list(self.class_counts.keys())
            msg.class_counts = list(self.class_counts.values())
            msg.density_score = self.density_score
            msg.shelf_capacity_percent = shelf_capacity_percent
            msg.timestamp = self.get_clock().now().to_msg()
            msg.status = status
            
            # Publish
            self.publisher.publish(msg)
            
            # Log every 10 seconds
            if int(time.time()) % 10 == 0:
                self.get_logger().info(
                    f'Inventory: {self.current_count} items, '
                    f'density: {self.density_score:.2f}, '
                    f'status: {status}'
                )
        
        except Exception as e:
            self.get_logger().error(f'Error publishing inventory: {str(e)}')
    
    def get_inventory_summary(self) -> dict:
        """Get current inventory summary"""
        return {
            'total_objects': self.current_count,
            'class_counts': dict(self.class_counts),
            'density_score': self.density_score,
            'last_update': self.last_update_time
        }
    
    def destroy_node(self):
        """Cleanup"""
        self.get_logger().info('Shutting down inventory node...')
        super().destroy_node()


def main(args=None):
    """Main entry point"""
    rclpy.init(args=args)
    
    try:
        node = InventoryNode()
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
