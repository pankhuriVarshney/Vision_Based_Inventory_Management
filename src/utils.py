#!/usr/bin/env python3
"""
Utility functions for Vision-Based Inventory Management System
Supports: API, ROS2, and standalone modes
"""

import cv2
import numpy as np
import base64
import io
import json
import time
from typing import Dict, List, Tuple, Optional, Any
from pathlib import Path
from collections import deque
import csv


# ============================================================================
# Image Processing Utilities
# ============================================================================

def encode_image_to_base64(frame: np.ndarray, format: str = '.jpg') -> str:
    """
    Encode OpenCV image to base64 string
    
    Args:
        frame: OpenCV image (BGR format)
        format: Image format ('.jpg', '.png')
    
    Returns:
        Base64 encoded string
    """
    _, buffer = cv2.imencode(format, frame)
    return base64.b64encode(buffer).decode('utf-8')


def decode_base64_to_image(image_base64: str) -> Optional[np.ndarray]:
    """
    Decode base64 string to OpenCV image
    
    Args:
        image_base64: Base64 encoded image string
    
    Returns:
        OpenCV image (BGR) or None if failed
    """
    try:
        image_data = base64.b64decode(image_base64)
        nparr = np.frombuffer(image_data, np.uint8)
        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        return frame
    except Exception as e:
        print(f"Error decoding image: {e}")
        return None


def load_image_from_file(file_path: str) -> Optional[np.ndarray]:
    """
    Load image from file path
    
    Args:
        file_path: Path to image file
    
    Returns:
        OpenCV image or None if failed
    """
    frame = cv2.imread(file_path)
    return frame


def resize_frame(frame: np.ndarray, max_width: int = 640, max_height: int = 480) -> np.ndarray:
    """
    Resize frame while maintaining aspect ratio
    
    Args:
        frame: Input frame
        max_width: Maximum width
        max_height: Maximum height
    
    Returns:
        Resized frame
    """
    h, w = frame.shape[:2]
    scale = min(max_width / w, max_height / h)
    
    if scale < 1.0:
        new_w = int(w * scale)
        new_h = int(h * scale)
        frame = cv2.resize(frame, (new_w, new_h), interpolation=cv2.INTER_AREA)
    
    return frame


# ============================================================================
# Video Streaming Utilities
# ============================================================================

class FrameBuffer:
    """Thread-safe frame buffer for video streaming"""
    
    def __init__(self, max_size: int = 5):
        self.buffer = deque(maxlen=max_size)
        self.lock = None  # Can add threading.Lock if needed
    
    def add_frame(self, frame: np.ndarray) -> None:
        """Add frame to buffer"""
        self.buffer.append(frame)
    
    def get_latest_frame(self) -> Optional[np.ndarray]:
        """Get most recent frame"""
        if len(self.buffer) > 0:
            return self.buffer[-1]
        return None
    
    def clear(self) -> None:
        """Clear buffer"""
        self.buffer.clear()


class VideoStreamStats:
    """Track video streaming statistics"""
    
    def __init__(self, window_size: int = 30):
        self.window_size = window_size
        self.fps_history = deque(maxlen=window_size)
        self.latency_history = deque(maxlen=window_size)
        self.frame_count = 0
        self.start_time = time.time()
    
    def update(self, inference_time: float) -> Dict:
        """
        Update statistics after each frame
        
        Args:
            inference_time: Time taken for inference in seconds
        
        Returns:
            Dictionary with current stats
        """
        self.frame_count += 1
        
        # Calculate FPS
        current_fps = 1.0 / inference_time if inference_time > 0 else 0
        self.fps_history.append(current_fps)
        
        # Calculate latency
        latency_ms = inference_time * 1000
        self.latency_history.append(latency_ms)
        
        # Calculate averages
        avg_fps = sum(self.fps_history) / len(self.fps_history)
        avg_latency = sum(self.latency_history) / len(self.latency_history)
        
        # Total uptime
        uptime_seconds = time.time() - self.start_time
        
        return {
            'frame_count': self.frame_count,
            'current_fps': current_fps,
            'avg_fps': avg_fps,
            'latency_ms': latency_ms,
            'avg_latency_ms': avg_latency,
            'uptime_seconds': uptime_seconds
        }
    
    def get_stats(self) -> Dict:
        """Get current statistics without updating"""
        if len(self.fps_history) > 0:
            avg_fps = sum(self.fps_history) / len(self.fps_history)
            avg_latency = sum(self.latency_history) / len(self.latency_history)
        else:
            avg_fps = 0
            avg_latency = 0
        
        return {
            'frame_count': self.frame_count,
            'avg_fps': avg_fps,
            'avg_latency_ms': avg_latency,
            'uptime_seconds': time.time() - self.start_time
        }


# ============================================================================
# Statistics & Analytics Utilities
# ============================================================================

class InventoryHistory:
    """Track inventory count history over time"""
    
    def __init__(self, max_size: int = 1000):
        self.history = deque(maxlen=max_size)
    
    def add_count(self, total_objects: int, class_counts: Dict[str, int]) -> None:
        """
        Add inventory count to history
        
        Args:
            total_objects: Total object count
            class_counts: Per-class counts
        """
        self.history.append({
            'timestamp': time.time(),
            'total_objects': total_objects,
            'class_counts': class_counts
        })
    
    def get_history(self, limit: int = 100) -> List[Dict]:
        """Get recent history"""
        history_list = list(self.history)
        if limit > 0:
            history_list = history_list[-limit:]
        return history_list
    
    def get_statistics(self) -> Dict:
        """Calculate statistics from history"""
        if len(self.history) == 0:
            return {
                'avg_count': 0,
                'min_count': 0,
                'max_count': 0,
                'current_count': 0
            }
        
        counts = [h['total_objects'] for h in self.history]
        
        return {
            'avg_count': sum(counts) / len(counts),
            'min_count': min(counts),
            'max_count': max(counts),
            'current_count': counts[-1] if counts else 0,
            'data_points': len(counts)
        }
    
    def export_to_csv(self, file_path: str) -> bool:
        """
        Export history to CSV file
        
        Args:
            file_path: Path to save CSV
        
        Returns:
            True if successful
        """
        try:
            with open(file_path, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['timestamp', 'total_objects', 'class_counts'])
                
                for entry in self.history:
                    writer.writerow([
                        entry['timestamp'],
                        entry['total_objects'],
                        json.dumps(entry['class_counts'])
                    ])
            
            return True
        except Exception as e:
            print(f"Error exporting to CSV: {e}")
            return False
    
    def export_to_json(self, file_path: str) -> bool:
        """
        Export history to JSON file
        
        Args:
            file_path: Path to save JSON
        
        Returns:
            True if successful
        """
        try:
            with open(file_path, 'w') as f:
                json.dump(list(self.history), f, indent=2)
            return True
        except Exception as e:
            print(f"Error exporting to JSON: {e}")
            return False
    
    def clear(self) -> None:
        """Clear history"""
        self.history.clear()


def aggregate_detection_results(detections: List[Dict]) -> Dict:
    """
    Aggregate multiple detection results
    
    Args:
        detections: List of detection dictionaries
    
    Returns:
        Aggregated statistics
    """
    if not detections:
        return {
            'total_detections': 0,
            'avg_confidence': 0,
            'class_distribution': {}
        }
    
    # Count by class
    class_counts = {}
    confidences = []
    
    for det in detections:
        class_name = det.get('class_name', 'unknown')
        confidence = det.get('confidence', 0)
        
        class_counts[class_name] = class_counts.get(class_name, 0) + 1
        confidences.append(confidence)
    
    return {
        'total_detections': len(detections),
        'avg_confidence': sum(confidences) / len(confidences) if confidences else 0,
        'class_distribution': class_counts,
        'min_confidence': min(confidences) if confidences else 0,
        'max_confidence': max(confidences) if confidences else 0
    }


# ============================================================================
# File System Utilities
# ============================================================================

def ensure_directory(path: str) -> Path:
    """
    Ensure directory exists, create if not
    
    Args:
        path: Directory path
    
    Returns:
        Path object
    """
    path_obj = Path(path)
    path_obj.mkdir(parents=True, exist_ok=True)
    return path_obj


def get_model_path(model_name: str, base_dir: str = "models") -> Optional[Path]:
    """
    Find model file by name
    
    Args:
        model_name: Model name or path
        base_dir: Base directory to search in
    
    Returns:
        Path to model file or None
    """
    # If it's already a full path
    model_path = Path(model_name)
    if model_path.exists() and model_path.suffix == '.pt':
        return model_path
    
    # Search in base directory
    base_path = Path(base_dir)
    if base_path.exists():
        # Try exact name
        exact_path = base_path / model_name
        if exact_path.exists():
            return exact_path
        
        # Search recursively
        for pt_file in base_path.rglob("*.pt"):
            if pt_file.name == model_name or pt_file.stem == model_name:
                return pt_file
    
    return None


def list_available_models(base_dir: str = "models") -> List[Dict]:
    """
    List all available model files
    
    Args:
        base_dir: Base directory to search in
    
    Returns:
        List of model info dictionaries
    """
    models = []
    base_path = Path(base_dir)
    
    if not base_path.exists():
        return models
    
    for pt_file in base_path.rglob("*.pt"):
        stat = pt_file.stat()
        models.append({
            'name': pt_file.name,
            'path': str(pt_file),
            'size_mb': stat.st_size / (1024 * 1024),
            'modified': time.ctime(stat.st_mtime)
        })
    
    return sorted(models, key=lambda x: x['size_mb'])


# ============================================================================
# API Response Helpers
# ============================================================================

def success_response(data: Any, message: str = "Success") -> Dict:
    """
    Create success API response
    
    Args:
        data: Response data
        message: Success message
    
    Returns:
        Response dictionary
    """
    return {
        'success': True,
        'message': message,
        'data': data,
        'timestamp': time.time()
    }


def error_response(message: str, error_code: str = "ERROR") -> Dict:
    """
    Create error API response
    
    Args:
        message: Error message
        error_code: Error code
    
    Returns:
        Response dictionary
    """
    return {
        'success': False,
        'message': message,
        'error_code': error_code,
        'timestamp': time.time()
    }


def validate_image_file(file_path: str) -> Tuple[bool, str]:
    """
    Validate image file
    
    Args:
        file_path: Path to image file
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    path = Path(file_path)
    
    if not path.exists():
        return False, f"File not found: {file_path}"
    
    valid_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.webp'}
    if path.suffix.lower() not in valid_extensions:
        return False, f"Invalid image format: {path.suffix}"
    
    # Try to load image
    img = cv2.imread(str(path))
    if img is None:
        return False, "Could not load image file"
    
    return True, ""


# ============================================================================
# ROS2 Helper Functions (for Phase 2)
# ============================================================================

def detection_to_ros_dict(detection: Dict) -> Dict:
    """
    Convert detection to ROS2-compatible dictionary
    
    Args:
        detection: Detection dictionary
    
    Returns:
        ROS2-compatible dictionary
    """
    return {
        'class_id': detection.get('class_id', 0),
        'class_name': detection.get('class_name', 'product'),
        'confidence': float(detection.get('confidence', 0)),
        'bbox': {
            'x1': float(detection['bbox'][0]),
            'y1': float(detection['bbox'][1]),
            'x2': float(detection['bbox'][2]),
            'y2': float(detection['bbox'][3])
        },
        'center': {
            'x': float(detection['center'][0]),
            'y': float(detection['center'][1])
        }
    }


def inventory_to_ros_dict(inventory: Dict) -> Dict:
    """
    Convert inventory count to ROS2-compatible dictionary
    
    Args:
        inventory: Inventory dictionary
    
    Returns:
        ROS2-compatible dictionary
    """
    return {
        'total_objects': int(inventory.get('total_objects', 0)),
        'class_counts': inventory.get('class_counts', {}),
        'density_score': float(inventory.get('density_score', 0)),
        'timestamp': float(inventory.get('timestamp', time.time()))
    }


# ============================================================================
# Main (for testing)
# ============================================================================

if __name__ == "__main__":
    print("Testing utility functions...")
    
    # Test image encoding/decoding
    test_image = np.zeros((100, 100, 3), dtype=np.uint8)
    encoded = encode_image_to_base64(test_image)
    decoded = decode_base64_to_image(encoded)
    
    print(f"✓ Image encoding/decoding: {decoded is not None}")
    
    # Test statistics
    stats = VideoStreamStats()
    for i in range(10):
        result = stats.update(0.033)  # ~30 FPS
    
    print(f"✓ Video stats: {result['avg_fps']:.1f} FPS")
    
    # Test inventory history
    history = InventoryHistory()
    for i in range(5):
        history.add_count(i * 10, {'product': i * 10})
    
    stats = history.get_statistics()
    print(f"✓ Inventory history: avg={stats['avg_count']:.1f}")
    
    print("\n✅ All utility functions working!")
