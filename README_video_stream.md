# 视频流功能说明

本文档说明如何在PyQt控制器项目中使用视频流功能。

## 功能概述

视频流功能允许您在PyQt应用中实时接收和显示来自`stream_server.py`的视频流。该功能包括：

- 实时视频流显示
- 帧率和分辨率显示
- 十字瞄准线覆盖
- 信息覆盖层显示
- 截图功能
- 录制状态显示（录制功能框架已就绪）

## 文件说明

### 核心文件

- `video_stream_visualization.py` - 视频流可视化模块
- `stream_server.py` - 视频流发送端服务器
- `test_video_stream.py` - 独立测试脚本

### 集成文件

- `joystick_gui_pyqt.py` - 主应用（已集成视频流标签页）
- `requirements_pyqt.txt` - 依赖列表（已添加OpenCV和requests）

## 安装依赖

```bash
pip install -r requirements_pyqt.txt
```

新增的依赖：
- `opencv-python>=4.5.0` - 用于视频处理
- `requests>=2.25.0` - 用于HTTP通信

## 使用方法

### 1. 启动视频流服务器

在发送端（如树莓派）运行：

```bash
python stream_server.py
```

服务器将在端口5000上提供MJPEG视频流。

### 2. 连接视频流

#### 在主应用中使用

1. 运行主应用：
   ```bash
   python joystick_gui_pyqt.py
   ```

2. 切换到"Video Stream"标签页

3. 输入视频流服务器的IP地址（默认：192.168.1.100）

4. 设置端口（默认：5000）

5. 点击"连接"按钮

#### 独立测试

```bash
python test_video_stream.py
```

### 3. 功能操作

- **显示信息**：勾选"显示信息"复选框可在视频上叠加FPS、分辨率等信息
- **十字瞄准线**：勾选"显示十字线"复选框可显示中心十字线
- **截图**：点击"截图"按钮保存当前帧为JPEG文件
- **录制状态**：点击"开始录制"按钮切换录制状态显示

## 技术实现

### 视频流协议

使用HTTP MJPEG流协议：
- URL格式：`http://IP:PORT/video_feed`
- 数据格式：`multipart/x-mixed-replace; boundary=frame`
- 每帧为JPEG格式

### 架构设计

1. **VideoStreamReceiver（QThread）**
   - 后台线程接收视频流
   - 使用requests库获取HTTP MJPEG流（解决OpenCV HTTP协议限制）
   - 手动解析MJPEG帧边界并用OpenCV解码JPEG数据
   - 通过信号发送帧数据和状态更新

2. **VideoDisplay（QLabel）**
   - 继承自QLabel的视频显示组件
   - 处理帧数据转换（OpenCV → Qt）
   - 添加信息覆盖和十字线

3. **VideoStreamVisualization（QWidget）**
   - 主界面组件
   - 连接控制和状态管理
   - 用户交互处理

### 性能优化

- 帧率限制：接收线程限制在30fps
- 内存管理：及时释放OpenCV资源
- 异步处理：UI和视频处理分离

## 配置选项

### 默认设置

- 服务器IP：192.168.1.100
- 端口：5000
- 显示尺寸：640x480（最小）
- 十字线：开启
- 信息显示：开启

### 可调整参数

在`video_stream_visualization.py`中可调整：

```python
# VideoStreamReceiver.run()
self.response = requests.get(self.stream_url, headers=headers, stream=True, timeout=10)
# timeout=10 - 连接超时时间（秒）

for chunk in self.response.iter_content(chunk_size=1024):
# chunk_size=1024 - 数据块大小，影响接收性能

if len(buffer) > 1024 * 1024:  # 1MB
    buffer = buffer[-512*1024:]  # 保留最后512KB
# 缓冲区管理参数

# VideoDisplay.__init__()
self.setMinimumSize(640, 480)  # 最小显示尺寸

# VideoDisplay.add_crosshair()
line_length = 20  # 十字线长度
color = (0, 255, 255)  # 十字线颜色（BGR格式）
```

## 故障排除

### 常见问题

1. **无法连接到视频流**
   - 检查IP地址和端口是否正确
   - 确认服务器端`stream_server.py`正在运行
   - 检查网络连接
   - 确认防火墙设置允许端口访问

2. **HTTP协议错误（'http' not on whitelist）**
   - 本模块已使用requests库替代OpenCV的VideoCapture
   - 无需额外配置OpenCV的HTTP支持
   - 如仍有问题，请检查requests库是否正确安装

3. **视频显示异常**
   - 确认OpenCV已正确安装（用于图像解码）
   - 检查服务器端视频格式是否为MJPEG
   - 确认requests库版本 >= 2.25.0

4. **性能问题**
   - 降低服务器端帧率设置
   - 检查网络带宽
   - 调整chunk_size参数（在VideoStreamReceiver.run()中）

5. **连接超时**
   - 增加连接超时时间（默认10秒）
   - 检查网络延迟
   - 确认服务器响应正常

### 调试信息

启用详细日志：

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## 扩展功能

### 添加录制功能

当前录制功能为状态显示，可扩展为实际录制：

```python
def toggle_recording(self):
    if not self.video_display.recording:
        # 开始录制
        timestamp = int(time.time())
        filename = f"recording_{timestamp}.avi"
        fourcc = cv2.VideoWriter_fourcc(*'XVID')
        self.video_writer = cv2.VideoWriter(filename, fourcc, 30.0, (width, height))
        self.video_display.recording = True
    else:
        # 停止录制
        if self.video_writer:
            self.video_writer.release()
            self.video_writer = None
        self.video_display.recording = False
```

### 添加多流支持

支持多个视频源：

```python
class MultiStreamVisualization(QWidget):
    def __init__(self):
        super().__init__()
        self.streams = {}  # 存储多个流接收器
        self.setup_multi_stream_ui()
```

## 与主控制器的集成

视频流功能已完全集成到主控制器应用中：

1. 在"Video Stream"标签页中可以独立控制视频流连接
2. 不影响控制器数据传输和消息总线功能
3. 可与其他可视化模块同时使用

## 版权和许可

此视频流模块基于开源协议，可自由修改和分发。 