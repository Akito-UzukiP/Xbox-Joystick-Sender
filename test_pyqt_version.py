#!/usr/bin/env python3
"""
测试PyQt版本的Xbox 360控制器GUI
"""

import sys
import os

def test_imports():
    """测试所有必需的模块导入"""
    print("测试模块导入...")
    
    try:
        import PyQt5
        print("✓ PyQt5 导入成功")
    except ImportError as e:
        print(f"✗ PyQt5 导入失败: {e}")
        return False
    
    try:
        import pygame
        print("✓ pygame 导入成功")
    except ImportError as e:
        print(f"✗ pygame 导入失败: {e}")
        return False
    
    try:
        import matplotlib
        print("✓ matplotlib 导入成功")
    except ImportError as e:
        print(f"✗ matplotlib 导入失败: {e}")
        return False
    
    try:
        import numpy
        print("✓ numpy 导入成功")
    except ImportError as e:
        print(f"✗ numpy 导入失败: {e}")
        return False
    
    return True

def test_application_modules():
    """测试应用程序模块"""
    print("\n测试应用程序模块...")
    
    # 确保模块文件存在
    required_files = [
        'joystick_gui_pyqt.py',
        'controller_visualization.py',
        'message_bus_visualization.py', 
        'plotting_visualization.py'
    ]
    
    for file in required_files:
        if os.path.exists(file):
            print(f"✓ {file} 存在")
        else:
            print(f"✗ {file} 不存在")
            return False
    
    # 尝试导入模块
    try:
        from controller_visualization import ControllerVisualization
        print("✓ controller_visualization 导入成功")
    except ImportError as e:
        print(f"✗ controller_visualization 导入失败: {e}")
        return False
    
    try:
        from message_bus_visualization import MessageBusVisualization
        print("✓ message_bus_visualization 导入成功")
    except ImportError as e:
        print(f"✗ message_bus_visualization 导入失败: {e}")
        return False
    
    try:
        from plotting_visualization import PlottingVisualization
        print("✓ plotting_visualization 导入成功")
    except ImportError as e:
        print(f"✗ plotting_visualization 导入失败: {e}")
        return False
    
    return True

def test_gui_creation():
    """测试GUI创建"""
    print("\n测试GUI创建...")
    
    try:
        from PyQt5.QtWidgets import QApplication
        
        # 如果已有QApplication实例，就不创建新的
        app = QApplication.instance()
        if app is None:
            app = QApplication(sys.argv)
        
        # 导入并创建主窗口
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        from joystick_gui_pyqt import Xbox360ControllerGUI
        
        window = Xbox360ControllerGUI()
        print("✓ 主窗口创建成功")
        
        # 显示窗口（但不进入事件循环）
        window.show()
        print("✓ 窗口显示成功")
        
        # 立即关闭窗口
        window.close()
        print("✓ 窗口关闭成功")
        
        return True
        
    except Exception as e:
        print(f"✗ GUI创建失败: {e}")
        return False

def main():
    """主测试函数"""
    print("Xbox 360控制器GUI PyQt版本测试")
    print("=" * 50)
    
    success = True
    
    # 测试导入
    if not test_imports():
        success = False
    
    # 测试应用程序模块
    if not test_application_modules():
        success = False
    
    # 测试GUI创建
    if not test_gui_creation():
        success = False
    
    print("\n" + "=" * 50)
    if success:
        print("✓ 所有测试通过！PyQt版本准备就绪。")
        print("\n要运行应用程序，请使用:")
        print("python joystick_gui_pyqt.py")
    else:
        print("✗ 某些测试失败。请检查依赖项和文件。")
        print("\n安装依赖项:")
        print("pip install -r requirements_pyqt.txt")
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 