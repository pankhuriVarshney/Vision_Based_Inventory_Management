# 🚀 Deployment Quick Reference Card

**Print this one-pager for your Raspberry Pi deployment!**

---

## ⚠️ **CRITICAL: Use Ubuntu 22.04 LTS!**

```
Raspberry Pi Imager → Choose OS:
✅ Ubuntu Server 22.04 LTS (64-bit) ← FOR ROS2!
❌ Raspberry Pi OS (won't work easily with ROS2)
```

---

## 🔌 **Pan-Tilt Wiring**

```
Pan-Tilt (6 wires) → Raspberry Pi 5

PAN Servo:
  Red (VCC)    → Buck Converter 5V (EXTERNAL!)
  Brown (GND)  → GPIO Pin 6
  Orange (Sig) → GPIO Pin 11 (GPIO17)

TILT Servo:
  Red (VCC)    → Buck Converter 5V (shared with Pan)
  Brown (GND)  → GPIO Pin 9
  Orange (Sig) → GPIO Pin 13 (GPIO27)

LED Ring:
  VCC → Pin 4, GND → Pin 6, DATA → Pin 12
```

**⚠️ NEVER power servos from Pi GPIO! Use external 5V!**

---

## 📋 **Quick Steps**

### **1. SD Card (20 min)**
```
1. Raspberry Pi Imager
2. Ubuntu Server 22.04 LTS (64-bit)
3. Configure WiFi, SSH, password
4. Write (~20 min)
```

### **2. Hardware (45 min)**
```
1. Pan-tilt → GPIO (see wiring above)
2. Camera → CSI port
3. LED → GPIO pins 4, 6, 12
4. Power → Buck converter → Pi + servos
```

### **3. First Boot (15 min)**
```
1. Power on Pi
2. Find IP: check router
3. SSH: ssh ubuntu@<IP>
4. Change password
```

### **4. Install ROS2 (40 min)**
```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y software-properties-common
curl -sSL https://raw.githubusercontent.com/ros/rosdistro/master/ros.key | sudo apt-key add -
sudo sh -c 'echo "deb http://packages.ros.org/ros2/ubuntu jammy main" > /etc/apt/sources.list.d/ros2.list'
sudo apt update
sudo apt install -y ros-humble-desktop
echo "source /opt/ros/humble/setup.bash" >> ~/.bashrc
source ~/.bashrc
```

### **5. Deploy Code (20 min)**
```bash
# From laptop
scp -r . ubuntu@<IP>:~/Vision_Inventory

# On Pi
cd ~/Vision_Inventory
pip3 install -r requirements.txt
cd ros2_inventory && colcon build
```

### **6. Test (25 min)**
```bash
# Test pan-tilt
sudo python3 test_pantil_t.py

# Test camera
libcamera-hello -t 5000

# Test API
python3 run.py api &
curl http://localhost:8000/api/health
```

### **7. Autostart (15 min)**
```bash
sudo nano /etc/systemd/system/inventory-api.service
sudo systemctl enable inventory-api.service
sudo reboot
```

**TOTAL: ~3 hours**

---

## 🧪 **Essential Commands**

### **Test Pan-Tilt**
```bash
sudo python3 test_pantil_t.py
```

### **Start API**
```bash
cd ~/Vision_Inventory
python3 run.py api --host 0.0.0.0 --port 8000
```

### **Start ROS2**
```bash
source /opt/ros/humble/setup.bash
cd ~/Vision_Inventory/ros2_inventory
ros2 launch ros2_inventory inventory_system.launch.py
```

### **Check Services**
```bash
sudo systemctl status inventory-api
ros2 node list
```

### **Monitor System**
```bash
vcgencmd measure_temp  # Temperature
vcgencmd measure_volts # Voltage
top                    # Processes
```

---

## 🔧 **Troubleshooting**

| Problem | Solution |
|---------|----------|
| Pan-tilt not moving | Check external 5V power |
| Camera not detected | Reseat FPC cable, check orientation |
| ROS2 not found | `source /opt/ros/humble/setup.bash` |
| API won't start | Check port: `sudo netstat -tulpn \| grep 8000` |
| WiFi disconnects | Check credentials, move closer |

---

## 📊 **GPIO Pin Reference**

| Component | GPIO | Physical Pin |
|-----------|------|--------------|
| Pan Signal | GPIO17 | 11 |
| Pan GND | - | 6 |
| Tilt Signal | GPIO27 | 13 |
| Tilt GND | - | 9 |
| LED Data | GPIO18 | 12 |
| LED VCC | - | 4 |
| LED GND | - | 6 |
| Pan/Tilt VCC | External 5V | - |

---

## ✅ **Success Checklist**

- [ ] Ubuntu 22.04 installed (NOT Raspberry Pi OS)
- [ ] Pan-tilt wired with external 5V power
- [ ] Camera FPC cable seated properly
- [ ] All grounds connected together
- [ ] ROS2 Humble installed: `ros2 --version`
- [ ] Pan-tilt test passes
- [ ] Camera test passes
- [ ] API accessible from browser
- [ ] Autostart configured

---

## 📞 **Important Info**

**WiFi Network:** ________________

**Pi IP Address:** ________________

**Username:** ubuntu (or pi)

**Password:** ________________

**SSH Command:** `ssh ubuntu@<IP>`

---

## 📚 **Full Documentation**

- `DEPLOYMENT_CHECKLIST_PAN_TILT.md` - Complete checklist
- `UBUNTU_SETUP.md` - Ubuntu-specific setup
- `HARDWARE_CONNECTIONS.md` - Wiring diagrams
- `PAN_TILT_QUICK_REF.md` - Pan-tilt reference
- `README.md` - System overview

---

**🎉 You're ready to deploy!**

**Estimated Time:** 3 hours
**Difficulty:** Intermediate
**Requirements:** Basic Linux knowledge, soldering (optional)
