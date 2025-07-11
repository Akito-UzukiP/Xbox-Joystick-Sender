#!/usr/bin/env python3
"""
演示PyQt版本界面布局修复的脚本
这个脚本会启动应用程序并显示修复后的界面
"""

import sys
import os
import time
from PyQt5.QtWidgets import QApplication, QMessageBox
from PyQt5.QtCore import QTimer

def main():
    app = QApplication(sys.argv)
    
    try:
        # 导入主应用程序
        from joystick_gui_pyqt import Xbox360ControllerGUI
        
        # 创建主窗口
        window = Xbox360ControllerGUI()
        window.show()
        
        # 显示欢迎信息
        msg = QMessageBox()
        msg.setWindowTitle("界面布局修复演示")
        msg.setText("""
界面布局已修复！

修复内容：
1. 控制器可视化：重新布局各控件位置，右摇杆不再与ABXY按钮重合
2. 控制器控制：状态信息紧凑布局，日志区域占据主要空间
3. 消息总线：连接设置紧凑化，Topics和消息显示区域更大

请查看各个标签页的改进效果！
        """)
        msg.setStandardButtons(QMessageBox.Ok)
        msg.exec_()
        
        # 运行应用程序
        sys.exit(app.exec_())
        
    except ImportError as e:
        error_msg = QMessageBox()
        error_msg.setWindowTitle("导入错误")
        error_msg.setText(f"无法导入应用程序模块：{e}")
        error_msg.setStandardButtons(QMessageBox.Ok)
        error_msg.exec_()
        sys.exit(1)
    except Exception as e:
        error_msg = QMessageBox()
        error_msg.setWindowTitle("运行错误")
        error_msg.setText(f"运行时错误：{e}")
        error_msg.setStandardButtons(QMessageBox.Ok)
        error_msg.exec_()
        sys.exit(1)

if __name__ == "__main__":
    main() 