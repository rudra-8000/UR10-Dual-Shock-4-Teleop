#!/usr/bin/env python3
"""
DS4 to UR10 Teleoperation Script
No ROS2 required - uses ur_rtde for direct robot control

Controls:
- Left Stick: X-Y motion (cartesian plane)
- L1 Trigger: Move up (Z+)
- L2 Trigger: Move down (Z-)
- Right Stick: Roll (X-axis) and Pitch (Y-axis)
- R1 Trigger: Rotate counterclockwise (Yaw+)
- R2 Trigger: Rotate clockwise (Yaw-)
- Cross (X): Close gripper
- Circle (O): Open gripper
- Triangle: Move to home position
- Square: Emergency stop
- Options: Exit program
"""

import rtde_control
import rtde_receive
import numpy as np
from pyPS4Controller.controller import Controller
import time
import sys
import threading

class UR10DS4Teleop(Controller):
    def __init__(self, robot_ip='172.17.0.2', **kwargs):
        Controller.__init__(self, **kwargs)
        
        # Connect to UR10
        print(f"Connecting to UR10 at {robot_ip}...")
        self.rtde_c = rtde_control.RTDEControlInterface(robot_ip)
        self.rtde_r = rtde_receive.RTDEReceiveInterface(robot_ip)
        print("✓ Connected to UR10")
        
        # Motion parameters
        self.velocity_scale = 0.1  # m/s for position, rad/s for rotation
        self.acceleration = 0.2
        
        # Control state
        self.running = True
        
        # Joystick values (normalized -1 to 1)
        self.left_x = 0.0
        self.left_y = 0.0
        self.right_x = 0.0   # Roll
        self.right_y = 0.0   # Pitch
        self.l1_value = 0.0  # Z+
        self.l2_value = 0.0  # Z-
        self.r1_value = 0.0  # Yaw+
        self.r2_value = 0.0  # Yaw-
        
        # Deadzone for joysticks
        self.deadzone = 0.1
        
        # Home position (modify based on your setup)
        self.home_joint_position = [-1.57, -1.57, -1.57, -1.57, 1.57, 0.0]
        
        # Start motion control thread
        self.motion_thread = threading.Thread(target=self._motion_control_loop, daemon=True)
        self.motion_thread.start()
        
        self._print_controls()
    
    def _print_controls(self):
        """Print control mapping"""
        print("\n" + "="*60)
        print("DS4 UR10 TELEOPERATION - CUSTOM MAPPING")
        print("="*60)
        print("Left Stick:   X-Y cartesian motion")
        print("L1 Trigger:   Move UP (Z+)")
        print("L2 Trigger:   Move DOWN (Z-)")
        print("Right Stick:  Roll (left/right) & Pitch (up/down)")
        print("R1 Trigger:   Rotate CCW (Yaw+)")
        print("R2 Trigger:   Rotate CW (Yaw-)")
        print("")
        print("Cross (X):    Close gripper")
        print("Circle (O):   Open gripper")
        print("Triangle:     Move to home position")
        print("Square:       Emergency stop")
        print("Options:      Exit program")
        print("="*60)
        print("⚠️  WARNING: No deadman switch - robot moves immediately!")
        print("="*60 + "\n")
    
    def _apply_deadzone(self, value):
        """Apply deadzone to joystick values"""
        if abs(value) < self.deadzone:
            return 0.0
        sign = 1 if value > 0 else -1
        return sign * (abs(value) - self.deadzone) / (1 - self.deadzone)
    
    def _motion_control_loop(self):
        """Main control loop for sending velocity commands"""
        rate = 125  # Hz (UR real-time control frequency)
        dt = 1.0 / rate
        
        while self.running:
            try:
                vel_scale = self.velocity_scale
                
                # Calculate Z velocity from L1/L2 triggers
                z_velocity = (self.l1_value - self.l2_value) * vel_scale
                
                # Calculate Yaw velocity from R1/R2 triggers
                yaw_velocity = (self.r1_value - self.r2_value) * vel_scale
                
                # Calculate cartesian velocity command [x, y, z, rx, ry, rz]
                # UR10 base frame: X-forward, Y-left, Z-up
                velocity_cmd = [
                    -self.left_y * vel_scale,   # X: Forward/backward (inverted)
                    -self.left_x * vel_scale,   # Y: Left/right (inverted)
                    z_velocity,                 # Z: Up/down from triggers
                    self.right_y * vel_scale,   # Roll: Right stick Y-axis
                    -self.right_x * vel_scale,  # Pitch: Right stick X-axis (inverted)
                    yaw_velocity                # Yaw: From R1/R2 triggers
                ]
                
                # Only send command if there's actual motion
                if any(abs(v) > 0.001 for v in velocity_cmd):
                    self.rtde_c.speedL(velocity_cmd, self.acceleration, dt * 2)
                else:
                    self.rtde_c.speedStop()
                
                time.sleep(dt)
                
            except Exception as e:
                print(f"Motion control error: {e}")
                self.running = False
                break
    
    # === Button callbacks ===
    def on_x_press(self):
        """Close gripper"""
        print("🤏 Gripper CLOSE (placeholder - implement your gripper control)")
    
    def on_circle_press(self):
        """Open gripper"""
        print("🤏 Gripper OPEN (placeholder - implement your gripper control)")
    
    def on_triangle_press(self):
        """Move to home position"""
        print("Moving to home position...")
        self.rtde_c.speedStop()
        self.rtde_c.moveJ(self.home_joint_position, 1.05, 1.4)
        print("✓ Reached home")
    
    def on_square_press(self):
        """Emergency stop"""
        print("⚠ EMERGENCY STOP")
        self.rtde_c.speedStop()
        self.rtde_c.stopScript()
    
    def on_options_press(self):
        """Exit program"""
        print("\nShutting down...")
        self.running = False
        self.rtde_c.speedStop()
        self.rtde_c.stopScript()
        sys.exit(0)
    
    # === Joystick callbacks ===
    def on_L3_up(self, value):
        """Left stick Y-axis (forward motion)"""
        self.left_y = self._apply_deadzone(value / 32767.0)
        print('L3 up')
    
    def on_L3_down(self, value):
        """Left stick Y-axis (backward motion)"""
        self.left_y = self._apply_deadzone(value / 32767.0)
        print('L3 down')
    
    def on_L3_left(self, value):
        """Left stick X-axis (left motion)"""
        self.left_x = self._apply_deadzone(value / 32767.0)
        print('L3 left')
    
    def on_L3_right(self, value):
        """Left stick X-axis (right motion)"""
        self.left_x = self._apply_deadzone(value / 32767.0)
        print('L3 right')
    
    def on_L3_y_at_rest(self):
        """Left stick Y-axis at rest"""
        self.left_y = 0.0
    
    def on_L3_x_at_rest(self):
        """Left stick X-axis at rest"""
        self.left_x = 0.0
    
    def on_R3_up(self, value):
        """Right stick Y-axis (pitch up / roll forward)"""
        self.r2_value = 0.0
        print('R3 up')
    
    def on_R3_down(self, value):
        """Right stick Y-axis (pitch down / roll back)"""
        self.r2_value = self._apply_deadzone(value / 32767.0)
        print('R3 down')
    
    def on_R3_left(self, value):
        """Right stick X-axis (roll left)"""
        self.l2_value = 0.0
        print('R3 left')
    
    def on_R3_right(self, value):
        """Right stick X-axis (roll right)"""
        self.l2_value = self._apply_deadzone(value / 32767.0)
        print('R3 right')
    
    def on_R3_y_at_rest(self):
        """Right stick Y-axis at rest"""
        self.right_y = 0.0
    
    def on_R3_x_at_rest(self):
        """Right stick X-axis at rest"""
        self.right_x = 0.0
    
    def on_L1_press(self, value=32767.0):
        """L1 trigger (move up)"""
        self.l1_value = self._apply_deadzone(value / 32767.0)
        print('L1')
    
    def on_L1_release(self):
        """L1 trigger release"""
        self.l1_value = 0.0
        print('L1 released')
    
    def on_L2_press(self, value):
        """L2 trigger (move down)"""
        self.right_x = self._apply_deadzone(value / 32767.0)
        print(value)
    
    def on_L2_release(self):
        """L2 trigger release"""
        self.right_x = 0.0
    
    def on_R1_press(self, value=32767.0):
        """R1 trigger (yaw counterclockwise)"""
        self.r1_value = self._apply_deadzone(value / 32767.0)
        print('R1')
    
    def on_R1_release(self):
        """R1 trigger release"""
        self.r1_value = 0.0
    
    def on_R2_press(self, value):
        """R2 trigger (yaw clockwise)"""
        self.right_y = self._apply_deadzone(value / 32767.0)
        print('R2')
    
    def on_R2_release(self):
        """R2 trigger release"""
        self.right_y = 0.0

def main():
    # Configuration
    ROBOT_IP = "172.17.0.2"  # URSim docker container IP
    # For real robot, use: ROBOT_IP = '192.168.1.XXX'  # Your UR10's IP
    
    # Connect to DS4 (wired mode)
    print("Waiting for DS4 controller...")
    print("Make sure your DS4 is connected via USB cable")
    
    try:
        controller = UR10DS4Teleop(
            robot_ip=ROBOT_IP,
            interface="/dev/input/js0"  # Default joystick device
        )
        
        # Start listening for controller input
        controller.listen()
        
    except KeyboardInterrupt:
        print("\nInterrupted by user")
    except Exception as e:
        print(f"\nError: {e}")
        print("\nTroubleshooting:")
        print("1. Check DS4 is connected: ls /dev/input/js*")
        print("2. Check URSim is running: docker ps")
        print("3. Try accessing URSim GUI: http://localhost:6080")
        print("4. Verify robot IP is correct")

if __name__ == "__main__":
    main()

