"""
控制器可视化模块 - PyQt版本
用于显示Xbox360控制器输入的实时可视化
"""

from PyQt5.QtWidgets import QWidget, QVBoxLayout
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPainter, QColor, QPen, QBrush, QFont


class ControllerVisualization(QWidget):
    """控制器输入可视化组件"""
    
    def __init__(self):
        super().__init__()
        self.setMinimumSize(800, 600)
        self.controller_data = {}
        
        # 设置背景色
        self.setStyleSheet("background-color: black;")
        
    def update_visualization(self, controller_data):
        """更新可视化显示"""
        self.controller_data = controller_data
        self.update()  # 触发重绘
    
    def paintEvent(self, event):
        """绘制控制器可视化"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # 绘制背景
        painter.fillRect(self.rect(), QColor(0, 0, 0))
        
        if not self.controller_data:
            # 如果没有控制器数据，显示提示
            painter.setPen(QPen(QColor(255, 255, 255), 2))
            painter.setFont(QFont("Arial", 16))
            painter.drawText(self.rect(), Qt.AlignCenter, "等待控制器数据...")
            return
        
        # 获取窗口尺寸并计算合适的偏移
        width = self.width()
        height = self.height()
        
        # 计算居中的基础偏移
        base_x = width // 2
        base_y = height // 2
        
        # 绘制左摇杆 (左侧)
        left_stick_x = base_x - 250
        left_stick_y = base_y - 80
        self.draw_stick(painter, left_stick_x, left_stick_y, 60, 
                       self.controller_data.get('left_stick_x', 0),
                       self.controller_data.get('left_stick_y', 0),
                       "Left Stick", QColor(255, 0, 0))
        
        # 绘制右摇杆 (右侧，远离ABXY按钮)
        right_stick_x = base_x + 280
        right_stick_y = base_y - 80
        self.draw_stick(painter, right_stick_x, right_stick_y, 60,
                       self.controller_data.get('right_stick_x', 0),
                       self.controller_data.get('right_stick_y', 0),
                       "Right Stick", QColor(0, 0, 255))
        
        # 绘制扳机 (更合理的位置)
        self.draw_trigger(painter, left_stick_x - 50, base_y + 100, 50, 80,
                         self.controller_data.get('left_trigger', -1),
                         "LT", QColor(0, 255, 0))
        
        self.draw_trigger(painter, right_stick_x + 20, base_y + 100, 50, 80,
                         self.controller_data.get('right_trigger', -1),
                         "RT", QColor(0, 255, 0))
        
        # 绘制方向键 (左侧中央)
        dpad_x = base_x - 120
        dpad_y = base_y + 60
        self.draw_dpad(painter, dpad_x, dpad_y, 25,
                      self.controller_data.get('dpad_x', 0),
                      self.controller_data.get('dpad_y', 0))
        
        # 绘制ABXY按钮 (右侧中央)
        self.draw_buttons(painter, base_x + 120, base_y - 20)
        
        # 绘制肩部按钮 (顶部)
        self.draw_shoulder_button(painter, left_stick_x, base_y - 250, 60, 25, 
                                 self.controller_data.get('lb_button', 0), "LB")
        self.draw_shoulder_button(painter, right_stick_x - 60, base_y - 250, 60, 25,
                                 self.controller_data.get('rb_button', 0), "RB")
    
    def draw_stick(self, painter, x, y, radius, stick_x, stick_y, label, dot_color):
        """绘制摇杆"""
        # 绘制外圈
        painter.setPen(QPen(QColor(255, 255, 255), 2))
        painter.setBrush(QBrush(QColor(0, 0, 0, 0)))
        painter.drawEllipse(x - radius, y - radius, radius * 2, radius * 2)
        
        # 绘制标签
        painter.setFont(QFont("Arial", 12))
        painter.drawText(x - 40, y - radius - 20, label)
        
        # 绘制摇杆位置点
        dot_x = x + stick_x * (radius - 10)
        dot_y = y + stick_y * (radius - 10)
        
        painter.setBrush(QBrush(dot_color))
        painter.drawEllipse(int(dot_x - 8), int(dot_y - 8), 16, 16)
    
    def draw_trigger(self, painter, x, y, width, height, trigger_value, label, color):
        """绘制扳机"""
        # 绘制外框
        painter.setPen(QPen(QColor(255, 255, 255), 2))
        painter.setBrush(QBrush(QColor(0, 0, 0, 0)))
        painter.drawRect(x, y, width, height)
        
        # 绘制填充（扳机值从-1到1，转换为0到1）
        fill_value = (trigger_value + 1) / 2
        fill_height = int(height * fill_value)
        
        painter.setBrush(QBrush(color))
        painter.drawRect(x, y + height - fill_height, width, fill_height)
        
        # 绘制标签
        painter.setPen(QPen(QColor(255, 255, 255), 2))
        painter.setFont(QFont("Arial", 12))
        painter.drawText(x + width//2 - 10, y + height + 20, label)
    
    def draw_dpad(self, painter, x, y, size, dpad_x, dpad_y):
        """绘制方向键"""
        # 绘制外框
        painter.setPen(QPen(QColor(255, 255, 255), 2))
        painter.setBrush(QBrush(QColor(0, 0, 0, 0)))
        painter.drawRect(x - size, y - size, size * 2, size * 2)
        
        # 绘制标签
        painter.setFont(QFont("Arial", 12))
        painter.drawText(x - 25, y - size - 10, "D-Pad")
        
        # 绘制方向指示器
        dot_x = x + dpad_x * (size - 5)
        dot_y = y - dpad_y * (size - 5)  # Y轴反转
        
        painter.setBrush(QBrush(QColor(255, 255, 0)))
        painter.drawEllipse(int(dot_x - 6), int(dot_y - 6), 12, 12)
    
    def draw_buttons(self, painter, center_x=420, center_y=150):
        """绘制ABXY按钮"""
        # 按钮位置（相对于中心点）
        buttons = [
            (center_x, center_y + 30, 'A', self.controller_data.get('a_button', 0)),
            (center_x + 30, center_y, 'B', self.controller_data.get('b_button', 0)),
            (center_x - 30, center_y, 'X', self.controller_data.get('x_button', 0)),
            (center_x, center_y - 30, 'Y', self.controller_data.get('y_button', 0))
        ]
        
        for x, y, label, pressed in buttons:
            # 设置颜色（按下时为红色，否则为黑色）
            color = QColor(255, 0, 0) if pressed else QColor(0, 0, 0)
            
            # 绘制按钮
            painter.setPen(QPen(QColor(255, 255, 255), 2))
            painter.setBrush(QBrush(color))
            painter.drawEllipse(x - 15, y - 15, 30, 30)
            
            # 绘制标签
            painter.setPen(QPen(QColor(255, 255, 255), 2))
            painter.setFont(QFont("Arial", 12, QFont.Bold))
            text_rect = painter.fontMetrics().boundingRect(label)
            painter.drawText(x - text_rect.width()//2, y + text_rect.height()//2 - 2, label)
    
    def draw_shoulder_button(self, painter, x, y, width, height, pressed, label):
        """绘制肩部按钮"""
        # 设置颜色（按下时为红色，否则为黑色）
        color = QColor(255, 0, 0) if pressed else QColor(0, 0, 0)
        
        # 绘制按钮
        painter.setPen(QPen(QColor(255, 255, 255), 2))
        painter.setBrush(QBrush(color))
        painter.drawRect(x, y, width, height)
        
        # 绘制标签
        painter.setPen(QPen(QColor(255, 255, 255), 2))
        painter.setFont(QFont("Arial", 12))
        text_rect = painter.fontMetrics().boundingRect(label)
        painter.drawText(x + width//2 - text_rect.width()//2, 
                        y + height//2 + text_rect.height()//2 - 2, label) 