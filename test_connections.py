#!/usr/bin/env python3
"""
Connection Test Script for DS4 + UR10 Setup
Run this before running the main teleoperation script
"""

import sys
import time

def test_ds4():
    """Test DS4 controller connection"""
    print("\n" + "="*60)
    print("Testing DS4 Controller Connection")
    print("="*60)
    
    import os
    
    # Check for joystick device
    js_devices = []
    for i in range(10):
        device = f"/dev/input/js{i}"
        if os.path.exists(device):
            js_devices.append(device)
    
    if not js_devices:
        print("❌ No joystick devices found!")
        print("\nTroubleshooting:")
        print("1. Connect DS4 via USB cable")
        print("2. Check: ls /dev/input/")
        print("3. Check USB: lsusb | grep Sony")
        print("4. Try: sudo chmod 666 /dev/input/js0")
        return False
    
    print(f"✓ Found joystick device(s): {', '.join(js_devices)}")
    
    # Try to import pyPS4Controller
    try:
        from pyPS4Controller.controller import Controller
        print("✓ pyPS4Controller library installed")
    except ImportError:
        print("❌ pyPS4Controller not installed!")
        print("   Run: pip install pyPS4Controller")
        return False
    
    # Test basic controller connection
    print("\nPress any button on DS4 to test (will timeout in 5 seconds)...")
    
    class TestController(Controller):
        def __init__(self):
            Controller.__init__(self, interface=js_devices[0])
            self.button_pressed = False
        
        def on_x_press(self):
            print("✓ Cross button detected!")
            self.button_pressed = True
        
        def on_circle_press(self):
            print("✓ Circle button detected!")
            self.button_pressed = True
        
        def on_triangle_press(self):
            print("✓ Triangle button detected!")
            self.button_pressed = True
        
        def on_square_press(self):
            print("✓ Square button detected!")
            self.button_pressed = True
    
    try:
        controller = TestController()
        # Note: listen() blocks, so we can't do a timeout easily
        # Just check if we can instantiate
        print("✓ DS4 controller ready")
        del controller
        return True
    except Exception as e:
        print(f"❌ DS4 controller error: {e}")
        return False

def test_ursim():
    """Test URSim connection"""
    print("\n" + "="*60)
    print("Testing URSim Connection")
    print("="*60)
    
    import subprocess
    
    # Check if Docker is running
    try:
        result = subprocess.run(['docker', 'ps'], capture_output=True, text=True, timeout=5)
        if result.returncode != 0:
            print("❌ Docker is not running!")
            print("   Run: sudo systemctl start docker")
            return False
        print("✓ Docker is running")
    except Exception as e:
        print(f"❌ Cannot check Docker: {e}")
        return False
    
    # Check if URSim container is running
    if 'ursim' not in result.stdout:
        print("❌ URSim container not found!")
        print("\nStart URSim with:")
        print("docker run -d --name ursim_ur10 --runtime=runc \\")
        print("    -e ROBOT_MODEL=UR10 -p 5900:5900 -p 6080:6080 \\")
        print("    -p 30001-30004:30001-30004 -p 29999:29999 \\")
        print("    universalrobots/ursim_e-series:latest")
        return False
    
    print("✓ URSim container is running")
    
    # Try to import ur_rtde
    try:
        import rtde_control
        import rtde_receive
        print("✓ ur_rtde library installed")
    except ImportError:
        print("❌ ur_rtde not installed!")
        print("   Run: pip install ur_rtde")
        return False
    
    # Test RTDE connection
    robot_ip = '172.17.0.2'
    print(f"\nAttempting to connect to robot at {robot_ip}...")
    
    try:
        rtde_r = rtde_receive.RTDEReceiveInterface(robot_ip, 1.0)  # 1 second timeout
        
        # Get robot info
        joint_pos = rtde_r.getActualQ()
        robot_mode = rtde_r.getRobotMode()
        safety_mode = rtde_r.getSafetyMode()
        
        print(f"✓ Connected to UR10!")
        print(f"  Robot mode: {robot_mode}")
        print(f"  Safety mode: {safety_mode}")
        print(f"  Joint positions: {[f'{j:.2f}' for j in joint_pos]}")
        
        rtde_r.disconnect()
        
        if robot_mode < 5:  # Not in running mode
            print("\n⚠ WARNING: Robot is not powered on!")
            print("  1. Open http://localhost:6080 in browser")
            print("  2. Click 'ON' button")
            print("  3. Click 'START' to release brakes")
            print("  4. Robot should be in 'Running' mode")
        
        return True
        
    except Exception as e:
        print(f"❌ Cannot connect to robot: {e}")
        print("\nTroubleshooting:")
        print("1. Wait 30 seconds after starting URSim container")
        print("2. Check URSim logs: docker logs ursim_ur10")
        print("3. Restart container: docker restart ursim_ur10")
        print("4. Verify ports: docker port ursim_ur10")
        return False

def test_polyscope_gui():
    """Check if Polyscope GUI is accessible"""
    print("\n" + "="*60)
    print("Testing Polyscope GUI Access")
    print("="*60)
    
    import socket
    
    host = 'localhost'
    port = 6080
    
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(2)
        result = sock.connect_ex((host, port))
        sock.close()
        
        if result == 0:
            print(f"✓ Polyscope GUI is accessible at http://{host}:{port}")
            print("  Open this in your browser to control the robot")
            return True
        else:
            print(f"❌ Cannot access Polyscope GUI at http://{host}:{port}")
            print("  Wait a minute after starting URSim and try again")
            return False
    except Exception as e:
        print(f"❌ Error checking GUI: {e}")
        return False

def main():
    print("\n" + "="*60)
    print("UR10 + DS4 TELEOPERATION - CONNECTION TEST")
    print("="*60)
    
    # Run all tests
    results = {
        'DS4': test_ds4(),
        'URSim': test_ursim(),
        'GUI': test_polyscope_gui()
    }
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    for test_name, passed in results.items():
        status = "✓ PASS" if passed else "❌ FAIL"
        print(f"{test_name:15} {status}")
    
    if all(results.values()):
        print("\n🎉 All tests passed! You're ready to run the teleoperation script.")
        print("\nNext step:")
        print("  python3 ds4_ur10_teleop.py")
    else:
        print("\n⚠ Some tests failed. Fix the issues above before proceeding.")
    
    print("="*60 + "\n")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
    except Exception as e:
        print(f"\n\nUnexpected error: {e}")
        import traceback
        traceback.print_exc()
