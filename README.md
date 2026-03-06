# 🛒 Vision-Based Smart Inventory Management System

A complete AI-powered inventory management system using computer vision (YOLOv8) for real-time product detection, counting, and shelf monitoring. Built with FastAPI backend, ROS2 for hardware deployment, and Next.js web dashboard.

## 📋 **Project Overview**

This system provides:
- ✅ **Real-time object detection** using YOLOv8
- ✅ **Inventory counting** with density analysis
- ✅ **REST API** for integration with other systems
- ✅ **WebSocket streaming** for live video feeds
- ✅ **ROS2 nodes** for hardware deployment (Raspberry Pi)
- ✅ **Web dashboard** for monitoring and control
- ✅ **Model export** to TFLite, ONNX, OpenVINO, TensorRT

---

## 🏗️ **System Architecture**

```
┌─────────────────────────────────────────────────────────┐
│                    Hardware Layer                        │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────┐ │
│  │ Camera Node │  │ Sensor Node │  │ Display Node    │ │
│  └──────┬──────┘  └──────┬──────┘  └────────┬────────┘ │
│         │                │                   │          │
│         └────────────────┼───────────────────┘          │
│                          │ ROS2 Topics                   │
└──────────────────────────┼──────────────────────────────┘
                           │
┌──────────────────────────┼──────────────────────────────┐
│                  Edge Computing Layer                    │
│  ┌───────────────────────▼────────────────────────┐     │
│  │         ROS2 Detection Node (YOLOv8)           │     │
│  │    - Subscribe: /camera/image_raw              │     │
│  │    - Publish: /detection/results               │     │
│  │    - Publish: /inventory/count                 │     │
│  └───────────────────────┬────────────────────────┘     │
│                          │                               │
│  ┌───────────────────────▼────────────────────────┐     │
│  │           FastAPI Backend (api.py)             │     │
│  │    - REST endpoints                            │     │
│  │    - WebSocket streaming                       │     │
│  └───────────────────────┬────────────────────────┘     │
└──────────────────────────┼──────────────────────────────┘
                           │ HTTP/WebSocket
┌──────────────────────────┼──────────────────────────────┐
│                   Frontend Layer                         │
│  ┌───────────────────────▼────────────────────────┐     │
│  │         Next.js Web Dashboard                  │     │
│  │    - Live video feed                           │     │
│  │    - Inventory counts                          │     │
│  │    - Historical analytics                      │     │
│  └────────────────────────────────────────────────┘     │
└─────────────────────────────────────────────────────────┘
```

---

## 📁 **Project Structure**

```
Vision_Based_Inventory_Management/
├── src/
│   ├── inference.py          # Core detection engine
│   ├── api.py                # FastAPI backend
│   ├── utils.py              # Helper utilities
│   ├── export_model.py       # Model export script
│   ├── preprocess.py         # Data preprocessing
│   ├── train.py              # Model training
│   └── gui.py                # PyQt5 GUI (legacy)
│
├── ros2_inventory/           # ROS2 package for hardware
│   ├── launch/
│   │   └── inventory_system.launch.py
│   ├── ros2_inventory/
│   │   ├── camera_node.py
│   │   ├── detection_node.py
│   │   ├── inventory_node.py
│   │   └── api_bridge_node.py
│   ├── msg/                  # Custom ROS2 messages
│   ├── config/
│   │   └── params.yaml
│   ├── package.xml
│   └── setup.py
│
├── frontend/                 # Next.js web dashboard
│   ├── components/
│   │   ├── video-stream.tsx
│   │   ├── inventory-dashboard.tsx
│   │   ├── detections-table.tsx
│   │   └── ...
│   ├── lib/
│   │   └── api-client.ts    # API client
│   └── app/
│       └── page.tsx
│
├── models/                   # Trained models
│   └── rpc_real_labels/
│       └── weights/
│           └── best.pt
│
├── requirements.txt
├── run.py                    # Main launcher
└── README.md
```

---

## 🚀 **Quick Start**

### **1. Installation**

```bash
# Install Python dependencies
pip install -r requirements.txt

# Install frontend dependencies
cd frontend
npm install
cd ..
```

### **2. Start the API Server**

```bash
# Option 1: Using run.py
python run.py api --host 0.0.0.0 --port 8000

# Option 2: Direct
python src/api.py --host 0.0.0.0 --port 8000

# Option 3: With uvicorn
uvicorn src.api:app --reload --host 0.0.0.0 --port 8000
```

API will be available at: `http://localhost:8000`
API Documentation: `http://localhost:8000/docs`

### **3. Start the Frontend**

```bash
cd frontend
npm run dev
```

Frontend will be available at: `http://localhost:3000`

### **4. Test Detection**

```bash
# Run detection with webcam
python run.py detect --source 0

# Run detection with video file
python run.py detect --source video.mp4 --model yolov8n.pt
```

---

## 🔌 **API Endpoints**

### **REST API**

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Health check |
| `/api/health` | GET | System health status |
| `/api/detect/image` | POST | Detect from uploaded image |
| `/api/detect/base64` | POST | Detect from base64 image |
| `/api/detect/url` | POST | Detect from image URL |
| `/api/inventory/count` | GET | Current inventory count |
| `/api/inventory/history` | GET | Inventory history |
| `/api/inventory/export` | POST | Export data (JSON/CSV) |
| `/api/model/info` | GET | Model information |
| `/api/model/list` | GET | List available models |
| `/api/model/switch` | POST | Switch to different model |
| `/api/video/start` | POST | Start video processing |
| `/api/video/stop` | POST | Stop video processing |
| `/api/video/status` | GET | Video processing status |

### **WebSocket Endpoints**

| Endpoint | Description |
|----------|-------------|
| `/ws/video` | Real-time video stream with detections |
| `/ws/inventory` | Real-time inventory updates |

---

## 🤖 **ROS2 Hardware Deployment**

### **Prerequisites**

- Ubuntu 22.04 LTS
- ROS2 Humble Hawksbill
- Raspberry Pi 5 (or similar)
- Camera module

### **Installation on Raspberry Pi**

```bash
# Install ROS2 Humble
sudo apt update
sudo apt install ros-humble-desktop
source /opt/ros/humble/setup.bash

# Install dependencies
pip3 install ultralytics opencv-python

# Copy ROS2 package to Raspberry Pi
scp -r ros2_inventory pi@raspberrypi:~/

# Build ROS2 package
cd ros2_inventory
rosdep install --from-paths src --ignore-src -r -y
colcon build
source install/setup.bash
```

### **Running ROS2 System**

```bash
# Launch all nodes
ros2 launch ros2_inventory inventory_system.launch.py

# Or run individual nodes
ros2 run ros2_inventory camera_node
ros2 run ros2_inventory detection_node
ros2 run ros2_inventory inventory_node
ros2 run ros2_inventory api_bridge_node
```

### **ROS2 Topics**

| Topic | Type | Description |
|-------|------|-------------|
| `/camera/image_raw` | sensor_msgs/Image | Raw camera feed |
| `/detections` | DetectionArray | Detection results |
| `/annotated_image` | sensor_msgs/Image | Annotated video |
| `/inventory_status` | InventoryCount | Inventory counts |

---

## 📊 **Model Training**

### **1. Prepare Dataset**

```bash
# Download and preprocess dataset
python run.py preprocess

# Or use specific dataset
python src/preprocess.py --dataset coco  # COCO-2017
python src/preprocess.py --dataset rpc   # Retail Product Checkout
```

### **2. Train Model**

```bash
# Train with default settings
python run.py train

# Train with custom settings
python src/train.py --epochs 50 --batch 8 --imgsz 640
```

### **3. Export for Deployment**

```bash
# Export to TFLite (for Raspberry Pi)
python src/export_model.py --model models/rpc_real_labels/weights/best.pt --format tflite --int8

# Export to ONNX (universal)
python src/export_model.py --model models/rpc_real_labels/weights/best.pt --format onnx

# Export to all formats
python src/export_model.py --model models/rpc_real_labels/weights/best.pt --format all
```

---

## 🎯 **Usage Examples**

### **Python API Client**

```python
from src.inference import InventoryDetector

# Initialize detector
detector = InventoryDetector(
    model_path="models/best.pt",
    conf_threshold=0.25
)

# Detect from image
result = detector.detect_image("shelf.jpg")
print(f"Detected: {result['inventory']['total_objects']} items")

# Detect from webcam
detector.process_video(source="0", display=True)
```

### **JavaScript/TypeScript Client**

```typescript
import apiClient from '@/lib/api-client'

// Detect from file
const file = document.querySelector('input[type="file"]').files[0]
const result = await apiClient.detectImage(file)
console.log(`Detected: ${result.inventory.total_objects} items`)

// Connect to real-time stream
apiClient.connectVideoStream('0', (frame) => {
  console.log(`FPS: ${frame.stats.fps}`)
  console.log(`Detections: ${frame.detections.length}`)
})
```

### **cURL Examples**

```bash
# Health check
curl http://localhost:8000/api/health

# Detect from image
curl -X POST http://localhost:8000/api/detect/image \
  -F "file=@shelf.jpg"

# Get inventory count
curl http://localhost:8000/api/inventory/count

# List models
curl http://localhost:8000/api/model/list
```

---

## ⚙️ **Configuration**

### **Environment Variables**

Create a `.env` file in the `frontend` directory:

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### **ROS2 Parameters**

Edit `ros2_inventory/config/params.yaml`:

```yaml
camera_node:
  ros__parameters:
    camera_id: 0
    width: 640
    height: 480
    fps: 30

detection_node:
  ros__parameters:
    model_path: "yolov8n.pt"
    conf_threshold: 0.25
    device: "cpu"
```

---

## 📈 **Performance Benchmarks**

| Device | Model | FPS | Latency |
|--------|-------|-----|---------|
| Raspberry Pi 5 | YOLOv8n TFLite | ~15 FPS | 67ms |
| Intel i7 CPU | YOLOv8n PyTorch | ~30 FPS | 33ms |
| NVIDIA Jetson Nano | YOLOv8n TensorRT | ~25 FPS | 40ms |
| RTX 3060 | YOLOv8n PyTorch | ~120 FPS | 8ms |

---

## 🔧 **Troubleshooting**

### **API won't start**

```bash
# Check if port is in use
netstat -tulpn | grep 8000

# Kill process using port 8000
kill -9 <PID>

# Restart API
python src/api.py --host 0.0.0.0 --port 8000
```

### **Camera not detected**

```bash
# List available cameras
ls -l /dev/video*

# Test camera with OpenCV
python -c "import cv2; cap = cv2.VideoCapture(0); print(cap.isOpened())"
```

### **ROS2 nodes not communicating**

```bash
# Check ROS2 domain
export ROS_DOMAIN_ID=0

# List active nodes
ros2 node list

# Check topic connections
ros2 topic info /camera/image_raw
```

---

## 📝 **License**

MIT License - See LICENSE file for details

---

## 👥 **Contributors**

- Sonika Das
- Naman Agarwal
- Ashmit Sanjay Katale

**Project Guide:** Dr. Sameer Sayyad

**Institution:** Symbiosis Institute of Technology, Pune

---

## 🙏 **Acknowledgments**

- YOLOv8 by Ultralytics
- ROS2 Community
- Next.js Team
- FastAPI Team

---

## 📞 **Support**

For issues or questions, please open an issue on GitHub or contact the development team.
