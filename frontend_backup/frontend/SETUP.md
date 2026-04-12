# Vision-Based Smart Inventory Management - Setup Guide

## Frontend Setup (This Application)

### 1. Clone and Install Dependencies
```bash
npm install
# or
pnpm install
```

### 2. Configure Backend Connection

**Option A: Using Environment Variable (Recommended)**
```bash
# Copy the example file
cp .env.local.example .env.local

# Edit .env.local with your backend URL
NEXT_PUBLIC_WS_URL=ws://192.168.1.100:8000/ws/detections
```

**Option B: Configure in App UI**
- The dashboard has a sidebar with WebSocket URL configuration
- You can change the URL directly in the UI and it will attempt to connect

### 3. Run Development Server
```bash
npm run dev
# or
pnpm dev
```

The app will be available at `http://localhost:3000`

### 4. Connect to Backend

**Make sure your backend is running first:**
- The backend should be serving on `http://192.168.1.100:8000` (or your IP)
- The WebSocket endpoint should be `/ws/detections`

**Connection Status:**
- Green indicator = Connected to backend
- Red indicator = Disconnected
- Will automatically attempt to reconnect every 2 seconds

## Backend Requirements

Your backend MUST send WebSocket messages in this format:

```json
{
  "frame_id": 123,
  "timestamp": 1698765432000,
  "detections": [
    {
      "bbox": [100, 50, 200, 150],
      "confidence": 0.95,
      "class_id": 0,
      "class_name": "Product",
      "center": [150, 100]
    }
  ],
  "inventory": {
    "total_objects": 45,
    "class_counts": {
      "Product": 30,
      "Box": 12,
      "Shelf": 3
    },
    "density_score": 0.75,
    "coverage_ratio": 0.82
  },
  "density_map": [
    [0.5, 0.7, 0.6],
    [0.8, 0.9, 0.7],
    [0.6, 0.7, 0.5]
  ],
  "system_health": {
    "cpu_usage": 45.2,
    "memory_usage": 62.1,
    "connection_latency": 12,
    "uptime": 3600
  }
}
```

## Features

### Live Data Display
- Real-time FPS counter
- Connection status indicator
- Last update timestamp

### Object Detection
- Live camera feed with bounding boxes
- Confidence scores for each detection
- Color-coded by object class
- Detected object count breakdown

### Inventory Tracking
- Total object count with animation
- Per-class inventory breakdown
- Density score and coverage ratio

### System Health Monitoring
- CPU usage percentage
- Memory usage percentage
- Connection latency
- System uptime

### Analytics
- 60-second rolling trend chart
- Shelf density heatmap (2x2, 3x3, or 4x4 grid)

### Controls
- Change WebSocket URL at runtime
- Select detection model (YOLOv8n/s/m)
- Adjust heatmap grid size
- Export data button

## Troubleshooting

### "Waiting for data from backend..."
1. Check if backend is running
2. Verify WebSocket URL is correct in sidebar
3. Check network connectivity
4. Ensure backend is sending messages every 30ms (for 30 FPS)

### Connection keeps dropping
1. Check backend logs for errors
2. Ensure system resources aren't exhausted
3. Verify network is stable
4. Try restarting backend

### Detections not showing
1. Verify YOLO model is loaded correctly in backend
2. Check detection confidence threshold (default 0.5)
3. Ensure camera feed is properly configured

### High latency
1. Check CPU/Memory usage on Raspberry Pi
2. Verify network bandwidth
3. Reduce frame resolution if needed
4. Move Raspberry Pi closer to router

## Backend Example Code

See `backend_example.py` for a complete FastAPI implementation with:
- YOLOv8 integration
- System health monitoring
- WebSocket streaming
- Proper error handling

## Deployment

### To Production
1. Use `wss://` instead of `ws://` for secure WebSocket
2. Set `NEXT_PUBLIC_WS_URL` environment variable in Vercel dashboard
3. Deploy to Vercel: `vercel deploy`
4. Ensure backend is accessible from your domain

### To Raspberry Pi
1. Run development build: `npm run build`
2. Copy to Pi: `scp -r .next pi@192.168.1.100:/path/to/app`
3. Start with PM2 or systemd service
