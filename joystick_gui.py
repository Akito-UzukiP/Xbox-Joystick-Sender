"""
Xbox 360 Controller GUI TCP Sender
- Visual GUI for Xbox360 controller input with TCP transmission
- Configurable IP/port settings with connection management
- Real-time controller input visualization
- Configuration file support
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import pygame
import pygame.joystick
import socket
import json
import time
import threading
import os
from datetime import datetime

class ControllerVisualization(tk.Frame):
    """Frame for visualizing controller input"""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        
        # Create canvas for visualization
        self.canvas = tk.Canvas(self, width=600, height=400, bg='black')
        self.canvas.pack(padx=10, pady=10)
        
        # Initialize visualization elements
        self.init_visualization()
        
    def init_visualization(self):
        """Initialize visual elements on canvas"""
        # Left stick
        self.left_stick_bg = self.canvas.create_oval(50, 50, 150, 150, outline='white', width=2)
        self.left_stick_dot = self.canvas.create_oval(95, 95, 105, 105, fill='red')
        self.canvas.create_text(100, 30, text="Left Stick", fill='white')
        
        # Right stick  
        self.right_stick_bg = self.canvas.create_oval(450, 50, 550, 150, outline='white', width=2)
        self.right_stick_dot = self.canvas.create_oval(495, 95, 505, 105, fill='blue')
        self.canvas.create_text(500, 30, text="Right Stick", fill='white')
        
        # Triggers
        self.left_trigger_bg = self.canvas.create_rectangle(50, 200, 100, 250, outline='white', width=2)
        self.left_trigger_fill = self.canvas.create_rectangle(50, 250, 100, 250, fill='green')
        self.canvas.create_text(75, 270, text="LT", fill='white')
        
        self.right_trigger_bg = self.canvas.create_rectangle(500, 200, 550, 250, outline='white', width=2)
        self.right_trigger_fill = self.canvas.create_rectangle(500, 250, 550, 250, fill='green')
        self.canvas.create_text(525, 270, text="RT", fill='white')
        
        # D-pad
        self.dpad_bg = self.canvas.create_rectangle(280, 80, 320, 120, outline='white', width=2)
        self.dpad_indicator = self.canvas.create_oval(295, 95, 305, 105, fill='yellow')
        self.canvas.create_text(300, 60, text="D-Pad", fill='white')
        
        # Buttons (A, B, X, Y)
        self.button_a = self.canvas.create_oval(380, 120, 400, 140, outline='white', width=2)
        self.button_b = self.canvas.create_oval(400, 100, 420, 120, outline='white', width=2)
        self.button_x = self.canvas.create_oval(360, 100, 380, 120, outline='white', width=2)
        self.button_y = self.canvas.create_oval(380, 80, 400, 100, outline='white', width=2)
        
        self.canvas.create_text(390, 150, text="A", fill='white')
        self.canvas.create_text(410, 90, text="B", fill='white')
        self.canvas.create_text(370, 90, text="X", fill='white')
        self.canvas.create_text(390, 70, text="Y", fill='white')
        
        # Shoulder buttons
        self.lb_button = self.canvas.create_rectangle(150, 200, 200, 230, outline='white', width=2)
        self.rb_button = self.canvas.create_rectangle(400, 200, 450, 230, outline='white', width=2)
        self.canvas.create_text(175, 215, text="LB", fill='white')
        self.canvas.create_text(425, 215, text="RB", fill='white')
        
    def update_visualization(self, controller_data):
        """Update visualization based on controller data"""
        if not controller_data:
            return
            
        # Update left stick
        left_x = controller_data.get('left_stick_x', 0) * 40
        left_y = controller_data.get('left_stick_y', 0) * 40
        self.canvas.coords(self.left_stick_dot, 
                          95 + left_x, 95 + left_y, 
                          105 + left_x, 105 + left_y)
        
        # Update right stick
        right_x = controller_data.get('right_stick_x', 0) * 40
        right_y = controller_data.get('right_stick_y', 0) * 40
        self.canvas.coords(self.right_stick_dot,
                          495 + right_x, 95 + right_y,
                          505 + right_x, 105 + right_y)
        
        # Update triggers
        left_trigger = (controller_data.get('left_trigger', -1) + 1) / 2  # Convert -1,1 to 0,1
        right_trigger = (controller_data.get('right_trigger', -1) + 1) / 2
        
        # Left trigger fill
        fill_height = int(50 * left_trigger)
        self.canvas.coords(self.left_trigger_fill, 50, 250 - fill_height, 100, 250)
        
        # Right trigger fill
        fill_height = int(50 * right_trigger)
        self.canvas.coords(self.right_trigger_fill, 500, 250 - fill_height, 550, 250)
        
        # Update D-pad
        dpad_x = controller_data.get('dpad_x', 0) * 10
        dpad_y = controller_data.get('dpad_y', 0) * -10  # Invert Y for screen coordinates
        self.canvas.coords(self.dpad_indicator,
                          295 + dpad_x, 95 + dpad_y,
                          305 + dpad_x, 105 + dpad_y)
        
        # Update buttons
        buttons = [
            (self.button_a, controller_data.get('a_button', 0)),
            (self.button_b, controller_data.get('b_button', 0)),
            (self.button_x, controller_data.get('x_button', 0)),
            (self.button_y, controller_data.get('y_button', 0)),
            (self.lb_button, controller_data.get('lb_button', 0)),
            (self.rb_button, controller_data.get('rb_button', 0))
        ]
        
        for button_obj, pressed in buttons:
            color = 'red' if pressed else 'black'
            self.canvas.itemconfig(button_obj, fill=color)


class Xbox360ControllerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Xbox 360 Controller TCP Sender")
        self.root.geometry("800x700")
        
        # Configuration
        self.config_file = "controller_config.json"
        self.config = self.load_config()
        
        # Connection state
        self.connected = False
        self.sock = None
        self.running = False
        self.send_thread = None
        
        # Controller
        self.controller = None
        self.joysticks = []
        
        # Statistics
        self.packets_sent = 0
        self.last_error = ""
        
        # Initialize pygame
        pygame.init()
        pygame.joystick.init()
        
        # Setup GUI
        self.setup_gui()
        self.init_controller()
        
        # Start update loop
        self.update_controller_list()
        self.update_status()
        
    def load_config(self):
        """Load configuration from file"""
        default_config = {
            "tcp_ip": "127.0.0.1",
            "tcp_port": 5555,
            "update_rate": 20,  # Hz
            "deadzone": 0.1
        }
        
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                    # Merge with defaults in case of missing keys
                    default_config.update(config)
            return default_config
        except Exception as e:
            messagebox.showerror("Config Error", f"Error loading config: {e}")
            return default_config
    
    def save_config(self):
        """Save configuration to file"""
        try:
            self.config["tcp_ip"] = self.ip_var.get()
            self.config["tcp_port"] = int(self.port_var.get())
            self.config["update_rate"] = int(self.rate_var.get())
            self.config["deadzone"] = float(self.deadzone_var.get())
            
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=2)
            messagebox.showinfo("Config", "Configuration saved successfully!")
        except Exception as e:
            messagebox.showerror("Config Error", f"Error saving config: {e}")
    
    def setup_gui(self):
        """Setup the GUI elements"""
        # Main notebook for tabs
        notebook = ttk.Notebook(self.root)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Control tab
        control_frame = ttk.Frame(notebook)
        notebook.add(control_frame, text="Control")
        
        # Visualization tab
        viz_frame = ttk.Frame(notebook)
        notebook.add(viz_frame, text="Visualization")
        
        # Setup control tab
        self.setup_control_tab(control_frame)
        
        # Setup visualization tab
        self.controller_viz = ControllerVisualization(viz_frame)
        self.controller_viz.pack(fill=tk.BOTH, expand=True)
        
    def setup_control_tab(self, parent):
        """Setup the control tab"""
        # Connection settings frame
        conn_frame = ttk.LabelFrame(parent, text="Connection Settings", padding=10)
        conn_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # IP and Port
        ttk.Label(conn_frame, text="Target IP:").grid(row=0, column=0, sticky=tk.W, padx=5)
        self.ip_var = tk.StringVar(value=self.config["tcp_ip"])
        ttk.Entry(conn_frame, textvariable=self.ip_var, width=15).grid(row=0, column=1, padx=5)
        
        ttk.Label(conn_frame, text="Port:").grid(row=0, column=2, sticky=tk.W, padx=5)
        self.port_var = tk.StringVar(value=str(self.config["tcp_port"]))
        ttk.Entry(conn_frame, textvariable=self.port_var, width=8).grid(row=0, column=3, padx=5)
        
        # Connection buttons
        self.connect_btn = ttk.Button(conn_frame, text="Connect", command=self.connect)
        self.connect_btn.grid(row=0, column=4, padx=10)
        
        self.disconnect_btn = ttk.Button(conn_frame, text="Disconnect", command=self.disconnect, state=tk.DISABLED)
        self.disconnect_btn.grid(row=0, column=5, padx=5)
        
        # Settings frame
        settings_frame = ttk.LabelFrame(parent, text="Settings", padding=10)
        settings_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(settings_frame, text="Update Rate (Hz):").grid(row=0, column=0, sticky=tk.W, padx=5)
        self.rate_var = tk.StringVar(value=str(self.config["update_rate"]))
        ttk.Entry(settings_frame, textvariable=self.rate_var, width=8).grid(row=0, column=1, padx=5)
        
        ttk.Label(settings_frame, text="Deadzone:").grid(row=0, column=2, sticky=tk.W, padx=5)
        self.deadzone_var = tk.StringVar(value=str(self.config["deadzone"]))
        ttk.Entry(settings_frame, textvariable=self.deadzone_var, width=8).grid(row=0, column=3, padx=5)
        
        ttk.Button(settings_frame, text="Save Config", command=self.save_config).grid(row=0, column=4, padx=10)
        ttk.Button(settings_frame, text="Load Config", command=self.load_config_file).grid(row=0, column=5, padx=5)
        
        # Controller frame
        controller_frame = ttk.LabelFrame(parent, text="Controller", padding=10)
        controller_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(controller_frame, text="Controller:").grid(row=0, column=0, sticky=tk.W, padx=5)
        self.controller_var = tk.StringVar(value="No controller detected")
        ttk.Label(controller_frame, textvariable=self.controller_var).grid(row=0, column=1, sticky=tk.W, padx=5)
        
        ttk.Button(controller_frame, text="Refresh", command=self.init_controller).grid(row=0, column=2, padx=10)
        
        # Status frame
        status_frame = ttk.LabelFrame(parent, text="Status", padding=10)
        status_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Connection status
        ttk.Label(status_frame, text="Connection:").grid(row=0, column=0, sticky=tk.W, padx=5)
        self.conn_status_var = tk.StringVar(value="Disconnected")
        ttk.Label(status_frame, textvariable=self.conn_status_var, foreground="red").grid(row=0, column=1, sticky=tk.W, padx=5)
        
        # Packet count
        ttk.Label(status_frame, text="Packets Sent:").grid(row=1, column=0, sticky=tk.W, padx=5)
        self.packets_var = tk.StringVar(value="0")
        ttk.Label(status_frame, textvariable=self.packets_var).grid(row=1, column=1, sticky=tk.W, padx=5)
        
        # Last error
        ttk.Label(status_frame, text="Last Error:").grid(row=2, column=0, sticky=tk.NW, padx=5)
        self.error_var = tk.StringVar(value="None")
        error_label = ttk.Label(status_frame, textvariable=self.error_var, foreground="red", wraplength=400)
        error_label.grid(row=2, column=1, sticky=tk.W, padx=5)
        
        # Log text area
        ttk.Label(status_frame, text="Log:").grid(row=3, column=0, sticky=tk.NW, padx=5, pady=(10,0))
        
        log_frame = tk.Frame(status_frame)
        log_frame.grid(row=3, column=1, sticky=tk.NSEW, padx=5, pady=(10,0))
        status_frame.grid_rowconfigure(3, weight=1)
        status_frame.grid_columnconfigure(1, weight=1)
        
        self.log_text = tk.Text(log_frame, height=8, width=60)
        scrollbar = ttk.Scrollbar(log_frame, orient=tk.VERTICAL, command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=scrollbar.set)
        
        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
    def load_config_file(self):
        """Load configuration from selected file"""
        filename = filedialog.askopenfilename(
            title="Load Configuration",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        if filename:
            try:
                with open(filename, 'r') as f:
                    config = json.load(f)
                    self.config.update(config)
                    
                # Update GUI
                self.ip_var.set(self.config["tcp_ip"])
                self.port_var.set(str(self.config["tcp_port"]))
                self.rate_var.set(str(self.config["update_rate"]))
                self.deadzone_var.set(str(self.config["deadzone"]))
                
                messagebox.showinfo("Config", "Configuration loaded successfully!")
            except Exception as e:
                messagebox.showerror("Config Error", f"Error loading config: {e}")
    
    def log_message(self, message):
        """Add message to log"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}\n"
        
        self.log_text.insert(tk.END, log_entry)
        self.log_text.see(tk.END)
        
        # Keep only last 100 lines
        lines = self.log_text.get("1.0", tk.END).split('\n')
        if len(lines) > 100:
            self.log_text.delete("1.0", f"{len(lines)-100}.0")
    
    def init_controller(self):
        """Initialize controller"""
        pygame.joystick.quit()
        pygame.joystick.init()
        
        self.joysticks = []
        joystick_count = pygame.joystick.get_count()
        
        if joystick_count == 0:
            self.controller_var.set("No controller detected")
            self.controller = None
            self.log_message("No controller detected")
        else:
            for i in range(joystick_count):
                joystick = pygame.joystick.Joystick(i)
                joystick.init()
                self.joysticks.append(joystick)
            
            self.controller = self.joysticks[0]
            controller_name = self.controller.get_name()
            self.controller_var.set(f"{controller_name} (ID: 0)")
            self.log_message(f"Controller connected: {controller_name}")
    
    def connect(self):
        """Connect to TCP server"""
        try:
            ip = self.ip_var.get()
            port = int(self.port_var.get())
            
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.settimeout(5)  # 5 second timeout
            self.sock.connect((ip, port))
            
            self.connected = True
            self.running = True
            
            # Update GUI
            self.connect_btn.config(state=tk.DISABLED)
            self.disconnect_btn.config(state=tk.NORMAL)
            self.conn_status_var.set("Connected")
            
            # Start sending thread
            self.send_thread = threading.Thread(target=self.send_loop, daemon=True)
            self.send_thread.start()
            
            self.log_message(f"Connected to {ip}:{port}")
            
        except Exception as e:
            self.last_error = str(e)
            self.error_var.set(self.last_error)
            self.log_message(f"Connection failed: {e}")
            messagebox.showerror("Connection Error", f"Failed to connect: {e}")
    
    def disconnect(self):
        """Disconnect from TCP server"""
        self.running = False
        self.connected = False
        
        if self.sock:
            try:
                self.sock.close()
            except:
                pass
            self.sock = None
        
        # Update GUI
        self.connect_btn.config(state=tk.NORMAL)
        self.disconnect_btn.config(state=tk.DISABLED)
        self.conn_status_var.set("Disconnected")
        
        self.log_message("Disconnected")
    
    def read_controller(self):
        """Read controller input"""
        if not self.controller:
            return None
        
        # Process pygame events
        pygame.event.pump()
        
        def apply_deadzone(value, deadzone):
            return 0.0 if abs(value) < deadzone else value
        
        deadzone = float(self.deadzone_var.get())
        
        try:
            # Analog sticks
            left_x = apply_deadzone(self.controller.get_axis(0), deadzone)
            left_y = apply_deadzone(self.controller.get_axis(1), deadzone)
            right_x = apply_deadzone(self.controller.get_axis(2), deadzone)
            right_y = apply_deadzone(self.controller.get_axis(3), deadzone)
            
            # Triggers
            try:
                left_trigger = self.controller.get_axis(4)
                right_trigger = self.controller.get_axis(5)
            except:
                left_trigger = -1.0
                right_trigger = -1.0
            
            # Buttons
            num_buttons = self.controller.get_numbuttons()
            button_states = {}
            for i in range(num_buttons):
                button_states[f'button_{i}'] = self.controller.get_button(i)
            
            # Button mapping
            button_mapping = {
                'a_button': button_states.get('button_0', 0),
                'b_button': button_states.get('button_1', 0),
                'x_button': button_states.get('button_2', 0),
                'y_button': button_states.get('button_3', 0),
                'lb_button': button_states.get('button_4', 0),
                'rb_button': button_states.get('button_5', 0),
                'back_button': button_states.get('button_6', 0),
                'start_button': button_states.get('button_7', 0),
                'xbox_button': button_states.get('button_8', 0),
                'left_stick_button': button_states.get('button_9', 0),
                'right_stick_button': button_states.get('button_10', 0)
            }
            
            # D-pad
            try:
                hat = self.controller.get_hat(0)
                dpad_x = hat[0]
                dpad_y = hat[1]
            except:
                dpad_x = 0
                dpad_y = 0
            
            controller_data = {
                'left_stick_x': left_x,
                'left_stick_y': left_y,
                'right_stick_x': right_x,
                'right_stick_y': right_y,
                'left_trigger': left_trigger,
                'right_trigger': right_trigger,
                'dpad_x': dpad_x,
                'dpad_y': dpad_y,
                'buttons': button_states,
                **button_mapping,
                'timestamp': time.time()
            }
            
            return controller_data
            
        except Exception as e:
            self.log_message(f"Error reading controller: {e}")
            return None
    
    def send_loop(self):
        """Main sending loop (runs in separate thread)"""
        update_rate = int(self.rate_var.get())
        sleep_time = 1.0 / update_rate
        
        while self.running and self.connected:
            try:
                controller_data = self.read_controller()
                if controller_data and self.sock:
                    data_json = json.dumps(controller_data)
                    self.sock.sendall((data_json + '\n').encode('utf-8'))
                    self.packets_sent += 1
                    
                    # Update visualization on main thread
                    self.root.after_idle(self.controller_viz.update_visualization, controller_data)
                
                time.sleep(sleep_time)
                
            except Exception as e:
                self.last_error = str(e)
                self.root.after_idle(lambda: self.error_var.set(self.last_error))
                self.root.after_idle(lambda: self.log_message(f"Send error: {e}"))
                break
        
        # Cleanup on thread exit
        self.root.after_idle(self.disconnect)
    
    def update_controller_list(self):
        """Update controller list periodically"""
        if not self.connected:  # Only check when not connected to avoid interruption
            current_count = pygame.joystick.get_count()
            if (current_count > 0 and not self.controller) or (current_count == 0 and self.controller):
                self.init_controller()
        
        # Schedule next update
        self.root.after(2000, self.update_controller_list)
    
    def update_status(self):
        """Update status displays"""
        self.packets_var.set(str(self.packets_sent))
        
        # Update connection status color
        if self.connected:
            # Find the label widget and update color
            for widget in self.root.winfo_children():
                if isinstance(widget, ttk.Notebook):
                    for tab in widget.tabs():
                        tab_widget = widget.nametowidget(tab)
                        for child in tab_widget.winfo_children():
                            if isinstance(child, ttk.LabelFrame) and "Status" in str(child.cget("text")):
                                for grandchild in child.winfo_children():
                                    if isinstance(grandchild, ttk.Label) and grandchild.cget("textvariable") == str(self.conn_status_var):
                                        grandchild.config(foreground="green")
        
        # Schedule next update
        self.root.after(1000, self.update_status)
    
    def on_closing(self):
        """Handle window closing"""
        if self.connected:
            self.disconnect()
        
        # Save config on exit
        try:
            self.save_config()
        except:
            pass
        
        pygame.quit()
        self.root.destroy()


def main():
    root = tk.Tk()
    app = Xbox360ControllerGUI(root)
    
    # Handle window closing
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    
    # Start the GUI
    root.mainloop()


if __name__ == "__main__":
    main()
