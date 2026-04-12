#!/usr/bin/env python3
"""
FastAPI Backend for Vision-Based Inventory Management System
Provides REST API and WebSocket endpoints for:
- Image/video detection
- Real-time inventory monitoring
- Model management
- Data export

Usage:
    python api.py --host 0.0.0.0 --port 8000
    OR
    uvicorn src.api:app --reload --host 0.0.0.0 --port 8000
"""

import sys
import os
import time
import asyncio
import base64
from pathlib import Path
from typing import Dict, List, Optional, Any
from contextlib import asynccontextmanager

# FastAPI imports
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, UploadFile, File, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from inference import InventoryDetector, Detection, InventoryCount
from utils import (
    encode_image_to_base64,
    decode_base64_to_image,
    load_image_from_file,
    resize_frame,
    FrameBuffer,
    VideoStreamStats,
    InventoryHistory,
    success_response,
    error_response,
    validate_image_file,
    list_available_models,
    get_model_path
)

import cv2
import numpy as np
import json


# ============================================================================
# Lifespan Manager
# ============================================================================

class AppState:
    """Global application state"""
    def __init__(self):
        self.detector: Optional[InventoryDetector] = None
        self.video_active = False
        self.video_buffer = FrameBuffer(max_size=5)
        self.stats = VideoStreamStats()
        self.inventory_history = InventoryHistory(max_size=1000)
        self.websocket_clients: List[WebSocket] = []
        self.inventory_websocket_clients: List[WebSocket] = []


app_state = AppState()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    # Startup
    print("🚀 Starting Inventory Management API...")
    
    # Initialize detector with default model
    model_path = "yolov8n.pt"
    
    # Check for trained model
    trained_model = get_model_path("best.pt", "models")
    if trained_model:
        model_path = str(trained_model)
        print(f"✓ Found trained model: {model_path}")
    
    app_state.detector = InventoryDetector(
        model_path=model_path,
        conf_threshold=0.25,
        device='cpu'
    )
    
    print(f"✅ API ready on http://0.0.0.0:8000")
    print(f"📊 Model loaded: {model_path}")
    
    yield
    
    # Shutdown
    print("\n🛑 Shutting down API...")
    app_state.video_active = False
    for client in app_state.websocket_clients:
        await client.close()


# ============================================================================
# FastAPI App
# ============================================================================

app = FastAPI(
    title="Vision-Based Inventory Management API",
    description="REST API and WebSocket endpoints for real-time inventory detection and monitoring",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware (allow frontend connection)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================================
# Pydantic Models (Request/Response Schemas)
# ============================================================================

class DetectionResponse(BaseModel):
    """Single detection response"""
    bbox: List[float]
    confidence: float
    class_id: int
    class_name: str
    center: List[float]


class InventoryResponse(BaseModel):
    """Inventory count response"""
    total_objects: int
    class_counts: Dict[str, int]
    density_score: float
    timestamp: float


class DetectionResult(BaseModel):
    """Full detection result"""
    success: bool
    detections: List[DetectionResponse]
    inventory: InventoryResponse
    metadata: Dict[str, Any]
    message: Optional[str] = None


class ModelInfo(BaseModel):
    """Model information"""
    path: str
    device: str
    conf_threshold: float
    iou_threshold: float
    frame_count: int


class SwitchModelRequest(BaseModel):
    """Request to switch model"""
    model_path: str
    conf_threshold: Optional[float] = 0.25


# ============================================================================
# REST API Endpoints
# ============================================================================

@app.get("/")
async def root():
    """API root - health check"""
    return success_response(
        data={
            "name": "Vision-Based Inventory Management API",
            "version": "1.0.0",
            "status": "running"
        },
        message="API is running"
    )


@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return success_response(
        data={
            "status": "healthy",
            "detector_loaded": app_state.detector is not None,
            "video_active": app_state.video_active,
            "active_clients": len(app_state.websocket_clients)
        },
        message="System healthy"
    )


@app.post("/api/detect/image", response_model=DetectionResult)
async def detect_image(file: UploadFile = File(...)):
    """
    Detect objects in uploaded image
    
    Args:
        file: Image file (jpg, png, etc.)
    
    Returns:
        Detection results with bounding boxes and inventory count
    """
    if app_state.detector is None:
        raise HTTPException(status_code=500, detail="Detector not initialized")
    
    # Validate file
    if not file.content_type.startswith('image/'):
        raise HTTPException(status_code=400, detail="File must be an image")
    
    try:
        # Read image
        contents = await file.read()
        nparr = np.frombuffer(contents, np.uint8)
        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if frame is None:
            raise HTTPException(status_code=400, detail="Could not decode image")
        
        # Run detection
        result = app_state.detector.detect_image(frame)
        
        if 'error' in result:
            raise HTTPException(status_code=500, detail=result['error'])
        
        # Add to inventory history
        app_state.inventory_history.add_count(
            result['inventory']['total_objects'],
            result['inventory']['class_counts']
        )
        
        return result
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/detect/base64", response_model=DetectionResult)
async def detect_base64(request: Dict):
    """
    Detect objects from base64 encoded image
    
    Args:
        request: {"image_base64": "<base64 string>"}
    
    Returns:
        Detection results
    """
    if app_state.detector is None:
        raise HTTPException(status_code=500, detail="Detector not initialized")
    
    image_base64 = request.get('image_base64')
    if not image_base64:
        raise HTTPException(status_code=400, detail="Missing image_base64 field")
    
    result = app_state.detector.detect_from_base64(image_base64)
    
    if 'error' in result:
        raise HTTPException(status_code=500, detail=result['error'])
    
    # Add to inventory history
    app_state.inventory_history.add_count(
        result['inventory']['total_objects'],
        result['inventory']['class_counts']
    )
    
    return result


@app.post("/api/detect/url")
async def detect_url(request: Dict):
    """
    Detect objects from image URL
    
    Args:
        request: {"url": "<image URL>"}
    
    Returns:
        Detection results
    """
    if app_state.detector is None:
        raise HTTPException(status_code=500, detail="Detector not initialized")
    
    url = request.get('url')
    if not url:
        raise HTTPException(status_code=400, detail="Missing url field")
    
    try:
        # Download image from URL
        import urllib.request
        temp_path = "/tmp/temp_image.jpg"
        urllib.request.urlretrieve(url, temp_path)
        
        result = app_state.detector.detect_image(temp_path)
        
        # Cleanup
        if os.path.exists(temp_path):
            os.remove(temp_path)
        
        if 'error' in result:
            raise HTTPException(status_code=500, detail=result['error'])
        
        return result
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/inventory/count")
async def get_inventory_count():
    """
    Get current inventory count
    
    Returns:
        Current inventory statistics
    """
    stats = app_state.inventory_history.get_statistics()
    
    return success_response(
        data={
            'current': stats,
            'last_updated': time.time()
        },
        message="Inventory count retrieved"
    )


@app.get("/api/inventory/history")
async def get_inventory_history(
    limit: int = Query(default=100, description="Number of history entries to return")
):
    """
    Get inventory count history
    
    Args:
        limit: Maximum number of entries to return
    
    Returns:
        List of historical inventory counts
    """
    history = app_state.inventory_history.get_history(limit=limit)
    
    return success_response(
        data={
            'history': history,
            'count': len(history)
        },
        message="Inventory history retrieved"
    )


@app.post("/api/inventory/export")
async def export_inventory(
    format: str = Query(default="json", description="Export format: json or csv"),
    output_path: Optional[str] = Query(default=None, description="Output file path")
):
    """
    Export inventory history to file
    
    Args:
        format: Export format (json or csv)
        output_path: Optional output path
    
    Returns:
        Exported data or file path
    """
    if format.lower() == 'json':
        history = app_state.inventory_history.get_history(limit=0)  # Get all
        
        if output_path:
            app_state.inventory_history.export_to_json(output_path)
            return success_response(
                data={'file_path': output_path},
                message=f"Exported to {output_path}"
            )
        else:
            return success_response(
                data={'history': history},
                message="Inventory history exported"
            )
    
    elif format.lower() == 'csv':
        if not output_path:
            output_path = f"inventory_export_{int(time.time())}.csv"
        
        success = app_state.inventory_history.export_to_csv(output_path)
        
        if success:
            return success_response(
                data={'file_path': output_path},
                message=f"Exported to {output_path}"
            )
        else:
            raise HTTPException(status_code=500, detail="Failed to export CSV")
    
    else:
        raise HTTPException(status_code=400, detail=f"Unsupported format: {format}")


@app.get("/api/model/info")
async def get_model_info():
    """
    Get current model information
    
    Returns:
        Model details and configuration
    """
    if app_state.detector is None:
        raise HTTPException(status_code=500, detail="Detector not initialized")
    
    info = app_state.detector.get_model_info()
    
    return success_response(
        data=info,
        message="Model info retrieved"
    )


@app.get("/api/model/list")
async def list_models():
    """
    List all available models
    
    Returns:
        List of model files
    """
    models = list_available_models("models")
    
    return success_response(
        data={'models': models, 'count': len(models)},
        message="Models listed successfully"
    )


@app.post("/api/model/switch")
async def switch_model(request: SwitchModelRequest):
    """
    Switch to a different model
    
    Args:
        request: Model path and configuration
    
    Returns:
        New model info
    """
    try:
        # Validate model path
        model_path = get_model_path(request.model_path, "models")
        if not model_path:
            raise HTTPException(status_code=404, detail=f"Model not found: {request.model_path}")
        
        # Load new model
        print(f"🔄 Switching to model: {model_path}")
        app_state.detector = InventoryDetector(
            model_path=str(model_path),
            conf_threshold=request.conf_threshold,
            device='cpu'
        )
        
        return success_response(
            data=app_state.detector.get_model_info(),
            message=f"Switched to model: {model_path.name}"
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/inventory/clear")
async def clear_inventory_history():
    """
    Clear inventory history
    
    Returns:
        Confirmation
    """
    app_state.inventory_history.clear()
    
    return success_response(
        data={},
        message="Inventory history cleared"
    )


# ============================================================================
# WebSocket Endpoints (Real-time Streaming)
# ============================================================================

@app.websocket("/ws/video")
async def websocket_video(websocket: WebSocket):
    """
    WebSocket for real-time video streaming with detections
    
    Client sends: Camera source (0 for webcam, or file path)
    Server sends: Annotated frames as base64 + detection data
    """
    await websocket.accept()
    app_state.websocket_clients.append(websocket)
    
    print(f"📹 Video WebSocket connected. Total clients: {len(app_state.websocket_clients)}")
    
    try:
        while app_state.video_active:
            # Receive configuration from client
            try:
                data = await asyncio.wait_for(websocket.receive_json(), timeout=1.0)
                source = data.get('source', '0')
                
                # Start video processing
                app_state.video_active = True
                
                # Open video source
                cap = cv2.VideoCapture(int(source) if source.isdigit() else source)
                
                if not cap.isOpened():
                    await websocket.send_json({'error': f'Cannot open source: {source}'})
                    break
                
                while app_state.video_active:
                    ret, frame = cap.read()
                    if not ret:
                        break
                    
                    # Run detection
                    start_time = time.time()
                    detections, annotated = app_state.detector.detect(frame)
                    inventory = app_state.detector.count_inventory(detections, frame.shape)
                    inference_time = time.time() - start_time
                    
                    # Update stats
                    stats = app_state.stats.update(inference_time)
                    
                    # Add to history
                    app_state.inventory_history.add_count(
                        inventory.total_objects,
                        inventory.class_counts
                    )
                    
                    # Encode frame
                    frame_base64 = encode_image_to_base64(annotated)
                    
                    # Send to client
                    await websocket.send_json({
                        'success': True,
                        'frame': frame_base64,
                        'detections': [det.to_dict() for det in detections],
                        'inventory': inventory.to_dict(),
                        'stats': {
                            'fps': stats['avg_fps'],
                            'latency_ms': stats['avg_latency_ms'],
                            'frame_count': stats['frame_count']
                        }
                    })
                    
                    # Small delay to control FPS
                    await asyncio.sleep(0.033)  # ~30 FPS
                
                cap.release()
                
            except asyncio.TimeoutError:
                # Check if still active
                if not app_state.video_active:
                    break
                continue
        
    except WebSocketDisconnect:
        print("📹 Video WebSocket disconnected")
    finally:
        app_state.websocket_clients.remove(websocket)
        print(f"📹 Client removed. Remaining: {len(app_state.websocket_clients)}")


@app.websocket("/ws/inventory")
async def websocket_inventory(websocket: WebSocket):
    """
    WebSocket for real-time inventory updates
    
    Server sends: Inventory count updates
    """
    await websocket.accept()
    app_state.inventory_websocket_clients.append(websocket)
    
    print(f"📊 Inventory WebSocket connected. Total clients: {len(app_state.inventory_websocket_clients)}")
    
    try:
        while True:
            # Send inventory updates every second
            stats = app_state.inventory_history.get_statistics()
            
            await websocket.send_json({
                'success': True,
                'inventory': stats,
                'timestamp': time.time()
            })
            
            await asyncio.sleep(1.0)
    
    except WebSocketDisconnect:
        print("📊 Inventory WebSocket disconnected")
    finally:
        app_state.inventory_websocket_clients.remove(websocket)


# ============================================================================
# Video Control Endpoints
# ============================================================================

@app.post("/api/video/start")
async def start_video(source: str = Query(default="0")):
    """
    Start video processing
    
    Args:
        source: Video source (camera index or file path)
    
    Returns:
        Status
    """
    if app_state.video_active:
        return success_response(
            data={'active': True, 'source': source},
            message="Video already active"
        )
    
    app_state.video_active = True
    
    return success_response(
        data={'active': True, 'source': source},
        message=f"Video started with source: {source}"
    )


@app.post("/api/video/stop")
async def stop_video():
    """
    Stop video processing
    
    Returns:
        Status
    """
    app_state.video_active = False
    
    return success_response(
        data={'active': False},
        message="Video stopped"
    )


@app.get("/api/video/status")
async def video_status():
    """
    Get video processing status
    
    Returns:
        Current status
    """
    stats = app_state.stats.get_stats()
    
    return success_response(
        data={
            'active': app_state.video_active,
            'clients': len(app_state.websocket_clients),
            'stats': stats
        },
        message="Video status retrieved"
    )


# ============================================================================
# Main Entry Point
# ============================================================================

def main():
    """Run API server"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Inventory Management API')
    parser.add_argument('--host', default='0.0.0.0', help='Host to bind to')
    parser.add_argument('--port', type=int, default=8000, help='Port to bind to')
    parser.add_argument('--reload', action='store_true', help='Enable auto-reload')
    
    args = parser.parse_args()
    
    print(f"""
╔═══════════════════════════════════════════════════════════╗
║   Vision-Based Inventory Management API                   ║
╠═══════════════════════════════════════════════════════════╣
║  Endpoints:                                               ║
║  • GET  /                    - Health check               ║
║  • GET  /api/health          - System health              ║
║  • POST /api/detect/image    - Detect from image file     ║
║  • POST /api/detect/base64   - Detect from base64         ║
║  • POST /api/detect/url      - Detect from URL            ║
║  • GET  /api/inventory/count - Current inventory          ║
║  • GET  /api/inventory/history - Inventory history        ║
║  • POST /api/inventory/export - Export data               ║
║  • GET  /api/model/info      - Model information          ║
║  • GET  /api/model/list      - List models                ║
║  • POST /api/model/switch    - Switch model               ║
║  • WS   /ws/video            - Real-time video stream     ║
║  • WS   /ws/inventory        - Real-time inventory        ║
╚═══════════════════════════════════════════════════════════╝
    """)
    
    import uvicorn
    uvicorn.run(
        "api:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
        log_level="info"
    )


if __name__ == "__main__":
    main()
