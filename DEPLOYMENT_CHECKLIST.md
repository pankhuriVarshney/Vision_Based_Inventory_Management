# 📋 Raspberry Pi Deployment Checklist

Print this checklist and use it during your Raspberry Pi deployment!

---

## 📦 **Pre-Deployment (At Home/Office)**

### **Hardware Preparation**

- [ ] Raspberry Pi 5 (8GB) with heatsink
- [ ] MicroSD card (32GB+)
- [ ] Raspberry Pi High Quality Camera
- [ ] 6mm lens
- [ ] LED ring light
- [ ] 2x Micro servos (pan-tilt)
- [ ] 7" touchscreen display
- [ ] 12V Li-ion battery (3S, 10Ah)
- [ ] Buck converter (12V → 5V)
- [ ] USB-C cable
- [ ] FPC cable (for camera)
- [ ] DSI cable (for display)
- [ ] Jumper wires (F/F, M/F, M/M)
- [ ] 3D printed enclosure
- [ ] Screws and standoffs (M3)
- [ ] Cable ties

### **Tools Needed**

- [ ] Small screwdriver set
- [ ] Multimeter
- [ ] Wire strippers
- [ ] Soldering iron (optional)
- [ ] Hot glue gun
- [ ] Cable ties
- [ ] Tweezers
- [ ] Scissors

### **Software Preparation (On Your Laptop)**

- [ ] Download Raspberry Pi Imager
- [ ] Download Raspberry Pi OS 64-bit image
- [ ] Clone/pull latest code from repository
- [ ] Test code locally: `python run.py api`
- [ ] Export model for Pi: `python export_model.py --format tflite`
- [ ] Copy model to project folder
- [ ] Test frontend build: `cd frontend && npm run build`

---

## 💾 **Step 1: Raspberry Pi Imager**

- [ ] Insert MicroSD card into computer
- [ ] Open Raspberry Pi Imager
- [ ] **CHOOSE OS:** Raspberry Pi OS (64-bit) ← MUST be 64-bit!
- [ ] **CHOOSE STORAGE:** Select MicroSD card
- [ ] **CHOOSE OPTIONS (⚙️):**
  - [ ] Enable SSH
  - [ ] Set username: `pi`
  - [ ] Set password: `raspberry` (change later!)
  - [ ] Configure WiFi (SSID + password)
  - [ ] Set timezone: `Asia/Kolkata`
  - [ ] Set keyboard layout
- [ ] Click **WRITE**
- [ ] Wait for completion (~10 min)
- [ ] Safely eject MicroSD card

**Time:** ~15 minutes

---

## 🔌 **Step 2: Hardware Assembly**

### **Camera Module**

- [ ] Insert FPC cable into camera module (gold contacts away from lens)
- [ ] Attach 6mm lens to camera
- [ ] Open CSI port latch on Pi
- [ ] Insert FPC cable into CSI port (gold contacts toward Ethernet)
- [ ] Close latch to secure cable
- [ ] Mount camera in enclosure

### **LED Ring Light**

- [ ] Connect VCC (5V) → GPIO Pin 4
- [ ] Connect GND → GPIO Pin 6
- [ ] Connect DATA → GPIO Pin 12 (GPIO18)
- [ ] Secure LED ring around camera lens
- [ ] Add diffuser if available

### **Pan-Tilt Servos**

- [ ] Mount pan servo on base
- [ ] Mount tilt servo on camera bracket
- [ ] Connect Servo 1 (Pan):
  - [ ] VCC (Red) → Pin 2 (5V) **[External power!]**
  - [ ] GND (Brown) → Pin 9 (Ground)
  - [ ] Signal (Orange) → Pin 11 (GPIO17)
- [ ] Connect Servo 2 (Tilt):
  - [ ] VCC (Red) → Pin 2 (5V) **[External power!]**
  - [ ] GND (Brown) → Pin 9 (Ground)
  - [ ] Signal (Orange) → Pin 13 (GPIO27)

### **Display**

- [ ] Connect DSI cable to display
- [ ] Connect DSI cable to Pi DSI port
- [ ] Mount display in enclosure front panel

### **Power System**

- [ ] Connect battery to buck converter input
- [ ] Adjust buck converter to 5.1V (use multimeter!)
- [ ] Connect buck converter output to:
  - [ ] USB-C → Raspberry Pi
  - [ ] Servo VCC (red wires)
- [ ] Secure battery in enclosure
- [ ] Add power switch (optional)

### **Final Assembly**

- [ ] Mount Raspberry Pi in enclosure
- [ ] Route all cables through channels
- [ ] Secure all connections with cable ties
- [ ] Close enclosure
- [ ] Attach mounting bracket to wall/ceiling

**Time:** ~30-45 minutes

---

## 💻 **Step 3: First Boot & Setup**

### **Initial Boot**

- [ ] Insert MicroSD card into Raspberry Pi
- [ ] Connect Ethernet cable (for initial setup)
- [ ] Connect HDMI display (optional)
- [ ] Connect USB keyboard/mouse (optional)
- [ ] Power on Raspberry Pi
- [ ] Wait for boot (1-2 minutes)

### **Find Pi's IP Address**

- [ ] Check router for connected devices
- [ ] OR use network scanner: `nmap -sn 192.168.1.0/24`
- [ ] OR check HDMI display: `hostname -I`
- [ ] Write down IP address: _______________

### **SSH Connection**

- [ ] Open terminal/PowerShell on your computer
- [ ] Connect: `ssh pi@<IP-address>`
- [ ] Password: `raspberry`
- [ ] **Change password immediately:** `passwd`
- [ ] New password: _______________

**Time:** ~15 minutes

---

## 📥 **Step 4: Install Dependencies**

### **System Update**

- [ ] `sudo apt update`
- [ ] `sudo apt upgrade -y`
- [ ] `sudo reboot`
- [ ] Reconnect via SSH

### **Python Installation**

- [ ] `sudo apt install -y python3 python3-pip python3-venv`
- [ ] `pip3 install --upgrade pip`

### **ROS2 Installation**

- [ ] `sudo apt install -y software-properties-common`
- [ ] `sudo add-apt-repository universe`
- [ ] Add ROS2 repository key
- [ ] `sudo apt update`
- [ ] `sudo apt install -y ros-humble-desktop`
- [ ] `sudo apt install -y ros-humble-rclpy ros-humble-sensor-msgs`
- [ ] Add to `.bashrc`: `echo "source /opt/ros/humble/setup.bash" >> ~/.bashrc`
- [ ] `source ~/.bashrc`
- [ ] Verify: `ros2 --version`

### **Camera Support**

- [ ] `sudo apt install -y libcamera-apps`
- [ ] Enable camera: `sudo raspi-config` → Interface → Camera → Enable
- [ ] `sudo reboot`
- [ ] Test: `libcamera-hello -t 5000`

**Time:** ~30-40 minutes

---

## 📂 **Step 5: Deploy Code**

### **Transfer Code**

**Option A: Git**
- [ ] `cd ~`
- [ ] `git clone <repository-url> Vision_Inventory`

**Option B: SCP**
- [ ] From laptop: `scp -r . pi@<IP>:~/Vision_Inventory`

**Option C: USB Drive**
- [ ] Copy to USB
- [ ] Plug into Pi
- [ ] Copy to `~/Vision_Inventory`

### **Install Python Dependencies**

- [ ] `cd ~/Vision_Inventory`
- [ ] `pip3 install -r requirements.txt`
- [ ] Wait for installation (~10 min)

### **Build ROS2 Package**

- [ ] `cd ~/Vision_Inventory/ros2_inventory`
- [ ] `rosdep install --from-paths . --ignore-src -r -y`
- [ ] `colcon build --symlink-install`
- [ ] `source install/setup.bash`
- [ ] Add to `.bashrc`

### **Export Model**

- [ ] `cd ~/Vision_Inventory`
- [ ] `python3 src/export_model.py --model models/best.pt --format tflite --int8`
- [ ] Wait for export (~5 min)
- [ ] Verify TFLite model created

**Time:** ~20 minutes

---

## 🚀 **Step 6: Testing**

### **Camera Test**

- [ ] `libcamera-hello -t 5000`
- [ ] Camera preview appears
- [ ] Adjust focus if needed
- [ ] Press Ctrl+C to exit

### **API Test**

- [ ] `cd ~/Vision_Inventory`
- [ ] `python3 run.py api &`
- [ ] `curl http://localhost:8000/api/health`
- [ ] Response shows "healthy"
- [ ] Open browser: `http://<IP>:8000/docs`
- [ ] API documentation loads

### **Detection Test**

- [ ] `fswebcam -r 640x480 test.jpg`
- [ ] `python3 -c "from src.inference import InventoryDetector; d = InventoryDetector('models/best.tflite'); r = d.detect_image('test.jpg'); print(r['inventory']['total_objects'])"`
- [ ] Detection count displayed

### **ROS2 Test**

- [ ] `ros2 launch ros2_inventory inventory_system.launch.py`
- [ ] In new terminal: `ros2 node list`
- [ ] Shows: camera_node, detection_node, inventory_node, api_bridge_node
- [ ] `ros2 topic echo /inventory_status`
- [ ] Shows inventory data

### **Web Dashboard Test**

- [ ] Open browser on laptop/phone
- [ ] Go to: `http://<IP>:3000` (if frontend running)
- [ ] OR go to: `http://<IP>:8000/docs`
- [ ] Test API endpoints
- [ ] Upload test image
- [ ] Detection results appear

**Time:** ~20 minutes

---

## ⚙️ **Step 7: Configure Autostart**

### **Create API Service**

- [ ] `sudo nano /etc/systemd/system/inventory-api.service`
- [ ] Paste service configuration
- [ ] Save and exit (Ctrl+X, Y, Enter)
- [ ] `sudo systemctl daemon-reload`
- [ ] `sudo systemctl enable inventory-api.service`
- [ ] `sudo systemctl start inventory-api.service`
- [ ] `sudo systemctl status inventory-api.service`
- [ ] Should show "active (running)"

### **Create ROS2 Service** (Optional)

- [ ] `sudo nano /etc/systemd/system/inventory-ros2.service`
- [ ] Paste service configuration
- [ ] Save and exit
- [ ] `sudo systemctl daemon-reload`
- [ ] `sudo systemctl enable inventory-ros2.service`
- [ ] `sudo systemctl start inventory-ros2.service`
- [ ] `sudo systemctl status inventory-ros2.service`

### **Test Autostart**

- [ ] `sudo reboot`
- [ ] Wait 1 minute
- [ ] SSH back in
- [ ] `curl http://localhost:8000/api/health`
- [ ] API should be running automatically

**Time:** ~15 minutes

---

## 🎯 **Step 8: Final Deployment**

### **Position on Shelf**

- [ ] Mount enclosure overlooking shelf
- [ ] Adjust camera angle (30-45° downward)
- [ ] Ensure full shelf view
- [ ] Secure mounting brackets
- [ ] Connect power

### **Configure LED Lighting**

- [ ] Power on LED ring
- [ ] Adjust brightness (50-70%)
- [ ] Check for glare/reflections
- [ ] Adjust position if needed

### **Focus Camera**

- [ ] View live feed: `python3 run.py detect --source 0`
- [ ] Adjust lens focus ring
- [ ] Ensure sharp image
- [ ] Lock focus with set screw (if available)

### **Final Testing**

- [ ] Run system for 5 minutes
- [ ] Check detection accuracy
- [ ] Monitor temperature: `vcgencmd measure_temp`
- [ ] Should be < 70°C
- [ ] Check power voltage: `vcgencmd measure_volts`
- [ ] Should be ~5.1V

### **Documentation**

- [ ] Take photos of final setup
- [ ] Note IP address: _______________
- [ ] Note WiFi network: _______________
- [ ] Note power consumption: _______________
- [ ] Label device with name/ID

**Time:** ~20 minutes

---

## 📊 **Total Time Summary**

| Step | Time |
|------|------|
| Raspberry Pi Imager | 15 min |
| Hardware Assembly | 45 min |
| First Boot & Setup | 15 min |
| Install Dependencies | 40 min |
| Deploy Code | 20 min |
| Testing | 20 min |
| Configure Autostart | 15 min |
| Final Deployment | 20 min |
| **TOTAL** | **~3 hours** |

---

## ✅ **Final Verification Checklist**

- [ ] Camera working and focused
- [ ] LED lighting properly positioned
- [ ] Detection running (14-16 FPS expected)
- [ ] API accessible from network
- [ ] ROS2 nodes running
- [ ] Autostart configured
- [ ] System stable after reboot
- [ ] Temperature normal (< 70°C)
- [ ] All connections secure
- [ ] Enclosure properly mounted

---

## 📝 **Notes & Configuration**

**WiFi Network:** _________________________

**WiFi Password:** _________________________

**Pi IP Address:** _________________________

**SSH Password:** _________________________

**Model Used:** _________________________

**Detection FPS:** _________________________

**Temperature (idle):** _________________________

**Temperature (load):** _________________________

**Issues Encountered:**
```
_____________________________________________
_____________________________________________
_____________________________________________
```

**Solutions Applied:**
```
_____________________________________________
_____________________________________________
_____________________________________________
```

---

## 🆘 **Emergency Troubleshooting**

**Pi won't boot:**
- [ ] Check power supply (5.1V)
- [ ] Reseat MicroSD card
- [ ] Check red/green LEDs on Pi

**Camera not detected:**
- [ ] Reseat FPC cable
- [ ] Check cable orientation
- [ ] Enable in raspi-config

**WiFi not connecting:**
- [ ] Check WiFi credentials
- [ ] Move closer to router
- [ ] Try Ethernet cable

**API won't start:**
- [ ] Check port: `sudo netstat -tulpn | grep 8000`
- [ ] Check Python: `python3 --version`
- [ ] Check logs: `journalctl -u inventory-api`

---

**🎉 Congratulations! Your Vision-Based Inventory System is deployed!**

**Next Steps:**
1. Monitor for 24 hours
2. Adjust detection parameters if needed
3. Set up continual learning (Phase 3)
4. Document performance metrics

---

**Emergency Contact:**
- Project Lead: _______________
- Technical Support: _______________
- Faculty Guide: Dr. Sameer Sayyad
