Raspberry Pi Vision Inventory System Setup

Complete setup for running the Vision-Based Inventory Management System on a Raspberry Pi with ROS2 Jazzy, camera, pan-tilt servos, and API server.

PHASE 1: System Setup
Step 1: Update System
sudo apt update && sudo apt upgrade -y
Step 2: Install Essential Tools
sudo apt install -y \
git curl wget vim net-tools htop \
python3 python3-pip python3-venv python3-dev \
build-essential software-properties-common
Step 3: Add Secondary WiFi Connection
sudo nano /etc/netplan/50-cloud-init.yaml

Edit the file:

network:
  version: 2
  wifis:
    wlan0:
      dhcp4: true
      optional: true
      access-points:
        "PRIMARY_WIFI_NAME":
          password: "PRIMARY_WIFI_PASSWORD"
        "SECONDARY_WIFI_NAME":
          password: "SECONDARY_WIFI_PASSWORD"
        "THIRD_WIFI_NAME":
          password: "THIRD_WIFI_PASSWORD"
        "FOURTH_WIFI_NAME":
          password: "FOURTH_WIFI_PASSWORD"

Apply changes:

sudo netplan apply
PHASE 2: Install ROS2 Jazzy (Ubuntu 24.04)
Step 4: Install ROS2
Set Locale
sudo locale-gen en_US en_US.UTF-8
sudo update-locale LC_ALL=en_US.UTF-8 LANG=en_US.UTF-8
Add ROS2 Repository
sudo apt install -y software-properties-common
sudo add-apt-repository universe -y
Add ROS2 Key and Repo
sudo curl -sSL https://raw.githubusercontent.com/ros/rosdistro/master/ros.key \
-o /usr/share/keyrings/ros-archive-keyring.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/ros-archive-keyring.gpg] \
http://packages.ros.org/ros2/ubuntu $(. /etc/os-release && echo $UBUNTU_CODENAME) main" \
| sudo tee /etc/apt/sources.list.d/ros2.list > /dev/null
Install ROS2 Jazzy
sudo apt update
sudo apt install -y \
ros-jazzy-desktop \
ros-jazzy-rclpy \
ros-jazzy-sensor-msgs \
ros-jazzy-vision-msgs \
ros-jazzy-cv-bridge \
ros-jazzy-image-transport \
python3-colcon-common-extensions \
python3-rosdep
Source ROS2
echo "source /opt/ros/jazzy/setup.bash" >> ~/.bashrc
source /opt/ros/jazzy/setup.bash
Initialize rosdep
sudo rosdep init
rosdep update
PHASE 3: Transfer Your Code
Step 5: From Your Laptop

Navigate to the project folder:

cd /path/to/Vision_Based_Inventory_Management

Transfer to the Pi:

scp -r . pi@172.20.10.xxx:~/Vision_Inventory
Step 6: On Your Pi – Install Dependencies
cd ~/Vision_Inventory

Create virtual environment:

python3 -m venv venv
source venv/bin/activate

Upgrade pip:

pip install --upgrade pip

Install requirements:

pip install -r requirements.txt

Install GPIO libraries:

pip install RPi.GPIO pigpio
PHASE 4: Build ROS2 Package
Step 7: Build the Package
cd ~/Vision_Inventory/ros2_inventory

Fix ROS2 references:

find . -type f -name "*.py" \
-exec sed -i 's|/opt/ros/humble|/opt/ros/jazzy|g' {} + 2>/dev/null || true

Install dependencies:

rosdep install --from-paths . --ignore-src -r -y

Build workspace:

colcon build --symlink-install

Source workspace:

source install/setup.bash

Add to .bashrc:

echo "source ~/Vision_Inventory/ros2_inventory/install/setup.bash" >> ~/.bashrc
PHASE 5: Hardware Setup
Step 8: Enable Camera

Install camera support:

sudo apt install -y libcamera-apps

Edit config:

sudo nano /boot/firmware/config.txt

Add:

dtoverlay=vc4-kms-v3d

Reboot:

sudo reboot

Test camera:

libcamera-hello -t 5000
Step 9: Enable GPIO for Pan-Tilt

Install libraries:

sudo apt install -y python3-rpi.gpio pigpio

Enable daemon:

sudo systemctl enable pigpiod
sudo systemctl start pigpiod

Add user to GPIO group:

sudo usermod -a -G gpio pi

Log out and SSH back in.

Step 10: Connect Hardware Components
Pan Servo
Red (VCC)    → External 5V
Brown (GND)  → GPIO Pin 6
Orange (Sig) → GPIO Pin 11 (GPIO17)
Tilt Servo
Red (VCC)    → External 5V
Brown (GND)  → GPIO Pin 9
Orange (Sig) → GPIO Pin 13 (GPIO27)

⚠️ Use external 5V, not Pi GPIO.

LED Ring Light
VCC  → GPIO Pin 4
GND  → GPIO Pin 6
DATA → GPIO Pin 12 (GPIO18)
Camera
FPC cable → CSI port
Gold contacts toward Ethernet
Power
12V Battery
   ↓
Buck Converter (5.1V)
   ├── USB-C → Raspberry Pi
   └── Servo VCC

All grounds must be common.

Step 11: Test Pan-Tilt
cd ~/Vision_Inventory
sudo python3 test_pantil_t.py

Select option 1 to test movement.

PHASE 6: Run Everything
Step 12: Start API Server
cd ~/Vision_Inventory
source venv/bin/activate

python3 run.py api --host 0.0.0.0 --port 8000

Leave this running.

Step 13: Access Dashboard from Laptop
http://172.20.10.xxx:8000/docs
http://172.20.10.xxx:8000

Replace with your Pi IP.

Step 14: Start ROS2 System
ssh pi@172.20.10.xxx

Source environment:

source /opt/ros/jazzy/setup.bash
source ~/Vision_Inventory/ros2_inventory/install/setup.bash

Launch nodes:

cd ~/Vision_Inventory/ros2_inventory
ros2 launch ros2_inventory inventory_system.launch.py
PHASE 7: Make It Permanent (Autostart)
Step 15: Create Systemd Service
sudo nano /etc/systemd/system/inventory-api.service

Paste:

[Unit]
Description=Vision Inventory API
After=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/Vision_Inventory
Environment="PATH=/home/pi/Vision_Inventory/venv/bin:/usr/bin:/bin"
ExecStart=/home/pi/Vision_Inventory/venv/bin/python -m src.api --host 0.0.0.0 --port 8000
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target

Enable service:

sudo systemctl daemon-reload
sudo systemctl enable inventory-api.service
sudo systemctl start inventory-api.service
sudo systemctl status inventory-api.service
Quick Reference Commands
# Check API status
sudo systemctl status inventory-api

# View logs
sudo journalctl -u inventory-api -f

# Restart API
sudo systemctl restart inventory-api

# ROS2 nodes
ros2 node list

# ROS topics
ros2 topic list

# Camera stream
ros2 topic echo /camera/image_raw

# Temperature
vcgencmd measure_temp

# IP address
hostname -I
Troubleshooting
Problem	Solution
API won't start	`sudo netstat -tulpn
Camera not detected	libcamera-hello --list-cameras
Pan-tilt not moving	Check external 5V power
Can't access from laptop	sudo ufw allow 8000
ROS2 not found	source /opt/ros/jazzy/setup.bash
Success Checklist

 SSH working

 System updated

 ROS2 installed

 Code transferred

 Python dependencies installed

 ROS2 package built

 Camera enabled and tested

 GPIO enabled

 Hardware connected

 API running on :8000

 Dashboard accessible

 Autostart configured

If you want, I can also clean this into a professional GitHub README (with architecture diagram + hardware diagram) so your inventory robot project looks publishable.