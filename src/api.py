# src/api.py - Updated with proper video streaming

from fastapi import FastAPI, File, UploadFile, HTTPException, WebSocket, WebSocketDisconnect, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from typing import Optional, Dict, Any
import cv2
import numpy as np
import base64
import asyncio
import json
import time
from datetime import datetime
import threading
from collections import deque

from .inference import InventoryDetector

app = FastAPI(title="Vision-Based Inventory Management API", version="1.0.0")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global variables
detector = None
video_thread = None
video_running = False
video_clients: list[WebSocket] = []
video_frame = None
frame_lock = threading.Lock()

# Store last frame for WebSocket clients
last_frame_data = None
last_detections = []
last_inventory = None

# Video capture
cap = None
camera_source = None

# Statistics
stats = {
    "fps": 0,
    "frame_count": 0,
    "last_fps_update": time.time(),
    "fps_samples": deque(maxlen=30),
    "total_inference_time": 0,
    "avg_inference_time": 0,
}

@app.on_event("startup")
async def startup_event():
    global detector
    try:
        detector = InventoryDetector(model_path="yolov8n.pt", device="cpu")
        print("✅ Model loaded successfully")
    except Exception as e:
        print(f"❌ Failed to load model: {e}")
        detector = None

@app.on_event("shutdown")
async def shutdown_event():
    global video_running, cap
    video_running = False
    if cap:
        cap.release()

# ========================================================================
# REST API Endpoints
# ========================================================================

@app.get("/")
async def root():
    return {
        "success": True,
        "message": "API is running",
        "data": {
            "name": "Vision-Based Inventory Management API",
            "version": "1.0.0",
            "status": "running"
        },
        "timestamp": time.time()
    }

@app.get("/api/health")
async def health_check():
    return {
        "success": True,
        "data": {
            "status": "healthy" if detector else "no_model",
            "detector_loaded": detector is not None,
            "camera_active": video_running,
            "websocket_clients": len(video_clients)
        }
    }

@app.get("/api/inventory/count")
async def get_inventory_count():
    global last_inventory
    if last_inventory:
        return {
            "success": True,
            "data": {
                "current": {
                    "avg_count": last_inventory.get("total_objects", 0),
                    "min_count": 0,
                    "max_count": 100,
                    "current_count": last_inventory.get("total_objects", 0),
                    "data_points": stats["frame_count"]
                }
            }
        }
    return {
        "success": True,
        "data": {
            "current": {
                "avg_count": 0,
                "min_count": 0,
                "max_count": 100,
                "current_count": 0,
                "data_points": 0
            }
        }
    }

@app.post("/api/video/start")
async def start_video(source: str = "0"):
    global cap, video_running, video_thread, camera_source
    
    if video_running:
        return {"active": True, "source": camera_source}
    
    camera_source = source
    
    # Open camera
    try:
        if source.isdigit():
            cap = cv2.VideoCapture(int(source))
        else:
            cap = cv2.VideoCapture(source)
        
        if not cap.isOpened():
            raise HTTPException(status_code=400, detail="Cannot open camera")
        
        # Set resolution
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        cap.set(cv2.CAP_PROP_FPS, 30)
        
        video_running = True
        video_thread = threading.Thread(target=process_video_stream, daemon=True)
        video_thread.start()
        
        return {"active": True, "source": source}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/video/stop")
async def stop_video():
    global video_running, cap
    video_running = False
    if cap:
        cap.release()
        cap = None
    return {"active": False}

@app.get("/api/video/status")
async def video_status():
    return {
        "success": True,
        "data": {
            "active": video_running,
            "clients": len(video_clients),
            "stats": {
                "avg_fps": stats["fps"],
                "avg_latency_ms": stats["avg_inference_time"]
            }
        }
    }

# ========================================================================
# Video Processing Function
# ========================================================================

def process_video_stream():
    global stats, last_frame_data, last_detections, last_inventory, video_frame
    
    frame_count = 0
    fps_update_counter = 0
    last_time = time.time()
    
    while video_running and cap and cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            print("Failed to read frame")
            time.sleep(0.01)
            continue
        
        frame_count += 1
        fps_update_counter += 1
        
        # Update FPS every 30 frames
        if fps_update_counter >= 30:
            current_time = time.time()
            elapsed = current_time - last_time
            if elapsed > 0:
                stats["fps"] = fps_update_counter / elapsed
                stats["fps_samples"].append(stats["fps"])
                stats["fps"] = sum(stats["fps_samples"]) / len(stats["fps_samples"])
            last_time = current_time
            fps_update_counter = 0
        
        # Run detection
        inference_start = time.time()
        if detector:
            try:
                detections, annotated_frame = detector.detect(frame)
                inference_time = (time.time() - inference_start) * 1000
                stats["total_inference_time"] += inference_time
                stats["avg_inference_time"] = stats["total_inference_time"] / frame_count if frame_count > 0 else 0
                
                # Update inventory
                total_objects = len(detections)
                class_counts = {}
                for det in detections:
                    class_counts[det.class_name] = class_counts.get(det.class_name, 0) + 1
                
                density_score = total_objects / 9.0  # Simple density calculation
                
                last_inventory = {
                    "total_objects": total_objects,
                    "class_counts": class_counts,
                    "density_score": min(density_score, 10.0),
                    "timestamp": time.time()
                }
                
                last_detections = [
                    {
                        "bbox": det.bbox,
                        "confidence": det.confidence,
                        "class_id": det.class_id,
                        "class_name": det.class_name,
                        "center": det.center
                    }
                    for det in detections
                ]
                
                # Encode frame to base64
                _, buffer = cv2.imencode('.jpg', annotated_frame)
                frame_base64 = base64.b64encode(buffer).decode('utf-8')
                
                last_frame_data = {
                    "success": True,
                    "frame": frame_base64,
                    "detections": last_detections,
                    "inventory": last_inventory,
                    "stats": {
                        "fps": stats["fps"],
                        "latency_ms": inference_time,
                        "frame_count": frame_count
                    }
                }
                
                # Broadcast to all WebSocket clients
                asyncio.run(broadcast_to_clients(last_frame_data))
                
            except Exception as e:
                print(f"Detection error: {e}")
        else:
            # No detector, just send raw frame
            _, buffer = cv2.imencode('.jpg', frame)
            frame_base64 = base64.b64encode(buffer).decode('utf-8')
            last_frame_data = {
                "success": True,
                "frame": frame_base64,
                "detections": [],
                "inventory": {"total_objects": 0, "class_counts": {}, "density_score": 0},
                "stats": {
                    "fps": stats["fps"],
                    "latency_ms": 0,
                    "frame_count": frame_count
                }
            }
            asyncio.run(broadcast_to_clients(last_frame_data))
        
        # Small delay to control frame rate
        time.sleep(0.01)
    
    print("Video processing stopped")

async def broadcast_to_clients(data):
    """Broadcast frame to all connected WebSocket clients"""
    global video_clients
    disconnected = []
    
    for client in video_clients:
        try:
            await client.send_json(data)
        except:
            disconnected.append(client)
    
    # Remove disconnected clients
    for client in disconnected:
        if client in video_clients:
            video_clients.remove(client)

# ========================================================================
# WebSocket Endpoints
# ========================================================================

@app.websocket("/ws/video")
async def video_websocket(websocket: WebSocket):
    global video_clients
    
    await websocket.accept()
    video_clients.append(websocket)
    print(f"📹 Video WebSocket connected. Total clients: {len(video_clients)}")
    
    try:
        # Send initial frame if available
        if last_frame_data:
            await websocket.send_json(last_frame_data)
        
        # Keep connection alive and listen for messages
        while True:
            # Receive messages (like source configuration)
            data = await websocket.receive_text()
            try:
                msg = json.loads(data)
                if "source" in msg:
                    print(f"Client requested source: {msg['source']}")
                    # Start video if not already running
                    if not video_running:
                        await start_video(msg['source'])
            except:
                pass
            
    except WebSocketDisconnect:
        video_clients.remove(websocket)
        print(f"📹 Client removed. Remaining: {len(video_clients)}")
    except Exception as e:
        print(f"WebSocket error: {e}")
        if websocket in video_clients:
            video_clients.remove(websocket)

@app.websocket("/ws/inventory")
async def inventory_websocket(websocket: WebSocket):
    await websocket.accept()
    print("📊 Inventory WebSocket connected")
    
    try:
        while True:
            # Send inventory updates every second
            if last_inventory:
                await websocket.send_json({
                    "success": True,
                    "inventory": last_inventory,
                    "timestamp": time.time()
                })
            await asyncio.sleep(1)
    except WebSocketDisconnect:
        print("Inventory WebSocket disconnected")
    except Exception as e:
        print(f"Inventory WebSocket error: {e}")

# ========================================================================
# Image Detection Endpoints
# ========================================================================

@app.post("/api/detect/image")
async def detect_image(file: UploadFile = File(...)):
    if not detector:
        raise HTTPException(status_code=503, detail="Detector not loaded")
    
    # Read image
    contents = await file.read()
    nparr = np.frombuffer(contents, np.uint8)
    frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    
    if frame is None:
        raise HTTPException(status_code=400, detail="Invalid image")
    
    # Run detection
    detections, annotated_frame = detector.detect(frame)
    
    # Encode result
    _, buffer = cv2.imencode('.jpg', annotated_frame)
    annotated_base64 = base64.b64encode(buffer).decode('utf-8')
    
    # Prepare response
    detections_list = [
        {
            "bbox": det.bbox,
            "confidence": det.confidence,
            "class_id": det.class_id,
            "class_name": det.class_name,
            "center": det.center
        }
        for det in detections
    ]
    
    total_objects = len(detections)
    class_counts = {}
    for det in detections:
        class_counts[det.class_name] = class_counts.get(det.class_name, 0) + 1
    
    return {
        "success": True,
        "detections": detections_list,
        "inventory": {
            "total_objects": total_objects,
            "class_counts": class_counts,
            "density_score": total_objects / 9.0,
            "timestamp": time.time()
        },
        "metadata": {
            "image_shape": [frame.shape[0], frame.shape[1]],
            "inference_time_ms": 0,
            "fps": 0,
            "model_info": {"name": "yolov8n.pt", "device": "cpu"}
        },
        "annotated_image_base64": annotated_base64
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)