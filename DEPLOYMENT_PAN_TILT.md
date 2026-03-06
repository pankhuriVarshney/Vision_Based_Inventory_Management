# 🥧 Raspberry Pi Hardware Deployment Guide (Pan-Tilt Version)

Complete step-by-step guide for deploying with an **Integrated Pan-Tilt Mechanism**.

---

## 📦 **Your Actual Hardware**

### **Hardware You Have**

| Component | Model | Notes |
|-----------|-------|-------|
| Raspberry Pi 5 | 8GB | Main computer |
| Camera | Pi HQ Camera with 6mm lens | For shelf monitoring |
| **Pan-Tilt** | **Integrated Pan-Tilt Kit** | **2 servos in one unit** |
| LED Ring Light | Programmable | For consistent lighting |
| Display | 7" Touchscreen | Optional UI |
| Power | 12V Battery + Buck Converter | All components |

### **What's Different**

✅ **Integrated Pan-Tilt** = 2 servos already mounted in a bracket
✅ Easier assembly (no individual servo mounting)
✅ Pre-aligned movement axes
✅ Single mounting point to Raspberry Pi

---

## 🔌 **Step 1: Pan-Tilt Mechanism Connections**

### **Understanding Your Pan-Tilt**

Most pan-tilt kits have:
- **Pan servo** (horizontal rotation) - Usually bottom servo
- **Tilt servo** (vertical rotation) - Usually top servo
- **3 wires per servo**: VCC (Red), GND (Brown/Black), Signal (Orange/Yellow)
- **Total 6 wires** coming from the mechanism

### **Wiring Diagram**

```
Pan-Tilt Mechanism
         │
         │ 6 wires total (3 per servo)
         │
    ┌────┴────┐
    │         │
Pan Servo   Tilt Servo
(3 wires)   (3 wires)
    │         │
    └────┬────┘
         │
         ▼
┌─────────────────────────┐
│  Raspberry Pi 5 GPIO    │
│                         │
│  Pan:                   │
│  VCC   → Pin 2  (5V)*   │
│  GND   → Pin 6  (GND)   │
│  Signal→ Pin 11 (GPIO17)│
│                         │
│  Tilt:                  │
│  VCC   → Pin 2  (5V)*   │
│  GND   → Pin 9  (GND)   │
│  Signal→ Pin 13 (GPIO27)│
│                         │
│  *Use EXTERNAL 5V!      │
└─────────────────────────┘
```

### **Wire Identification**

**Typical Pan-Tilt Wire Colors:**

| Servo | Wire Color | Function | GPIO Pin |
|-------|------------|----------|----------|
| Pan | Red | VCC (5V) | Pin 2* |
| Pan | Brown/Black | Ground | Pin 6 |
| Pan | Orange/Yellow | Signal | Pin 11 (GPIO17) |
| Tilt | Red | VCC (5V) | Pin 2* |
| Tilt | Brown/Black | Ground | Pin 9 |
| Tilt | Orange/Yellow | Signal | Pin 13 (GPIO27) |

**⚠️ IMPORTANT:** 
- **DO NOT power servos from Raspberry Pi GPIO!**
- Use external 5V power supply (buck converter from 12V battery)
- Connect servo GND to Pi GND (common ground)

### **External Power Setup (CRITICAL!)**

```
12V Li-ion Battery
       │
       ▼
Buck Converter (set to 5.1V)
       │
       ├──────────────┐
       │              │
       ▼              ▼
┌──────────┐   ┌────────────┐
│ USB-C    │   │ Pan-Tilt   │
│ to Pi 5  │   │ VCC (both  │
│          │   │ red wires) │
└──────────┘   └────────────┘
                    │
                    │ (servo GND)
                    ▼
            Raspberry Pi GND
            (Pins 6, 9)
```

**Why External Power?**
- Servos can draw 500mA-1A each during movement
- Raspberry Pi GPIO can only supply ~500mA TOTAL
- Drawing too much current can damage Pi!

---

## 🔧 **Step 2: Mechanical Assembly**

### **2.1 Mount Pan-Tilt to Raspberry Pi**

**Option A: Direct Mount (if kit includes bracket)**

```
1. Position pan-tilt base on Raspberry Pi case
2. Mark screw holes
3. Use M3 screws to attach
4. Ensure stable mounting (no wobble)
```

**Option B: Separate Mount (recommended)**

```
1. Mount pan-tilt on separate plate/bracket
2. Position bracket overlooking shelf area
3. Run cables to Raspberry Pi
4. Secure cables with cable ties
```

### **2.2 Connect Camera to Pan-Tilt**

```
1. Attach camera mount to tilt servo horn
2. Secure camera with screws or adhesive
3. Connect FPC cable from camera to Pi CSI port
4. Route cable carefully (allow movement)
5. Attach 6mm lens to camera
```

### **2.3 Connect LED Ring Light**

```
LED Ring Light     Raspberry Pi GPIO
--------------     -----------------
VCC (5V)        →  Pin 4  (5V Power)
GND             →  Pin 6  (Ground)
DATA IN         →  Pin 12 (GPIO18 / PWM)
```

**Mount LED ring:**
- Around camera lens
- Or around pan-tilt mechanism
- Use diffuser for even lighting

### **2.4 Cable Management**

```
Camera FPC Cable:
- Route along pan-tilt arm
- Leave slack for movement
- Secure with cable ties
- Avoid pinching

Servo Wires:
- Bundle together
- Route through pan-tilt base
- Connect to GPIO header
- Keep away from moving parts

LED Wires:
- Route separately from servo wires
- Connect to GPIO pins 4, 6, 12
```

---

## 💻 **Step 3: Software Configuration**

### **3.1 Update ROS2 Code for Pan-Tilt**

The ROS2 code already supports pan-tilt! Just verify these files:

**File: `ros2_inventory/config/params.yaml`**

```yaml
camera_node:
  ros__parameters:
    camera_id: 0
    width: 640
    height: 480
    fps: 30
    frame_id: "camera_frame"
    topic_name: "camera/image_raw"

# Pan-Tilt Control (add this section if not present)
pantil_t_node:
  ros__parameters:
    pan_gpio: 17      # GPIO17 = Pin 11
    tilt_gpio: 27     # GPIO27 = Pin 13
    pan_min: 0        # Minimum pan angle (degrees)
    pan_max: 180      # Maximum pan angle
    tilt_min: 0       # Minimum tilt angle
    tilt_max: 90      # Maximum tilt angle
    pan_home: 90      # Home position (center)
    tilt_home: 45     # Home position (center)
```

### **3.2 Create Pan-Tilt Control Node (Optional)**

If you want to control pan-tilt position:

```bash
nano ros2_inventory/ros2_inventory/pantil_t_node.py
```

**Add this code:**

```python
#!/usr/bin/env python3
"""
Pan-Tilt Control Node
Controls integrated pan-tilt mechanism

Subscribes: /pantil_t_command
Publishes: None
"""

import rclpy
from rclpy.node import Node
from std_msgs.msg import Float32MultiArray
import RPi.GPIO as GPIO
import time

class PanTiltNode(Node):
    def __init__(self):
        super().__init__('pantil_t_node')
        
        # GPIO setup
        self.pan_gpio = 17    # GPIO17 = Pin 11
        self.tilt_gpio = 27   # GPIO27 = Pin 13
        
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.pan_gpio, GPIO.OUT)
        GPIO.setup(self.tilt_gpio, GPIO.OUT)
        
        # PWM setup (50Hz for servos)
        self.pan_pwm = GPIO.PWM(self.pan_gpio, 50)
        self.tilt_pwm = GPIO.PWM(self.tilt_gpio, 50)
        
        self.pan_pwm.start(7.5)  # Center position
        self.tilt_pwm.start(7.5)
        
        # Create subscription
        self.subscription = self.create_subscription(
            Float32MultiArray,
            '/pantil_t_command',
            self.command_callback,
            10
        )
        
        self.get_logger().info('Pan-Tilt node initialized')
    
    def angle_to_duty_cycle(self, angle):
        """Convert angle (0-180) to PWM duty cycle (2.5-12.5)"""
        # Map 0-180 to 2.5-12.5
        return 2.5 + (angle / 180.0) * 10.0
    
    def command_callback(self, msg):
        """Receive pan-tilt command [pan_angle, tilt_angle]"""
        try:
            pan_angle = msg.data[0]
            tilt_angle = msg.data[1]
            
            # Clamp angles
            pan_angle = max(0, min(180, pan_angle))
            tilt_angle = max(0, min(90, tilt_angle))
            
            # Set PWM
            self.pan_pwm.ChangeDutyCycle(self.angle_to_duty_cycle(pan_angle))
            self.tilt_pwm.ChangeDutyCycle(self.angle_to_duty_cycle(tilt_angle))
            
            time.sleep(0.02)  # Allow servo to move
            
            # Reset duty cycle to prevent jitter
            self.pan_pwm.ChangeDutyCycle(0)
            self.tilt_pwm.ChangeDutyCycle(0)
            
            self.get_logger().info(f'Pan: {pan_angle}°, Tilt: {tilt_angle}°')
        
        except Exception as e:
            self.get_logger().error(f'Error: {str(e)}')
    
    def destroy_node(self):
        self.pan_pwm.stop()
        self.tilt_pwm.stop()
        GPIO.cleanup()
        super().destroy_node()

def main(args=None):
    rclpy.init(args=args)
    node = PanTiltNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
```

### **3.3 Test Pan-Tilt Movement**

**Manual Test (Python):**

```bash
python3 << 'EOF'
import RPi.GPIO as GPIO
import time

GPIO.setmode(GPIO.BCM)
GPIO.setup(17, GPIO.OUT)  # Pan
GPIO.setup(27, GPIO.OUT)  # Tilt

pan_pwm = GPIO.PWM(17, 50)
tilt_pwm = GPIO.PWM(27, 50)

pan_pwm.start(7.5)  # Center
tilt_pwm.start(7.5)

time.sleep(1)

# Test pan (left to right)
for duty in [2.5, 7.5, 12.5]:
    pan_pwm.ChangeDutyCycle(duty)
    time.sleep(1)

# Test tilt (up and down)
for duty in [2.5, 7.5, 12.5]:
    tilt_pwm.ChangeDutyCycle(duty)
    time.sleep(1)

pan_pwm.stop()
tilt_pwm.stop()
GPIO.cleanup()
print("Pan-Tilt test complete!")
EOF
```

**ROS2 Test:**

```bash
# Start pan-tilt node
ros2 run ros2_inventory pantil_t_node

# In another terminal, send command
ros2 topic pub /pantil_t_command std_msgs/msg/Float32MultiArray "{data: [90.0, 45.0]}"
```

---

## 🎯 **Step 4: Positioning for Shelf Monitoring**

### **Optimal Pan-Tilt Position**

```
        Shelf Area
    ┌─────────────────┐
    │                 │
    │   Products      │
    │                 │
    └─────────────────┘
            ▲
            │ 30-50cm distance
            │
       ┌────┴────┐
       │ Camera  │ ← Mounted on pan-tilt
       │   [●]   │
       └────┬────┘
            │
      Pan-Tilt Mechanism
      (Pan: ←→, Tilt: ↑↓)
```

**Recommended Settings:**

| Parameter | Value | Purpose |
|-----------|-------|---------|
| Pan Range | 60°-120° | Cover shelf width |
| Tilt Range | 30°-60° | Downward angle |
| Home Position | Pan: 90°, Tilt: 45° | Center view |
| Movement Speed | Slow | Smooth scanning |

### **Scanning Pattern (Optional)**

For wide shelves, implement scanning:

```python
# Scan pattern: Left to Right
positions = [
    [60, 45],   # Left
    [90, 45],   # Center
    [120, 45],  # Right
]

for pan, tilt in positions:
    # Move pan-tilt
    # Capture image
    # Run detection
    # Wait 2 seconds
```

---

## 📋 **Updated Wiring Checklist**

### **Pan-Tilt Mechanism**

- [ ] Identify Pan servo wires (Red, Brown, Orange)
- [ ] Identify Tilt servo wires (Red, Brown, Orange)
- [ ] Connect Pan VCC (Red) → Buck Converter 5V
- [ ] Connect Pan GND (Brown) → GPIO Pin 6
- [ ] Connect Pan Signal (Orange) → GPIO Pin 11 (GPIO17)
- [ ] Connect Tilt VCC (Red) → Buck Converter 5V
- [ ] Connect Tilt GND (Brown) → GPIO Pin 9
- [ ] Connect Tilt Signal (Orange) → GPIO Pin 13 (GPIO27)
- [ ] Secure wires with cable ties
- [ ] Test movement with Python script

### **Camera**

- [ ] Attach camera to pan-tilt mount
- [ ] Connect FPC cable to CSI port
- [ ] Route cable carefully (allow movement)
- [ ] Attach 6mm lens
- [ ] Test with `libcamera-hello`

### **LED Ring Light**

- [ ] Connect VCC → GPIO Pin 4 (5V)
- [ ] Connect GND → GPIO Pin 6
- [ ] Connect DATA → GPIO Pin 12 (GPIO18)
- [ ] Mount around camera or pan-tilt
- [ ] Test with Python neopixel library

### **Power**

- [ ] Set buck converter to 5.1V
- [ ] Connect to Raspberry Pi USB-C
- [ ] Connect to servo VCC (both red wires)
- [ ] Connect all GND together (common ground)
- [ ] Verify voltage with multimeter

---

## 🧪 **Testing Pan-Tilt**

### **Test 1: Basic Movement**

```bash
python3 test_pantil_t.py
```

**Expected:** Pan-tilt moves left-right, up-down

### **Test 2: ROS2 Control**

```bash
# Start node
ros2 run ros2_inventory pantil_t_node

# Send command
ros2 topic pub /pantil_t_command std_msgs/msg/Float32MultiArray "{data: [90.0, 45.0]}"
```

**Expected:** Pan-tilt moves to center position

### **Test 3: Integration with Detection**

```bash
# Run detection while moving pan-tilt
python3 run.py detect --source 0

# In another terminal, move pan-tilt
ros2 topic pub /pantil_t_command std_msgs/msg/Float32MultiArray "{data: [60.0, 30.0]}"
```

**Expected:** Detection continues while pan-tilt moves

---

## ⚙️ **Advanced: Auto-Scan Mode**

Create auto-scan node:

```bash
nano ros2_inventory/ros2_inventory/auto_scan_node.py
```

```python
#!/usr/bin/env python3
"""
Auto-Scan Node
Automatically scans shelf area with pan-tilt

Publishes: /pantil_t_command
"""

import rclpy
from rclpy.node import Node
from std_msgs.msg import Float32MultiArray
import time

class AutoScanNode(Node):
    def __init__(self):
        super().__init__('auto_scan_node')
        
        self.publisher = self.create_publisher(
            Float32MultiArray,
            '/pantil_t_command',
            10
        )
        
        # Scan positions
        self.positions = [
            [60, 45],   # Left
            [90, 45],   # Center
            [120, 45],  # Right
            [90, 30],   # Up
            [90, 60],   # Down
        ]
        
        self.current_pos = 0
        
        # Timer for scanning
        self.timer = self.create_timer(3.0, self.scan_callback)
        
        self.get_logger().info('Auto-scan node started')
    
    def scan_callback(self):
        """Move to next position"""
        pos = self.positions[self.current_pos]
        
        msg = Float32MultiArray()
        msg.data = [float(pos[0]), float(pos[1])]
        
        self.publisher.publish(msg)
        self.get_logger().info(f'Moving to Pan:{pos[0]}°, Tilt:{pos[1]}°')
        
        # Next position
        self.current_pos = (self.current_pos + 1) % len(self.positions)

def main(args=None):
    rclpy.init(args=args)
    node = AutoScanNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
```

**Run auto-scan:**

```bash
ros2 run ros2_inventory auto_scan_node
```

---

## 📊 **Updated Performance Expectations**

| Metric | Value |
|--------|-------|
| Pan Range | 0-180° |
| Tilt Range | 0-90° |
| Movement Time | 0.5-1s per position |
| Power Consumption (moving) | 500mA-1A |
| Power Consumption (idle) | ~10mA |
| Detection FPS (stationary) | 14-16 FPS |
| Detection FPS (moving) | 10-12 FPS |

---

## ⚠️ **Important Notes for Pan-Tilt**

1. **Always use external 5V power** for servos
2. **Connect common ground** (servo GND to Pi GND)
3. **Route cables carefully** to avoid snagging
4. **Limit tilt range** to prevent camera cable damage
5. **Move slowly** to avoid image blur during detection
6. **Home position** before shutting down

---

## 🎯 **Quick Reference**

### **GPIO Pin Assignment (Pan-Tilt)**

| Component | GPIO | Physical Pin |
|-----------|------|--------------|
| Pan Signal | GPIO17 | 11 |
| Pan GND | - | 6 |
| Tilt Signal | GPIO27 | 13 |
| Tilt GND | - | 9 |
| Shared VCC | External 5V | - |
| LED Data | GPIO18 | 12 |
| LED VCC | 5V | 4 |
| LED GND | - | 6 |

### **Common Commands**

```bash
# Test pan-tilt
python3 test_pantil_t.py

# Move to position
ros2 topic pub /pantil_t_command std_msgs/msg/Float32MultiArray "{data: [90.0, 45.0]}"

# Start auto-scan
ros2 run ros2_inventory auto_scan_node
```

---

**🎉 Your pan-tilt mechanism is now integrated!**

The system will work exactly the same, but now you can:
- Adjust camera angle remotely
- Scan wider shelf areas
- Implement auto-tracking
- Get better coverage with fewer cameras
