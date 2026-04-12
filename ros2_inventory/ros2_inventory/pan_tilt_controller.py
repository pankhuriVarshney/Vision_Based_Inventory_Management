#!/usr/bin/env python3
"""
Pan-Tilt Mechanism Controller for Inventory Management System
Controls 2x MG90S/MG995 servo motors for camera positioning
Hardware: Raspberry Pi 5 + GPIO + External 5V power
"""

import rclpy
from rclpy.node import Node
from std_msgs.msg import Float64, Bool
from geometry_msgs.msg import Point
import threading
import time

try:
    import RPi.GPIO as GPIO
    HAS_GPIO = True
except ImportError:
    HAS_GPIO = False
    print("WARNING: RPi.GPIO not available. Running in simulation mode.")


class PanTiltController(Node):
    """
    Pan-Tilt servo controller with smooth motion and position feedback
    Pan: 0-180 degrees (horizontal sweep)
    Tilt: 0-90 degrees (vertical sweep, limited to avoid cable strain)
    """
    
    # Servo configuration
    PAN_PIN = 14      # GPIO 14 (Pin 8)
    TILT_PIN = 15     # GPIO 15 (Pin 10)
    PWM_FREQ = 50     # 50Hz standard for servos
    
    # Angle limits (degrees)
    PAN_MIN = 0
    PAN_MAX = 180
    TILT_MIN = 0
    TILT_MAX = 90     # Limit tilt to prevent cable tangling
    
    # Smoothing parameters
    STEP_SIZE = 2     # Degrees per step for smooth motion
    STEP_DELAY = 0.02 # Seconds between steps (20ms)
    
    def __init__(self):
        super().__init__('pan_tilt_controller')
        
        # Declare parameters
        self.declare_parameter('pan_pin', self.PAN_PIN)
        self.declare_parameter('tilt_pin', self.TILT_PIN)
        self.declare_parameter('pan_min', self.PAN_MIN)
        self.declare_parameter('pan_max', self.PAN_MAX)
        self.declare_parameter('tilt_min', self.TILT_MIN)
        self.declare_parameter('tilt_max', self.TILT_MAX)
        self.declare_parameter('smooth_motion', True)
        self.declare_parameter('auto_scan', False)
        self.declare_parameter('scan_interval', 10.0)  # Seconds between scans
        
        # Get parameters
        self.pan_pin = self.get_parameter('pan_pin').get_parameter_value().integer_value
        self.tilt_pin = self.get_parameter('tilt_pin').get_parameter_value().integer_value
        self.pan_min = self.get_parameter('pan_min').get_parameter_value().integer_value
        self.pan_max = self.get_parameter('pan_max').get_parameter_value().integer_value
        self.tilt_min = self.get_parameter('tilt_min').get_parameter_value().integer_value
        self.tilt_max = self.get_parameter('tilt_max').get_parameter_value().integer_value
        self.smooth_motion = self.get_parameter('smooth_motion').get_parameter_value().bool_value
        self.auto_scan = self.get_parameter('auto_scan').get_parameter_value().bool_value
        self.scan_interval = self.get_parameter('scan_interval').get_parameter_value().double_value
        
        # Current positions
        self.current_pan = 90.0   # Center position
        self.current_tilt = 45.0  # Center position
        self.target_pan = 90.0
        self.target_tilt = 45.0
        
        # GPIO setup
        self.pan_pwm = None
        self.tilt_pwm = None
        self._gpio_setup()
        
        # Publishers
        self.position_pub = self.create_publisher(Point, 'pan_tilt/position', 10)
        self.status_pub = self.create_publisher(Bool, 'pan_tilt/status', 10)
        
        # Subscribers
        self.create_subscription(Float64, 'pan_tilt/pan_cmd', self.pan_callback, 10)
        self.create_subscription(Float64, 'pan_tilt/tilt_cmd', self.tilt_callback, 10)
        self.create_subscription(Point, 'pan_tilt/position_cmd', self.position_callback, 10)
        self.create_subscription(Bool, 'pan_tilt/scan_trigger', self.scan_trigger_callback, 10)
        
        # Timers
        self.position_timer = self.create_timer(0.1, self.publish_position)  # 10Hz position feedback
        self.motion_timer = self.create_timer(0.05, self.update_motion)      # 20Hz motion update
        
        if self.auto_scan:
            self.scan_timer = self.create_timer(self.scan_interval, self.auto_scan_callback)
            self.scan_positions = [(45, 30), (90, 30), (135, 30), (90, 60)]  # Scan pattern
            self.scan_index = 0
        
        self.get_logger().info(
            f'Pan-Tilt controller initialized: '
            f'Pan[{self.pan_min}-{self.pan_max}] Tilt[{self.tilt_min}-{self.tilt_max}]'
        )
        
        # Move to home position
        self.set_position(90, 45)
    
    def _gpio_setup(self):
        """Initialize GPIO pins for servo control"""
        if not HAS_GPIO:
            self.get_logger().warn('GPIO not available - running in simulation mode')
            return
            
        try:
            GPIO.setmode(GPIO.BCM)
            GPIO.setwarnings(False)
            
            # Setup pins
            GPIO.setup(self.pan_pin, GPIO.OUT)
            GPIO.setup(self.tilt_pin, GPIO.OUT)
            
            # Initialize PWM
            self.pan_pwm = GPIO.PWM(self.pan_pin, self.PWM_FREQ)
            self.tilt_pwm = GPIO.PWM(self.tilt_pin, self.PWM_FREQ)
            
            self.pan_pwm.start(0)
            self.tilt_pwm.start(0)
            
            self.get_logger().info(f'GPIO initialized: Pan(GPIO{self.pan_pin}), Tilt(GPIO{self.tilt_pin})')
            
        except Exception as e:
            self.get_logger().error(f'GPIO setup failed: {str(e)}')
            self.pan_pwm = None
            self.tilt_pwm = None
    
    def angle_to_duty_cycle(self, angle: float) -> float:
        """
        Convert angle (0-180) to duty cycle (2.5-12.5)
        Standard servo: 0.5ms pulse = 0°, 2.5ms pulse = 180°
        At 50Hz: 20ms period, so duty cycle = pulse_width/20 * 100
        """
        # Clamp angle
        angle = max(0, min(180, angle))
        # Map 0-180 to 2.5-12.5 duty cycle
        duty = 2.5 + (angle / 180.0) * 10.0
        return duty
    
    def set_servo_position(self, pan_angle: float, tilt_angle: float):
        """Set servo positions immediately (no smoothing)"""
        if not HAS_GPIO or self.pan_pwm is None:
            self.get_logger().debug(f'Simulate: Pan={pan_angle:.1f}, Tilt={tilt_angle:.1f}')
            self.current_pan = pan_angle
            self.current_tilt = tilt_angle
            return
        
        try:
            # Clamp to limits
            pan_angle = max(self.pan_min, min(self.pan_max, pan_angle))
            tilt_angle = max(self.tilt_min, min(self.tilt_max, tilt_angle))
            
            # Convert to duty cycle and set
            pan_duty = self.angle_to_duty_cycle(pan_angle)
            tilt_duty = self.angle_to_duty_cycle(tilt_angle)
            
            self.pan_pwm.ChangeDutyCycle(pan_duty)
            self.tilt_pwm.ChangeDutyCycle(tilt_duty)
            
            # Small delay for servo to respond
            time.sleep(0.02)
            
            # Stop PWM to prevent jitter (servos hold position)
            self.pan_pwm.ChangeDutyCycle(0)
            self.tilt_pwm.ChangeDutyCycle(0)
            
            self.current_pan = pan_angle
            self.current_tilt = tilt_angle
            
        except Exception as e:
            self.get_logger().error(f'Servo control error: {str(e)}')
    
    def set_position(self, pan_angle: float, tilt_angle: float, smooth: bool = None):
        """
        Set target position with optional smoothing
        """
        if smooth is None:
            smooth = self.smooth_motion
            
        # Clamp to limits
        self.target_pan = max(self.pan_min, min(self.pan_max, pan_angle))
        self.target_tilt = max(self.tilt_min, min(self.tilt_max, tilt_angle))
        
        if not smooth:
            self.set_servo_position(self.target_pan, self.target_tilt)
    
    def update_motion(self):
        """Smooth motion update (called by timer)"""
        if not self.smooth_motion:
            return
            
        # Calculate steps toward target
        pan_diff = self.target_pan - self.current_pan
        tilt_diff = self.target_tilt - self.current_tilt
        
        # If close enough, snap to target
        if abs(pan_diff) < self.STEP_SIZE and abs(tilt_diff) < self.STEP_SIZE:
            if pan_diff != 0 or tilt_diff != 0:
                self.set_servo_position(self.target_pan, self.target_tilt)
            return
        
        # Move one step toward target
        new_pan = self.current_pan + (self.STEP_SIZE if pan_diff > 0 else -self.STEP_SIZE)
        new_tilt = self.current_tilt + (self.STEP_SIZE if tilt_diff > 0 else -self.STEP_SIZE)
        
        self.set_servo_position(new_pan, new_tilt)
    
    def pan_callback(self, msg: Float64):
        """Handle pan angle command"""
        self.set_position(msg.data, self.target_tilt)
        self.get_logger().debug(f'Pan command: {msg.data}')
    
    def tilt_callback(self, msg: Float64):
        """Handle tilt angle command"""
        self.set_position(self.target_pan, msg.data)
        self.get_logger().debug(f'Tilt command: {msg.data}')
    
    def position_callback(self, msg: Point):
        """Handle combined position command (Point.x=pan, Point.y=tilt)"""
        self.set_position(msg.x, msg.y)
        self.get_logger().info(f'Position command: Pan={msg.x:.1f}, Tilt={msg.y:.1f}')
    
    def scan_trigger_callback(self, msg: Bool):
        """Trigger shelf scan sequence"""
        if msg.data:
            self.perform_scan()
    
    def auto_scan_callback(self):
        """Auto-scan timer callback"""
        if self.auto_scan:
            self.perform_scan()
    
    def perform_scan(self):
        """Perform shelf scan sequence"""
        self.get_logger().info('Starting shelf scan sequence...')
        
        # Define scan positions: (pan, tilt) for different shelf sections
        scan_positions = [
            (45, 30),   # Left section, lower
            (90, 30),   # Center section, lower
            (135, 30),  # Right section, lower
            (135, 60),  # Right section, upper
            (90, 60),   # Center section, upper
            (45, 60),   # Left section, upper
            (90, 45),   # Return to center
        ]
        
        for pan, tilt in scan_positions:
            self.set_position(pan, tilt)
            time.sleep(1.5)  # Wait for capture at each position
        
        self.get_logger().info('Scan sequence complete')
    
    def publish_position(self):
        """Publish current position"""
        msg = Point()
        msg.x = self.current_pan
        msg.y = self.current_tilt
        msg.z = 0.0  # Reserved for zoom if added later
        self.position_pub.publish(msg)
        
        # Publish status
        status = Bool()
        status.data = (HAS_GPIO and self.pan_pwm is not None)
        self.status_pub.publish(status)
    
    def get_camera_aim_point(self, frame_width: int, frame_height: int) -> tuple:
        """
        Calculate where the camera is currently aimed in the frame
        Returns: (x, y) in pixel coordinates
        """
        # Map pan/tilt angles to frame coordinates
        # Assuming 60° FOV for camera
        fov_h = 60  # Horizontal FOV
        fov_v = 45  # Vertical FOV
        
        pan_offset = (self.current_pan - 90) / 90.0 * (fov_h / 2)
        tilt_offset = (self.current_tilt - 45) / 45.0 * (fov_v / 2)
        
        x = frame_width / 2 + (pan_offset / (fov_h / 2)) * (frame_width / 2)
        y = frame_height / 2 - (tilt_offset / (fov_v / 2)) * (frame_height / 2)
        
        return (int(x), int(y))
    
    def destroy_node(self):
        """Cleanup GPIO"""
        self.get_logger().info('Shutting down pan-tilt controller...')
        
        # Return to home position
        self.set_position(90, 45, smooth=False)
        time.sleep(0.5)
        
        if HAS_GPIO and self.pan_pwm is not None:
            self.pan_pwm.stop()
            self.tilt_pwm.stop()
            GPIO.cleanup()
        
        super().destroy_node()


def main(args=None):
    rclpy.init(args=args)
    node = PanTiltController()
    
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()