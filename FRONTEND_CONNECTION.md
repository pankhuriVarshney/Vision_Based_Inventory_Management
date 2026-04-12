# 🔌 Frontend-Backend Connection Guide

## ✅ **Status: NOW CONNECTED TO REAL DATA!**

Your frontend is now configured to use **real API data** from your backend.

---

## 🎯 **What Changed**

### **Before:**
```typescript
// Using mock data (simulated)
useInventoryStream({ useMock: true })
```

### **After:**
```typescript
// Using real WebSocket data from backend
useInventoryStream({ 
  useMock: false,
  wsUrl: 'ws://localhost:8000/ws/inventory'
})
```

---

## 🚀 **How to Test Real-Time Connection**

### **Step 1: Start Backend API**

```bash
cd ~/Vision_Inventory
python3 run.py api --host 0.0.0.0 --port 8000
```

**Expected Output:**
```
🚀 Starting Inventory Management API...
✅ API ready on http://0.0.0.0:8000
📊 Model loaded: models/best.pt
```

### **Step 2: Start Frontend**

```bash
cd ~/Vision_Inventory/frontend

# Development mode
npm run dev

# OR production build
npm run build
npm run start
```

**Expected Output:**
```
✓ Ready in 1234ms
○ Local: http://localhost:3000
```

### **Step 3: Access Dashboard**

Open browser: `http://<YOUR-PI-IP>:3000`

### **Step 4: Verify Connection**

**Check these indicators:**

1. **Top Right Corner** - Should show connection status
   - 🟢 Green = Connected to backend
   - 🔴 Red = Disconnected

2. **Live Stream View** - Navigate to "Live Stream" in sidebar
   - Click "Start Stream"
   - Should show real video feed
   - Detections should appear
   - Inventory count should update

3. **Browser Console** - Press F12
   - Should NOT see WebSocket errors
   - Should see API requests succeeding

---

## 🧪 **Test Each Component**

### **Test 1: API Health Check**

In browser console (F12):
```javascript
fetch('http://localhost:8000/api/health')
  .then(r => r.json())
  .then(d => console.log('API Health:', d))
```

**Expected:**
```json
{
  "success": true,
  "data": {
    "status": "healthy",
    "detector_loaded": true
  }
}
```

### **Test 2: WebSocket Connection**

In browser console:
```javascript
const ws = new WebSocket('ws://localhost:8000/ws/inventory');
ws.onopen = () => console.log('✅ WebSocket Connected');
ws.onmessage = (e) => console.log('📊 Data:', JSON.parse(e.data));
ws.onerror = (e) => console.log('❌ Error:', e);
```

**Expected:**
```
✅ WebSocket Connected
📊 Data: {success: true, inventory: {...}, timestamp: ...}
```

### **Test 3: Live Video Stream**

In browser console:
```javascript
const ws = new WebSocket('ws://localhost:8000/ws/video');
ws.onopen = () => {
  console.log('✅ Video WebSocket Connected');
  ws.send(JSON.stringify({source: '0'})); // Start webcam
};
ws.onmessage = (e) => {
  const data = JSON.parse(e.data);
  console.log('📹 Frame received:', data.detections.length, 'detections');
};
```

**Expected:**
```
✅ Video WebSocket Connected
📹 Frame received: 5 detections
📹 Frame received: 5 detections
...
```

---

## 📊 **Real-Time Data Flow**

```
┌──────────────┐
│   Camera     │
│   (Webcam)   │
└──────┬───────┘
       │
       ▼
┌──────────────┐
│  FastAPI     │
│  Backend     │
│  (Port 8000) │
└──────┬───────┘
       │
       │ WebSocket
       │ /ws/video
       │
       ▼
┌──────────────┐
│  Next.js     │
│  Frontend    │
│  (Port 3000) │
└──────┬───────┘
       │
       ▼
┌──────────────┐
│   Browser    │
│   Display    │
└──────────────┘
```

---

## ⚙️ **Configuration for Different Environments**

### **Development (Localhost)**

**File: `frontend/.env.local`**
```env
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_WS_URL=ws://localhost:8000
```

### **Production (Raspberry Pi)**

**File: `frontend/.env.local`**
```env
# Replace with your Pi's actual IP
NEXT_PUBLIC_API_URL=http://192.168.1.100:8000
NEXT_PUBLIC_WS_URL=ws://192.168.1.100:8000
```

### **Remote Access**

**File: `frontend/.env.local`**
```env
# Use Pi's network hostname
NEXT_PUBLIC_API_URL=http://inventory-pi.local:8000
NEXT_PUBLIC_WS_URL=ws://inventory-pi.local:8000
```

---

## 🔧 **Troubleshooting**

### **Frontend Shows "Disconnected"**

**Check:**
```bash
# Is API running?
curl http://localhost:8000/api/health

# Is WebSocket accessible?
wscat -c ws://localhost:8000/ws/inventory
```

**Fix:**
```bash
# Restart API
cd ~/Vision_Inventory
python3 run.py api
```

### **Video Stream Not Working**

**Check:**
1. Camera is connected: `ls -l /dev/video*`
2. API has model loaded: Check API logs
3. WebSocket is open: Browser console should show "Connected"

**Fix:**
```bash
# Test camera directly
libcamera-hello -t 5000

# Test API detection
curl -X POST http://localhost:8000/api/detect/image \
  -F "file=@test_image.jpg"
```

### **CORS Errors in Browser**

**Check API logs for CORS configuration**

**Fix:** The API already has CORS enabled for all origins. If you see CORS errors:
```bash
# Check API is running with CORS
curl -v http://localhost:8000/api/health
# Look for: Access-Control-Allow-Origin: *
```

---

## ✅ **Connection Checklist**

- [ ] API running on port 8000
- [ ] Frontend running on port 3000
- [ ] `.env.local` file created with correct URLs
- [ ] Browser shows green connection indicator
- [ ] "Live Stream" view shows real video
- [ ] Detections appear on screen
- [ ] Inventory count updates in real-time
- [ ] No errors in browser console
- [ ] WebSocket shows "Connected" status

---

## 🎯 **Quick Verification Command**

Run this in your browser console on the dashboard page:

```javascript
// Test API connection
fetch('/api/health')
  .then(r => r.json())
  .then(d => {
    console.log('✅ API Status:', d.data.status);
    console.log('✅ Detector Loaded:', d.data.detector_loaded);
  });

// Test WebSocket
const ws = new WebSocket(window.location.origin.replace('http', 'ws') + '/ws/inventory');
ws.onopen = () => console.log('✅ WebSocket: Connected');
ws.onmessage = (e) => console.log('📊 Real-time data received!');
```

**Expected Output:**
```
✅ API Status: healthy
✅ Detector Loaded: true
✅ WebSocket: Connected
📊 Real-time data received!
```

---

## 🎉 **Success!**

If you see the above outputs, your frontend is **100% connected to real backend data**!

**Your dashboard now shows:**
- ✅ Real-time video from camera
- ✅ Actual detection results
- ✅ Live inventory counts
- ✅ Real FPS and latency stats
- ✅ True inventory history

---

**No more mock data! Everything is live! 🚀**
