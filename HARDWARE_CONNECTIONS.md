# 🔌 Hardware Connection Quick Reference

## 📷 Camera & Pan-Tilt Connections

### **Raspberry Pi High Quality Camera with Pan-Tilt**

```
                    ┌────────────────────────┐
                    │  Raspberry Pi 5        │
                    │                        │
CSI Port ──────────│● CSI (Camera)          │
(FPC cable)        │                        │
                   │                        │
                   └────────────────────────┘
                          ▲
                          │ FPC Cable
                          │ (gold contacts
                          │  toward Ethernet)
                          │
                   ┌──────┴──────┐
                   │ Pi HQ       │
                   │ Camera      │
                   │  [6mm Lens] │
                   │      ●      │ ← Mounted on Pan-Tilt
                   └──────┬──────┘
                          │
                   ┌──────┴──────┐
                   │ Pan-Tilt    │
                   │ Mechanism   │
                   │ (Integrated)│
                   └─────────────┘
```

**Steps:**
1. Mount camera on pan-tilt bracket (use provided screws)
2. Open CSI port latch (pull up)
3. Insert FPC cable with **gold contacts facing Ethernet ports**
4. Push latch down to lock
5. Attach 6mm lens by screwing onto mount
6. Adjust focus by rotating lens
7. Route FPC cable carefully (allow pan-tilt movement)
8. Secure with cable ties

---

## 💡 LED Ring Light Connections

```
LED Ring Light         Raspberry Pi 5 GPIO
─────────────         ─────────────────────

     VCC (5V)  ────────→  Pin 4  (5V Power)
     GND       ────────→  Pin 6  (Ground)
     DATA IN   ────────→  Pin 12 (GPIO18 / PWM)
```

**GPIO Pin Layout:**
```
        ┌──────────────────────┐
        │  1  2  3  4  5  6    │
        │  7  8  9 10 11 12    │  ← Pin 12 = DATA
        │ 13 14 15 16 17 18    │
        │ 19 20 21 22 23 24    │
        │ 25 26 27 28 29 30    │
        │ 31 32 33 34 35 36    │
        │ 37 38 39 40          │
        └──────────────────────┘

Pin 4  = 5V Power (Red wire)
Pin 6  = Ground (Black wire)
Pin 12 = GPIO18 PWM (Yellow/Green data wire)
```

**⚠️ Important:** If LED ring draws more than 500mA, use external 5V power supply!

---

## 🔄 Pan-Tilt Mechanism Connections

### **Integrated Pan-Tilt (2 Servos in One Unit)**

Your pan-tilt has **6 wires total** (3 per servo):
- **Pan servo** (horizontal rotation) - Bottom servo
- **Tilt servo** (vertical rotation) - Top servo

### **Wire Identification**

Typical wire colors from pan-tilt:

| Servo | Wire Color | Function | Connection |
|-------|------------|----------|------------|
| **Pan** | Red | VCC (5V) | → Buck Converter 5V* |
| **Pan** | Brown/Black | Ground | → GPIO Pin 6 |
| **Pan** | Orange/Yellow | Signal | → GPIO Pin 11 (GPIO17) |
| **Tilt** | Red | VCC (5V) | → Buck Converter 5V* |
| **Tilt** | Brown/Black | Ground | → GPIO Pin 9 |
| **Tilt** | Orange/Yellow | Signal | → GPIO Pin 13 (GPIO27) |

**⚠️ CRITICAL: External Power Required!**

```
DO NOT connect servo VCC (red) to Raspberry Pi GPIO!
Use external 5V from buck converter.
```

### **Power Wiring Diagram**

```
Pan-Tilt Mechanism
       │
       │ 6 wires
       │
  ┌────┴────┐
  │         │
Pan       Tilt
│         │
│         │
└────┬────┘
     │
     ├──────────────┐
     │              │
     ▼              ▼
Red Wires      Brown/Black Wires
(Both)         (Both)
     │              │
     │              ├────→ GPIO Pin 6 (Pan GND)
     │              │
     │              └────→ GPIO Pin 9 (Tilt GND)
     │
     ▼
Buck Converter 5V Output
(Set to 5.1V)
```

### **Complete Connection Table**

| Component | Wire Color | GPIO Pin | Physical Pin | Notes |
|-----------|------------|----------|--------------|-------|
| Pan Signal | Orange | GPIO17 | 11 | PWM |
| Pan GND | Brown | - | 6 | Common ground |
| Pan VCC | Red | External | - | Buck converter 5V |
| Tilt Signal | Orange | GPIO27 | 13 | PWM |
| Tilt GND | Brown | - | 9 | Common ground |
| Tilt VCC | Red | External | - | Buck converter 5V |
| LED Data | Yellow/Green | GPIO18 | 12 | PWM |
| LED VCC | Red | - | 4 | GPIO 5V (if <500mA) |
| LED GND | Black | - | 6 | Shared with Pan GND |

**External Power Setup:**

```
12V Battery → Buck Converter → Set to 5.1V
                                │
                                ├─→ Raspberry Pi (USB-C)
                                │
                                ├─→ Pan Servo VCC (red wire)
                                │
                                └─→ Tilt Servo VCC (red wire)

All grounds must connect together:
- Servo GND → GPIO Pin 6, 9
- Buck converter GND → Battery GND
- Raspberry Pi GND → GPIO pins
```

---

## 🖥️ Display Connections

### **7" Touchscreen (DSI)**

```
                   ┌────────────────────────┐
                   │  Raspberry Pi 5        │
                   │                        │
DSI Port ──────────│● DSI (Display)         │
(flat cable)       │                        │
                   │                        │
                   └────────────────────────┘
                          ▲
                          │ DSI Cable
                          │
                   ┌──────┴──────┐
                   │ 7" Display  │
                   │ Touchscreen │
                   └─────────────┘
```

**Enable DSI:**
```bash
sudo raspi-config
# Advanced Options → Resolution → DSI 800x480
```

---

## 🔋 Power System

### **Complete Power Diagram**

```
     ┌─────────────────┐
     │ 12V Li-ion      │
     │ Battery (3S)    │
     │ 10Ah            │
     └────────┬────────┘
              │
              ▼
     ┌─────────────────┐
     │ Buck Converter  │
     │ (12V → 5.1V)    │
     │ Set to 5.1V     │
     └────────┬────────┘
              │
         ┌────┴────┐
         │         │
         ▼         ▼
    ┌────────┐  ┌────────────┐
    │ USB-C  │  │ Servo VCC  │
    │ to Pi  │  │ (Red wires)│
    │ 5.1V   │  │            │
    └────────┘  └────────────┘
```

**Buck Converter Adjustment:**
```bash
# Use small screwdriver to adjust potentiometer
# Measure with multimeter until it reads 5.1V
```

---

## 📊 Complete Wiring Summary

### **GPIO Pin Assignment Table**

| Component | GPIO Pin | Physical Pin | Function |
|-----------|----------|--------------|----------|
| LED Data | GPIO18 | 12 | PWM |
| Servo 1 Signal | GPIO17 | 11 | PWM |
| Servo 2 Signal | GPIO27 | 13 | PWM |
| 5V Power | - | 2, 4 | VCC |
| Ground | - | 6, 9 | GND |
| Camera | CSI | - | MIPI CSI-2 |
| Display | DSI | - | MIPI DSI |

### **Color Coding Reference**

| Wire Color | Function |
|------------|----------|
| Red | 5V Power (VCC) |
| Black/Brown | Ground (GND) |
| Yellow/Green | Data Signal |
| Orange | Servo Signal |
| White | LED Data (alternative) |

---

## 🔧 Assembly Checklist

### **Mechanical Assembly**

- [ ] Raspberry Pi 5 mounted in enclosure
- [ ] Camera module attached to mount
- [ ] 6mm lens screwed onto camera
- [ ] LED ring light positioned around camera
- [ ] Pan servo connected to base
- [ ] Tilt servo connected to camera mount
- [ ] All wires routed through cable channels
- [ ] Enclosure closed and secured

### **Electrical Connections**

- [ ] Camera FPC cable connected to CSI
- [ ] LED ring connected to GPIO (Pins 4, 6, 12)
- [ ] Servo 1 connected to GPIO (Pins 2, 9, 11)
- [ ] Servo 2 connected to GPIO (Pins 2, 9, 13)
- [ ] Display DSI cable connected
- [ ] Buck converter set to 5.1V
- [ ] Battery connected to buck converter
- [ ] USB-C power to Raspberry Pi

### **Initial Testing**

- [ ] Power on Raspberry Pi (LED should light up)
- [ ] Camera detected: `vcgencmd get_camera`
- [ ] LED controllable via Python
- [ ] Servos move to initial position
- [ ] Display shows desktop
- [ ] WiFi connected

---

## 🧪 Testing Commands

### **Test Camera**
```bash
libcamera-hello -t 5000
```

### **Test LED (Python)**
```python
import board
import neopixel

pixels = neopixel.NeoPixel(board.D18, 12, brightness=0.5)
pixels.fill((255, 255, 255))  # White
```

### **Test Servos (Python)**
```python
import RPi.GPIO as GPIO
import time

GPIO.setmode(GPIO.BCM)
GPIO.setup(17, GPIO.OUT)  # Servo 1
GPIO.setup(27, GPIO.OUT)  # Servo 2

# Test pan servo
pwm1 = GPIO.PWM(17, 50)
pwm1.start(7.5)  # Center position
time.sleep(2)
pwm1.stop()
```

### **Check Temperature**
```bash
vcgencmd measure_temp
# Should be 40-60°C with heatsink
```

### **Check Power**
```bash
vcgencmd measure_volts
# Should show ~5.1V
```

---

## ⚠️ Safety Warnings

1. **NEVER connect servos directly to Pi 5V without external power**
   - Can damage Raspberry Pi
   - Use buck converter for servo power

2. **ALWAYS disconnect power before wiring**
   - Prevents short circuits
   - Protects GPIO pins

3. **Use heatsink/fan on Raspberry Pi 5**
   - Pi 5 runs hot under load
   - Thermal throttling reduces performance

4. **Secure all connections**
   - Vibration can loosen wires
   - Use cable ties in enclosure

5. **Don't exceed GPIO current limits**
   - Total GPIO: 500mA max
   - Per pin: 16mA max
   - Use external power for LEDs and servos

---

## 📐 Mounting Dimensions

### **Camera Position**
- Height: 15-20cm above shelf
- Angle: 30-45° downward
- Distance from shelf: 30-50cm

### **LED Position**
- Around camera lens
- Diffused to prevent glare
- Brightness: 50-70%

### **Enclosure Mounting**
- Wall mount or ceiling mount
- Secure with M3 screws
- Cable management channels

---

**🎯 Quick Start: Connect these 3 things first!**

1. **Camera** → CSI port (FPC cable)
2. **Power** → USB-C to Pi (5.1V from buck converter)
3. **Network** → WiFi or Ethernet

Then test with: `python3 run.py detect --source 0`
