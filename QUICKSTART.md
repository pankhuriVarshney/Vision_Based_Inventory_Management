# 🚀 Quick Start Guide

This guide will help you get the Vision-Based Inventory Management System up and running in under 10 minutes.

---

## **Prerequisites**

- Python 3.8 or higher
- Node.js 18 or higher
- Git (optional, for cloning)
- Webcam or video file (for testing)

---

## **Step 1: Install Dependencies**

### **Python Backend**

```bash
# Navigate to project directory
cd Vision_Based_Inventory_Management

# Install Python dependencies
pip install -r requirements.txt
```

### **Frontend**

```bash
# Navigate to frontend directory
cd frontend

# Install Node.js dependencies
npm install

# Return to root
cd ..
```

---

## **Step 2: Verify Installation**

```bash
# Test Python installation
python -c "from ultralytics import YOLO; print('✅ YOLO installed')"

# Test frontend
cd frontend && npm run build
cd ..
```

---

## **Step 3: Start the API Server**

### **Option A: Using run.py (Recommended)**

```bash
python run.py api --host 0.0.0.0 --port 8000
```

### **Option B: Direct execution**

```bash
python src/api.py --host 0.0.0.0 --port 8000
```

### **Option C: With uvicorn**

```bash
uvicorn src.api:app --reload --host 0.0.0.0 --port 8000
```

**✅ API should be running at:** `http://localhost:8000`
**📚 API Documentation:** `http://localhost:8000/docs`

---

## **Step 4: Start the Frontend**

Open a **new terminal** window:

```bash
cd frontend
npm run dev
```

**✅ Frontend should be running at:** `http://localhost:3000`

---

## **Step 5: Test the System**

### **Test via Web Interface**

1. Open browser: `http://localhost:3000`
2. Navigate to **"Live Stream"** in the sidebar
3. Click **"Start Stream"**
4. You should see live video with detections

### **Test via API**

```bash
# Health check
curl http://localhost:8000/api/health

# Should return:
# {"success": true, "data": {"status": "healthy", ...}}
```

### **Test Detection**

```bash
# If you have an image
curl -X POST http://localhost:8000/api/detect/image \
  -F "file=@path/to/your/image.jpg"

# Or use the API documentation UI
# Go to: http://localhost:8000/docs
# Find POST /api/detect/image
# Click "Try it out" and upload an image
```

---

## **Step 6: Train Your Own Model (Optional)**

### **Download Dataset**

```bash
python run.py preprocess
```

### **Train Model**

```bash
python run.py train
```

### **Test Trained Model**

```bash
python run.py detect --source 0 --model models/rpc_real_labels/weights/best.pt
```

---

## **Common Issues & Solutions**

### **Issue: Port 8000 already in use**

**Solution:** Use a different port

```bash
python run.py api --port 8001
```

### **Issue: Cannot open camera**

**Solution:** Check camera index

```bash
# Try different camera indices
python run.py detect --source 0  # Default
python run.py detect --source 1  # Second camera
```

### **Issue: Frontend won't connect to API**

**Solution:** Check `.env` file in `frontend` directory

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### **Issue: Module not found**

**Solution:** Reinstall dependencies

```bash
pip install -r requirements.txt --upgrade
```

---

## **Next Steps**

### **1. Explore API Documentation**

Visit `http://localhost:8000/docs` to see all available endpoints and test them interactively.

### **2. Configure ROS2 for Hardware**

See `README.md` section on ROS2 deployment for Raspberry Pi setup.

### **3. Customize the Dashboard**

Edit components in `frontend/components/` to customize the UI.

### **4. Export Model for Deployment**

```bash
# Export to TFLite for Raspberry Pi
python src/export_model.py --model models/best.pt --format tflite --int8
```

---

## **Project Commands Summary**

```bash
# Backend
python run.py setup          # Install dependencies
python run.py preprocess     # Download & prepare dataset
python run.py train          # Train model
python run.py detect         # Run detection
python run.py api            # Start API server
python run.py ros2           # Launch ROS2 system

# Frontend
cd frontend
npm run dev      # Development server
npm run build    # Build for production
npm run start    # Start production server
```

---

## **Getting Help**

- 📚 Full documentation: `README.md`
- 🐛 Report issues: Create an issue on GitHub
- 💬 Questions: Check API docs at `/docs`

---

## **Success Checklist**

- [ ] API server running on port 8000
- [ ] Frontend running on port 3000
- [ ] Can access API docs at `/docs`
- [ ] Can see live video stream
- [ ] Detections appearing on video
- [ ] Inventory counts updating

**🎉 If all boxes are checked, you're ready to go!**
