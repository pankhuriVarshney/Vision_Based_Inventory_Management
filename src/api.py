# src/api.py
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import rclpy
from rclpy.node import Node
from rclpy.executors import MultiThreadedExecutor
from ros2_inventory.msg import InventoryCount
import json
import threading
import asyncio
from collections import deque
import time
from typing import Dict, List, Any
from datetime import datetime
from pathlib import Path
import pickle
import os
import subprocess

app = FastAPI(title="Vision-Based Inventory API - Real-time")

# CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global state to store ROS data
inventory_state = {
    "current_count": 0,
    "avg_count": 0,
    "min_count": 0,
    "max_count": 0,
    "data_points": 0,
    "last_update": 0,
    "history": deque(maxlen=100),
    "detections": [],
    "class_counts": {},
    "density_score": 0,
    "shelf_capacity_percent": 0,
    "status": "unknown"
}

class ROSInventorySubscriber(Node):
    """ROS2 Node that subscribes to inventory topic"""
    
    def __init__(self):
        super().__init__('api_inventory_subscriber')
        
        # Subscribe to inventory status
        self.inventory_sub = self.create_subscription(
            InventoryCount,
            '/inventory_status',
            self.inventory_callback,
            10
        )
        
        self.get_logger().info('✅ API Subscriber Node initialized')
        print("📡 Listening to /inventory_status topic...")
    
    def inventory_callback(self, msg: InventoryCount):
        """Handle inventory status messages from ROS"""
        try:
            total_items = msg.total_objects
            
            # Build class counts dictionary
            class_counts = {}
            for i, class_name in enumerate(msg.class_names):
                if i < len(msg.class_counts):
                    class_counts[class_name] = msg.class_counts[i]
            
            density_score = msg.density_score
            shelf_capacity = msg.shelf_capacity_percent
            status = msg.status
            
            # Update global inventory state
            inventory_state["current_count"] = total_items
            inventory_state["class_counts"] = class_counts
            inventory_state["density_score"] = density_score
            inventory_state["shelf_capacity_percent"] = shelf_capacity
            inventory_state["status"] = status
            inventory_state["last_update"] = time.time()
            
            # Update statistics
            if inventory_state["data_points"] == 0:
                inventory_state["avg_count"] = float(total_items)
                inventory_state["min_count"] = total_items
                inventory_state["max_count"] = total_items
            else:
                n = inventory_state["data_points"]
                inventory_state["avg_count"] = (inventory_state["avg_count"] * n + total_items) / (n + 1)
                inventory_state["min_count"] = min(inventory_state["min_count"], total_items)
                inventory_state["max_count"] = max(inventory_state["max_count"], total_items)
            
            inventory_state["data_points"] += 1
            
            # Add to history
            inventory_state["history"].append({
                "timestamp": time.time(),
                "datetime": datetime.now().isoformat(),
                "total_objects": total_items,
                "density_score": float(density_score),
                "shelf_capacity_percent": float(shelf_capacity),
                "status": status,
                "class_counts": class_counts
            })
            
            print(f"📊 Inventory: {total_items} items | Status: {status} | Density: {density_score:.2f}")
            
        except Exception as e:
            print(f"❌ Error parsing inventory message: {e}")

# ROS2 Node instance
ros_node = None
ros_thread = None
ros_executor = None

def run_ros_node():
    """Run ROS2 node in a separate thread"""
    global ros_node, ros_executor
    
    if not rclpy.ok():
        rclpy.init()
    
    ros_node = ROSInventorySubscriber()
    ros_executor = MultiThreadedExecutor()
    ros_executor.add_node(ros_node)
    
    try:
        ros_executor.spin()
    except KeyboardInterrupt:
        pass
    finally:
        ros_executor.shutdown()
        if ros_node:
            ros_node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()

# Start ROS thread on startup
@app.on_event("startup")
async def startup_event():
    global ros_thread
    print("=" * 60)
    print("🚀 Starting FastAPI Server")
    print("=" * 60)
    print("📡 Connecting to ROS2 topics...")
    
    ros_thread = threading.Thread(target=run_ros_node, daemon=True)
    ros_thread.start()
    
    await asyncio.sleep(2)
    
    print(f"✅ ROS subscriber started")
    print(f"📊 Current inventory: {inventory_state['current_count']} items")
    print(f"🌐 API available at: http://0.0.0.0:8000")
    print(f"📖 API docs: http://0.0.0.0:8000/docs")
    print("=" * 60)

@app.on_event("shutdown")
async def shutdown_event():
    print("🛑 Shutting down FastAPI server...")
    if ros_executor:
        ros_executor.shutdown()
    if ros_node:
        ros_node.destroy_node()
    if rclpy.ok():
        rclpy.shutdown()

# ========== API Endpoints ==========

@app.get("/")
async def root():
    return {
        "name": "Vision-Based Inventory API",
        "version": "2.0.0",
        "status": "running",
        "ros_connected": inventory_state["last_update"] > 0,
        "endpoints": [
            "/api/health",
            "/api/inventory/count",
            "/api/inventory/history",
            "/api/detections/current",
            "/api/learning/status",
            "/api/learning/history",
            "/api/learning/trigger",
            "/ws/inventory"
        ]
    }

@app.get("/api/health")
async def health_check():
    time_since_update = time.time() - inventory_state["last_update"] if inventory_state["last_update"] > 0 else 999
    is_connected = time_since_update < 10
    
    return {
        "success": True,
        "data": {
            "status": "healthy",
            "ros_connected": is_connected,
            "detector_loaded": True,
            "last_update": inventory_state["last_update"],
            "seconds_since_update": round(time_since_update, 1),
            "current_inventory": inventory_state["current_count"]
        }
    }

@app.get("/api/inventory/count")
async def get_inventory_count():
    return {
        "success": True,
        "data": {
            "current": {
                "avg_count": round(inventory_state["avg_count"], 1),
                "min_count": inventory_state["min_count"],
                "max_count": inventory_state["max_count"],
                "current_count": inventory_state["current_count"],
                "data_points": inventory_state["data_points"],
                "density_score": round(inventory_state["density_score"], 2),
                "status": inventory_state["status"]
            }
        }
    }

@app.get("/api/inventory/history")
async def get_inventory_history(limit: int = 100):
    history_list = list(inventory_state["history"])
    return {
        "success": True,
        "data": {
            "history": history_list[-limit:],
            "total_points": len(history_list)
        }
    }

@app.get("/api/inventory/class_counts")
async def get_class_counts():
    return {
        "success": True,
        "data": {
            "class_counts": inventory_state["class_counts"],
            "total_items": inventory_state["current_count"],
            "last_update": inventory_state["last_update"]
        }
    }

@app.get("/api/detections/current")
async def get_current_detections():
    return {
        "success": True,
        "data": {
            "detections": inventory_state["detections"],
            "count": len(inventory_state["detections"])
        }
    }

@app.post("/api/inventory/export")
async def export_inventory(format: str = "json"):
    if format == "json":
        export_data = {
            "export_time": time.time(),
            "total_points": len(inventory_state["history"]),
            "current_inventory": inventory_state["current_count"],
            "history": list(inventory_state["history"])
        }
        return JSONResponse(content=export_data, media_type="application/json")
    else:
        import csv
        from io import StringIO
        
        output = StringIO()
        writer = csv.writer(output)
        writer.writerow(["timestamp", "datetime", "total_objects", "density_score", "shelf_capacity_percent", "status"])
        
        for record in inventory_state["history"]:
            writer.writerow([
                record["timestamp"],
                record.get("datetime", ""),
                record["total_objects"],
                record["density_score"],
                record.get("shelf_capacity_percent", 0),
                record["status"]
            ])
        
        return JSONResponse(content=output.getvalue(), media_type="text/csv")

@app.get("/api/stream/frame")
async def get_latest_frame():
    return {
        "success": True,
        "frame": {
            "frame_id": inventory_state["data_points"],
            "timestamp": time.time(),
            "inventory": {
                "total_objects": inventory_state["current_count"],
                "density_score": inventory_state["density_score"],
                "coverage_ratio": inventory_state["shelf_capacity_percent"] / 100.0 if inventory_state["shelf_capacity_percent"] > 0 else 0,
                "class_counts": inventory_state["class_counts"]
            },
            "detections": inventory_state["detections"],
            "fps": 1.0,
            "density_map": generate_density_map(inventory_state["current_count"])
        }
    }

def generate_density_map(item_count: int):
    if item_count == 0:
        return [[0,0,0], [0,0,0], [0,0,0]]
    elif item_count <= 2:
        return [[0,1,0], [0,0,0], [0,0,0]]
    elif item_count <= 5:
        return [[1,1,0], [0,1,0], [0,0,0]]
    elif item_count <= 10:
        return [[1,2,1], [0,2,1], [0,1,0]]
    else:
        return [[2,2,2], [1,2,2], [1,1,1]]

# ========== Continual Learning Endpoints ==========

@app.get("/api/learning/status")
async def get_learning_status():
    """Get current continual learning status"""
    try:
        # Try multiple possible state file paths
        state_paths = [
            Path("/home/sonik/Vision_Based_Inventory_Management/models/learning_state.pkl"),
            Path("/home/sonik/Vision_Based_Inventory_Management/models/continual_learning_state.pkl"),
            Path("/home/sonik/ros2_ws/learning_state.pkl")
        ]
        
        learning_stats = {
            "status": "active",
            "buffer_size": 0,
            "buffer_max": 500,
            "avg_confidence": 0,
            "fill_percent": 0,
            "total_learning_events": 0,
            "last_learning_time": None,
            "auto_learn_enabled": True,
            "trigger_threshold": 0.6,
            "min_buffer_for_learning": 50,
            "detection_count": 0
        }
        
        for state_path in state_paths:
            if state_path.exists():
                try:
                    with open(state_path, 'rb') as f:
                        state = pickle.load(f)
                        learning_stats["total_learning_events"] = state.get('learning_events', 0)
                        learning_stats["last_learning_time"] = state.get('timestamp', None)
                        learning_stats["detection_count"] = state.get('detection_count', 0)
                    break
                except:
                    pass
        
        # Also check buffer file
        buffer_path = Path("/home/sonik/Vision_Based_Inventory_Management/models/learning_state_buffer.pkl")
        if buffer_path.exists():
            try:
                with open(buffer_path, 'rb') as f:
                    buffer_data = pickle.load(f)
                    confidences = buffer_data.get('confidences', [])
                    learning_stats["buffer_size"] = len(confidences)
                    if confidences:
                        avg_conf = sum(confidences) / len(confidences)
                        learning_stats["avg_confidence"] = round(avg_conf, 3)
                        learning_stats["fill_percent"] = round((len(confidences) / learning_stats["buffer_max"]) * 100, 1)
            except:
                pass
        
        return {
            "success": True,
            "data": learning_stats
        }
    except Exception as e:
        print(f"Error in learning status: {e}")
        return {
            "success": False,
            "error": str(e),
            "data": {
                "status": "initializing",
                "message": "No learning data yet. System is collecting experiences."
            }
        }

@app.get("/api/learning/history")
async def get_learning_history(limit: int = 20):
    """Get history of learning events"""
    try:
        history = []
        state_paths = [
            Path("/home/sonik/Vision_Based_Inventory_Management/models/learning_state.pkl"),
            Path("/home/sonik/Vision_Based_Inventory_Management/models/continual_learning_state.pkl")
        ]
        
        for state_path in state_paths:
            if state_path.exists():
                try:
                    with open(state_path, 'rb') as f:
                        state = pickle.load(f)
                        history.append({
                            "timestamp": state.get('timestamp', time.time()),
                            "buffer_size": state.get('detection_count', 0),
                            "avg_confidence": 0,
                            "loss_before": 0,
                            "loss_after": 0,
                            "success": True,
                            "learning_events": state.get('learning_events', 0)
                        })
                    break
                except:
                    pass
        
        return {
            "success": True,
            "data": {
                "learning_events": history[-limit:],
                "total_events": len(history)
            }
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "data": {"learning_events": []}
        }

@app.post("/api/learning/trigger")
async def trigger_learning():
    """Manually trigger continual learning"""
    try:
        # Try to publish to ROS topic
        result = subprocess.run(
            ['ros2', 'topic', 'pub', '/learning/trigger', 'std_msgs/Bool', 'data: true', '--once'],
            capture_output=True,
            text=True,
            timeout=2
        )
        
        return {
            "success": True,
            "message": "Learning triggered successfully",
            "ros_output": result.stdout
        }
    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "error": "Timeout - Make sure ROS2 is running",
            "message": "Could not trigger learning. Check if ROS2 is running."
        }
    except FileNotFoundError:
        return {
            "success": False,
            "error": "ROS2 not found",
            "message": "Learning trigger only works when ROS2 is running"
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": "Could not trigger learning"
        }

# ========== WebSocket for Real-time Updates ==========

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
    
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        print(f"🔌 WebSocket client connected. Total: {len(self.active_connections)}")
    
    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        print(f"🔌 WebSocket client disconnected. Total: {len(self.active_connections)}")
    
    async def broadcast(self, message: dict):
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except:
                disconnected.append(connection)
        
        for connection in disconnected:
            self.disconnect(connection)

manager = ConnectionManager()

@app.websocket("/ws/inventory")
async def websocket_inventory(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        last_count = -1
        last_status = ""
        
        while True:
            current_count = inventory_state["current_count"]
            current_status = inventory_state["status"]
            
            # Send update every second or when data changes
            if current_count != last_count or current_status != last_status:
                data = {
                    "total_objects": current_count,
                    "density_score": inventory_state["density_score"],
                    "shelf_capacity_percent": inventory_state["shelf_capacity_percent"],
                    "status": current_status,
                    "class_counts": inventory_state["class_counts"],
                    "timestamp": time.time()
                }
                await websocket.send_json(data)
                last_count = current_count
                last_status = current_status
            
            await asyncio.sleep(1)  # Update every second
            
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        print(f"WebSocket error: {e}")
        manager.disconnect(websocket)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=8000,
        log_level="info"
    )