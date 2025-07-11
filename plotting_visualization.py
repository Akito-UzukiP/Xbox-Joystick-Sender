"""
绘图可视化模块 - PyQt版本
用于绘制电机输出和深度的实时图表
"""

import time
import threading
from datetime import datetime
from collections import deque
import numpy as np

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, 
                            QLabel, QPushButton, QSpinBox, QCheckBox)
from PyQt5.QtCore import QTimer, Qt

import matplotlib
matplotlib.use('Qt5Agg')
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from matplotlib.animation import FuncAnimation
import matplotlib.dates as mdates

# 配置matplotlib以适应中文显示
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False


class PlottingVisualization(QWidget):
    """电机输出和深度绘图可视化组件"""
    
    def __init__(self):
        super().__init__()
        
        # 数据存储
        self.motor_data = [deque(maxlen=200) for _ in range(6)]  # 6个电机
        self.depth_data = deque(maxlen=200)
        self.timestamp_data = deque(maxlen=200)
        
        # 线程安全锁
        self.lock = threading.Lock()
        
        # 设置绘图界面
        self.setup_plotting_interface()
        
        # 启动动画
        self.start_animation()
        
    def setup_plotting_interface(self):
        """设置绘图界面"""
        layout = QVBoxLayout(self)
        
        # 控制面板
        control_layout = QHBoxLayout()
        
        # 清除数据按钮
        clear_btn = QPushButton("清除数据")
        clear_btn.clicked.connect(self.clear_data)
        control_layout.addWidget(clear_btn)
        
        # 时间窗口控制
        control_layout.addWidget(QLabel("Time Window (sec):"))
        self.time_window_spinbox = QSpinBox()
        self.time_window_spinbox.setRange(10, 300)
        self.time_window_spinbox.setValue(30)
        self.time_window_spinbox.valueChanged.connect(self.update_time_window)
        control_layout.addWidget(self.time_window_spinbox)
        
        # 自动缩放复选框
        self.auto_scale_checkbox = QCheckBox("自动缩放")
        self.auto_scale_checkbox.setChecked(True)
        control_layout.addWidget(self.auto_scale_checkbox)
        
        control_layout.addStretch()
        
        layout.addLayout(control_layout)
        
        # 创建matplotlib图形
        self.fig = Figure(figsize=(12, 6), dpi=100)
        self.fig.suptitle('电机输出和深度监控', fontsize=14, fontweight='bold')
        
        # 创建子图
        self.ax_motors = self.fig.add_subplot(2, 1, 1)
        self.ax_depth = self.fig.add_subplot(2, 1, 2)
        
        # 配置电机子图
        self.ax_motors.set_title('电机输出 (PWM值 1000-2000)', fontsize=12)
        self.ax_motors.set_ylabel('PWM值')
        self.ax_motors.grid(True, alpha=0.3)
        self.ax_motors.set_ylim(950, 2050)
        
        # 配置深度子图
        self.ax_depth.set_title('深度', fontsize=12)
        self.ax_depth.set_ylabel('深度 (m)')
        self.ax_depth.set_xlabel('时间')
        self.ax_depth.grid(True, alpha=0.3)
        
        # 初始化绘图线条
        self.motor_lines = []
        motor_colors = ['red', 'blue', 'green', 'orange', 'purple', 'brown']
        for i in range(6):
            line, = self.ax_motors.plot([], [], color=motor_colors[i], 
                                      label=f'电机{i+1}', linewidth=1.5)
            self.motor_lines.append(line)
        self.ax_motors.legend(loc='upper right', bbox_to_anchor=(1, 1))
        
        self.depth_line, = self.ax_depth.plot([], [], 'cyan', linewidth=2, label='深度')
        self.ax_depth.legend()
        
        # 创建画布
        self.canvas = FigureCanvas(self.fig)
        layout.addWidget(self.canvas)
        
        # 紧凑布局
        self.fig.tight_layout()
        
    def add_data_point(self, topic, data):
        """从消息总线添加数据点"""
        current_time = time.time()
        
        with self.lock:
            if topic == "fc_data":
                # 提取电机速度
                motor_speeds = data.get("motor_speeds", [0]*6)
                # 确保我们有恰好6个电机值
                while len(motor_speeds) < 6:
                    motor_speeds.append(0)
                    
                for i, speed in enumerate(motor_speeds[:6]):
                    self.motor_data[i].append(speed)
                
                # 提取深度
                depth = data.get("depth", 0.0)
                self.depth_data.append(depth)
                
                # 添加时间戳 - fc_data驱动时间戳
                self.timestamp_data.append(current_time)
                
    def update_time_window(self):
        """更新数据显示的时间窗口"""
        try:
            window_seconds = self.time_window_spinbox.value()
            max_points = int(window_seconds * 10)  # 假设约10Hz数据率
            
            with self.lock:
                # 更新deque最大长度
                new_motor_data = [deque(list(data)[-max_points:], maxlen=max_points) for data in self.motor_data]
                self.motor_data = new_motor_data
                
                self.depth_data = deque(list(self.depth_data)[-max_points:], maxlen=max_points)
                self.timestamp_data = deque(list(self.timestamp_data)[-max_points:], maxlen=max_points)
                
        except ValueError:
            pass
            
    def clear_data(self):
        """清除所有绘图数据"""
        with self.lock:
            for motor_deque in self.motor_data:
                motor_deque.clear()
            self.depth_data.clear()
            self.timestamp_data.clear()
            
    def update_plots(self, frame):
        """更新图表（由动画调用）"""
        try:
            with self.lock:
                if len(self.timestamp_data) == 0:
                    return
                    
                # 获取当前时间窗口
                current_time = time.time()
                window_seconds = self.time_window_spinbox.value()
                time_cutoff = current_time - window_seconds
                
                # 将时间戳转换为datetime用于绘图
                times = list(self.timestamp_data)
                times_dt = [datetime.fromtimestamp(t) for t in times if t >= time_cutoff]
                
                if len(times_dt) == 0:
                    return
                    
                # 按时间窗口过滤数据
                valid_indices = [i for i, t in enumerate(times) if t >= time_cutoff]
                
                # 更新电机图表
                for i, line in enumerate(self.motor_lines):
                    if i < len(self.motor_data):
                        motor_values = [list(self.motor_data[i])[idx] for idx in valid_indices if idx < len(self.motor_data[i])]
                        if len(motor_values) == len(times_dt):
                            line.set_data(times_dt, motor_values)
                
                # 更新深度图表
                depth_values = [list(self.depth_data)[idx] for idx in valid_indices if idx < len(self.depth_data)]
                if len(depth_values) == len(times_dt):
                    self.depth_line.set_data(times_dt, depth_values)
                
                # 更新轴限制（减少频率以避免递归）
                if times_dt and len(times_dt) > 1 and frame % 5 == 0:  # 只每5帧更新一次
                    # 时间轴
                    for ax in [self.ax_motors, self.ax_depth]:
                        if times_dt[-1] != times_dt[0]:  # 避免相同的时间范围
                            ax.set_xlim(times_dt[0], times_dt[-1])
                        
                        # 格式化时间轴
                        if len(times_dt) > 1:
                            time_span = (times_dt[-1] - times_dt[0]).total_seconds()
                            if time_span < 300:  # 少于5分钟
                                ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M:%S'))
                            else:
                                ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
                            ax.tick_params(axis='x', rotation=45)
                    
                    # 如果启用自动缩放Y轴
                    if self.auto_scale_checkbox.isChecked():
                        if depth_values:
                            depth_min, depth_max = min(depth_values), max(depth_values)
                            margin = (depth_max - depth_min) * 0.1 + 0.1
                            self.ax_depth.set_ylim(depth_min - margin, depth_max + margin)
        
        except Exception as e:
            # 防止递归错误导致应用程序崩溃
            pass
        
        return self.motor_lines + [self.depth_line]
        
    def start_animation(self):
        """启动实时绘图动画"""
        self.animation = FuncAnimation(self.fig, self.update_plots, interval=200, 
                                     blit=False, cache_frame_data=False)
        self.canvas.draw() 