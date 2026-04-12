#!/usr/bin/env python3
"""
Pan-Tilt Test Script
Test your integrated pan-tilt mechanism

Usage:
    python3 test_pantil_t.py
"""

import RPi.GPIO as GPIO
import time
import sys

# GPIO Pin Configuration
PAN_GPIO = 17    # GPIO17 = Physical Pin 11
TILT_GPIO = 27   # GPIO27 = Physical Pin 13

# PWM Frequency (50Hz for standard servos)
PWM_FREQ = 50

def angle_to_duty_cycle(angle):
    """
    Convert angle (0-180) to PWM duty cycle (2.5-12.5)
    
    0°   → 2.5% duty cycle
    90°  → 7.5% duty cycle (center)
    180° → 12.5% duty cycle
    """
    return 2.5 + (angle / 180.0) * 10.0

def setup():
    """Initialize GPIO and PWM"""
    print("Initializing GPIO...")
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(PAN_GPIO, GPIO.OUT)
    GPIO.setup(TILT_GPIO, GPIO.OUT)
    
    print("Starting PWM...")
    pan_pwm = GPIO.PWM(PAN_GPIO, PWM_FREQ)
    tilt_pwm = GPIO.PWM(TILT_GPIO, PWM_FREQ)
    
    pan_pwm.start(7.5)  # Start at center (90°)
    tilt_pwm.start(7.5)
    
    time.sleep(0.5)  # Allow servos to initialize
    
    return pan_pwm, tilt_pwm

def move_to(pan_pwm, tilt_pwm, pan_angle, tilt_angle, duration=1.0):
    """
    Move pan-tilt to specified position
    
    Args:
        pan_pwm: Pan PWM object
        tilt_pwm: Tilt PWM object
        pan_angle: Pan angle (0-180)
        tilt_angle: Tilt angle (0-90 recommended)
        duration: Time to wait for movement
    """
    pan_duty = angle_to_duty_cycle(pan_angle)
    tilt_duty = angle_to_duty_cycle(tilt_angle)
    
    print(f"Moving to Pan: {pan_angle}°, Tilt: {tilt_angle}°")
    
    pan_pwm.ChangeDutyCycle(pan_duty)
    tilt_pwm.ChangeDutyCycle(tilt_duty)
    
    time.sleep(duration)
    
    # Reset to prevent jitter
    pan_pwm.ChangeDutyCycle(0)
    tilt_pwm.ChangeDutyCycle(0)

def test_basic_movement(pan_pwm, tilt_pwm):
    """Test basic pan and tilt movement"""
    print("\n=== Basic Movement Test ===\n")
    
    # Center position
    move_to(pan_pwm, tilt_pwm, 90, 45)
    print("✓ Center position")
    time.sleep(1)
    
    # Pan test (left to right)
    print("\nTesting Pan (horizontal)...")
    move_to(pan_pwm, tilt_pwm, 0, 45)
    print("  ← Pan Left (0°)")
    time.sleep(1)
    
    move_to(pan_pwm, tilt_pwm, 90, 45)
    print("  → Pan Center (90°)")
    time.sleep(1)
    
    move_to(pan_pwm, tilt_pwm, 180, 45)
    print("  → Pan Right (180°)")
    time.sleep(1)
    
    move_to(pan_pwm, tilt_pwm, 90, 45)
    print("  → Pan Center (90°)")
    time.sleep(1)
    
    # Tilt test (up and down)
    print("\nTesting Tilt (vertical)...")
    move_to(pan_pwm, tilt_pwm, 90, 0)
    print("  ↑ Tilt Up (0°)")
    time.sleep(1)
    
    move_to(pan_pwm, tilt_pwm, 90, 45)
    print("  ↓ Tilt Center (45°)")
    time.sleep(1)
    
    move_to(pan_pwm, tilt_pwm, 90, 90)
    print("  ↓ Tilt Down (90°)")
    time.sleep(1)
    
    move_to(pan_pwm, tilt_pwm, 90, 45)
    print("  ↑ Tilt Center (45°)")
    time.sleep(1)

def test_scan_pattern(pan_pwm, tilt_pwm):
    """Test scanning pattern for shelf monitoring"""
    print("\n=== Shelf Scan Pattern Test ===\n")
    
    positions = [
        [60, 45, "Left"],
        [90, 45, "Center"],
        [120, 45, "Right"],
        [90, 30, "Up"],
        [90, 60, "Down"],
    ]
    
    for pan, tilt, label in positions:
        move_to(pan_pwm, tilt_pwm, pan, tilt)
        print(f"  Scanning {label} position...")
        time.sleep(2)  # Simulate detection time
    
    # Return to center
    move_to(pan_pwm, tilt_pwm, 90, 45)
    print("\n✓ Scan pattern complete")

def test_smooth_movement(pan_pwm, tilt_pwm):
    """Test smooth sweeping movement"""
    print("\n=== Smooth Sweep Test ===\n")
    
    print("Sweeping pan from left to right...")
    
    for angle in range(0, 181, 10):
        duty = angle_to_duty_cycle(angle)
        pan_pwm.ChangeDutyCycle(duty)
        time.sleep(0.1)
    
    # Reset
    pan_pwm.ChangeDutyCycle(0)
    print("✓ Sweep complete")

def cleanup(pan_pwm, tilt_pwm):
    """Cleanup GPIO"""
    print("\nCleaning up...")
    pan_pwm.stop()
    tilt_pwm.stop()
    GPIO.cleanup()
    print("Done!")

def main():
    print("="*50)
    print("Pan-Tilt Mechanism Test")
    print("="*50)
    print()
    print("⚠️  WARNING: Make sure servos are connected correctly!")
    print("    - Pan Signal → GPIO17 (Pin 11)")
    print("    - Tilt Signal → GPIO27 (Pin 13)")
    print("    - Servo VCC → External 5V (NOT Pi GPIO!)")
    print("    - Servo GND → Pi GND (Pins 6, 9)")
    print()
    
    try:
        # Setup
        pan_pwm, tilt_pwm = setup()
        
        print("✓ Initialization successful")
        print()
        
        # Ask user what test to run
        print("Select test:")
        print("1. Basic Movement Test (pan + tilt)")
        print("2. Shelf Scan Pattern")
        print("3. Smooth Sweep")
        print("4. Run All Tests")
        print()
        
        choice = input("Enter choice (1-4): ").strip()
        
        if choice == '1':
            test_basic_movement(pan_pwm, tilt_pwm)
        elif choice == '2':
            test_scan_pattern(pan_pwm, tilt_pwm)
        elif choice == '3':
            test_smooth_movement(pan_pwm, tilt_pwm)
        elif choice == '4':
            test_basic_movement(pan_pwm, tilt_pwm)
            test_scan_pattern(pan_pwm, tilt_pwm)
            test_smooth_movement(pan_pwm, tilt_pwm)
        else:
            print("Invalid choice. Running basic test...")
            test_basic_movement(pan_pwm, tilt_pwm)
        
        # Return to center position
        move_to(pan_pwm, tilt_pwm, 90, 45)
        print("\n✓ All tests complete!")
        print("Pan-tilt returned to center position (90°, 45°)")
        
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
    except Exception as e:
        print(f"\nError: {str(e)}")
        print("\nTroubleshooting:")
        print("  - Check servo connections")
        print("  - Ensure external 5V power is connected")
        print("  - Verify GPIO pin numbers")
        print("  - Run with sudo: sudo python3 test_pantil_t.py")
    finally:
        cleanup(pan_pwm, tilt_pwm)

if __name__ == "__main__":
    main()
