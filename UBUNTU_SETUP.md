# 🥧 Raspberry Pi OS Selection for ROS2

## ⚠️ **CRITICAL: Use Ubuntu 22.04 LTS (64-bit) for ROS2 Humble**

---

## 📀 **Correct OS to Select in Raspberry Pi Imager**

### **For ROS2 Humble (Required for this project):**

```
Raspberry Pi Imager → Choose OS:

✅ CORRECT:
  "Ubuntu" → "Ubuntu Server 22.04 LTS (64-bit)"
  
  OR
  
  "Ubuntu" → "Ubuntu Desktop 22.04 LTS (64-bit)" (if using display)

❌ WRONG (won't work easily with ROS2 Humble):
  "Raspberry Pi OS (64-bit)" ← This is Debian-based, not Ubuntu!
  "Raspberry Pi OS (32-bit)"
  "Raspberry Pi OS Lite"
```

---

## 🔍 **Why Ubuntu and Not Raspberry Pi OS?**

| Feature | Ubuntu 22.04 | Raspberry Pi OS |
|---------|--------------|-----------------|
| Base | Ubuntu (Debian-based) | Debian |
| ROS2 Humble Support | ✅ Native support | ⚠️ Requires workarounds |
| Package Compatibility | ✅ Full ROS2 packages | ⚠️ Limited |
| Long-term Support | ✅ Until 2027 | ✅ Until 2026 |
| ROS2 Installation | `apt install ros-humble-desktop` | Complex manual install |
| Community Support | ✅ Extensive | ⚠️ Limited for ROS2 |

**ROS2 Humble Hawksbill** is built for **Ubuntu 22.04 (Jammy Jellyfish)**

---

## 📋 **Updated Step 1: Raspberry Pi Imager with Ubuntu**

### **1.1 Download Raspberry Pi Imager**

```
https://www.raspberrypi.com/software/
```

### **1.2 Select Ubuntu OS**

**CHOOSE OS:**
```
1. Click "CHOOSE OS"
2. Select "Ubuntu"
3. Choose ONE of:
   
   a) Ubuntu Server 22.04 LTS (64-bit) ← Recommended for headless
      - Smaller footprint
      - No GUI (use SSH)
      - Better performance
      - Use if accessing via web browser only
   
   b) Ubuntu Desktop 22.04 LTS (64-bit)
      - Full desktop environment
      - Use if connecting monitor directly
      - More resource-intensive
```

### **1.3 Configure Ubuntu**

**CHOOSE STORAGE:**
- Select your MicroSD card (32GB+ recommended)

**CHOOSE OPTIONS (⚙️ icon):**
- ✅ **Enable SSH:** Use password authentication
- ✅ **Set username and password:**
  - Username: `pi` (or `ubuntu`, `inventory`, etc.)
  - Password: Choose a strong password
- ✅ **Configure wireless LAN:**
  - SSID: Your WiFi network
  - Password: Your WiFi password
  - Country: `IN` (India)
- ✅ **Set local settings:**
  - Timezone: `Asia/Kolkata`
  - Keyboard layout: Default
- ✅ **Optional: Configure settings**
  - Set hostname: `inventory-pi` (or your choice)

### **1.4 Write Image**

```
1. Click SAVE
2. Click WRITE
3. Wait (~15-20 minutes, Ubuntu is larger)
4. Safely eject MicroSD card
```

---

## 💻 **First Boot with Ubuntu**

### **Boot Time**
- Ubuntu takes **longer to boot** than Raspberry Pi OS (~2-3 minutes)
- First boot may take even longer (configuration)

### **Find IP Address**
```bash
# Same as before - check router or use:
nmap -sn 192.168.1.0/24
```

### **SSH Connection**
```bash
# Ubuntu on Pi uses standard SSH
ssh pi@<IP-address>
# Password: (your chosen password)
```

### **Initial Ubuntu Setup**
```bash
# Update system
sudo apt update
sudo apt upgrade -y

# Install essential tools
sudo apt install -y \
    git \
    curl \
    wget \
    vim \
    net-tools \
    python3 \
    python3-pip
```

---

## 🤖 **Installing ROS2 Humble on Ubuntu**

### **Ubuntu 22.04 is Pre-configured for ROS2!**

```bash
# 1. Enable repositories (Ubuntu has these by default)
sudo apt install -y software-properties-common
sudo add-apt-repository universe

# 2. Add ROS2 GPG key
curl -sSL https://raw.githubusercontent.com/ros/rosdistro/master/ros.key | sudo apt-key add -

# 3. Add ROS2 repository
sudo sh -c 'echo "deb http://packages.ros.org/ros2/ubuntu jammy main" > /etc/apt/sources.list.d/ros2.list'

# 4. Update package index
sudo apt update

# 5. Install ROS2 Humble Desktop
sudo apt install -y ros-humble-desktop

# 6. Install additional ROS2 packages
sudo apt install -y \
    ros-humble-rclpy \
    ros-humble-sensor-msgs \
    ros-humble-vision-msgs \
    ros-humble-cv-bridge \
    ros-humble-image-transport \
    ros-humble-ros2-control \
    ros-humble-ros2-controllers

# 7. Source ROS2
echo "source /opt/ros/humble/setup.bash" >> ~/.bashrc
source ~/.bashrc

# 8. Verify installation
ros2 --version
# Should show: ROS 2 humble Hawksbill
```

---

## 📦 **Complete Ubuntu Installation Script**

Save this as `install_ros2_ubuntu.sh`:

```bash
#!/bin/bash
# ROS2 Humble Installation for Ubuntu 22.04

echo "Installing ROS2 Humble on Ubuntu 22.04..."

# Update system
sudo apt update
sudo apt upgrade -y

# Install dependencies
sudo apt install -y \
    software-properties-common \
    curl \
    gnupg \
    lsb-release

# Add ROS2 repository
sudo add-apt-repository universe
curl -sSL https://raw.githubusercontent.com/ros/rosdistro/master/ros.key | sudo apt-key add -
sudo sh -c 'echo "deb http://packages.ros.org/ros2/ubuntu jammy main" > /etc/apt/sources.list.d/ros2.list'

# Install ROS2
sudo apt update
sudo apt install -y ros-humble-desktop

# Install additional packages
sudo apt install -y \
    ros-humble-rclpy \
    ros-humble-sensor-msgs \
    ros-humble-vision-msgs \
    ros-humble-cv-bridge

# Source ROS2
echo "" >> ~/.bashrc
echo "# ROS2 Humble" >> ~/.bashrc
echo "source /opt/ros/humble/setup.bash" >> ~/.bashrc
source ~/.bashrc

# Verify
echo ""
echo "ROS2 Installation Complete!"
ros2 --version

echo ""
echo "Next steps:"
echo "1. Install Python dependencies: pip3 install -r requirements.txt"
echo "2. Build ROS2 package: cd ros2_inventory && colcon build"
```

**Run it:**
```bash
chmod +x install_ros2_ubuntu.sh
./install_ros2_ubuntu.sh
```

---

## ⚙️ **Ubuntu-Specific Configuration**

### **Camera Enablement**

Ubuntu may need additional configuration for camera:

```bash
# Install camera support
sudo apt install -y libcamera-apps libcamera-tools

# Enable camera (if using Pi Camera Module)
# Edit /boot/firmware/config.txt or /boot/config.txt
sudo nano /boot/firmware/config.txt

# Add this line:
dtoverlay=vc4-kms-v3d

# Reboot
sudo reboot
```

### **GPIO Access on Ubuntu**

```bash
# Install RPi.GPIO for Ubuntu
sudo apt install -y python3-rpi.gpio

# For PWM (servo control), install pigpio
sudo apt install -y pigpio
sudo systemctl enable pigpiod
sudo systemctl start pigpiod

# Test
python3 -c "import RPi.GPIO as GPIO; print('GPIO OK')"
```

### **WiFi Power Management**

Ubuntu may have aggressive WiFi power saving:

```bash
# Disable WiFi power saving
sudo sed -i 's/3/2/' /etc/NetworkManager/conf.d/default-wifi-powersave-on.conf
sudo systemctl restart NetworkManager
```

---

## 🆚 **Ubuntu vs Raspberry Pi OS Comparison**

### **Ubuntu 22.04 LTS (Recommended for ROS2)**

**Pros:**
- ✅ Native ROS2 Humble support
- ✅ Official ROS2 repository
- ✅ Easy installation (`apt install ros-humble-desktop`)
- ✅ Full package compatibility
- ✅ Long-term support until 2027
- ✅ Standard Ubuntu environment

**Cons:**
- ⚠️ Larger footprint (needs more SD card space)
- ⚠️ Slightly slower boot time
- ⚠️ Some Pi-specific tools not available

### **Raspberry Pi OS (Not Recommended for ROS2)**

**Pros:**
- ✅ Optimized for Raspberry Pi hardware
- ✅ Smaller footprint
- ✅ Faster boot time
- ✅ Pi-specific tools included

**Cons:**
- ❌ Not officially supported by ROS2 Humble
- ❌ Requires manual ROS2 installation
- ❌ Potential compatibility issues
- ❌ More complex setup

---

## 📊 **Updated Deployment Time with Ubuntu**

| Step | Time |
|------|------|
| Raspberry Pi Imager (Ubuntu) | 20 min |
| First Boot & Ubuntu Setup | 20 min |
| ROS2 Humble Installation | 30 min |
| Python Dependencies | 15 min |
| Code Deployment | 20 min |
| ROS2 Package Build | 15 min |
| Testing | 25 min |
| Configuration | 15 min |
| **TOTAL** | **~2 hours 40 minutes** |

---

## ✅ **Updated Pre-Deployment Checklist**

Before you start:

- [ ] Download Raspberry Pi Imager
- [ ] **Select Ubuntu 22.04 LTS (64-bit)** ← CRITICAL!
- [ ] MicroSD card 32GB+ (Ubuntu is larger)
- [ ] Stable internet connection (for ROS2 download)
- [ ] Ethernet cable recommended for initial setup

---

## 🚀 **Quick Ubuntu Setup Commands**

```bash
# After first boot, run these in order:

# 1. Update system
sudo apt update && sudo apt upgrade -y

# 2. Install ROS2 Humble
sudo apt install -y ros-humble-desktop

# 3. Install ROS2 tools
sudo apt install -y ros-humble-rclpy ros-humble-sensor-msgs

# 4. Source ROS2
echo "source /opt/ros/humble/setup.bash" >> ~/.bashrc
source ~/.bashrc

# 5. Install Python dependencies
pip3 install -r requirements.txt

# 6. Build ROS2 package
cd ~/Vision_Inventory/ros2_inventory
rosdep install --from-paths . --ignore-src -r -y
colcon build --symlink-install
source install/setup.bash

# 7. Test ROS2
ros2 --version
```

---

## 📝 **Important Ubuntu Notes**

1. **Username**: Default is `ubuntu` for Ubuntu Server, or your custom username
2. **Hostname**: Default is `ubuntu`, change with `sudo hostnamectl set-hostname inventory-pi`
3. **Config file location**: `/boot/firmware/config.txt` (not `/boot/config.txt`)
4. **Network**: Uses NetworkManager (not dhcpcd)
5. **Services**: Uses systemd (same as Raspberry Pi OS)

---

## 🆘 **Ubuntu Troubleshooting**

### **ROS2 installation fails:**
```bash
# Check Ubuntu version
lsb_release -a
# Should show: Ubuntu 22.04 LTS

# Check repository
cat /etc/apt/sources.list.d/ros2.list
# Should contain: deb http://packages.ros.org/ros2/ubuntu jammy main
```

### **Camera not working:**
```bash
# Check camera module
sudo vcgencmd get_camera
# Should show: supported=1 detected=1

# Edit config file
sudo nano /boot/firmware/config.txt
# Add: dtoverlay=vc4-kms-v3d
# Reboot: sudo reboot
```

### **WiFi keeps disconnecting:**
```bash
# Disable power saving
sudo nmcli radio wifi off
sudo nmcli radio wifi on

# Check connection
nmcli device status
```

---

## 🎯 **Summary**

**For ROS2 Humble on Raspberry Pi:**

✅ **USE:** Ubuntu Server 22.04 LTS (64-bit)
- Best ROS2 compatibility
- Easy installation
- Official support

❌ **DON'T USE:** Raspberry Pi OS
- Not officially supported
- Complex manual installation
- Potential issues

---

**This is the correct OS for your ROS2-based inventory system!** 🎉
