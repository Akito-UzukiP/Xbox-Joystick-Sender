#!/usr/bin/env python3
"""
HTTP MJPEG Stream Test Script
For verifying the fixed video stream functionality
"""

import requests
import cv2
import numpy as np
import time

def test_http_mjpeg_stream(url):
    """Test HTTP MJPEG stream connection and parsing"""
    print(f"Testing connection to: {url}")
    
    try:
        # 发送HTTP请求
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        response = requests.get(url, headers=headers, stream=True, timeout=10)
        
        if response.status_code != 200:
            print(f"HTTP Error: {response.status_code}")
            return False
            
        print("✓ HTTP connection successful")
        print(f"Content-Type: {response.headers.get('content-type', 'Unknown')}")
        
        # Process MJPEG stream
        buffer = b''
        frame_count = 0
        start_time = time.time()
        
        for chunk in response.iter_content(chunk_size=1024):
            if chunk:
                buffer += chunk
                
                # Find JPEG frame boundaries
                while True:
                    # Find JPEG start marker
                    start = buffer.find(b'\xff\xd8')
                    if start == -1:
                        break
                        
                    # Find JPEG end marker
                    end = buffer.find(b'\xff\xd9', start)
                    if end == -1:
                        break
                        
                    # Extract complete JPEG frame
                    jpeg_data = buffer[start:end+2]
                    buffer = buffer[end+2:]
                    
                    # Decode JPEG data
                    try:
                        nparr = np.frombuffer(jpeg_data, np.uint8)
                        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                        
                        if frame is not None:
                            frame_count += 1
                            
                            # Display info every 10 frames
                            if frame_count % 10 == 0:
                                elapsed = time.time() - start_time
                                fps = frame_count / elapsed
                                height, width = frame.shape[:2]
                                print(f"Frame #{frame_count}: {width}x{height}, FPS: {fps:.1f}")
                                
                            # Exit after testing 10 frames
                            if frame_count >= 10:
                                print("✓ MJPEG parsing successful")
                                return True
                                
                        else:
                            print("✗ Frame decode failed")
                            
                    except Exception as e:
                        print(f"✗ Frame decode error: {e}")
                        
                    # Prevent buffer from getting too large
                    if len(buffer) > 1024 * 1024:  # 1MB
                        buffer = buffer[-512*1024:]  # Keep last 512KB
                        
            # Timeout after 30 seconds of testing
            if time.time() - start_time > 30:
                print("✗ Test timeout")
                break
                
    except requests.exceptions.Timeout:
        print("✗ Connection timeout")
        return False
    except requests.exceptions.ConnectionError:
        print("✗ Connection error, please check network and server status")
        return False
    except Exception as e:
        print(f"✗ Test error: {e}")
        return False
    finally:
        try:
            response.close()
        except:
            pass
            
    return False

def main():
    print("HTTP MJPEG Stream Connection Test")
    print("=" * 50)
    
    # Test default URLs
    test_urls = [
        "http://192.168.1.100:5000/video_feed",
        "http://127.0.0.1:5000/video_feed",
        "http://localhost:5000/video_feed"
    ]
    
    for url in test_urls:
        print(f"\nTesting URL: {url}")
        if test_http_mjpeg_stream(url):
            print(f"✓ {url} test successful!")
            break
        else:
            print(f"✗ {url} test failed")
    else:
        print("\nAll test URLs failed, please check:")
        print("1. Is stream_server.py running?")
        print("2. Are IP address and port correct?")
        print("3. Is network connection normal?")
        print("4. Does firewall allow access?")
        
    print("\n" + "=" * 50)
    print("Test completed")

if __name__ == "__main__":
    main() 