# src/api.py - Simplified for inventory-only API

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import time
from typing import Optional, Dict, Any
import json

app = FastAPI(title="Vision-Based Inventory API", version="2.0.0")

# CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Store latest inventory data (updated by ROS bridge or manually)
latest_inventory = {
    "total_objects": 0,
    "class_counts": {},
    "density_score": 0,
    "status": "unknown",
    "last_updated": time.time()
}

# Store detection history
detection_history = []
MAX_HISTORY = 100

# ========================================================================
# Health & Status Endpoints
# ========================================================================

@app.get("/")
async def root():
    return {
        "success": True,
        "message": "Inventory Management API",
        "data": {
            "name": "Vision-Based Inventory API",
            "version": "2.0.0",
            "status": "running",
            "ros_stream_url": f"http://{get_pi_ip()}:8080/stream.mjpg"
        },
        "timestamp": time.time()
    }

@app.get("/api/health")
async def health_check():
    return {
        "success": True,
        "data": {
            "status": "healthy",
            "inventory_available": latest_inventory["total_objects"] > 0,
            "last_update": latest_inventory["last_updated"],
            "ros_stream_active": check_ros_stream()
        }
    }

# ========================================================================
# Inventory Endpoints
# ========================================================================

@app.get("/api/inventory/count")
async def get_inventory_count():
    """Get current inventory count"""
    return {
        "success": True,
        "data": {
            "current": {
                "avg_count": latest_inventory["total_objects"],
                "min_count": 0,
                "max_count": 100,
                "current_count": latest_inventory["total_objects"],
                "data_points": len(detection_history)
            }
        }
    }

@app.get("/api/inventory/status")
async def get_inventory_status():
    """Get full inventory status"""
    return {
        "success": True,
        "data": {
            "inventory": latest_inventory,
            "history": detection_history[-20:]  # Last 20 entries
        }
    }

@app.post("/api/inventory/update")
async def update_inventory(data: dict):
    """Endpoint for ROS bridge to push inventory updates"""
    global latest_inventory, detection_history
    
    latest_inventory = {
        "total_objects": data.get("total_objects", 0),
        "class_counts": data.get("class_counts", {}),
        "density_score": data.get("density_score", 0),
        "status": data.get("status", "unknown"),
        "shelf_capacity_percent": data.get("shelf_capacity_percent", 0),
        "last_updated": time.time()
    }
    
    # Add to history
    detection_history.append({
        "timestamp": time.time(),
        "total_objects": latest_inventory["total_objects"],
        "class_counts": latest_inventory["class_counts"],
        "density_score": latest_inventory["density_score"]
    })
    
    # Keep history limited
    if len(detection_history) > MAX_HISTORY:
        detection_history.pop(0)
    
    return {"success": True, "message": "Inventory updated"}

@app.get("/api/inventory/history")
async def get_inventory_history(limit: int = 50):
    """Get inventory history"""
    return {
        "success": True,
        "data": {
            "history": detection_history[-limit:],
            "count": len(detection_history)
        }
    }

@app.post("/api/inventory/export")
async def export_inventory(format: str = "json"):
    """Export inventory data"""
    import csv
    from io import StringIO
    
    if format == "csv":
        output = StringIO()
        writer = csv.writer(output)
        writer.writerow(["timestamp", "total_objects", "density_score", "status"])
        for record in detection_history:
            writer.writerow([
                record["timestamp"],
                record["total_objects"],
                record["density_score"],
                latest_inventory["status"]
            ])
        return Response(
            content=output.getvalue(),
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=inventory.csv"}
        )
    else:
        return {
            "success": True,
            "data": {
                "current": latest_inventory,
                "history": detection_history
            }
        }

# ========================================================================
# Helper Functions
# ========================================================================

def get_pi_ip():
    """Get Raspberry Pi IP address"""
    import socket
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "192.168.1.4"  # Fallback

def check_ros_stream():
    """Check if ROS stream is accessible"""
    import urllib.request
    try:
        urllib.request.urlopen(f"http://{get_pi_ip()}:8080/health", timeout=1)
        return True
    except:
        return False

# ========================================================================
# ROS Bridge Endpoint (for api_bridge_node to push data)
# ========================================================================

@app.post("/api/ros2/data")
async def receive_ros_data(data: dict):
    """Receive data from ROS api_bridge_node"""
    if "inventory" in data:
        inv = data["inventory"]
        await update_inventory({
            "total_objects": inv.get("total_objects", 0),
            "class_counts": dict(zip(inv.get("class_names", []), inv.get("class_counts", []))),
            "density_score": inv.get("density_score", 0),
            "status": inv.get("status", "unknown"),
            "shelf_capacity_percent": inv.get("shelf_capacity_percent", 0)
        })
    return {"success": True}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)