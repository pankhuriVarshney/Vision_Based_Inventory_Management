# 🥧 Raspberry Pi Hardware Deployment Guide

Complete step-by-step guide to deploy the Vision-Based Inventory Management System on Raspberry Pi 5.

---

## 📦 **Hardware Requirements**

### **From Your Project Report (Section 4.3)**

| Component | Model | Cost (₹) |
|-----------|-------|----------|
| Raspberry Pi 5 | 8GB variant | 11,000 |
| Camera | Raspberry Pi High Quality Camera with 6mm lens | 1,500 |
| Lighting | Programmable LED Ring Light | 1,000 |
| Pan-Tilt | 2x Micro Servo Motors | 800 |
| Power | 12V Li-ion Battery (3S, 10Ah) + Buck Converter | 1,100 |
| Display | 7" Capacitive Touchscreen | 1,800 |
| Enclosure | Custom 3D-printed mount | 500 |
| **TOTAL** | | **₹16,700** |

### **Additional Items Needed**

- MicroSD card (32GB minimum, Class 10 recommended)
- USB keyboard and mouse (for initial setup)
- HDMI cable (for display)
- Ethernet cable (for initial network setup)
- USB webcam (alternative to Pi Camera)

---

## 🔧 **Step 1: Raspberry Pi Imager Setup**

### **1.1 Download Raspberry Pi Imager**

1. Go to: https://www.raspberrypi.com/software/
2. Download for your OS (Windows/Mac/Linux)
3. Install and launch the application

### **1.2 Configure OS Image**

**CHOOSE OS:**
- Select: **Raspberry Pi OS (64-bit)**
- Version: **Bookworm** (latest)
- ⚠️ **IMPORTANT:** Must be 64-bit for ROS2 Humble!

**CHOOSE STORAGE:**
- Select your MicroSD card

**CHOOSE OPTIONS** (⚙️ icon):
- ✅ **Enable SSH:** Use password authentication
- ✅ **Set username and password:**
  - Username: `pi`
  - Password: `raspberry` (change later!)
- ✅ **Configure wireless LAN:**
  - SSID: Your WiFi network
  - Password: Your WiFi password
  - Country: `IN` (India)
- ✅ **Set local settings:**
  - Timezone: `Asia/Kolkata`
  - Keyboard layout: Default
- ✅ **Enable telemetry:** Optional

### **1.3 Write Image**

1. Click **SAVE**
2. Click **WRITE**
3. Wait for completion (~10 minutes)
4. Safely eject the MicroSD card

---

## 🔌 **Step 2: Hardware Assembly**

### **2.1 Camera Module Connection**

**For Raspberry Pi High Quality Camera:**

```
1. Insert FPC cable into camera module
   - Gold contacts facing AWAY from lens mount

2. Connect FPC cable to Raspberry Pi
   - Open CSI port latch (pull up)
   - Insert cable with contacts facing TOWARD Ethernet ports
   - Push latch down to lock

3. Attach 6mm lens
   - Screw onto camera mount
   - Adjust focus by rotating lens
```

**For USB Webcam (Alternative):**
```
1. Plug USB webcam into USB 3.0 port (blue)
2. System will auto-detect
```

### **2.2 LED Ring Light Connection**

```
LED Ring Light → GPIO Pins:

LED Ring Light     Raspberry Pi GPIO
--------------     -----------------
VCC (5V)        →  GPIO Pin 4 (5V Power)
GND             →  GPIO Pin 6 (Ground)
DATA IN         →  GPIO Pin 12 (GPIO18 / PWM)

Note: Use a separate 5V power supply for LED ring if drawing >500mA
```

### **2.3 Pan-Tilt Servo Connection**

```
Servo Motor 1 (Pan)   Raspberry Pi GPIO
------------------   ------------------
VCC (5V)           →  GPIO Pin 2 (5V Power)
GND                →  GPIO Pin 9 (Ground)
Signal             →  GPIO Pin 11 (GPIO17)

Servo Motor 2 (Tilt)  Raspberry Pi GPIO
------------------   ------------------
VCC (5V)           →  GPIO Pin 2 (5V Power)
GND                →  GPIO Pin 9 (Ground)
Signal             →  GPIO Pin 13 (GPIO27)

⚠️ IMPORTANT: Use external 5V power supply for servos!
```

### **2.4 Display Connection**

```
7" Touchscreen → DSI Port on Raspberry Pi
- Connect DSI cable carefully
- Enable DSI in raspi-config
```

### **2.5 Power Connection**

```
12V Li-ion Battery → Buck Converter → Raspberry Pi

Battery (12V)   →  Buck Converter Input
Buck Converter  →  Set output to 5.1V
Buck Output     →  USB-C port on Pi 5

⚠️ Pi 5 requires 5.1V/5A USB-C power supply
```

---

## 💻 **Step 3: First Boot & Initial Setup**

### **3.1 Boot Raspberry Pi**

1. Insert MicroSD card
2. Connect Ethernet cable (for initial setup)
3. Connect HDMI display (optional)
4. Connect USB keyboard/mouse (optional)
5. Power on Raspberry Pi

### **3.2 Find Pi's IP Address**

**Option A: From Router**
- Check your router's connected devices list
- Look for "raspberrypi"

**Option B: Using Network Scanner**
```bash
# On your computer
nmap -sn 192.168.1.0/24
# Look for Raspberry Pi Foundation vendor
```

**Option C: From Pi (if display connected)**
```bash
hostname -I
```

### **3.3 SSH into Raspberry Pi**

```bash
# From Windows (PowerShell)
ssh pi@<raspberry-pi-ip>
# Password: raspberry

# From Mac/Linux
ssh pi@<raspberry-pi-ip>
# Password: raspberry
```

**Change password immediately:**
```bash
passwd
```

---

## 📥 **Step 4: Install System Dependencies**

### **4.1 Update System**

```bash
sudo apt update
sudo apt upgrade -y
sudo reboot
```

### **4.2 Install Python Dependencies**

```bash
# Install Python 3.11+
sudo apt install -y python3 python3-pip python3-venv python3-dev

# Install system dependencies for OpenCV
sudo apt install -y \
    libatlas-base-dev \
    libjasper-dev \
    libqtgui4 \
    libqt4-test \
    libilmbase-dev \
    libopenexr-dev
```

### **4.3 Install ROS2 Humble**

```bash
# Set locale
sudo locale-gen en_US en_US.UTF-8
sudo update-locale LC_ALL=en_US.UTF-8 LANG=en_US.UTF-8

# Add ROS2 repository
sudo apt install -y software-properties-common
sudo add-apt-repository universe
sudo apt update
sudo apt install -y curl
curl -sSL https://raw.githubusercontent.com/ros/rosdistro/master/ros.key | sudo apt-key add -
sudo sh -c 'echo "deb http://packages.ros.org/ros2/ubuntu jammy main" > /etc/apt/sources.list.d/ros2.list'

# Install ROS2 Humble Desktop
sudo apt update
sudo apt install -y ros-humble-desktop

# Install additional ROS2 packages
sudo apt install -y \
    ros-humble-rclpy \
    ros-humble-sensor-msgs \
    ros-humble-vision-msgs \
    ros-humble-cv-bridge \
    ros-humble-image-transport

# Source ROS2
echo "source /opt/ros/humble/setup.bash" >> ~/.bashrc
source ~/.bashrc

# Verify installation
ros2 --version
```

### **4.4 Install Camera Support**

```bash
# Enable camera interface
sudo raspi-config nonint do_camera 0

# For legacy camera support (if needed)
echo "dtoverlay=vc4-kms-v3d" | sudo tee -a /boot/config.txt

# Reboot
sudo reboot
```

### **4.5 Test Camera**

```bash
# Install camera tools
sudo apt install -y libcamera-apps

# Test camera
libcamera-hello -t 5000

# Or for USB webcam
sudo apt install -y fswebcam
fswebcam -r 640x480 test.jpg
```

---

## 📂 **Step 5: Deploy Code to Raspberry Pi**

### **Option A: Using Git (Recommended)**

```bash
# On Raspberry Pi
cd ~
git clone <your-repository-url> Vision_Inventory
cd Vision_Inventory

# Install Python dependencies
pip3 install -r requirements.txt
```

### **Option B: Using SCP**

```bash
# From your computer (not Pi)
cd Documents/Vision_Based_Inventory_Management

# Copy entire project to Pi
scp -r . pi@<raspberry-pi-ip>:~/Vision_Inventory

# SSH to Pi
ssh pi@<raspberry-pi-ip>
cd ~/Vision_Inventory

# Install dependencies
pip3 install -r requirements.txt
```

### **Option C: Using USB Drive**

```bash
# Copy project to USB drive from your computer
# Plug USB into Raspberry Pi

# Mount USB (usually auto-mounted)
cd /media/pi/<USB-NAME>

# Copy to home directory
cp -r . ~/Vision_Inventory
cd ~/Vision_Inventory

# Install dependencies
pip3 install -r requirements.txt
```

---

## 🏗️ **Step 6: Build ROS2 Package**

```bash
# Navigate to ROS2 package
cd ~/Vision_Inventory/ros2_inventory

# Install rosdep
sudo apt install -y python3-rosdep
sudo rosdep init
rosdep update

# Install package dependencies
rosdep install --from-paths . --ignore-src -r -y

# Build package
colcon build --symlink-install

# Source the workspace
source install/setup.bash

# Add to .bashrc for persistence
echo "source ~/Vision_Inventory/ros2_inventory/install/setup.bash" >> ~/.bashrc
source ~/.bashrc
```

---

## ⚙️ **Step 7: Configure System**

### **7.1 Create Configuration File**

```bash
# Create config directory
mkdir -p ~/Vision_Inventory/config

# Create configuration file
nano ~/Vision_Inventory/config/pi_config.yaml
```

**Add this content:**

```yaml
camera:
  device: 0  # 0 for USB webcam, use libcamera for Pi Camera
  width: 640
  height: 480
  fps: 30

detection:
  model_path: "/home/pi/Vision_Inventory/models/rpc_real_labels/weights/best.pt"
  conf_threshold: 0.25
  iou_threshold: 0.45
  device: "cpu"

api:
  host: "0.0.0.0"
  port: 8000

ros2:
  enabled: true
  domain_id: 0
```

### **7.2 Export Model for Pi (TFLite)**

```bash
cd ~/Vision_Inventory

# Export to TFLite with INT8 quantization
python3 src/export_model.py \
  --model models/rpc_real_labels/weights/best.pt \
  --format tflite \
  --int8 \
  --benchmark
```

---

## 🚀 **Step 8: Run the System**

### **Option 1: Run API Server Only**

```bash
cd ~/Vision_Inventory
python3 run.py api --host 0.0.0.0 --port 8000
```

**Access from browser:**
- API: `http://<raspberry-pi-ip>:8000`
- API Docs: `http://<raspberry-pi-ip>:8000/docs`

### **Option 2: Run ROS2 System**

**Terminal 1 - Launch all nodes:**
```bash
source /opt/ros/humble/setup.bash
cd ~/Vision_Inventory/ros2_inventory
ros2 launch ros2_inventory inventory_system.launch.py
```

**Terminal 2 - Monitor topics:**
```bash
# List nodes
ros2 node list

# View camera feed
ros2 topic echo /camera/image_raw

# View detections
ros2 topic echo /detections

# View inventory
ros2 topic echo /inventory_status
```

### **Option 3: Run Detection Directly**

```bash
cd ~/Vision_Inventory

# Run detection with USB webcam
python3 run.py detect --source 0 --model models/best.pt

# Run detection with video file
python3 run.py detect --source shelf_video.mp4 --model models/best.pt
```

---

## 🔄 **Step 9: Configure Autostart**

### **Create Systemd Service for API**

```bash
sudo nano /etc/systemd/system/inventory-api.service
```

**Add this content:**

```ini
[Unit]
Description=Vision Inventory API
After=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/Vision_Inventory
Environment="PATH=/home/pi/.local/bin:/usr/bin:/bin"
ExecStart=/usr/bin/python3 -m src.api --host 0.0.0.0 --port 8000
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**Enable service:**

```bash
# Reload systemd
sudo systemctl daemon-reload

# Enable service
sudo systemctl enable inventory-api.service

# Start service
sudo systemctl start inventory-api.service

# Check status
sudo systemctl status inventory-api.service
```

### **Create Systemd Service for ROS2**

```bash
sudo nano /etc/systemd/system/inventory-ros2.service
```

**Add this content:**

```ini
[Unit]
Description=Vision Inventory ROS2 System
After=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/Vision_Inventory/ros2_inventory
Environment="PATH=/opt/ros/humble/bin:/home/pi/.local/bin:/usr/bin:/bin"
Environment="ROS_DOMAIN_ID=0"
ExecStart=/bin/bash -c "source /opt/ros/humble/setup.bash && ros2 launch ros2_inventory inventory_system.launch.py"
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**Enable service:**

```bash
sudo systemctl daemon-reload
sudo systemctl enable inventory-ros2.service
sudo systemctl start inventory-ros2.service
sudo systemctl status inventory-ros2.service
```

---

## 🧪 **Step 10: Testing & Verification**

### **Test 1: API Health Check**

```bash
# From Raspberry Pi
curl http://localhost:8000/api/health

# From another computer
curl http://<raspberry-pi-ip>:8000/api/health
```

**Expected response:**
```json
{
  "success": true,
  "data": {
    "status": "healthy",
    "detector_loaded": true
  }
}
```

### **Test 2: Camera Feed**

```bash
# Test with OpenCV
python3 -c "
import cv2
cap = cv2.VideoCapture(0)
ret, frame = cap.read()
print(f'Camera working: {ret}')
cap.release()
"
```

### **Test 3: Detection**

```bash
# Take a photo and detect
fswebcam -r 640x480 test_shelf.jpg

python3 -c "
from src.inference import InventoryDetector
detector = InventoryDetector(model_path='models/best.pt')
result = detector.detect_image('test_shelf.jpg')
print(f'Detected {result[\"inventory\"][\"total_objects\"]} items')
"
```

### **Test 4: ROS2 Nodes**

```bash
# List all active nodes
ros2 node list

# Should show:
# /camera_node
# /detection_node
# /inventory_node
# /api_bridge_node
```

### **Test 5: Web Dashboard**

1. Open browser on any device
2. Go to: `http://<raspberry-pi-ip>:8000/docs`
3. Try the `/api/detect/image` endpoint
4. Upload a test image
5. Verify detection results

---

## 🔧 **Troubleshooting**

### **Camera Not Working**

```bash
# Check if camera is detected
ls -l /dev/video*

# For Pi Camera Module
vcgencmd get_camera

# Enable camera if disabled
sudo raspi-config
# Interface Options → Camera → Enable
```

### **ROS2 Nodes Not Starting**

```bash
# Check ROS2 installation
ros2 --version

# Source ROS2 again
source /opt/ros/humble/setup.bash

# Check for missing dependencies
cd ~/Vision_Inventory/ros2_inventory
rosdep install --from-paths . --ignore-src -r -y
```

### **API Won't Start**

```bash
# Check if port is in use
sudo netstat -tulpn | grep 8000

# Kill process using port 8000
sudo kill -9 <PID>

# Check Python path
which python3
python3 --version
```

### **Model Not Loading**

```bash
# Verify model exists
ls -lh models/best.pt

# Check model path in code
# Edit ros2_inventory/config/params.yaml if needed
```

### **Performance Issues**

```bash
# Monitor CPU usage
top

# Monitor temperature
vcgencmd measure_temp

# If overheating, add heatsink/fan
```

---

## 📊 **Expected Performance on Raspberry Pi 5**

| Metric | Value |
|--------|-------|
| Model | YOLOv8n TFLite (INT8) |
| Image Size | 640x480 |
| Inference Time | ~60-70ms |
| FPS | 14-16 FPS |
| CPU Usage | ~80-90% |
| RAM Usage | ~500MB |
| Temperature | 50-60°C (with heatsink) |

---

## 🎯 **Final Checklist**

- [ ] Raspberry Pi Imager used with 64-bit OS
- [ ] Camera connected and working
- [ ] ROS2 Humble installed
- [ ] Code deployed to Pi
- [ ] ROS2 package built
- [ ] API server running
- [ ] ROS2 nodes running
- [ ] Can access API from browser
- [ ] Detection working
- [ ] Autostart configured

---

## 📞 **Next Steps After Deployment**

1. **Mount in Enclosure:** 3D print and assemble the enclosure
2. **Position Camera:** Aim at shelf with appropriate angle
3. **Configure LED:** Set up LED ring for consistent lighting
4. **Test in Real Environment:** Deploy to actual shelf location
5. **Monitor Performance:** Check logs and adjust parameters
6. **Set Up Continual Learning:** Implement Phase 3 from your report

---

## 📚 **Useful Commands Reference**

```bash
# Service management
sudo systemctl start inventory-api
sudo systemctl stop inventory-api
sudo systemctl restart inventory-api
sudo systemctl status inventory-api

# ROS2 commands
ros2 node list
ros2 topic list
ros2 topic echo /inventory_status
ros2 launch ros2_inventory inventory_system.launch.py

# Process monitoring
top
htop
vcgencmd measure_temp
free -h

# Network
hostname -I
ifconfig
ping google.com
```

---

**🎉 Your system is now deployed and running on Raspberry Pi!**

For any issues, check the troubleshooting section or refer to the logs:
```bash
journalctl -u inventory-api -f
journalctl -u inventory-ros2 -f
```
