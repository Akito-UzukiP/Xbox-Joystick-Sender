#!/usr/bin/env python3
"""
Test script to verify connection failure handling
"""

import sys
import time
from PyQt5.QtWidgets import QApplication, QPushButton, QVBoxLayout, QWidget, QLabel, QHBoxLayout
from PyQt5.QtCore import QTimer
from video_stream_visualization import VideoStreamVisualization

class ConnectionFailureTestWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Connection Failure Test")
        self.setGeometry(100, 100, 800, 600)
        
        layout = QVBoxLayout(self)
        
        # Instructions
        instructions = QLabel("""
Test Instructions:
1. Make sure stream_server.py is NOT running
2. Click 'Test Connection to Non-existent Server' 
3. Verify that disconnect button works after connection failure
4. Check that UI resets properly after timeout/failure
        """)
        instructions.setStyleSheet("background-color: #f0f0f0; padding: 10px; margin: 5px;")
        layout.addWidget(instructions)
        
        # Test buttons
        button_layout = QHBoxLayout()
        
        self.test_nonexistent_btn = QPushButton("Test Connection to Non-existent Server")
        self.test_nonexistent_btn.clicked.connect(self.test_nonexistent_server)
        button_layout.addWidget(self.test_nonexistent_btn)
        
        self.test_wrong_port_btn = QPushButton("Test Wrong Port")
        self.test_wrong_port_btn.clicked.connect(self.test_wrong_port)
        button_layout.addWidget(self.test_wrong_port_btn)
        
        self.test_timeout_btn = QPushButton("Test Connection Timeout")
        self.test_timeout_btn.clicked.connect(self.test_timeout)
        button_layout.addWidget(self.test_timeout_btn)
        
        layout.addLayout(button_layout)
        
        # Status label
        self.test_status_label = QLabel("Ready to test connection failures")
        self.test_status_label.setStyleSheet("font-weight: bold; padding: 5px;")
        layout.addWidget(self.test_status_label)
        
        # Create video stream widget
        self.video_widget = VideoStreamVisualization()
        layout.addWidget(self.video_widget)
        
        # Manual test instructions
        manual_test = QLabel("""
Manual Test:
1. Try connecting to the video stream above (should fail)
2. Click the Disconnect button - it should work and reset UI
3. Try connecting again - Connect button should be enabled
        """)
        manual_test.setStyleSheet("background-color: #e8f4f8; padding: 10px; margin: 5px;")
        layout.addWidget(manual_test)
        
    def test_nonexistent_server(self):
        """Test connecting to a non-existent server"""
        self.test_status_label.setText("Testing connection to non-existent server (192.168.999.999)...")
        self.test_status_label.setStyleSheet("color: orange; font-weight: bold;")
        
        # Set non-existent IP
        self.video_widget.ip_edit.setText("192.168.999.999")
        self.video_widget.port_spinbox.setValue(5000)
        
        # Try to connect
        self.video_widget.connect_stream()
        
        # Check status after a delay
        QTimer.singleShot(5000, self.check_test_result)
        
    def test_wrong_port(self):
        """Test connecting to wrong port"""
        self.test_status_label.setText("Testing connection to wrong port (localhost:9999)...")
        self.test_status_label.setStyleSheet("color: orange; font-weight: bold;")
        
        # Set localhost with wrong port
        self.video_widget.ip_edit.setText("127.0.0.1")
        self.video_widget.port_spinbox.setValue(9999)
        
        # Try to connect
        self.video_widget.connect_stream()
        
        # Check status after a delay
        QTimer.singleShot(5000, self.check_test_result)
        
    def test_timeout(self):
        """Test connection timeout"""
        self.test_status_label.setText("Testing connection timeout (may take up to 15 seconds)...")
        self.test_status_label.setStyleSheet("color: orange; font-weight: bold;")
        
        # Set IP that exists but doesn't respond (using a non-routable IP)
        self.video_widget.ip_edit.setText("10.254.254.254")
        self.video_widget.port_spinbox.setValue(5000)
        
        # Try to connect
        self.video_widget.connect_stream()
        
        # Check status after a longer delay
        QTimer.singleShot(15000, self.check_test_result)
        
    def check_test_result(self):
        """Check the result of the test"""
        # Check UI state
        connect_enabled = self.video_widget.connect_btn.isEnabled()
        disconnect_enabled = self.video_widget.disconnect_btn.isEnabled()
        is_connected = self.video_widget.connected
        
        if connect_enabled and not disconnect_enabled and not is_connected:
            self.test_status_label.setText("✓ Test PASSED - UI properly reset after connection failure")
            self.test_status_label.setStyleSheet("color: green; font-weight: bold;")
        else:
            self.test_status_label.setText(f"✗ Test FAILED - UI state incorrect (connect: {connect_enabled}, disconnect: {disconnect_enabled}, connected: {is_connected})")
            self.test_status_label.setStyleSheet("color: red; font-weight: bold;")
            
        # Additional check: try disconnect button
        QTimer.singleShot(1000, self.test_disconnect_functionality)
        
    def test_disconnect_functionality(self):
        """Test if disconnect button works after connection failure"""
        try:
            # Try to disconnect
            self.video_widget.disconnect_stream()
            
            # Check if UI is still correct
            connect_enabled = self.video_widget.connect_btn.isEnabled()
            disconnect_enabled = self.video_widget.disconnect_btn.isEnabled()
            
            if connect_enabled and not disconnect_enabled:
                current_text = self.test_status_label.text()
                if "PASSED" in current_text:
                    self.test_status_label.setText(current_text + " + Disconnect button works correctly")
            else:
                self.test_status_label.setText("✗ Disconnect button test FAILED - UI state incorrect after disconnect")
                self.test_status_label.setStyleSheet("color: red; font-weight: bold;")
                
        except Exception as e:
            self.test_status_label.setText(f"✗ Disconnect button test FAILED with exception: {e}")
            self.test_status_label.setStyleSheet("color: red; font-weight: bold;")

def main():
    app = QApplication(sys.argv)
    
    window = ConnectionFailureTestWidget()
    window.show()
    
    print("Connection Failure Test")
    print("=" * 40)
    print("This test verifies that:")
    print("1. Connection failures are properly handled")
    print("2. UI state is correctly reset after failure")
    print("3. Disconnect button works even after connection failure")
    print("4. Timeouts are properly handled")
    print("\nMake sure stream_server.py is NOT running for accurate tests!")
    
    sys.exit(app.exec_())

if __name__ == "__main__":
    main() 