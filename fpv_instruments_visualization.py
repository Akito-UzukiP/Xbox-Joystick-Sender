"""
FPV仪表可视化模块
包含水平仪、罗盘仪表、深度计等FPV风格的飞行仪表
"""

import sys
import math
import time
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, 
                            QLabel, QFrame, QGroupBox)
from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtGui import (QPainter, QColor, QPen, QBrush, QFont, QPolygon, 
                        QLinearGradient, QRadialGradient, QConicalGradient, 
                        QFontMetrics, QPolygonF)
from PyQt5.QtCore import QPointF, QRectF, QPoint
import numpy as np


class AttitudeIndicator(QWidget):
    """姿态仪表 - 显示roll和pitch"""
    
    def __init__(self):
        super().__init__()
        self.setMinimumSize(300, 300)
        self.setStyleSheet("background-color: black; border: 2px solid gray;")
        
        # 姿态数据
        self.roll = 0.0  # 横滚角 (弧度)
        self.pitch = 0.0  # 俯仰角 (弧度)
        
        # 目标值
        self.desired_roll = 0.0
        
    def update_attitude(self, roll, pitch, desired_roll=None):
        """更新姿态数据"""
        self.roll = roll
        self.pitch = pitch
        if desired_roll is not None:
            self.desired_roll = desired_roll
        self.update()
        
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # 获取绘制区域
        rect = self.rect()
        center_x = rect.width() // 2
        center_y = rect.height() // 2
        radius = min(center_x, center_y) - 20
        
        # 绘制背景
        painter.fillRect(rect, QColor(0, 0, 0))
        
        # 保存画家状态
        painter.save()
        
        # 移动到中心并应用横滚旋转
        painter.translate(center_x, center_y)
        painter.rotate(math.degrees(self.roll))
        
        # 绘制天空和地面
        # 计算俯仰角对应的偏移
        pitch_offset = self.pitch * radius * 2  # 放大俯仰角效果
        
        # 天空 (蓝色)
        sky_rect = QRectF(-radius, -radius - pitch_offset, radius * 2, radius + pitch_offset)
        painter.fillRect(sky_rect, QColor(87, 149, 221))
        
        # 地面 (棕色)
        ground_rect = QRectF(-radius, -pitch_offset, radius * 2, radius + pitch_offset)
        painter.fillRect(ground_rect, QColor(139, 69, 19))
        
        # 绘制地平线
        painter.setPen(QPen(QColor(255, 255, 255), 3))
        painter.drawLine(int(-radius), int(-pitch_offset), int(radius), int(-pitch_offset))
        
        # 绘制俯仰角刻度线
        painter.setPen(QPen(QColor(255, 255, 255), 2))
        font = QFont("Arial", 10)
        painter.setFont(font)
        
        # 10度间隔的刻度线
        for angle in range(-90, 91, 10):
            if angle == 0:  # 地平线已经绘制
                continue
            y_pos = -pitch_offset + (angle * radius / 90)
            if abs(y_pos) < radius:
                line_width = 40 if angle % 30 == 0 else 20
                painter.drawLine(int(-line_width//2), int(y_pos), int(line_width//2), int(y_pos))
                
                # 绘制角度标记
                if angle % 30 == 0:
                    painter.drawText(-30, int(y_pos - 5), f"{angle}°")
                    painter.drawText(15, int(y_pos - 5), f"{angle}°")
        
        # 恢复画家状态
        painter.restore()
        
        # 绘制飞机符号（固定在中心）
        painter.setPen(QPen(QColor(255, 255, 0), 4))
        painter.drawLine(center_x - 50, center_y, center_x - 20, center_y)
        painter.drawLine(center_x + 20, center_y, center_x + 50, center_y)
        painter.drawLine(center_x, center_y - 20, center_x, center_y + 20)
        
        # 绘制横滚角刻度
        painter.save()
        painter.translate(center_x, center_y)
        
        # 外圈刻度
        painter.setPen(QPen(QColor(255, 255, 255), 2))
        for angle in range(0, 360, 10):
            if angle <= 60 or angle >= 300:  # 只显示顶部区域
                painter.save()
                painter.rotate(angle)
                line_length = 15 if angle % 30 == 0 else 10
                painter.drawLine(0, int(-radius + 5), 0, int(-radius + 5 + line_length))
                painter.restore()
        
        # 绘制横滚角指示器
        painter.setPen(QPen(QColor(255, 255, 0), 3))
        banker_angle = math.degrees(self.roll)
        painter.save()
        painter.rotate(banker_angle)
        # 绘制三角形指示器
        triangle = QPolygon([
            QPoint(0, int(-radius + 5)),
            QPoint(-8, int(-radius + 20)),
            QPoint(8, int(-radius + 20))
        ])
        painter.setBrush(QBrush(QColor(255, 255, 0)))
        painter.drawPolygon(triangle)
        painter.restore()
        
        # 绘制期望横滚角指示
        if self.desired_roll != 0:
            painter.setPen(QPen(QColor(0, 255, 0), 3))
            desired_angle = math.degrees(self.desired_roll)
            painter.save()
            painter.rotate(desired_angle)
            # 绘制绿色三角形指示器
            desired_triangle = QPolygon([
                QPoint(0, int(-radius + 25)),
                QPoint(-6, int(-radius + 35)),
                QPoint(6, int(-radius + 35))
            ])
            painter.setBrush(QBrush(QColor(0, 255, 0)))
            painter.drawPolygon(desired_triangle)
            painter.restore()
        
        painter.restore()
        
        # 绘制文字信息
        painter.setPen(QPen(QColor(255, 255, 255), 1))
        font = QFont("Arial", 12, QFont.Bold)
        painter.setFont(font)
        roll_text = f"Roll: {math.degrees(self.roll):.1f}°"
        pitch_text = f"Pitch: {math.degrees(self.pitch):.1f}°"
        painter.drawText(10, rect.height() - 40, roll_text)
        painter.drawText(10, rect.height() - 20, pitch_text)


class CompassIndicator(QWidget):
    """罗盘仪表 - 显示航向角"""
    
    def __init__(self):
        super().__init__()
        self.setMinimumSize(300, 300)
        self.setStyleSheet("background-color: black; border: 2px solid gray;")
        
        # 航向数据
        self.yaw = 0.0  # 航向角 (弧度)
        self.desired_yaw = 0.0
        self.gps_navigation_yaw = None  # GPS导航偏航角 (弧度)
        
    def update_heading(self, yaw, desired_yaw=None):
        """更新航向数据"""
        self.yaw = -yaw
        if desired_yaw is not None:
            self.desired_yaw = -desired_yaw
        self.update()
    
    def update_gps_navigation_yaw(self, gps_yaw):
        """更新GPS导航偏航角"""
        self.gps_navigation_yaw = -gps_yaw if gps_yaw is not None else None
        self.update()
        
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # 获取绘制区域
        rect = self.rect()
        center_x = rect.width() // 2
        center_y = rect.height() // 2
        radius = min(center_x, center_y) - 20
        
        # 绘制背景
        painter.fillRect(rect, QColor(0, 0, 0))
        
        # 绘制罗盘圆环
        painter.setPen(QPen(QColor(255, 255, 255), 2))
        painter.drawEllipse(center_x - radius, center_y - radius, radius * 2, radius * 2)
        
        # 绘制方位刻度和标记
        painter.save()
        painter.translate(center_x, center_y)
        
        font = QFont("Arial", 12, QFont.Bold)
        painter.setFont(font)
        
        # 主要方向标记
        directions = ["N", "E", "S", "W"]
        for i, direction in enumerate(directions):
            angle = i * 90
            painter.save()
            painter.rotate(angle - math.degrees(self.yaw))
            
            # 绘制刻度线
            painter.setPen(QPen(QColor(255, 255, 255), 3))
            painter.drawLine(0, int(-radius + 5), 0, int(-radius + 25))
            
            # 绘制方向标记
            if direction == "N":
                painter.setPen(QPen(QColor(255, 0, 0), 2))
            else:
                painter.setPen(QPen(QColor(255, 255, 255), 2))
            
            text_rect = QRectF(-15, int(-radius + 30), 30, 20)
            painter.drawText(text_rect, Qt.AlignCenter, direction)
            painter.restore()
        
        # 绘制度数刻度
        painter.setPen(QPen(QColor(200, 200, 200), 1))
        font_small = QFont("Arial", 8)
        painter.setFont(font_small)
        
        for angle in range(0, 360, 30):
            if angle % 90 != 0:  # 跳过主要方向
                painter.save()
                painter.rotate(angle - math.degrees(self.yaw))
                painter.drawLine(0, int(-radius + 5), 0, int(-radius + 15))
                
                text_rect = QRectF(-15, int(-radius + 20), 30, 15)
                painter.drawText(text_rect, Qt.AlignCenter, str(angle))
                painter.restore()
        
        # 绘制期望航向指示
        if self.desired_yaw != 0:
            painter.setPen(QPen(QColor(0, 255, 0), 4))
            painter.save()
            painter.rotate(math.degrees(self.desired_yaw - self.yaw))
            painter.drawLine(0, int(-radius + 35), 0, int(-radius + 50))
            # 绘制箭头
            painter.drawLine(0, int(-radius + 35), -5, int(-radius + 40))
            painter.drawLine(0, int(-radius + 35), 5, int(-radius + 40))
            painter.restore()
        
        # 绘制GPS导航偏航角指示 (粉色箭头)
        if self.gps_navigation_yaw is not None:
            painter.setPen(QPen(QColor(255, 20, 147), 5))  # 深粉色
            painter.setBrush(QBrush(QColor(255, 20, 147)))
            painter.save()
            painter.rotate(math.degrees(self.gps_navigation_yaw - self.yaw))
            
            # 绘制更粗的指示线
            painter.drawLine(0, int(-radius + 55), 0, int(-radius + 75))
            
            # 绘制三角形箭头
            triangle = QPolygon([
                QPoint(0, int(-radius + 55)),
                QPoint(-8, int(-radius + 65)),
                QPoint(8, int(-radius + 65))
            ])
            painter.drawPolygon(triangle)
            painter.restore()
        
        painter.restore()
        
        # 绘制固定的北方指示器
        painter.setPen(QPen(QColor(255, 0, 0), 4))
        painter.setBrush(QBrush(QColor(255, 0, 0)))
        triangle = QPolygon([
            QPoint(int(center_x), int(center_y - radius + 5)),
            QPoint(int(center_x - 8), int(center_y - radius + 20)),
            QPoint(int(center_x + 8), int(center_y - radius + 20))
        ])
        painter.drawPolygon(triangle)
        
        # 绘制中心点
        painter.setPen(QPen(QColor(255, 255, 255), 2))
        painter.setBrush(QBrush(QColor(255, 255, 255)))
        painter.drawEllipse(center_x - 5, center_y - 5, 10, 10)
        
        # 绘制文字信息
        painter.setPen(QPen(QColor(255, 255, 255), 1))
        font = QFont("Arial", 12, QFont.Bold)
        painter.setFont(font)
        heading_deg = (math.degrees(self.yaw) + 360) % 360
        heading_text = f"Heading: {heading_deg:.1f}°"
        painter.drawText(10, rect.height() - 40, heading_text)
        
        # 绘制GPS导航偏航角信息
        if self.gps_navigation_yaw is not None:
            painter.setPen(QPen(QColor(255, 20, 147), 1))
            gps_yaw_deg = (math.degrees(self.gps_navigation_yaw) + 360) % 360
            gps_text = f"GPS Nav: {gps_yaw_deg:.1f}°"
            painter.drawText(10, rect.height() - 20, gps_text)


class DepthIndicator(QWidget):
    """深度计 - 显示深度信息"""
    
    def __init__(self):
        super().__init__()
        self.setMinimumSize(80, 300)
        self.setStyleSheet("background-color: black; border: 2px solid gray;")
        
        # 深度数据
        self.depth = 0.0  # 当前深度
        self.desired_depth = 0.0  # 期望深度
        self.max_depth = 10.0  # 最大显示深度
        
    def update_depth(self, depth, desired_depth=None):
        """更新深度数据"""
        self.depth = depth
        if desired_depth is not None:
            self.desired_depth = desired_depth
        # 动态调整最大深度显示范围
        max_val = max(abs(self.depth), abs(self.desired_depth), 1.0)
        self.max_depth = max(self.max_depth, max_val * 1.2)
        self.update()
        
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # 获取绘制区域
        rect = self.rect()
        margin = 10
        scale_x = margin
        scale_width = 20
        scale_height = rect.height() - 2 * margin
        
        # 绘制背景
        painter.fillRect(rect, QColor(0, 0, 0))
        
        # 绘制刻度背景
        painter.setPen(QPen(QColor(100, 100, 100), 1))
        painter.drawRect(scale_x, margin, scale_width, scale_height)
        
        # 绘制刻度线和数值
        painter.setPen(QPen(QColor(255, 255, 255), 1))
        font = QFont("Arial", 8)
        painter.setFont(font)
        
        # 计算刻度间隔
        num_ticks = 10
        for i in range(num_ticks + 1):
            depth_val = -self.max_depth + (2 * self.max_depth * i / num_ticks)
            y_pos = margin + (scale_height * i / num_ticks)
            
            # 绘制刻度线
            if i % 2 == 0:  # 主刻度
                painter.drawLine(int(scale_x), int(y_pos), int(scale_x + scale_width), int(y_pos))
                # 绘制数值
                text = f"{depth_val:.1f}"
                painter.drawText(int(scale_x + scale_width + 5), int(y_pos + 5), text)
            else:  # 副刻度
                painter.drawLine(int(scale_x + scale_width//2), int(y_pos), int(scale_x + scale_width), int(y_pos))
        
        # 绘制当前深度指示
        if abs(self.depth) <= self.max_depth:
            depth_ratio = (self.depth + self.max_depth) / (2 * self.max_depth)
            depth_y = margin + scale_height * depth_ratio
            
            painter.setPen(QPen(QColor(255, 255, 0), 3))
            painter.setBrush(QBrush(QColor(255, 255, 0)))
            # 绘制三角形指示器
            triangle = QPolygon([
                QPoint(int(scale_x + scale_width), int(depth_y)),
                QPoint(int(scale_x + scale_width + 10), int(depth_y - 5)),
                QPoint(int(scale_x + scale_width + 10), int(depth_y + 5))
            ])
            painter.drawPolygon(triangle)
        
        # 绘制期望深度指示
        if abs(self.desired_depth) <= self.max_depth:
            desired_ratio = (self.desired_depth + self.max_depth) / (2 * self.max_depth)
            desired_y = margin + scale_height * desired_ratio
            
            painter.setPen(QPen(QColor(0, 255, 0), 3))
            painter.setBrush(QBrush(QColor(0, 255, 0)))
            # 绘制方形指示器
            rect_indicator = QRectF(scale_x + scale_width + 2, desired_y - 3, 6, 6)
            painter.drawRect(rect_indicator)
        
        # 绘制零线
        zero_ratio = (0 + self.max_depth) / (2 * self.max_depth)
        zero_y = margin + scale_height * zero_ratio
        painter.setPen(QPen(QColor(255, 0, 0), 2))
        painter.drawLine(int(scale_x), int(zero_y), int(scale_x + scale_width), int(zero_y))
        
        # 绘制文字信息
        painter.setPen(QPen(QColor(255, 255, 255), 1))
        font = QFont("Arial", 10, QFont.Bold)
        painter.setFont(font)
        depth_text = f"Depth\n{self.depth:.2f}m"
        painter.drawText(5, rect.height() - 40, depth_text)


class MotorSpeedIndicator(QWidget):
    """电机转速指示器 - 显示六个电机的PWM值"""
    
    def __init__(self):
        super().__init__()
        self.setMinimumSize(200, 300)
        self.setStyleSheet("background-color: black; border: 2px solid gray;")
        
        # 电机PWM数据 (6个电机)
        self.motor_speeds = [1500, 1500, 1500, 1500, 1500, 1500]  # 1000 to 2000 PWM values
        
    def update_motor_speeds(self, speeds):
        """更新电机PWM数据"""
        if len(speeds) >= 6:
            self.motor_speeds = speeds[:6]
        else:
            self.motor_speeds = speeds + [1500] * (6 - len(speeds))
        self.update()
        
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # 获取绘制区域
        rect = self.rect()
        margin = 20
        
        # 绘制背景
        painter.fillRect(rect, QColor(0, 0, 0))
        
        # 计算每个电机指示器的大小和位置
        indicator_width = 25
        indicator_height = rect.height() - 2 * margin - 40  # 留出底部空间显示数值
        
        # 电机排列: 2 1, 6 5, 4 3 (从上到下，从左到右)
        motor_layout = [
            [1, 0],  # 第一行: 电机2, 电机1
            [5, 4],  # 第二行: 电机6, 电机5  
            [3, 2]   # 第三行: 电机4, 电机3
        ]
        
        row_height = indicator_height // 3
        col_width = (rect.width() - 2 * margin) // 2
        
        painter.setPen(QPen(QColor(255, 255, 255), 1))
        font = QFont("Arial", 8)
        painter.setFont(font)
        
        for row_idx, motor_row in enumerate(motor_layout):
            for col_idx, motor_idx in enumerate(motor_row):
                # 计算位置
                x = margin + col_idx * col_width + (col_width - indicator_width) // 2
                y = margin + row_idx * row_height
                
                # 获取电机PWM值 (1000 to 2000)
                pwm_value = self.motor_speeds[motor_idx]
                
                # 绘制外框
                painter.setPen(QPen(QColor(100, 100, 100), 2))
                painter.drawRect(x, y, indicator_width, row_height - 10)
                
                # 计算填充高度 (1000=0%, 1500=50%, 2000=100%)
                if pwm_value < 1000:
                    pwm_value = 1000
                elif pwm_value > 2000:
                    pwm_value = 2000
                    
                pwm_ratio = (pwm_value - 1000) / 1000.0  # 0 to 1 (1000-2000 mapped to 0-1)
                fill_height = int((row_height - 10) * pwm_ratio)
                
                # 确定颜色基于PWM值
                if pwm_value < 1100:
                    color = QColor(50, 50, 50)  # 极低：深灰色
                elif pwm_value < 1400:
                    color = QColor(0, 100, 255)  # 低速：蓝色
                elif pwm_value < 1600:
                    color = QColor(0, 255, 0)  # 中速：绿色
                elif pwm_value < 1800:
                    color = QColor(255, 255, 0)  # 高速：黄色
                else:
                    color = QColor(255, 0, 0)  # 极高：红色
                
                # 从底部向上填充
                fill_y = y + (row_height - 10) - fill_height
                painter.fillRect(x + 1, fill_y, indicator_width - 2, fill_height, color)
                
                # 绘制电机编号和PWM数值
                painter.setPen(QPen(QColor(255, 255, 255), 1))
                motor_label = f"M{motor_idx + 1}"
                pwm_text = f"{pwm_value:.0f}"
                
                # 根据列位置决定文字显示位置
                if col_idx == 0:  # 左列，文字显示在左边
                    painter.drawText(x - 25, y + (row_height - 10) // 2, motor_label)
                    painter.drawText(x - 35, y + (row_height - 10) // 2 + 15, pwm_text)
                else:  # 右列，文字显示在右边
                    painter.drawText(x + indicator_width + 5, y + (row_height - 10) // 2, motor_label)
                    painter.drawText(x + indicator_width + 5, y + (row_height - 10) // 2 + 15, pwm_text)


class FPVInstrumentsVisualization(QWidget):
    """FPV仪表可视化主界面"""
    
    def __init__(self):
        super().__init__()
        self.setup_ui()
        
        # 数据存储
        self.imu_data = {}
        self.fc_data = {}  # 添加fc_data存储
        self.desired_values = {
            'roll': 0.0,
            'yaw': 0.0,
            'depth': 0.0
        }
        
        # MUR状态数据
        self.armed = False
        self.depth_hold = False
        
        # 设置更新定时器
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_displays)
        self.update_timer.start(50)  # 20Hz更新
        
    def setup_ui(self):
        """设置用户界面"""
        layout = QGridLayout(self)
        
        # 姿态仪表
        attitude_group = QGroupBox("Attitude Indicator (Artificial Horizon)")
        attitude_layout = QVBoxLayout(attitude_group)
        self.attitude_indicator = AttitudeIndicator()
        attitude_layout.addWidget(self.attitude_indicator)
        layout.addWidget(attitude_group, 0, 0)
        
        # 罗盘仪表
        compass_group = QGroupBox("Compass Indicator")
        compass_layout = QVBoxLayout(compass_group)
        self.compass_indicator = CompassIndicator()
        compass_layout.addWidget(self.compass_indicator)
        layout.addWidget(compass_group, 0, 1)
        
        # 深度计
        depth_group = QGroupBox("Depth Indicator")
        depth_layout = QVBoxLayout(depth_group)
        self.depth_indicator = DepthIndicator()
        depth_layout.addWidget(self.depth_indicator)
        layout.addWidget(depth_group, 0, 2)
        
        # 底部区域：信息面板和电机转速指示器并列
        # 信息面板
        info_group = QGroupBox("MUR Information")
        info_layout = QVBoxLayout(info_group)
        self.info_label = QLabel("Waiting for MUR data...")
        self.info_label.setStyleSheet("color: white; background-color: black; padding: 10px;")
        self.info_label.setAlignment(Qt.AlignTop)
        info_layout.addWidget(self.info_label)
        layout.addWidget(info_group, 1, 0, 1, 2)  # 占2列
        
        # 电机转速指示器
        motor_group = QGroupBox("Motor Speed Indicators")
        motor_layout = QVBoxLayout(motor_group)
        self.motor_speed_indicator = MotorSpeedIndicator()
        motor_layout.addWidget(self.motor_speed_indicator)
        layout.addWidget(motor_group, 1, 2)  # 占1列
        
    def update_imu_data(self, data):
        """更新IMU数据"""
        self.imu_data = data
        
    def update_fc_data(self, data):
        """更新FC数据"""
        self.fc_data = data
        
    def update_desired_roll(self, value):
        """更新期望横滚角"""
        self.desired_values['roll'] = value
        
    def update_desired_yaw(self, value):
        """更新期望航向角"""
        self.desired_values['yaw'] = value
        
    def update_desired_depth(self, value):
        """更新期望深度"""
        self.desired_values['depth'] = value
        
    def update_armed_status(self, armed):
        """更新Armed状态"""
        self.armed = armed
        
    def update_depth_hold_status(self, depth_hold):
        """更新Depth Hold状态"""
        self.depth_hold = depth_hold
        
    def update_all_params(self, params):
        """更新所有参数"""
        if 'armed' in params:
            self.armed = params['armed']
        if 'depth_hold' in params:
            self.depth_hold = params['depth_hold']
    
    def update_gps_navigation_yaw(self, gps_yaw):
        """更新GPS导航偏航角"""
        if hasattr(self, 'compass_indicator'):
            self.compass_indicator.update_gps_navigation_yaw(gps_yaw)
        
    def update_displays(self):
        """更新显示"""
        # 优先使用FC数据中的深度信息
        depth = 0.0
        if self.fc_data and 'depth' in self.fc_data:
            depth = self.fc_data.get('depth', 0.0)
        elif self.imu_data:
            # 如果没有FC深度数据，从IMU加速度推算
            az = self.imu_data.get('az', 0.0)
            depth = (az - 9.8) / 9.8  # 标准化深度
        
        # 更新深度计
        self.depth_indicator.update_depth(depth, self.desired_values['depth'])
        
        if self.imu_data:
            # 更新姿态仪表 - 确保数值不为None
            roll = self.imu_data.get('roll', 0.0)
            pitch = self.imu_data.get('pitch', 0.0)
            roll = 0.0 if roll is None else float(roll)
            pitch = 0.0 if pitch is None else float(pitch)
            self.attitude_indicator.update_attitude(roll, pitch, self.desired_values['roll'])
            
            # 更新罗盘 - 确保数值不为None
            yaw = self.imu_data.get('yaw', 0.0)
            yaw = 0.0 if yaw is None else float(yaw)
            self.compass_indicator.update_heading(yaw, self.desired_values['yaw'])
            
            # 更新信息面板
            armed_status = "✓ ARMED" if self.armed else "✗ DISARMED"
            depth_hold_status = "✓ DEPTH HOLD" if self.depth_hold else "✗ MANUAL DEPTH"
            
            # 确保所有数值都不为None
            ax = self.imu_data.get('ax', 0.0)
            ay = self.imu_data.get('ay', 0.0) 
            az = self.imu_data.get('az', 0.0)
            ax = 0.0 if ax is None else float(ax)
            ay = 0.0 if ay is None else float(ay)
            az = 0.0 if az is None else float(az)
            
            # 确保desired_values也不为None
            desired_roll = self.desired_values.get('roll', 0.0)
            desired_yaw = self.desired_values.get('yaw', 0.0)
            desired_depth = self.desired_values.get('depth', 0.0)
            desired_roll = 0.0 if desired_roll is None else float(desired_roll)
            desired_yaw = 0.0 if desired_yaw is None else float(desired_yaw)
            desired_depth = 0.0 if desired_depth is None else float(desired_depth)
            
            info_text = f"""MUR System Status:
{armed_status}
{depth_hold_status}

IMU Data:
Roll: {math.degrees(roll):.2f}° (Target: {math.degrees(desired_roll):.2f}°)
Pitch: {math.degrees(pitch):.2f}°
Yaw: {math.degrees(yaw):.2f}° (Target: {math.degrees(desired_yaw):.2f}°)
Acceleration: X={ax:.2f} Y={ay:.2f} Z={az:.2f}
Depth: {depth:.2f}m (Target: {desired_depth:.2f}m)
Timestamp: {self.imu_data.get('utc_timestamp', 'N/A')}"""
            self.info_label.setText(info_text)
            
        # 处理FC数据中的电机转速
        if self.fc_data:
            # 更新电机转速（从fc_data获取）
            motor_speeds = self.fc_data.get('motor_speeds', [1500, 1500, 1500, 1500, 1500, 1500])
            self.motor_speed_indicator.update_motor_speeds(motor_speeds)
        elif self.imu_data:
            # 如果没有FC数据，尝试从IMU数据获取电机转速
            motor_speeds = self.imu_data.get('motor_speeds', [1500, 1500, 1500, 1500, 1500, 1500])
            self.motor_speed_indicator.update_motor_speeds(motor_speeds) 