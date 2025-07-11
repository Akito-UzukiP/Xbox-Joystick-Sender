#!/usr/bin/env python3
"""
Video Stream Test Script
For testing video_stream_visualization module
"""

import sys
from PyQt5.QtWidgets import QApplication
from video_stream_visualization import VideoStreamVisualization

def main():
    app = QApplication(sys.argv)
    
    # Create video stream window
    window = VideoStreamVisualization()
    window.setWindowTitle("Video Stream Test")
    window.resize(1000, 800)
    window.show()
    
    sys.exit(app.exec_())

if __name__ == "__main__":
    main() 