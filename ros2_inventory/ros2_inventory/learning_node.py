#!/usr/bin/env python3
"""
ROS2 Continual Learning Node
Monitors detections, manages experience buffer, triggers learning
"""

import rclpy
from rclpy.node import Node
from std_msgs.msg import String, Float32, Bool
from ros2_inventory.msg import DetectionArray, InventoryCount
import json
import numpy as np
from collections import deque
import time
import threading

# Import continual learning module
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / 'src'))
from continual_learning import ContinualLearner

class LearningNode(Node):
    """ROS2 Node for continual learning"""
    
    def __init__(self):
        super().__init__('learning_node')
        
        # Parameters
        self.declare_parameter('buffer_size', 500)
        self.declare_parameter('learning_interval', 60)  # seconds
        self.declare_parameter('conf_threshold', 0.6)
        self.declare_parameter('auto_learn', True)
        
        buffer_size = self.get_parameter('buffer_size').value
        self.learning_interval = self.get_parameter('learning_interval').value
        self.conf_threshold = self.get_parameter('conf_threshold').value
        self.auto_learn = self.get_parameter('auto_learn').value
        
        # Initialize continual learner
        self.learner = ContinualLearner(buffer_size=buffer_size)
        
        # Subscribers
        self.detection_sub = self.create_subscription(
            DetectionArray,
            '/detections',
            self.detection_callback,
            10
        )
        
        self.inventory_sub = self.create_subscription(
            InventoryCount,
            '/inventory_status',
            self.inventory_callback,
            10
        )
        
        self.trigger_sub = self.create_subscription(
            Bool,
            '/learning/trigger',
            self.trigger_callback,
            10
        )
        
        # Publishers
        self.status_pub = self.create_publisher(String, '/learning/status', 10)
        self.stats_pub = self.create_publisher(String, '/learning/stats', 10)
        
        # Timer for periodic learning check
        self.check_timer = self.create_timer(10.0, self.check_learning)
        
        # Statistics
        self.detection_count = 0
        self.last_detection_time = time.time()
        
        self.get_logger().info('✅ Continual Learning Node initialized')
        self.get_logger().info(f'   Buffer size: {buffer_size}')
        self.get_logger().info(f'   Learning interval: {self.learning_interval}s')
        self.get_logger().info(f'   Confidence threshold: {self.conf_threshold}')
    
    def detection_callback(self, msg: DetectionArray):
        """Process detection messages and add to experience buffer"""
        self.detection_count += 1
        self.last_detection_time = time.time()
        
        # Convert ROS detections to dict format
        detections = []
        for det in msg.detections:
            detections.append({
                'bbox': [det.x1, det.y1, det.x2, det.y2],
                'confidence': det.confidence,
                'class_id': det.class_id,
                'class_name': det.class_name,
                'center': [det.center_x, det.center_y]
            })
        
        # Calculate average confidence
        if detections:
            avg_conf = np.mean([d['confidence'] for d in detections])
        else:
            avg_conf = 0.0
        
        # Add to experience buffer
        self.learner.add_experience(detections, avg_conf)
        
        # Log occasionally
        if self.detection_count % 50 == 0:
            stats = self.learner.get_stats()
            self.get_logger().info(
                f'📊 Buffer: {stats["buffer"]["size"]}/{stats["buffer"]["max_size"]}, '
                f'AvgConf: {stats["buffer"]["avg_confidence"]:.2f}'
            )
    
    def inventory_callback(self, msg: InventoryCount):
        """Monitor inventory for learning triggers"""
        # Could trigger learning based on inventory changes
        pass
    
    def trigger_callback(self, msg: Bool):
        """Manual learning trigger"""
        if msg.data:
            self.get_logger().info('🎯 Manual learning triggered')
            self.perform_learning()
    
    def check_learning(self):
        """Periodic check for learning conditions"""
        if not self.auto_learn:
            return
        
        # Check cooldown
        stats = self.learner.get_stats()
        
        # Check conditions
        should_learn, reason = self.learner.should_learn()
        
        if should_learn:
            self.get_logger().info(f'🎯 Auto-learning triggered: {reason}')
            self.perform_learning()
        else:
            # Publish status
            status_msg = String()
            status_msg.data = json.dumps({
                'status': 'monitoring',
                'reason': reason,
                'buffer_size': stats['buffer']['size'],
                'avg_confidence': stats['buffer']['avg_confidence']
            })
            self.status_pub.publish(status_msg)
    
    def perform_learning(self):
        """Execute learning step"""
        self.get_logger().info('🔄 Starting learning process...')
        
        # Publish learning start
        status_msg = String()
        status_msg.data = json.dumps({'status': 'learning_started'})
        self.status_pub.publish(status_msg)
        
        # Perform learning
        learning_stats = self.learner.learn()
        
        # Publish results
        if learning_stats.success:
            self.get_logger().info('✅ Learning completed successfully')
            status_msg.data = json.dumps({
                'status': 'learning_complete',
                'loss_before': learning_stats.loss_before,
                'loss_after': learning_stats.loss_after,
                'num_samples': learning_stats.num_samples
            })
        else:
            self.get_logger().warn('⚠️ Learning failed')
            status_msg.data = json.dumps({'status': 'learning_failed'})
        
        self.status_pub.publish(status_msg)
        
        # Publish stats
        self.publish_stats()
    
    def publish_stats(self):
        """Publish learning statistics"""
        stats = self.learner.get_stats()
        stats_msg = String()
        stats_msg.data = json.dumps({
            'buffer': stats['buffer'],
            'total_learning_events': stats['total_learning_events'],
            'last_learning_time': stats['last_learning_time']
        })
        self.stats_pub.publish(stats_msg)
    
    def destroy_node(self):
        """Save state before shutdown"""
        self.get_logger().info('💾 Saving continual learning state...')
        self.learner.save_state()
        super().destroy_node()

def main(args=None):
    rclpy.init(args=args)
    node = LearningNode()
    
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()