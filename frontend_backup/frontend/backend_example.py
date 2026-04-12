"""
Vision-Based Smart Inventory Management System - Backend Example
FastAPI WebSocket Server for Raspberry Pi

Usage:
    pip install fastapi uvicorn ultralytics opencv-python psutil
    python backend_example.py
    
    Access at: ws://localhost:8000/ws/detections
"""

import asyncio
import cv2
import json
import psutil
import time
from datetime import datetime
from fastapi import FastAPI, WebSocket
from fastapi.responses import HTMLResponse
from ultralytics import YOLO

# ============================================================================
# Configuration
# ============================================================================

MODEL_NAME = "yolov8n"  # nano, small, medium
CONFIDENCE_THRESHOLD = 0.5
CAMERA_SOURCE = 0  # 0 for webcam, or path to video file
FRAME_WIDTH = 640
FRAME_HEIGHT = 480
TARGET_FPS = 30

# ============================================================================
# Initialize
# ============================================================================

app = FastAPI(title="Smart Inventory Detection API")
model = YOLO(f"{MODEL_NAME}.pt")
uptime_start = time.time()
frame_count = 0

# Default YOLO class names (adjust based on your trained model)
CLASS_NAMES = {
    0: "Product",
    1: "Box",
    2: "Shelf",
    # Add more classes if using custom model
}

# ============================================================================
# Health Monitoring
# ============================================================================

def get_system_health():
    """Collect system metrics for dashboard"""
    try:
        cpu = psutil.cpu_percent(interval=0.05)
        memory = psutil.virtual_memory().percent
        uptime = int(time.time() - uptime_start)
        
        return {
            "cpu_usage": round(cpu, 1),
            "memory_usage": round(memory, 1),
            "connection_latency": 5,  # Approximate, measure actual roundtrip
            "uptime": uptime
        }
    except Exception as e:
        print(f"Error getting system health: {e}")
        return {
            "cpu_usage": 0,
            "memory_usage": 0,
            "connection_latency": 0,
            "uptime": int(time.time() - uptime_start)
        }

# ============================================================================
# Frame Processing
# ============================================================================

def process_frame(frame, frame_id):
    """
    Run YOLOv8 inference and format response for frontend
    
    Args:
        frame: OpenCV image (640x480)
        frame_id: Frame counter
        
    Returns:
        dict: Formatted detection data with inventory metrics
    """
    
    # Run YOLO inference
    results = model.predict(
        frame, 
        conf=CONFIDENCE_THRESHOLD,
        verbose=False
    )
    
    detections = []
    class_counts = {}
    
    h, w = frame.shape[:2]
    
    # Process each detection
    for result in results:
        for box in result.boxes:
            try:
                # Extract values
                confidence = float(box.conf[0])
                class_id = int(box.cls[0])
                
                # Get class name
                if class_id in CLASS_NAMES:
                    class_name = CLASS_NAMES[class_id]
                else:
                    class_name = result.names.get(class_id, f"Class_{class_id}")
                
                # Bounding box coordinates [x_min, y_min, x_max, y_max]
                bbox = box.xyxy[0].cpu().numpy().tolist()
                x_min, y_min, x_max, y_max = bbox
                
                # Center point
                center_x = (x_min + x_max) / 2
                center_y = (y_min + y_max) / 2
                
                # Add to detections
                detections.append({
                    "bbox": [float(x_min), float(y_min), float(x_max), float(y_max)],
                    "confidence": round(confidence, 3),
                    "class_id": class_id,
                    "class_name": class_name,
                    "center": [float(center_x), float(center_y)]
                })
                
                # Track class counts
                class_counts[class_name] = class_counts.get(class_name, 0) + 1
                
            except Exception as e:
                print(f"Error processing detection: {e}")
                continue
    
    # Calculate inventory metrics
    total_objects = len(detections)
    
    # Density score: 0-10 scale (adjust based on shelf capacity)
    # Assuming max 50 objects for full shelf
    density_score = min(10.0, (total_objects / 50) * 10)
    
    # Coverage ratio: percentage of shelf covered (0-1)
    # Adjust the divisor based on typical shelf capacity
    coverage_ratio = min(1.0, total_objects / 60)
    
    # Create 3x3 density heatmap
    density_map = [[0 for _ in range(3)] for _ in range(3)]
    
    for det in detections:
        center_x, center_y = det['center']
        
        # Map center coordinates to grid
        grid_x = int((center_x / w) * 3)
        grid_y = int((center_y / h) * 3)
        
        # Clamp to valid range
        grid_x = min(2, max(0, grid_x))
        grid_y = min(2, max(0, grid_y))
        
        density_map[grid_y][grid_x] += 1
    
    # Construct response
    response = {
        "frame_id": frame_id,
        "timestamp": int(time.time() * 1000),  # milliseconds
        "detections": detections,
        "inventory": {
            "total_objects": total_objects,
            "class_counts": class_counts,
            "density_score": round(density_score, 2),
            "coverage_ratio": round(coverage_ratio, 3)
        },
        "density_map": density_map,
        "system_health": get_system_health()
    }
    
    return response

# ============================================================================
# WebSocket Endpoint
# ============================================================================

@app.websocket("/ws/detections")
async def websocket_detections(websocket: WebSocket):
    """
    WebSocket endpoint for real-time object detection streaming
    
    Clients connect and receive continuous detection data at ~30 FPS
    """
    await websocket.accept()
    
    print("[WebSocket] Client connected")
    
    cap = cv2.VideoCapture(CAMERA_SOURCE)
    
    # Set camera properties
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, FRAME_WIDTH)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, FRAME_HEIGHT)
    cap.set(cv2.CAP_PROP_FPS, TARGET_FPS)
    
    frame_id = 0
    frame_time = 1.0 / TARGET_FPS
    
    try:
        while True:
            ret, frame = cap.read()
            
            if not ret:
                print("[Error] Failed to read frame from camera")
                await websocket.send_json({
                    "error": "Camera disconnected"
                })
                break
            
            # Ensure correct frame size
            if frame.shape[:2] != (FRAME_HEIGHT, FRAME_WIDTH):
                frame = cv2.resize(frame, (FRAME_WIDTH, FRAME_HEIGHT))
            
            # Process frame
            try:
                detection_data = process_frame(frame, frame_id)
                
                # Send to client
                await websocket.send_json(detection_data)
                
                frame_id += 1
                
                # Throttle to target FPS
                await asyncio.sleep(frame_time)
                
            except Exception as e:
                print(f"[Error] Processing error: {e}")
                await websocket.send_json({
                    "error": f"Processing error: {str(e)}"
                })
                break
    
    except Exception as e:
        print(f"[WebSocket Error] {e}")
    
    finally:
        cap.release()
        print("[WebSocket] Client disconnected")

# ============================================================================
# Health Check Endpoint
# ============================================================================

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "ok",
        "model": MODEL_NAME,
        "frames_processed": frame_count,
        "uptime_seconds": int(time.time() - uptime_start),
        **get_system_health()
    }

# ============================================================================
# Info Endpoint
# ============================================================================

@app.get("/info")
async def info():
    """System information"""
    return {
        "name": "Smart Inventory Detection System",
        "version": "1.0.0",
        "model": MODEL_NAME,
        "confidence_threshold": CONFIDENCE_THRESHOLD,
        "frame_resolution": [FRAME_WIDTH, FRAME_HEIGHT],
        "target_fps": TARGET_FPS,
        "available_classes": CLASS_NAMES,
        "websocket_url": "ws://localhost:8000/ws/detections"
    }

# ============================================================================
# Main
# ============================================================================

if __name__ == "__main__":
    print("=" * 70)
    print("Smart Inventory Detection System - Backend Server")
    print("=" * 70)
    print(f"Model: {MODEL_NAME}")
    print(f"Confidence Threshold: {CONFIDENCE_THRESHOLD}")
    print(f"Frame Size: {FRAME_WIDTH}x{FRAME_HEIGHT}")
    print(f"Target FPS: {TARGET_FPS}")
    print(f"WebSocket URL: ws://0.0.0.0:8000/ws/detections")
    print(f"Health Check: http://0.0.0.0:8000/health")
    print("=" * 70)
    print()
    
    # Run server
    import uvicorn
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )
