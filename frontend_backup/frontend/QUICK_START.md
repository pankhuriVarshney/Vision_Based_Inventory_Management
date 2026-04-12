# Quick Start Guide

## 1. Configure Backend URL

Create `.env.local` in project root:
```
NEXT_PUBLIC_WS_URL=ws://192.168.1.100:8000/ws/detections
```

Replace `192.168.1.100` with your Raspberry Pi's IP address.

## 2. Start Frontend

```bash
npm run dev
```

Open `http://localhost:3000` in your browser.

## 3. Start Backend

Your backend should send WebSocket messages to this endpoint:
```
ws://localhost:8000/ws/detections
```

**Required message format:**
```json
{
  "frame_id": 1,
  "timestamp": 1698765432000,
  "detections": [
    {
      "bbox": [x1, y1, x2, y2],
      "confidence": 0.95,
      "class_id": 0,
      "class_name": "Product",
      "center": [x, y]
    }
  ],
  "inventory": {
    "total_objects": 45,
    "class_counts": {"Product": 30, "Box": 12, "Shelf": 3},
    "density_score": 0.75,
    "coverage_ratio": 0.82
  },
  "density_map": [[0.5, 0.7, 0.6], [0.8, 0.9, 0.7], [0.6, 0.7, 0.5]],
  "system_health": {
    "cpu_usage": 45.2,
    "memory_usage": 62.1,
    "connection_latency": 12,
    "uptime": 3600
  }
}
```

## 4. Verify Connection

- Dashboard should show "Live" status (green indicator)
- Check FPS counter (should show > 0)
- Verify object detections appear on canvas
- System health metrics should update

## Connection Issues?

- Use sidebar to change WebSocket URL without restarting
- Check browser console for connection errors
- Verify backend is sending messages continuously
- Ensure firewall allows WebSocket connections

## Files Overview

- **`app/page.tsx`** - Main dashboard (all real data, no mock)
- **`config.ts`** - Configuration constants and settings
- **`.env.local`** - Environment variables (create from `.env.local.example`)
- **`SETUP.md`** - Detailed setup and troubleshooting
- **`BACKEND_API_SPEC.md`** - Backend requirements and specification
- **`backend_example.py`** - Example backend implementation
