"""
Xbox 360 Controller GUI TCP Sender - PyQt Version
- Visual GUI for Xbox360 controller input with TCP transmission
- Configurable IP/port settings with connection management
- Real-time controller input visualization
- Configuration file support
- Message Bus TCP receiver for pub-sub topics
- Real-time plotting for motor outputs, depth and heading
"""

import sys
import os
import json
import time
import threading
import socket
from datetime import datetime
from collections import defaultdict, deque
import numpy as np
import yaml

import pygame
import pygame.joystick

from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                            QHBoxLayout, QGridLayout, QTabWidget, QLabel, 
                            QLineEdit, QPushButton, QCheckBox, QSpinBox, 
                            QTextEdit, QTreeWidget, QTreeWidgetItem, QSplitter,
                            QGroupBox, QMessageBox, QFileDialog, QComboBox,
                            QDoubleSpinBox, QFrame)
from PyQt5.QtCore import QTimer, QThread, pyqtSignal, QObject, Qt
from PyQt5.QtGui import QFont, QPixmap, QPainter, QColor, QPen, QBrush

import matplotlib
matplotlib.use('Qt5Agg')
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from matplotlib.animation import FuncAnimation
import matplotlib.dates as mdates

# Configure matplotlib for better display
plt.rcParams['font.sans-serif'] = ['DejaVu Sans', 'Arial', 'sans-serif']
plt.rcParams['axes.unicode_minus'] = False


class ControllerDataSender(QThread):
    """Controller data sender thread"""
    error_occurred = pyqtSignal(str)
    packet_sent = pyqtSignal()
    controller_data_updated = pyqtSignal(dict)
    
    def __init__(self, controller, sock, config):
        super().__init__()
        self.controller = controller
        self.sock = sock
        self.config = config
        self.running = True
        
    def stop(self):
        self.running = False
        
    def apply_deadzone(self, value, deadzone):
        return 0.0 if abs(value) < deadzone else value
        
    def read_controller(self):
        """Read controller input"""
        if not self.controller:
            return None
        
        pygame.event.pump()
        deadzone = float(self.config.get("deadzone", 0.1))
        
        try:
            # Analog sticks
            left_x = self.apply_deadzone(self.controller.get_axis(0), deadzone)
            left_y = self.apply_deadzone(self.controller.get_axis(1), deadzone)
            right_x = self.apply_deadzone(self.controller.get_axis(2), deadzone)
            right_y = self.apply_deadzone(self.controller.get_axis(3), deadzone)
            
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
            self.error_occurred.emit(f"Controller read error: {e}")
            return None
    
    def run(self):
        """Main sending loop"""
        update_rate = int(self.config.get("update_rate", 20))
        sleep_time = 1.0 / update_rate
        
        while self.running:
            try:
                controller_data = self.read_controller()
                if controller_data and self.sock:
                    data_json = json.dumps(controller_data)
                    self.sock.sendall((data_json + '\n').encode('utf-8'))
                    self.packet_sent.emit()
                    self.controller_data_updated.emit(controller_data)
                
                self.msleep(int(sleep_time * 1000))
                
            except Exception as e:
                self.error_occurred.emit(f"Send error: {e}")
                break


class MessageBusReceiver(QThread):
    """Message bus receiver thread"""
    error_occurred = pyqtSignal(str)
    message_received = pyqtSignal(str, float, dict)  # topic, timestamp, data
    
    def __init__(self, sock):
        super().__init__()
        self.sock = sock
        self.running = True
        
    def stop(self):
        self.running = False
        
    def run(self):
        """Message receiving loop"""
        buffer = ""
        
        while self.running:
            try:
                if self.sock:
                    data = self.sock.recv(4096).decode('utf-8')
                    if not data:
                        # Connection closed by remote
                        self.error_occurred.emit("Connection closed by remote")
                        break
                    
                    buffer += data
                    
                    while '\n' in buffer:
                        line, buffer = buffer.split('\n', 1)
                        if line.strip():
                            try:
                                message = json.loads(line.strip())
                                topic = message.get('topic', 'unknown')
                                timestamp = message.get('timestamp', time.time())
                                data = message.get('data', {})
                                
                                self.message_received.emit(topic, timestamp, data)
                                
                            except json.JSONDecodeError as e:
                                self.error_occurred.emit(f"JSON parse error: {e}")
                            except Exception as e:
                                self.error_occurred.emit(f"Message processing error: {e}")
                
                self.msleep(1)  # Small delay to prevent excessive CPU usage
                
            except socket.timeout:
                # Timeout is expected, continue checking for disconnection
                continue
            except ConnectionResetError:
                self.error_occurred.emit("Connection reset by remote")
                break
            except ConnectionAbortedError:
                self.error_occurred.emit("Connection aborted")
                break
            except OSError as e:
                # Handle socket errors (including connection closed)
                self.error_occurred.emit(f"Socket error: {e}")
                break
            except Exception as e:
                self.error_occurred.emit(f"Message receive error: {e}")
                break


class Xbox360ControllerGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Xbox 360 Controller TCP Sender - PyQt Version")
        self.setGeometry(100, 100, 1200, 900)
        
        # Configuration
        self.config_file = "controller_config.json"
        self.config = self.load_config()
        
        # Connection status
        self.connected = False
        self.sock = None
        self.sender_thread = None
        
        # Message bus connection status
        self.msgbus_connected = False
        self.msgbus_sock = None
        self.msgbus_thread = None
        
        # Controller
        self.controller = None
        self.joysticks = []
        
        # Statistics
        self.packets_sent = 0
        self.last_error = ""
        
        # GPS Waypoints
        self.waypoints = []
        self.gps_navigation_yaw = 0.0  # GPS导航偏航角
        
        # Initialize pygame
        pygame.init()
        pygame.joystick.init()
        
        # Setup GUI
        self.setup_gui()
        self.init_controller()
        
        # Start update timers
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_controller_list)
        self.update_timer.start(2000)  # Check controller every 2 seconds
        
        self.status_timer = QTimer()
        self.status_timer.timeout.connect(self.update_status)
        self.status_timer.start(1000)  # Update status every second
        
    def load_config(self):
        """Load configuration from file"""
        default_config = {
            "tcp_ip": "127.0.0.1",
            "tcp_port": 5555,
            "msgbus_port": 9999,
            "update_rate": 20,
            "deadzone": 0.1,
            "invert_yaw": False,
            "video_stream_ip": "192.168.1.100",
            "video_stream_port": 5000
        }
        
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                    default_config.update(config)
            return default_config
        except Exception as e:
            QMessageBox.critical(self, "Configuration Error", f"Configuration loading error: {e}")
            return default_config
    
    def save_config(self):
        """Save configuration to file"""
        try:
            self.config["tcp_ip"] = self.ip_edit.text()
            self.config["tcp_port"] = int(self.port_spinbox.value())
            self.config["msgbus_port"] = int(self.msgbus_port_spinbox.value())
            self.config["update_rate"] = int(self.rate_spinbox.value())
            self.config["deadzone"] = float(self.deadzone_spinbox.value())
            self.config["invert_yaw"] = self.invert_yaw_checkbox.isChecked()
            
            # Save video stream configuration
            if hasattr(self, 'video_stream_widget'):
                video_config = self.video_stream_widget.get_config()
                self.config.update(video_config)
            
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=2)
        except Exception as e:
            QMessageBox.critical(self, "Configuration Error", f"Failed to save configuration: {e}")
    
    def setup_gui(self):
        """Setup GUI elements"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout(central_widget)
        
        # Main tab widget
        self.tab_widget = QTabWidget()
        layout.addWidget(self.tab_widget)
        
        # Controller control tab
        self.setup_control_tab()
        
        # Controller visualization tab
        self.setup_visualization_tab()
        
        # Message bus tab
        self.setup_msgbus_tab()
        
        # Plotting tab
        self.setup_plotting_tab()
        
        # FPV instruments tab
        self.setup_fpv_instruments_tab()
        
        # Video stream tab
        self.setup_video_stream_tab()
        
    def setup_control_tab(self):
        """Setup control tab"""
        control_widget = QWidget()
        self.tab_widget.addTab(control_widget, "Controller Control")
        
        layout = QVBoxLayout(control_widget)
        
        # Connection settings group
        conn_group = QGroupBox("Connection Settings")
        conn_layout = QGridLayout(conn_group)
        
        # Controller Data Transmission Settings
        conn_layout.addWidget(QLabel("Controller Data Transmission"), 0, 0, 1, 6)
        conn_layout.addWidget(QLabel("Target IP:"), 1, 0)
        self.ip_edit = QLineEdit(self.config["tcp_ip"])
        conn_layout.addWidget(self.ip_edit, 1, 1)
        
        conn_layout.addWidget(QLabel("Controller Port:"), 1, 2)
        self.port_spinbox = QSpinBox()
        self.port_spinbox.setRange(1, 65535)
        self.port_spinbox.setValue(self.config["tcp_port"])
        conn_layout.addWidget(self.port_spinbox, 1, 3)
        
        self.connect_btn = QPushButton("Connect")
        self.connect_btn.clicked.connect(self.connect)
        conn_layout.addWidget(self.connect_btn, 1, 4)
        
        self.disconnect_btn = QPushButton("Disconnect")
        self.disconnect_btn.clicked.connect(self.disconnect)
        self.disconnect_btn.setEnabled(False)
        conn_layout.addWidget(self.disconnect_btn, 1, 5)
        
        conn_layout.addWidget(QLabel("Controller Status:"), 2, 0)
        self.controller_conn_status_label = QLabel("Disconnected")
        self.controller_conn_status_label.setStyleSheet("color: red")
        conn_layout.addWidget(self.controller_conn_status_label, 2, 1, 1, 2)
        
        # Message Bus Connection Settings
        conn_layout.addWidget(QLabel("Message Bus Connection"), 3, 0, 1, 6)
        conn_layout.addWidget(QLabel("Target IP:"), 4, 0)
        self.msgbus_ip_edit = QLineEdit(self.config["tcp_ip"])
        conn_layout.addWidget(self.msgbus_ip_edit, 4, 1)
        
        conn_layout.addWidget(QLabel("Message Bus Port:"), 4, 2)
        self.msgbus_port_spinbox = QSpinBox()
        self.msgbus_port_spinbox.setRange(1, 65535)
        self.msgbus_port_spinbox.setValue(self.config["msgbus_port"])
        conn_layout.addWidget(self.msgbus_port_spinbox, 4, 3)
        
        self.msgbus_connect_btn = QPushButton("Connect")
        self.msgbus_connect_btn.clicked.connect(self.connect_msgbus)
        conn_layout.addWidget(self.msgbus_connect_btn, 4, 4)
        
        self.msgbus_disconnect_btn = QPushButton("Disconnect")
        self.msgbus_disconnect_btn.clicked.connect(self.disconnect_msgbus)
        self.msgbus_disconnect_btn.setEnabled(False)
        conn_layout.addWidget(self.msgbus_disconnect_btn, 4, 5)
        
        conn_layout.addWidget(QLabel("Message Bus Status:"), 5, 0)
        self.msgbus_status_label = QLabel("Disconnected")
        self.msgbus_status_label.setStyleSheet("color: red")
        conn_layout.addWidget(self.msgbus_status_label, 5, 1, 1, 2)
        
        layout.addWidget(conn_group)
        
        # Settings group
        settings_group = QGroupBox("Settings")
        settings_layout = QGridLayout(settings_group)
        
        settings_layout.addWidget(QLabel("Update Rate (Hz):"), 0, 0)
        self.rate_spinbox = QSpinBox()
        self.rate_spinbox.setRange(1, 100)
        self.rate_spinbox.setValue(self.config["update_rate"])
        settings_layout.addWidget(self.rate_spinbox, 0, 1)
        
        settings_layout.addWidget(QLabel("Deadzone:"), 0, 2)
        self.deadzone_spinbox = QDoubleSpinBox()
        self.deadzone_spinbox.setRange(0.0, 1.0)
        self.deadzone_spinbox.setSingleStep(0.01)
        self.deadzone_spinbox.setValue(self.config["deadzone"])
        settings_layout.addWidget(self.deadzone_spinbox, 0, 3)
        
        self.invert_yaw_checkbox = QCheckBox("Invert Yaw")
        self.invert_yaw_checkbox.setChecked(self.config.get("invert_yaw", False))
        settings_layout.addWidget(self.invert_yaw_checkbox, 0, 4)
        
        save_btn = QPushButton("Save Config")
        save_btn.clicked.connect(self.save_config)
        settings_layout.addWidget(save_btn, 0, 5)
        
        load_btn = QPushButton("Load Config")
        load_btn.clicked.connect(self.load_config_file)
        settings_layout.addWidget(load_btn, 0, 6)
        
        layout.addWidget(settings_group)
        
        # Controller group
        controller_group = QGroupBox("Controller")
        controller_layout = QGridLayout(controller_group)
        
        controller_layout.addWidget(QLabel("Controller:"), 0, 0)
        self.controller_label = QLabel("No controller detected")
        controller_layout.addWidget(self.controller_label, 0, 1)
        
        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self.init_controller)
        controller_layout.addWidget(refresh_btn, 0, 2)
        
        # Control commands group
        command_group = QGroupBox("Control Commands")
        command_layout = QHBoxLayout(command_group)
        
        reset_yaw_btn = QPushButton("Reset Yaw Direction")
        reset_yaw_btn.clicked.connect(self.reset_yaw_direction)
        reset_yaw_btn.setStyleSheet("QPushButton { background-color: #4CAF50; color: white; font-weight: bold; }")
        command_layout.addWidget(reset_yaw_btn)
        
        command_layout.addStretch()  # Add flexible space
        
        controller_layout.addWidget(command_group, 1, 0, 1, 3)  # Span 3 columns
        
        layout.addWidget(controller_group)
        
        # GPS Waypoints group
        waypoints_group = QGroupBox("GPS Waypoints")
        waypoints_layout = QGridLayout(waypoints_group)
        
        # File selection
        waypoints_layout.addWidget(QLabel("Waypoints File:"), 0, 0)
        self.waypoints_file_edit = QLineEdit()
        self.waypoints_file_edit.setPlaceholderText("Select waypoints YAML file...")
        waypoints_layout.addWidget(self.waypoints_file_edit, 0, 1, 1, 3)
        
        browse_btn = QPushButton("Browse")
        browse_btn.clicked.connect(self.browse_waypoints_file)
        waypoints_layout.addWidget(browse_btn, 0, 4)
        
        # Navigation control buttons
        load_waypoints_btn = QPushButton("Load Waypoints")
        load_waypoints_btn.clicked.connect(self.load_waypoints)
        load_waypoints_btn.setStyleSheet("QPushButton { background-color: #2196F3; color: white; font-weight: bold; }")
        waypoints_layout.addWidget(load_waypoints_btn, 1, 0)
        
        start_nav_btn = QPushButton("Start Navigation")
        start_nav_btn.clicked.connect(self.start_navigation)
        start_nav_btn.setStyleSheet("QPushButton { background-color: #4CAF50; color: white; font-weight: bold; }")
        waypoints_layout.addWidget(start_nav_btn, 1, 1)
        
        stop_nav_btn = QPushButton("Stop Navigation") 
        stop_nav_btn.clicked.connect(self.stop_navigation)
        stop_nav_btn.setStyleSheet("QPushButton { background-color: #f44336; color: white; font-weight: bold; }")
        waypoints_layout.addWidget(stop_nav_btn, 1, 2)
        
        next_waypoint_btn = QPushButton("Next Waypoint")
        next_waypoint_btn.clicked.connect(self.next_waypoint)
        waypoints_layout.addWidget(next_waypoint_btn, 1, 3)
        
        prev_waypoint_btn = QPushButton("Prev Waypoint")
        prev_waypoint_btn.clicked.connect(self.prev_waypoint)
        waypoints_layout.addWidget(prev_waypoint_btn, 1, 4)
        
        # Waypoints status
        waypoints_layout.addWidget(QLabel("Waypoints Status:"), 2, 0)
        self.waypoints_status_label = QLabel("No waypoints loaded")
        self.waypoints_status_label.setStyleSheet("color: orange")
        waypoints_layout.addWidget(self.waypoints_status_label, 2, 1, 1, 4)
        
        layout.addWidget(waypoints_group)
        
        # Status group
        status_group = QGroupBox("Status")
        status_layout = QVBoxLayout(status_group)
        
        # Connection status (compact layout)
        status_info_layout = QGridLayout()
        status_info_layout.addWidget(QLabel("Connection Status:"), 0, 0)
        self.conn_status_label = QLabel("Disconnected")
        self.conn_status_label.setStyleSheet("color: red")
        status_info_layout.addWidget(self.conn_status_label, 0, 1)
        
        status_info_layout.addWidget(QLabel("Packets Sent:"), 0, 2)
        self.packets_label = QLabel("0")
        status_info_layout.addWidget(self.packets_label, 0, 3)
        
        status_info_layout.addWidget(QLabel("Last Error:"), 1, 0)
        self.error_label = QLabel("None")
        self.error_label.setStyleSheet("color: red")
        self.error_label.setWordWrap(True)
        status_info_layout.addWidget(self.error_label, 1, 1, 1, 3)  # Span columns
        
        # Set column stretch to allow error info to take more space
        status_info_layout.setColumnStretch(1, 1)
        status_info_layout.setColumnStretch(3, 1)
        
        status_layout.addLayout(status_info_layout)
        
        # Log area (takes main space)
        status_layout.addWidget(QLabel("Log:"))
        self.log_text = QTextEdit()
        self.log_text.setMinimumHeight(300)  # Increase minimum height
        status_layout.addWidget(self.log_text, 1)  # Set stretch factor to 1, occupy remaining space
        
        layout.addWidget(status_group)
        
    def setup_visualization_tab(self):
        """Setup visualization tab"""
        from controller_visualization import ControllerVisualization
        self.viz_widget = ControllerVisualization()
        self.tab_widget.addTab(self.viz_widget, "Controller Visualization")
        
    def setup_msgbus_tab(self):
        """Setup message bus tab"""
        from message_bus_visualization import MessageBusVisualization
        self.msgbus_widget = MessageBusVisualization()
        self.tab_widget.addTab(self.msgbus_widget, "Message Bus")
        
    def setup_plotting_tab(self):
        """Setup plotting tab"""
        from plotting_visualization import PlottingVisualization
        self.plotting_widget = PlottingVisualization()
        self.tab_widget.addTab(self.plotting_widget, "Motor & Depth Monitor")
        
    def setup_fpv_instruments_tab(self):
        """Setup FPV instruments tab"""
        from fpv_instruments_visualization import FPVInstrumentsVisualization
        self.fpv_instruments_widget = FPVInstrumentsVisualization()
        self.tab_widget.addTab(self.fpv_instruments_widget, "FPV Instruments")
        
    def setup_video_stream_tab(self):
        """Setup video stream tab"""
        from video_stream_visualization import VideoStreamVisualization
        self.video_stream_widget = VideoStreamVisualization(self.config)
        self.tab_widget.addTab(self.video_stream_widget, "Video Stream")
        
    def load_config_file(self):
        """Load configuration from selected file"""
        filename, _ = QFileDialog.getOpenFileName(
            self, "Load Configuration", "", "JSON files (*.json);;All files (*.*)"
        )
        if filename:
            try:
                with open(filename, 'r') as f:
                    config = json.load(f)
                    self.config.update(config)
                    
                # Update GUI
                self.ip_edit.setText(self.config["tcp_ip"])
                self.port_spinbox.setValue(self.config["tcp_port"])
                self.msgbus_port_spinbox.setValue(self.config["msgbus_port"])
                self.rate_spinbox.setValue(self.config["update_rate"])
                self.deadzone_spinbox.setValue(self.config["deadzone"])
                self.invert_yaw_checkbox.setChecked(self.config.get("invert_yaw", False))
                
                # Update video stream GUI if available
                if hasattr(self, 'video_stream_widget'):
                    self.video_stream_widget.ip_edit.setText(self.config.get("video_stream_ip", "192.168.1.100"))
                    self.video_stream_widget.port_spinbox.setValue(self.config.get("video_stream_port", 5000))
                
                QMessageBox.information(self, "Configuration", "Configuration loaded successfully!")
            except Exception as e:
                QMessageBox.critical(self, "Configuration Error", f"Failed to load configuration: {e}")
    
    def log_message(self, message):
        """添加消息到日志"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}"
        
        self.log_text.append(log_entry)
        
        # 保持最新100行
        document = self.log_text.document()
        if document.blockCount() > 100:
            cursor = self.log_text.textCursor()
            cursor.movePosition(cursor.Start)
            cursor.movePosition(cursor.Down, cursor.KeepAnchor, document.blockCount() - 100)
            cursor.removeSelectedText()
            
    def init_controller(self):
        """初始化控制器"""
        pygame.joystick.quit()
        pygame.joystick.init()
        
        self.joysticks = []
        joystick_count = pygame.joystick.get_count()
        
        if joystick_count == 0:
            self.controller_label.setText("No controller detected")
            self.controller = None
            self.log_message("No controller detected")
        else:
            for i in range(joystick_count):
                joystick = pygame.joystick.Joystick(i)
                joystick.init()
                self.joysticks.append(joystick)
            
            self.controller = self.joysticks[0]
            controller_name = self.controller.get_name()
            self.controller_label.setText(f"{controller_name} (ID: 0)")
            self.log_message(f"Controller connected: {controller_name}")
    
    def connect(self):
        """连接到TCP服务器"""
        try:
            ip = self.ip_edit.text()
            port = self.port_spinbox.value()
            
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.settimeout(5)
            self.sock.connect((ip, port))
            
            self.connected = True
            
            # 更新GUI
            self.connect_btn.setEnabled(False)
            self.disconnect_btn.setEnabled(True)
            self.conn_status_label.setText("Connected")
            self.conn_status_label.setStyleSheet("color: green")
            self.controller_conn_status_label.setText("Connected")
            self.controller_conn_status_label.setStyleSheet("color: green")
            
            # 启动发送线程
            self.sender_thread = ControllerDataSender(self.controller, self.sock, self.config)
            self.sender_thread.error_occurred.connect(self.on_sender_error)
            self.sender_thread.packet_sent.connect(self.on_packet_sent)
            self.sender_thread.controller_data_updated.connect(self.on_controller_data_updated)
            self.sender_thread.start()
            
            self.log_message(f"Connected to {ip}:{port}")
            
        except Exception as e:
            self.last_error = str(e)
            self.error_label.setText(self.last_error)
            self.log_message(f"Connection failed: {e}")
            QMessageBox.critical(self, "Connection Error", f"Connection failed: {e}")
    
    def disconnect(self):
        """断开TCP服务器连接"""
        self.connected = False
        
        if self.sender_thread:
            self.sender_thread.stop()
            self.sender_thread.wait(1000)
            self.sender_thread = None
        
        if self.sock:
            try:
                self.sock.close()
            except:
                pass
            self.sock = None
        
        # 更新GUI
        self.connect_btn.setEnabled(True)
        self.disconnect_btn.setEnabled(False)
        self.conn_status_label.setText("Disconnected")
        self.conn_status_label.setStyleSheet("color: red")
        self.controller_conn_status_label.setText("Disconnected")
        self.controller_conn_status_label.setStyleSheet("color: red")
        
        self.log_message("Disconnected")
    
    def connect_msgbus(self):
        """连接到消息总线TCP服务器"""
        try:
            ip = self.msgbus_ip_edit.text()
            port = self.msgbus_port_spinbox.value()
            
            self.msgbus_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.msgbus_sock.settimeout(5)  # 连接超时
            self.msgbus_sock.connect((ip, port))
            self.msgbus_sock.settimeout(1.0)  # 设置接收超时，便于检测断开
            
            self.msgbus_connected = True
            
            # 更新GUI
            self.msgbus_connect_btn.setEnabled(False)
            self.msgbus_disconnect_btn.setEnabled(True)
            self.msgbus_status_label.setText("Connected")
            self.msgbus_status_label.setStyleSheet("color: green")
            
            # 启动接收线程
            self.msgbus_thread = MessageBusReceiver(self.msgbus_sock)
            self.msgbus_thread.error_occurred.connect(self.on_msgbus_error)
            self.msgbus_thread.message_received.connect(self.on_message_received)
            self.msgbus_thread.start()
            
            # 连接成功后立即请求广播所有参数
            try:
                message = {
                    "topic": "request_broadcast_all_params",
                    "data": ""
                }
                message_json = json.dumps(message)
                self.msgbus_sock.sendall((message_json + '\n').encode('utf-8'))
                self.log_message("Broadcast all params request sent")
            except Exception as e:
                self.log_message(f"Failed to send broadcast all params request: {e}")
            
            self.log_message(f"Message bus connected to {ip}:{port}")
            
        except Exception as e:
            self.last_error = str(e)
            self.error_label.setText(self.last_error)
            self.log_message(f"Message bus connection failed: {e}")
            QMessageBox.critical(self, "Connection Error", f"Message bus connection failed: {e}")
    
    def disconnect_msgbus(self):
        """断开消息总线TCP服务器连接"""
        self.msgbus_connected = False
        
        if self.msgbus_thread:
            self.msgbus_thread.stop()
            self.msgbus_thread.wait(1000)
            self.msgbus_thread = None
        
        if self.msgbus_sock:
            try:
                self.msgbus_sock.close()
            except:
                pass
            self.msgbus_sock = None
        
        # 更新GUI
        self.msgbus_connect_btn.setEnabled(True)
        self.msgbus_disconnect_btn.setEnabled(False)
        self.msgbus_status_label.setText("Disconnected")
        self.msgbus_status_label.setStyleSheet("color: red")
        
        self.log_message("Message bus disconnected")
    
    def on_sender_error(self, error_msg):
        """处理发送线程错误"""
        self.last_error = error_msg
        self.error_label.setText(self.last_error)
        self.log_message(error_msg)
        self.disconnect()
    
    def on_packet_sent(self):
        """处理数据包发送事件"""
        self.packets_sent += 1
    
    def on_controller_data_updated(self, controller_data):
        """处理控制器数据更新"""
        if hasattr(self, 'viz_widget'):
            self.viz_widget.update_visualization(controller_data)
    
    def on_msgbus_error(self, error_msg):
        """处理消息总线错误"""
        self.log_message(error_msg)
        self.disconnect_msgbus()
    
    def on_message_received(self, topic, timestamp, data):
        """处理收到的消息"""
        # 添加到消息总线可视化
        if hasattr(self, 'msgbus_widget'):
            self.msgbus_widget.add_message(topic, timestamp, data)
        
        # 添加到绘图可视化
        if hasattr(self, 'plotting_widget') and topic == "fc_data":
            self.plotting_widget.add_data_point(topic, data)
            
        # 添加到FPV仪表可视化
        if hasattr(self, 'fpv_instruments_widget'):
            if topic == "extra_imu":
                self.fpv_instruments_widget.update_imu_data(data)
            elif topic == "fc_data":
                self.fpv_instruments_widget.update_fc_data(data)
            elif topic == "param_desired_roll_changed":
                if data.get("param_name") == "desired_roll":
                    self.fpv_instruments_widget.update_desired_roll(data.get("param_value", 0.0))
            elif topic == "param_desired_yaw_changed":
                if data.get("param_name") == "desired_yaw":
                    self.fpv_instruments_widget.update_desired_yaw(data.get("param_value", 0.0))
            elif topic == "param_desired_z_changed":
                if data.get("param_name") == "desired_z":
                    self.fpv_instruments_widget.update_desired_depth(data.get("param_value", 0.0))
            elif topic == "all_params":
                # 处理所有参数更新，包括armed和depth_hold状态
                self.fpv_instruments_widget.update_all_params(data)
            elif topic == "param_armed_changed":
                if data.get("param_name") == "armed":
                    self.fpv_instruments_widget.update_armed_status(data.get("param_value", False))
            elif topic == "param_depth_hold_changed":
                if data.get("param_name") == "depth_hold":
                    self.fpv_instruments_widget.update_depth_hold_status(data.get("param_value", False))
            elif topic == "gps_navigation_yaw":
                # 处理GPS导航偏航角数据
                if "yaw" in data:
                    self.gps_navigation_yaw = data["yaw"]
                    self.fpv_instruments_widget.update_gps_navigation_yaw(self.gps_navigation_yaw)
    
    def update_controller_list(self):
        """定期更新控制器列表"""
        if not self.connected:  # 只在未连接时检查以避免中断
            current_count = pygame.joystick.get_count()
            if (current_count > 0 and not self.controller) or (current_count == 0 and self.controller):
                self.init_controller()
    
    def update_status(self):
        """更新状态显示"""
        self.packets_label.setText(str(self.packets_sent))
    
    def reset_yaw_direction(self):
        """重置航向角方向"""
        if not self.msgbus_connected or not self.msgbus_sock:
            QMessageBox.warning(self, "Warning", "Please connect to message bus first to send reset command!")
            return
        
        try:
            # 构造消息
            message = {
                "topic": "set_current_yaw_as_zero",
                "data": ""
            }
            
            # 发送消息
            message_json = json.dumps(message)
            self.msgbus_sock.sendall((message_json + '\n').encode('utf-8'))
            
            self.log_message("Reset yaw direction command sent")
            QMessageBox.information(self, "Success", "Reset yaw direction command sent!")
            
        except Exception as e:
            error_msg = f"Failed to send reset yaw direction command: {e}"
            self.log_message(error_msg)
            QMessageBox.critical(self, "Error", error_msg)
    
    def browse_waypoints_file(self):
        """浏览选择waypoints文件"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, 
            "选择Waypoints YAML文件", 
            "", 
            "YAML files (*.yaml *.yml);;All files (*)"
        )
        if file_path:
            self.waypoints_file_edit.setText(file_path)
    
    def load_waypoints(self):
        """加载waypoints文件"""
        file_path = self.waypoints_file_edit.text().strip()
        if not file_path:
            QMessageBox.warning(self, "警告", "请先选择waypoints文件!")
            return
        
        if not os.path.exists(file_path):
            QMessageBox.critical(self, "错误", f"文件不存在: {file_path}")
            return
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
            
            # 检查文件格式
            if 'waypoints' not in data:
                QMessageBox.critical(self, "错误", "无效的waypoints文件格式: 缺少'waypoints'字段")
                return
            
            waypoints_list = data['waypoints']
            if not isinstance(waypoints_list, list):
                QMessageBox.critical(self, "错误", "无效的waypoints文件格式: 'waypoints'应该是列表")
                return
            
            # 转换为所需格式
            self.waypoints = []
            for wp in waypoints_list:
                if isinstance(wp, list) and len(wp) >= 2:
                    lat, lon = float(wp[0]), float(wp[1])
                    self.waypoints.append((lat, lon))
                else:
                    QMessageBox.critical(self, "错误", f"无效的waypoint格式: {wp}")
                    return
            
            # 更新状态
            count = len(self.waypoints)
            self.waypoints_status_label.setText(f"已加载 {count} 个waypoints")
            self.waypoints_status_label.setStyleSheet("color: green")
            
            self.log_message(f"成功加载 {count} 个waypoints from {file_path}")
            QMessageBox.information(self, "成功", f"成功加载 {count} 个waypoints!")
            
        except Exception as e:
            error_msg = f"加载waypoints文件失败: {e}"
            self.log_message(error_msg)
            QMessageBox.critical(self, "错误", error_msg)
    
    def send_gps_command(self, topic, data=None):
        """发送GPS相关命令到消息总线"""
        if not self.msgbus_connected or not self.msgbus_sock:
            QMessageBox.warning(self, "警告", "请先连接到消息总线!")
            return False
        
        try:
            message = {
                "topic": topic,
                "data": data if data is not None else {}
            }
            
            message_json = json.dumps(message)
            self.msgbus_sock.sendall((message_json + '\n').encode('utf-8'))
            
            self.log_message(f"GPS命令已发送: {topic}")
            return True
            
        except Exception as e:
            error_msg = f"发送GPS命令失败: {e}"
            self.log_message(error_msg)
            QMessageBox.critical(self, "错误", error_msg)
            return False
    
    def start_navigation(self):
        """开始导航"""
        if not self.waypoints:
            QMessageBox.warning(self, "警告", "请先加载waypoints!")
            return
        
        # 发送waypoints
        if self.send_gps_command("gps_nav_set_waypoints", {"waypoints": self.waypoints}):
            # 开始导航
            if self.send_gps_command("gps_nav_start"):
                QMessageBox.information(self, "成功", f"导航已开始，共 {len(self.waypoints)} 个waypoints!")
    
    def stop_navigation(self):
        """停止导航"""
        if self.send_gps_command("gps_nav_stop"):
            QMessageBox.information(self, "成功", "导航已停止!")
    
    def next_waypoint(self):
        """下一个waypoint"""
        if self.send_gps_command("gps_nav_next_waypoint"):
            self.log_message("切换到下一个waypoint")
    
    def prev_waypoint(self):
        """上一个waypoint"""
        if self.send_gps_command("gps_nav_prev_waypoint"):
            self.log_message("切换到上一个waypoint")

    def closeEvent(self, event):
        """处理窗口关闭事件"""
        if self.connected:
            self.disconnect()
        
        if self.msgbus_connected:
            self.disconnect_msgbus()
        
        # 保存配置
        try:
            self.save_config()
        except:
            pass
        
        pygame.quit()
        event.accept()


def main():
    app = QApplication(sys.argv)
    
    # 设置应用程序信息
    app.setApplicationName("Xbox 360 Controller TCP Sender")
    app.setApplicationVersion("2.0")
    
    # 创建主窗口
    window = Xbox360ControllerGUI()
    window.show()
    
    sys.exit(app.exec_())


if __name__ == "__main__":
    main() 