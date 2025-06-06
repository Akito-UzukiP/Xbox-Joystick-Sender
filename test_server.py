"""
Simple TCP test server to receive controller data
For testing the Xbox Controller GUI application
"""

import socket
import json
import threading
import time

class TestServer:
    def __init__(self, host='127.0.0.1', port=5555):
        self.host = host
        self.port = port
        self.running = False
        self.socket = None
        self.client_socket = None
        self.packets_received = 0
        
    def start(self):
        """Start the test server"""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.socket.bind((self.host, self.port))
            self.socket.listen(1)
            
            print(f"Test server listening on {self.host}:{self.port}")
            print("Waiting for controller GUI to connect...")
            
            self.running = True
            
            while self.running:
                try:
                    client_socket, client_address = self.socket.accept()
                    print(f"Connection established from {client_address}")
                    self.client_socket = client_socket
                    
                    # Handle client in separate thread
                    client_thread = threading.Thread(
                        target=self.handle_client, 
                        args=(client_socket,), 
                        daemon=True
                    )
                    client_thread.start()
                    client_thread.join()
                    
                except socket.error as e:
                    if self.running:
                        print(f"Socket error: {e}")
                    break
                    
        except Exception as e:
            print(f"Server error: {e}")
        finally:
            self.cleanup()
    
    def handle_client(self, client_socket):
        """Handle client connection"""
        buffer = ""
        last_print_time = time.time()
        
        try:
            while self.running:
                try:
                    data = client_socket.recv(1024).decode('utf-8')
                    if not data:
                        break
                        
                    buffer += data
                    
                    # Process complete JSON messages (separated by newlines)
                    while '\n' in buffer:
                        line, buffer = buffer.split('\n', 1)
                        if line.strip():
                            try:
                                controller_data = json.loads(line.strip())
                                self.packets_received += 1
                                
                                # Print status every 2 seconds
                                current_time = time.time()
                                if current_time - last_print_time >= 2.0:
                                    self.print_controller_status(controller_data)
                                    last_print_time = current_time
                                    
                            except json.JSONDecodeError as e:
                                print(f"JSON decode error: {e}")
                                
                except socket.timeout:
                    continue
                except socket.error as e:
                    print(f"Client socket error: {e}")
                    break
                    
        except Exception as e:
            print(f"Client handling error: {e}")
        finally:
            client_socket.close()
            print("Client disconnected")
    
    def print_controller_status(self, data):
        """Print controller status summary"""
        print(f"\n--- Controller Status (Packets: {self.packets_received}) ---")
        print(f"Left Stick:  X:{data.get('left_stick_x', 0):6.2f}  Y:{data.get('left_stick_y', 0):6.2f}")
        print(f"Right Stick: X:{data.get('right_stick_x', 0):6.2f}  Y:{data.get('right_stick_y', 0):6.2f}")
        print(f"Triggers:    LT:{data.get('left_trigger', -1):6.2f}  RT:{data.get('right_trigger', -1):6.2f}")
        print(f"D-pad:       X:{data.get('dpad_x', 0):2d}       Y:{data.get('dpad_y', 0):2d}")
        
        # Show pressed buttons
        pressed_buttons = []
        for button in ['a_button', 'b_button', 'x_button', 'y_button', 'lb_button', 'rb_button']:
            if data.get(button, 0):
                pressed_buttons.append(button.replace('_button', '').upper())
        
        if pressed_buttons:
            print(f"Buttons:     {', '.join(pressed_buttons)}")
        else:
            print("Buttons:     None pressed")
    
    def stop(self):
        """Stop the server"""
        self.running = False
        if self.socket:
            self.socket.close()
        if self.client_socket:
            self.client_socket.close()
    
    def cleanup(self):
        """Cleanup resources"""
        if self.client_socket:
            self.client_socket.close()
        if self.socket:
            self.socket.close()
        print("Server stopped")

def main():
    """Main function"""
    print("Xbox Controller Test Server")
    print("=" * 30)
    print("This server receives and displays controller data from the GUI application")
    print("Press Ctrl+C to stop")
    print()
    
    server = TestServer()
    
    try:
        server.start()
    except KeyboardInterrupt:
        print("\nShutting down server...")
        server.stop()

if __name__ == "__main__":
    main()
