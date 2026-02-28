#!/usr/bin/env python3
"""
Real-time Inference Engine for Retail Inventory Detection
Features: Object detection, tracking, counting, and analytics
"""

import cv2
import numpy as np
import torch
from ultralytics import YOLO
from collections import defaultdict, deque
from dataclasses import dataclass
from typing import List, Dict, Tuple, Optional
import time
from pathlib import Path

@dataclass
class Detection:
    """Single detection result"""
    bbox: np.ndarray  # [x1, y1, x2, y2]
    confidence: float
    class_id: int
    class_name: str
    center: Tuple[float, float]
    
@dataclass
class InventoryCount:
    """Inventory counting result"""
    total_objects: int
    class_counts: Dict[str, int]
    density_score: float  # Objects per area
    timestamp: float

class ShelfAnalyzer:
    """Analyzes shelf density and arrangement"""
    
    def __init__(self, grid_size=(3, 3)):
        self.grid_size = grid_size
        
    def analyze_density(self, detections: List[Detection], frame_shape: Tuple[int, ...]) -> Dict:
        """Analyze spatial density of products"""
        h, w = frame_shape[:2]
        grid_h, grid_w = self.grid_size
        
        cell_h, cell_w = h // grid_h, w // grid_w
        density_map = np.zeros(self.grid_size)
        
        for det in detections:
            cx, cy = int(det.center[0]), int(det.center[1])
            grid_x = min(cx // cell_w, grid_w - 1)
            grid_y = min(cy // cell_h, grid_h - 1)
            density_map[grid_y, grid_x] += 1
            
        return {
            'density_map': density_map,
            'max_density_cell': np.unravel_index(np.argmax(density_map), density_map.shape),
            'avg_density': len(detections) / (grid_h * grid_w),
            'total_area': h * w,
            'coverage_ratio': sum([((d.bbox[2]-d.bbox[0]) * (d.bbox[3]-d.bbox[1])) for d in detections]) / (h * w)
        }

class InventoryDetector:
    """
    Main detection class with tracking and counting capabilities
    """
    
    def __init__(
        self,
        model_path: str = "yolov8n.pt",
        conf_threshold: float = 0.25,
        iou_threshold: float = 0.45,
        max_detections: int = 1000,
        device: str = None,
        track: bool = True
    ):
        self.conf_threshold = conf_threshold
        self.iou_threshold = iou_threshold
        self.max_detections = max_detections
        self.track = track
        
        # Load model
        self.device = device or ('cuda' if torch.cuda.is_available() else 'cpu')
        print(f"Loading model from {model_path} on {self.device}...")
        self.model = YOLO(model_path)
        self.model.to(self.device)
        
        # Initialize tracker if needed
        self.track_history = defaultdict(lambda: deque(maxlen=30))
        self.shelf_analyzer = ShelfAnalyzer()
        
        # Counting statistics
        self.frame_count = 0
        self.detection_history = []
        
    def detect(self, frame: np.ndarray) -> Tuple[List[Detection], np.ndarray]:
        """
        Run detection on a single frame
        
        Returns:
            detections: List of Detection objects
            annotated_frame: Frame with visualizations
        """
        # Run inference
        results = self.model(
            frame,
            conf=self.conf_threshold,
            iou=self.iou_threshold,
            max_det=self.max_detections,
            verbose=False,
            device=self.device
        )[0]
        
        detections = []
        annotated_frame = frame.copy()
        
        # Process detections
        if results.boxes is not None:
            boxes = results.boxes.xyxy.cpu().numpy()
            confs = results.boxes.conf.cpu().numpy()
            classes = results.boxes.cls.cpu().numpy().astype(int)
            
            # Get class names (SKU-110K is single class)
            names = results.names if hasattr(results, 'names') else {0: 'product'}
            
            for i, (box, conf, cls) in enumerate(zip(boxes, confs, classes)):
                x1, y1, x2, y2 = box
                center = ((x1 + x2) / 2, (y1 + y2) / 2)
                
                det = Detection(
                    bbox=box,
                    confidence=float(conf),
                    class_id=int(cls),
                    class_name=names.get(int(cls), 'product'),
                    center=center
                )
                detections.append(det)
                
                # Draw bounding box
                color = (0, 255, 0)  # Green for products
                cv2.rectangle(annotated_frame, (int(x1), int(y1)), (int(x2), int(y2)), color, 2)
                
                # Draw label
                label = f"{det.class_name}: {conf:.2f}"
                (tw, th), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 1)
                cv2.rectangle(annotated_frame, (int(x1), int(y1)-20), (int(x1)+tw, int(y1)), color, -1)
                cv2.putText(annotated_frame, label, (int(x1), int(y1)-5), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 1)
        
        self.frame_count += 1
        return detections, annotated_frame
    
    def count_inventory(self, detections: List[Detection], frame_shape: Tuple[int, ...]) -> InventoryCount:
        """Generate inventory count from detections"""
        class_counts = defaultdict(int)
        
        for det in detections:
            class_counts[det.class_name] += 1
        
        # Calculate density
        analysis = self.shelf_analyzer.analyze_density(detections, frame_shape)
        
        return InventoryCount(
            total_objects=len(detections),
            class_counts=dict(class_counts),
            density_score=analysis['avg_density'],
            timestamp=time.time()
        )
    
    def process_video(
        self,
        source: str,
        output_path: Optional[str] = None,
        display: bool = True,
        save_stats: bool = True
    ):
        """
        Process video stream or file
        
        Args:
            source: Video file path, RTSP URL, or camera index (0, 1, etc.)
            output_path: Path to save output video
            display: Whether to show live display
            save_stats: Whether to save statistics to file
        """
        # Open video source
        if source.isdigit():
            source = int(source)
        
        cap = cv2.VideoCapture(source)
        if not cap.isOpened():
            raise ValueError(f"Cannot open video source: {source}")
        
        # Get video properties
        fps = int(cap.get(cv2.CAP_PROP_FPS)) or 30
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        
        # Setup video writer if output path specified
        writer = None
        if output_path:
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            writer = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
        
        # Statistics storage
        stats = []
        fps_history = deque(maxlen=30)
        
        print(f"Processing video... Press 'q' to quit")
        
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            start_time = time.time()
            
            # Detect objects
            detections, annotated_frame = self.detect(frame)
            
            # Count inventory
            inventory = self.count_inventory(detections, frame.shape)
            
            # Calculate FPS
            inference_time = time.time() - start_time
            current_fps = 1.0 / inference_time if inference_time > 0 else 0
            fps_history.append(current_fps)
            avg_fps = sum(fps_history) / len(fps_history)
            
            # Draw HUD (Heads Up Display)
            self._draw_hud(annotated_frame, inventory, avg_fps)
            
            # Save frame
            if writer:
                writer.write(annotated_frame)
            
            # Display
            if display:
                cv2.imshow('Retail Inventory Detection', annotated_frame)
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
            
            # Save stats
            if save_stats and self.frame_count % 10 == 0:  # Every 10 frames
                stats.append({
                    'frame': self.frame_count,
                    'timestamp': inventory.timestamp,
                    'total_count': inventory.total_objects,
                    'fps': avg_fps
                })
        
        # Cleanup
        cap.release()
        if writer:
            writer.release()
        cv2.destroyAllWindows()
        
        # Save statistics
        if save_stats and stats:
            import json
            stats_path = Path(output_path).parent / "stats.json" if output_path else "stats.json"
            with open(stats_path, 'w') as f:
                json.dump(stats, f, indent=2)
            print(f"Statistics saved to {stats_path}")
        
        print(f"Processing complete! Total frames: {self.frame_count}")
    
    def _draw_hud(self, frame: np.ndarray, inventory: InventoryCount, fps: float):
        """Draw heads-up display with inventory info"""
        h, w = frame.shape[:2]
        
        # Background panel
        overlay = frame.copy()
        cv2.rectangle(overlay, (10, 10), (350, 150), (0, 0, 0), -1)
        cv2.addWeighted(overlay, 0.6, frame, 0.4, 0, frame)
        
        # Text info
        y_offset = 40
        cv2.putText(frame, "📦 INVENTORY STATUS", (20, y_offset), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
        
        y_offset += 30
        cv2.putText(frame, f"Total Items: {inventory.total_objects}", (20, y_offset),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
        
        y_offset += 25
        cv2.putText(frame, f"Density Score: {inventory.density_score:.1f}", (20, y_offset),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
        
        y_offset += 25
        cv2.putText(frame, f"FPS: {fps:.1f}", (20, y_offset),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 1)

def main():
    import argparse
    parser = argparse.ArgumentParser(description='Retail Inventory Detection')
    parser.add_argument('--source', default='0', help='Video source (0 for webcam, or path/URL)')
    parser.add_argument('--model', default='yolov8n.pt', help='Model path')
    parser.add_argument('--output', default=None, help='Output video path')
    parser.add_argument('--conf', type=float, default=0.25, help='Confidence threshold')
    parser.add_argument('--no-display', action='store_true', help='Disable display')
    
    args = parser.parse_args()
    
    # Initialize detector
    detector = InventoryDetector(
        model_path=args.model,
        conf_threshold=args.conf
    )
    
    # Process video
    detector.process_video(
        source=args.source,
        output_path=args.output,
        display=not args.no_display
    )

if __name__ == "__main__":
    main()