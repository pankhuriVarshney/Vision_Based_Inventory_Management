# Vision-Based Smart Inventory Management System
## Backend API Specification

This document outlines the required API format for the backend to integrate seamlessly with the frontend dashboard.

---

## WebSocket Connection

### Endpoint
```
ws://[YOUR_RASPBERRY_PI_IP]:8000/ws/detections
```

### Connection Parameters
- **Path**: `/ws/detections`
- **Protocol**: WebSocket
- **Expected Data Rate**: 30 FPS (33ms per frame)
- **Timeout**: 30 seconds (auto-reconnect on timeout)

---

## Data Structures

### 1. WebSocket Message Format (Required)

The backend MUST send the following JSON structure every frame:

```json
{
  "frame_id": 1234,
  "timestamp": 1698765432000,
  "detections": [
    {
      "bbox": [100, 150, 250, 300],
      "confidence": 0.95,
      "class_id": 0,
      "class_name": "Product",
      "center": [175, 225]
    }
  ],
  "inventory": {
    "total_objects": 45,
    "class_counts": {
      "Product": 30,
      "Box": 10,
      "Shelf": 5
    },
    "density_score": 7.5,
    "coverage_ratio": 0.68
  },
  "density_map": [
    [2, 3, 1],
    [4, 5, 3],
    [2, 2, 1]
  ],
  "system_health": {
    "cpu_usage": 45.2,
    "memory_usage": 62.1,
    "connection_latency": 12,
    "uptime": 3600
  }
}
```

### 2. Detection Object (Per Item)

```typescript
{
  // Bounding box: [x_min, y_min, x_max, y_max]
  // Coordinates relative to 640x480 frame
  bbox: [number, number, number, number],
  
  // Confidence score (0.0 to 1.0) - NEW: MUST ADD THIS
  confidence: number,
  
  // Class identifier (0, 1, 2, etc.)
  class_id: number,
  
  // Human-readable class name ("Product", "Box", "Shelf", etc.)
  class_name: string,
  
  // Center point of bounding box [x, y]
  center: [number, number]
}
```

### 3. Inventory Object

```typescript
{
  // Total count of all detected objects
  total_objects: number,
  
  // Count breakdown by product category
  class_counts: {
    [category_name: string]: number
  },
  
  // Shelf density score (0-10 scale)
  // 0 = empty, 10 = very crowded
  density_score: number,
  
  // Percentage of shelf covered (0-1.0)
  coverage_ratio: number
}
```

### 4. System Health Object (NEW)

```typescript
{
  // CPU usage percentage (0-100)
  cpu_usage: number,
  
  // Memory usage percentage (0-100)
  memory_usage: number,
  
  // Network latency in milliseconds
  connection_latency: number,
  
  // System uptime in seconds
  uptime: number
}
```

### 5. Density Map (Heatmap)

3x3 (or configurable NxN) grid showing object count per section:

```typescript
[
  [2, 3, 1],  // Top row (left, center, right)
  [4, 5, 3],  // Middle row
  [2, 2, 1]   // Bottom row
]
```

---

## Implementation Requirements

### YOLOv8 Integration

Your backend is using YOLOv8. Here's how to modify it to send confidence scores:

#### Python (FastAPI + YOLOv8)

```python
from ultralytics import YOLO
import json
import psutil
import time

model = YOLO('yolov8n.pt')  # nano, small, medium
uptime_start = time.time()

def get_system_health():
    """Collect system metrics"""
    return {
        "cpu_usage": psutil.cpu_percent(interval=0.1),
        "memory_usage": psutil.virtual_memory().percent,
        "connection_latency": 0,  # Measure client roundtrip
        "uptime": int(time.time() - uptime_start)
    }

def process_frame(frame):
    """Run inference and format response"""
    results = model.predict(frame, conf=0.5)  # confidence threshold
    
    detections = []
    class_counts = {}
    
    for result in results:
        for box in result.boxes:
            # IMPORTANT: Add confidence to output
            confidence = float(box.conf[0])
            class_id = int(box.cls[0])
            class_name = result.names[class_id]
            
            # Bounding box [x_min, y_min, x_max, y_max]
            x_min, y_min, x_max, y_max = box.xyxy[0].tolist()
            center_x = (x_min + x_max) / 2
            center_y = (y_min + y_max) / 2
            
            detections.append({
                "bbox": [x_min, y_min, x_max, y_max],
                "confidence": confidence,  # NEW
                "class_id": class_id,
                "class_name": class_name,
                "center": [center_x, center_y]
            })
            
            # Track class counts
            class_counts[class_name] = class_counts.get(class_name, 0) + 1
    
    # Calculate inventory metrics
    total_objects = len(detections)
    density_score = min(10, (total_objects / 50) * 10)
    coverage_ratio = total_objects / 60  # Adjust based on your shelf capacity
    
    # Create 3x3 density map
    h, w = frame.shape[:2]
    density_map = [[0 for _ in range(3)] for _ in range(3)]
    
    for det in detections:
        center_x, center_y = det['center']
        grid_x = int((center_x / w) * 3)
        grid_y = int((center_y / h) * 3)
        grid_x = min(2, max(0, grid_x))
        grid_y = min(2, max(0, grid_y))
        density_map[grid_y][grid_x] += 1
    
    return {
        "frame_id": frame_id,
        "timestamp": int(time.time() * 1000),  # milliseconds
        "detections": detections,
        "inventory": {
            "total_objects": total_objects,
            "class_counts": class_counts,
            "density_score": density_score,
            "coverage_ratio": min(1.0, coverage_ratio)
        },
        "density_map": density_map,
        "system_health": get_system_health()
    }

# WebSocket handler
@app.websocket("/ws/detections")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    cap = cv2.VideoCapture(0)  # Your camera source
    frame_id = 0
    
    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            # Resize to 640x480 for consistency
            frame = cv2.resize(frame, (640, 480))
            
            # Process and send
            data = process_frame(frame)
            frame_id += 1
            
            await websocket.send_json(data)
            await asyncio.sleep(1/30)  # 30 FPS
    
    except Exception as e:
        print(f"WebSocket error: {e}")
    finally:
        cap.release()
```

---

## Integration Checklist

- [x] Detection objects include **confidence scores** (0.0-1.0)
- [x] System health metrics included in every message
- [x] Timestamp in milliseconds (not seconds)
- [x] Bounding box coordinates relative to 640x480 frame
- [x] Center point calculated for each detection
- [x] 3x3 density map grid calculation
- [x] Class counts properly aggregated
- [x] WebSocket sends at 30 FPS (33ms per frame)
- [x] Proper error handling and reconnection logic

---

## Frontend Connection

The frontend automatically attempts to connect to:
```
ws://localhost:8000/ws/detections
```

To connect to your Raspberry Pi, modify the WebSocket URL in the frontend code or set an environment variable:

```typescript
const WS_URL = process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000/ws/detections'
```

---

## Testing Your Backend

1. **Test WebSocket Connection**
   ```bash
   wscat -c ws://localhost:8000/ws/detections
   ```

2. **Validate JSON Format**
   - All required fields present
   - Proper data types
   - Confidence scores between 0-1

3. **Performance Requirements**
   - 30 FPS minimum
   - <50ms latency
   - <100MB memory usage

---

## Common Issues & Solutions

### Issue: "Connection refused"
- Ensure backend is running and WebSocket endpoint is exposed
- Check firewall rules on Raspberry Pi
- Verify correct IP address in frontend

### Issue: "Detections not showing"
- Check bounding box coordinates are relative to 640x480
- Verify confidence threshold setting
- Ensure detections array is not empty

### Issue: "High latency"
- Reduce frame resolution or model size
- Use `yolov8n` (nano) instead of larger models
- Check network bandwidth

---

## Next Steps

1. Modify your backend to include confidence scores
2. Add system health metrics collection
3. Test WebSocket connection with the provided Python code
4. Deploy to Raspberry Pi
5. Update frontend WS_URL to point to your device IP

