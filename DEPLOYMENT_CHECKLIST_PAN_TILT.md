# 📋 Raspberry Pi Deployment Checklist (Pan-Tilt Version)

Print this checklist and use it during your Raspberry Pi deployment!

---

## 📦 **Pre-Deployment (At Home/Office)**

### **Hardware Preparation**

- [ ] Raspberry Pi 5 (8GB) with heatsink
- [ ] MicroSD card (32GB minimum)
- [ ] Raspberry Pi High Quality Camera
- [ ] 6mm lens
- [ ] **Integrated Pan-Tilt Mechanism** (2 servos)
- [ ] LED ring light
- [ ] 7" touchscreen display (optional)
- [ ] 12V Li-ion battery (3S, 10Ah)
- [ ] Buck converter (12V → 5V)
- [ ] USB-C cable
- [ ] FPC cable (for camera)
- [ ] DSI cable (for display)
- [ ] Jumper wires (F/F, M/F, M/M)
- [ ] 3D printed enclosure or mounting bracket
- [ ] Screws and standoffs (M3)
- [ ] Cable ties
- [ ] **External 5V power distribution** (for pan-tilt servos)

### **Tools Needed**

- [ ] Small screwdriver set
- [ ] Multimeter (for checking voltage)
- [ ] Wire strippers
- [ ] Soldering iron (optional, for connections)
- [ ] Hot glue gun
- [ ] Cable ties
- [ ] Tweezers
- [ ] Scissors
- [ ] Small wrench (for pan-tilt mounting)

### **Software Preparation (On Your Laptop)**

- [ ] Download Raspberry Pi Imager
- [ ] Download Raspberry Pi OS 64-bit image
- [ ] Clone/pull latest code from repository
- [ ] Test code locally: `python run.py api`
- [ ] Export model for Pi: `python export_model.py --format tflite`
- [ ] Copy model to project folder
- [ ] Test frontend build: `cd frontend && npm run build`

---

## 💾 **Step 1: Raspberry Pi Imager with Ubuntu**

- [ ] Insert MicroSD card into computer
- [ ] Open Raspberry Pi Imager
- [ ] **CHOOSE OS:** ⚠️ **Ubuntu Server 22.04 LTS (64-bit)** ← MUST be Ubuntu for ROS2!
      - NOT Raspberry Pi OS (that's Debian-based)
      - ROS2 Humble requires Ubuntu 22.04
      - Select: "Ubuntu" → "Ubuntu Server 22.04 LTS (64-bit)"
- [ ] **CHOOSE STORAGE:** Select MicroSD card (32GB+ recommended, Ubuntu is larger)
- [ ] **CHOOSE OPTIONS (⚙️):**
  - [ ] Enable SSH
  - [ ] Set username: `pi` or `ubuntu`
  - [ ] Set password: (choose strong password)
  - [ ] Configure WiFi (SSID + password)
  - [ ] Set timezone: `Asia/Kolkata`
  - [ ] Set hostname: `inventory-pi` (optional)
- [ ] Click **WRITE**
- [ ] Wait for completion (~20 min, Ubuntu is larger)
- [ ] Safely eject MicroSD card

**Time:** ~20 minutes

---

## 🔌 **Step 2: Hardware Assembly (Pan-Tilt)**

### **Pan-Tilt Mechanism**

- [ ] Identify pan-tilt wires:
  - [ ] Pan servo: Red (VCC), Brown (GND), Orange (Signal)
  - [ ] Tilt servo: Red (VCC), Brown (GND), Orange (Signal)
- [ ] **Connect Pan Servo:**
  - [ ] VCC (Red) → Buck Converter 5V Output (NOT Pi GPIO!)
  - [ ] GND (Brown) → GPIO Pin 6 (Ground)
  - [ ] Signal (Orange) → GPIO Pin 11 (GPIO17)
- [ ] **Connect Tilt Servo:**
  - [ ] VCC (Red) → Buck Converter 5V Output (shared with Pan)
  - [ ] GND (Brown) → GPIO Pin 9 (Ground)
  - [ ] Signal (Orange) → GPIO Pin 13 (GPIO27)
- [ ] Secure all connections
- [ ] Bundle wires with cable ties
- [ ] Mount pan-tilt mechanism in enclosure/bracket

### **Camera Module**

- [ ] Mount camera on pan-tilt bracket (use provided screws)
- [ ] Insert FPC cable into camera module (gold contacts away from lens)
- [ ] Attach 6mm lens to camera
- [ ] Open CSI port latch on Pi
- [ ] Insert FPC cable into CSI port (**gold contacts toward Ethernet**)
- [ ] Close latch to secure cable
- [ ] **Route FPC cable carefully** (allow pan-tilt movement!)
- [ ] Secure with cable ties (leave slack for movement)

### **LED Ring Light**

- [ ] Connect VCC (5V) → GPIO Pin 4
- [ ] Connect GND → GPIO Pin 6 (shared with Pan GND)
- [ ] Connect DATA → GPIO Pin 12 (GPIO18)
- [ ] Mount LED ring around camera lens or pan-tilt
- [ ] Add diffuser if available
- [ ] Secure wires

### **Display** (Optional)

- [ ] Connect DSI cable to display
- [ ] Connect DSI cable to Pi DSI port
- [ ] Mount display in enclosure front panel

### **Power System**

- [ ] Connect battery to buck converter input
- [ ] **Adjust buck converter to 5.1V** (use multimeter!)
- [ ] Connect buck converter output to:
  - [ ] USB-C → Raspberry Pi
  - [ ] Pan Servo VCC (red wire)
  - [ ] Tilt Servo VCC (red wire)
- [ ] **Connect all grounds together:**
  - [ ] Buck converter GND → Battery GND
  - [ ] Servo GND → GPIO Pins 6, 9
  - [ ] Raspberry Pi GND
- [ ] Secure battery in enclosure
- [ ] Add power switch (optional)

### **Final Assembly**

- [ ] Mount Raspberry Pi in enclosure
- [ ] Mount pan-tilt mechanism overlooking shelf area
- [ ] Route all cables through channels
- [ ] **Ensure pan-tilt can move freely** (no cable snagging)
- [ ] Secure all connections with cable ties
- [ ] Close enclosure
- [ ] Attach mounting bracket to wall/ceiling

**Time:** ~45 minutes

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

## 📥 **Step 4: Install Dependencies on Ubuntu**

### **System Update**

- [ ] `sudo apt update`
- [ ] `sudo apt upgrade -y`
- [ ] `sudo reboot`
- [ ] Reconnect via SSH

### **Install Ubuntu Essential Tools**

- [ ] `sudo apt install -y software-properties-common curl git vim net-tools`
- [ ] `sudo apt install -y python3 python3-pip python3-venv`
- [ ] `pip3 install --upgrade pip`

### **Install ROS2 Humble on Ubuntu**

- [ ] Add ROS2 repository:
  ```bash
  sudo add-apt-repository universe
  curl -sSL https://raw.githubusercontent.com/ros/rosdistro/master/ros.key | sudo apt-key add -
  sudo sh -c 'echo "deb http://packages.ros.org/ros2/ubuntu jammy main" > /etc/apt/sources.list.d/ros2.list'
  ```
- [ ] `sudo apt update`
- [ ] `sudo apt install -y ros-humble-desktop`
- [ ] `sudo apt install -y ros-humble-rclpy ros-humble-sensor-msgs ros-humble-vision-msgs ros-humble-cv-bridge`
- [ ] Add to `.bashrc`: `echo "source /opt/ros/humble/setup.bash" >> ~/.bashrc`
- [ ] `source ~/.bashrc`
- [ ] Verify: `ros2 --version` (should show "ROS 2 humble Hawksbill")

### **Camera Support on Ubuntu**

- [ ] `sudo apt install -y libcamera-apps libcamera-tools`
- [ ] Enable camera: Edit `/boot/firmware/config.txt`
  ```bash
  sudo nano /boot/firmware/config.txt
  # Add: dtoverlay=vc4-kms-v3d
  ```
- [ ] `sudo reboot`
- [ ] Test: `libcamera-hello -t 5000`

### **GPIO Library for Pan-Tilt**

- [ ] `sudo apt install -y python3-rpi.gpio pigpio`
- [ ] `sudo systemctl enable pigpiod`
- [ ] `sudo systemctl start pigpiod`
- [ ] Test: `python3 -c "import RPi.GPIO as GPIO; print('GPIO OK')"`

**Time:** ~40 minutes

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

## 🧪 **Step 6: Testing Pan-Tilt**

### **Test 1: GPIO Test**

- [ ] `cd ~/Vision_Inventory`
- [ ] `python3 -c "import RPi.GPIO as GPIO; print('GPIO OK')"`
- [ ] Should print "GPIO OK"

### **Test 2: Pan-Tilt Movement**

- [ ] `sudo python3 test_pantil_t.py`
- [ ] Select test option (1-4)
- [ ] **Observe pan-tilt movement:**
  - [ ] Pan moves left (0°)
  - [ ] Pan moves center (90°)
  - [ ] Pan moves right (180°)
  - [ ] Tilt moves up (0°)
  - [ ] Tilt moves center (45°)
  - [ ] Tilt moves down (90°)
- [ ] Should return to center position

### **Test 3: Camera with Pan-Tilt**

- [ ] `libcamera-hello -t 5000`
- [ ] Camera preview appears
- [ ] Gently move pan-tilt manually
- [ ] Image should remain stable
- [ ] Adjust focus if needed

### **Test 4: API Test**

- [ ] `cd ~/Vision_Inventory`
- [ ] `python3 run.py api &`
- [ ] `curl http://localhost:8000/api/health`
- [ ] Response shows "healthy"
- [ ] Open browser: `http://<IP>:8000/docs`
- [ ] API documentation loads

### **Test 5: Detection with Pan-Tilt**

- [ ] `python3 run.py detect --source 0`
- [ ] Detection window appears
- [ ] Gently move pan-tilt (if motorized)
- [ ] Detection continues working
- [ ] Press 'q' to exit

### **Test 6: ROS2 Nodes**

- [ ] `ros2 launch ros2_inventory inventory_system.launch.py`
- [ ] In new terminal: `ros2 node list`
- [ ] Shows: camera_node, detection_node, inventory_node
- [ ] `ros2 topic echo /inventory_status`
- [ ] Shows inventory data

**Time:** ~25 minutes

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

### **Create Pan-Tilt Service** (Optional)

- [ ] `sudo nano /etc/systemd/system/pantil_t.service`
- [ ] Paste service configuration (if using auto-scan)
- [ ] Save and exit
- [ ] `sudo systemctl daemon-reload`
- [ ] `sudo systemctl enable pantil_t.service`
- [ ] `sudo systemctl start pantil_t.service`

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
- [ ] Adjust pan-tilt base angle
- [ ] Set pan range (60°-120° recommended)
- [ ] Set tilt range (30°-60° downward)
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
- [ ] Lock focus with set screw

### **Configure Pan-Tilt Limits**

- [ ] Test full pan range (0° to 180°)
- [ ] Test full tilt range (0° to 90°)
- [ ] **Ensure cables don't snag**
- [ ] Set software limits if needed
- [ ] Set home position (90°, 45°)

### **Final Testing**

- [ ] Run system for 5 minutes
- [ ] Check detection accuracy
- [ ] Monitor temperature: `vcgencmd measure_temp`
- [ ] Should be < 70°C
- [ ] Check power voltage: `vcgencmd measure_volts`
- [ ] Should be ~5.1V
- [ ] **Test pan-tilt movement during detection**

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
| Hardware Assembly (Pan-Tilt) | 45 min |
| First Boot & Setup | 15 min |
| Install Dependencies | 40 min |
| Deploy Code | 20 min |
| Testing Pan-Tilt | 25 min |
| Configure Autostart | 15 min |
| Final Deployment | 20 min |
| **TOTAL** | **~3 hours 15 minutes** |

---

## ✅ **Final Verification Checklist**

- [ ] Pan-tilt mechanism securely mounted
- [ ] Camera attached and focused
- [ ] All servo wires connected correctly
- [ ] External 5V power connected to servos
- [ ] Common ground established
- [ ] LED lighting properly positioned
- [ ] Detection running (14-16 FPS)
- [ ] Pan-tilt moves freely (no cable snagging)
- [ ] API accessible from network
- [ ] ROS2 nodes running
- [ ] Autostart configured
- [ ] System stable after reboot
- [ ] Temperature normal (< 70°C)
- [ ] All connections secure
- [ ] FPC cable routed safely

---

## 📝 **Notes & Configuration**

**WiFi Network:** _________________________

**WiFi Password:** _________________________

**Pi IP Address:** _________________________

**SSH Password:** _________________________

**Model Used:** _________________________

**Pan-Tilt Home Position:** Pan: ____°, Tilt: ____°

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

**Pan-Tilt not moving:**
- [ ] Check external 5V power connection
- [ ] Verify servo signal wires (Pins 11, 13)
- [ ] Check common ground (servo GND to Pi GND)
- [ ] Run with sudo: `sudo python3 test_pantil_t.py`

**Camera not detected:**
- [ ] Reseat FPC cable
- [ ] Check cable orientation
- [ ] Enable in raspi-config
- [ ] Ensure FPC cable not damaged by pan-tilt movement

**WiFi not connecting:**
- [ ] Check WiFi credentials
- [ ] Move closer to router
- [ ] Try Ethernet cable

**API won't start:**
- [ ] Check port: `sudo netstat -tulpn | grep 8000`
- [ ] Check Python: `python3 --version`
- [ ] Check logs: `journalctl -u inventory-api`

**Detection fails:**
- [ ] Check model exists: `ls -lh models/best.tflite`
- [ ] Test camera: `libcamera-hello -t 5000`
- [ ] Reduce image size: Use 480x320 instead of 640x480

---

## 🎯 **Pan-Tilt Specific Tips**

1. **Always test movement range before final mounting**
2. **Route FPC cable with slack for pan-tilt movement**
3. **Use external 5V power for servos (CRITICAL!)**
4. **Set software limits to prevent cable damage**
5. **Return to center position before shutdown**
6. **Monitor FPC cable during pan-tilt movement**

---

**🎉 Congratulations! Your Pan-Tilt Inventory System is deployed!**

**Next Steps:**
1. Monitor for 24 hours
2. Adjust pan-tilt limits if needed
3. Set up auto-scan pattern (optional)
4. Document performance metrics

---

**Emergency Contact:**
- Project Lead: _______________
- Technical Support: _______________
- Faculty Guide: Dr. Sameer Sayyad
