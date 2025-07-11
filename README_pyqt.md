# Xbox 360 Controller GUI - PyQt版本

这是Xbox 360控制器GUI应用程序的PyQt实现版本，从原来的tkinter版本迁移而来。

## 功能特性

- **控制器输入处理**: 实时读取Xbox 360控制器输入
- **TCP数据发送**: 将控制器数据通过TCP发送到指定服务器
- **消息总线接收**: 接收并可视化TCP消息总线数据
- **实时可视化**: 
  - 控制器输入的图形化显示
  - 消息总线topics和消息的树形显示
  - 电机输出和深度数据的实时图表
- **配置管理**: 保存和加载连接设置

## 依赖要求

安装所需的Python包：

```bash
pip install -r requirements_pyqt.txt
```

或手动安装：

```bash
pip install PyQt5>=5.15.0 pygame>=2.0.0 matplotlib>=3.5.0 numpy>=1.20.0
```

## 运行应用

```bash
python joystick_gui_pyqt.py
```

## 主要变化（相对于tkinter版本）

### 技术栈变化
- **GUI框架**: tkinter → PyQt5
- **matplotlib后端**: TkAgg → Qt5Agg
- **线程通信**: tkinter的after() → PyQt的信号槽机制

### 界面改进
- 更现代的GUI外观
- 更好的布局管理
- 改进的分割器和标签页
- 更流畅的实时更新

### 性能优化
- 使用PyQt的信号槽机制实现线程安全的UI更新
- 优化的消息处理和显示
- 改进的内存管理

## 模块结构

- `joystick_gui_pyqt.py` - 主应用程序文件
- `controller_visualization.py` - 控制器可视化模块
- `message_bus_visualization.py` - 消息总线可视化模块
- `plotting_visualization.py` - 实时绘图模块

## 使用说明

### 1. 控制器连接
- 连接Xbox 360控制器到计算机
- 启动应用程序，控制器会自动检测
- 如果检测不到，点击"刷新"按钮

### 2. TCP连接设置
- 在"控制器控制"标签页设置目标IP和端口
- 点击"连接"开始发送控制器数据

### 3. 消息总线
- 在"消息总线"标签页设置消息总线连接
- 可以实时查看接收到的topics和消息

### 4. 实时监控
- "控制器可视化"标签页显示控制器输入状态
- "电机和深度监控"标签页显示实时数据图表

## 配置文件

应用程序会自动保存配置到 `controller_config.json` 文件，包含：
- IP地址和端口设置
- 更新频率
- 死区设置
- 其他用户首选项

## 故障排除

### 控制器检测问题
- 确保控制器已正确连接
- 检查pygame是否正确安装
- 尝试重新插拔控制器

### 连接问题
- 检查网络连接
- 验证目标服务器是否运行
- 检查防火墙设置

### 性能问题
- 降低更新频率
- 关闭不需要的可视化标签页
- 清除历史数据

## 开发说明

### 信号槽机制
PyQt版本使用信号槽机制进行线程间通信：
- `ControllerDataSender.controller_data_updated` - 控制器数据更新
- `MessageBusReceiver.message_received` - 消息总线消息接收
- `ControllerDataSender.error_occurred` - 错误处理

### 自定义绘图
控制器可视化使用PyQt的QPainter进行自定义绘图，提供更好的性能和外观。

### 线程安全
所有数据访问都使用threading.Lock()保护，确保多线程环境下的数据一致性。

## 许可证

与原tkinter版本相同的许可证。 