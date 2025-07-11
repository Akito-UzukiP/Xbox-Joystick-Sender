#!/usr/bin/env python3
"""
Test script to verify the disconnect button fix
"""

import sys
import time
from PyQt5.QtWidgets import QApplication, QPushButton, QVBoxLayout, QWidget, QLabel
from PyQt5.QtCore import QTimer
from video_stream_visualization import VideoStreamVisualization

class DisconnectTestWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Disconnect Button Test")
        self.setGeometry(100, 100, 400, 300)
        
        layout = QVBoxLayout(self)
        
        self.status_label = QLabel("Test the disconnect button functionality")
        layout.addWidget(self.status_label)
        
        # Create video stream widget
        self.video_widget = VideoStreamVisualization()
        layout.addWidget(self.video_widget)
        
        # Test buttons
        self.quick_test_btn = QPushButton("Quick Connect/Disconnect Test")
        self.quick_test_btn.clicked.connect(self.quick_test)
        layout.addWidget(self.quick_test_btn)
        
        self.stress_test_btn = QPushButton("Stress Test (10 cycles)")
        self.stress_test_btn.clicked.connect(self.stress_test)
        layout.addWidget(self.stress_test_btn)
        
        self.test_counter = 0
        self.max_tests = 0
        
    def quick_test(self):
        """Quick connect and disconnect test"""
        self.status_label.setText("Running quick test...")
        
        # Set test URL (localhost)
        self.video_widget.ip_edit.setText("127.0.0.1")
        self.video_widget.port_spinbox.setValue(5000)
        
        # Connect
        self.video_widget.connect_stream()
        
        # Schedule disconnect after 2 seconds
        QTimer.singleShot(2000, self.delayed_disconnect)
        
    def delayed_disconnect(self):
        """Disconnect after delay"""
        try:
            self.video_widget.disconnect_stream()
            self.status_label.setText("✓ Quick test completed successfully")
        except Exception as e:
            self.status_label.setText(f"✗ Quick test failed: {e}")
            
    def stress_test(self):
        """Stress test with multiple connect/disconnect cycles"""
        self.test_counter = 0
        self.max_tests = 10
        self.status_label.setText(f"Starting stress test: {self.test_counter}/{self.max_tests}")
        
        # Set test URL
        self.video_widget.ip_edit.setText("127.0.0.1")
        self.video_widget.port_spinbox.setValue(5000)
        
        self.run_stress_cycle()
        
    def run_stress_cycle(self):
        """Run one cycle of stress test"""
        if self.test_counter >= self.max_tests:
            self.status_label.setText("✓ Stress test completed successfully")
            return
            
        self.test_counter += 1
        self.status_label.setText(f"Stress test cycle: {self.test_counter}/{self.max_tests}")
        
        try:
            # Connect
            self.video_widget.connect_stream()
            
            # Schedule disconnect and next cycle
            QTimer.singleShot(1000, self.stress_disconnect)
            
        except Exception as e:
            self.status_label.setText(f"✗ Stress test failed at cycle {self.test_counter}: {e}")
            
    def stress_disconnect(self):
        """Disconnect in stress test"""
        try:
            self.video_widget.disconnect_stream()
            # Schedule next cycle
            QTimer.singleShot(500, self.run_stress_cycle)
        except Exception as e:
            self.status_label.setText(f"✗ Stress test disconnect failed at cycle {self.test_counter}: {e}")

def main():
    app = QApplication(sys.argv)
    
    window = DisconnectTestWidget()
    window.show()
    
    print("Disconnect Button Test")
    print("=" * 30)
    print("1. Click 'Quick Connect/Disconnect Test' for a simple test")
    print("2. Click 'Stress Test' for multiple connect/disconnect cycles")
    print("3. You can also manually test the disconnect button in the video widget")
    print("Note: Tests will try to connect to localhost:5000")
    
    sys.exit(app.exec_())

if __name__ == "__main__":
    main() 