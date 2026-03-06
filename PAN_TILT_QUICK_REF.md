# 🔄 Pan-Tilt Mechanism - Quick Reference

**Updated for Integrated Pan-Tilt Mechanism** (not separate servos)

---

## ⚡ **Quick Start - Just Need to Connect?**

### **1. Wire Connections**

```
Pan-Tilt Mechanism (6 wires total)

PAN Servo:
  Red (VCC)    → Buck Converter 5V (NOT Pi GPIO!)
  Brown (GND)  → GPIO Pin 6
  Orange (Sig) → GPIO Pin 11 (GPIO17)

TILT Servo:
  Red (VCC)    → Buck Converter 5V (shared with Pan)
  Brown (GND)  → GPIO Pin 9
  Orange (Sig) → GPIO Pin 13 (GPIO27)
```

### **2. Test Immediately**

```bash
# On Raspberry Pi
cd ~/Vision_Inventory
sudo python3 test_pantil_t.py

# Select option 1 (Basic Movement Test)
# Should see pan-tilt move left-right, up-down
```

### **3. Common Issues**

| Problem | Solution |
|---------|----------|
| No movement | Check external 5V power |
| Jittery movement | Check ground connections |
| Only one servo works | Check signal wire connections |
| Movement backwards | Swap signal wires |

---

## 📌 **What Changed from Separate Servos**

### **Before (Individual Servos)**
- Mount each servo separately
- More wiring
- More complex assembly

### **After (Integrated Pan-Tilt)**
- ✅ Pre-mounted servos in bracket
- ✅ Cleaner assembly
- ✅ Same wiring (6 wires total)
- ✅ Better stability
- ✅ Pre-aligned movement

---

## 🔌 **Wiring Diagram (Simplified)**

```
         Pan-Tilt Mechanism
         ┌────────────────┐
         │   [Camera]     │
         │      ●         │
         │   ┌─────┐      │
         │   │Pan  │      │ ← Bottom servo (horizontal)
         │   │Tilt │      │ ← Top servo (vertical)
         └───┴──┬──┴──────┘
                │
          6 wires out
                │
    ┌───────────┴──────────┐
    │                      │
Red Wires (2)         Brown/Black (2)
(Both VCC)            (Both GND)
    │                      │
    ▼                      ▼
Buck Converter       GPIO Pins
5V Output            Pin 6 (Pan GND)
                     Pin 9 (Tilt GND)
                     
Orange Wires (2)
(Both Signal)
    │
    ├─→ Pin 11 (GPIO17) - Pan
    └─→ Pin 13 (GPIO27) - Tilt
```

---

## 🧪 **Test Commands**

### **Basic Test**
```bash
sudo python3 test_pantil_t.py
```

### **Manual Position**
```bash
python3 << 'EOF'
import RPi.GPIO as GPIO
import time

GPIO.setmode(GPIO.BCM)
GPIO.setup(17, GPIO.OUT)  # Pan
GPIO.setup(27, GPIO.OUT)  # Tilt

pan_pwm = GPIO.PWM(17, 50)
tilt_pwm = GPIO.PWM(27, 50)

pan_pwm.start(7.5)
tilt_pwm.start(7.5)

# Move to specific position
pan_pwm.ChangeDutyCycle(2.5)  # Pan left (0°)
tilt_pwm.ChangeDutyCycle(7.5)  # Tilt center (45°)
time.sleep(1)

pan_pwm.stop()
tilt_pwm.stop()
GPIO.cleanup()
EOF
```

### **ROS2 Control**
```bash
# Start pan-tilt node
ros2 run ros2_inventory pantil_t_node

# Send command
ros2 topic pub /pantil_t_command std_msgs/msg/Float32MultiArray \
  "{data: [90.0, 45.0]}"
```

---

## 📐 **Recommended Settings**

### **For Shelf Monitoring**

| Parameter | Value | Why |
|-----------|-------|-----|
| Pan Home | 90° | Center of shelf |
| Tilt Home | 45° | Downward angle |
| Pan Range | 60°-120° | Cover shelf width |
| Tilt Range | 30°-60° | Avoid ceiling/floor |
| Movement Speed | Slow | Prevent blur |

### **Power Settings**

| Component | Voltage | Current |
|-----------|---------|---------|
| Pan-Tilt VCC | 5.0-5.1V | 500mA-1A (moving) |
| Pan-Tilt GND | Common with Pi | - |
| Signal | 3.3V (GPIO) | <10mA |

---

## 🔧 **Code Integration**

### **Add to ROS2 Launch File**

Edit: `ros2_inventory/launch/inventory_system.launch.py`

```python
# Add pan-tilt node
pantil_t_node = Node(
    package='ros2_inventory',
    executable='pantil_t_node',
    name='pantil_t_node',
    output='screen',
    parameters=[{
        'pan_gpio': 17,
        'tilt_gpio': 27,
        'pan_home': 90.0,
        'tilt_home': 45.0,
    }]
)

# Add to launch description
ld.add_action(pantil_t_node)
```

### **Auto-Scan Pattern**

```python
# Scan positions for wide shelf
positions = [
    [60, 45],   # Left
    [90, 45],   # Center  
    [120, 45],  # Right
]

# Cycle through positions
for pan, tilt in positions:
    # Move pan-tilt
    # Capture image
    # Run detection
    # Wait 2 seconds
```

---

## ⚠️ **Critical Warnings**

1. **NEVER connect servo VCC (red) to Pi GPIO 5V**
   - Use external 5V from buck converter
   - Can damage Raspberry Pi!

2. **ALWAYS connect common ground**
   - Servo GND → Pi GND (Pins 6, 9)
   - Required for signal reference

3. **Route FPC cable carefully**
   - Leave slack for pan-tilt movement
   - Avoid pinching or snagging

4. **Test movement range first**
   - Before final mounting
   - Ensure no obstructions

5. **Return to center before shutdown**
   - Prevents cable strain
   - Easier startup next time

---

## 📚 **Documentation Reference**

| Document | Use For |
|----------|---------|
| `DEPLOYMENT_PAN_TILT.md` | Complete setup guide |
| `DEPLOYMENT_CHECKLIST_PAN_TILT.md` | Step-by-step checklist |
| `HARDWARE_CONNECTIONS.md` | Wiring diagrams |
| `test_pantil_t.py` | Testing script |

---

## 🎯 **Quick Troubleshooting**

**No movement at all:**
```bash
# Check external power with multimeter
# Should read 5.0-5.1V at servo VCC

# Check ground connections
# Servo GND must connect to Pi GND
```

**Only pan works:**
```bash
# Check tilt signal wire (Pin 13)
# Test with: sudo python3 test_pantil_t.py
```

**Servos jitter:**
```bash
# Check power supply capacity
# May need separate 5V for servos
# Add capacitor (100uF) across servo power
```

**Camera disconnects during movement:**
```bash
# Reseat FPC cable
# Add strain relief loop
# Check for cable damage
```

---

## ✅ **Success Checklist**

- [ ] Pan-tilt moves smoothly through full range
- [ ] No jitter or stuttering
- [ ] Camera feed stable during movement
- [ ] External 5V power connected
- [ ] All grounds connected together
- [ ] FPC cable routed safely
- [ ] Returns to center position
- [ ] Detection works while moving

---

**🎉 Pan-tilt mechanism ready for deployment!**

For complete setup, follow `DEPLOYMENT_CHECKLIST_PAN_TILT.md`
