"""
Video Stream Visualization Module
使用ffplay播放RTSP流，并可选择使用ffmpeg进行录制
"""

import subprocess
import threading
import time
import os
import sys
import traceback

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, 
                           QLabel, QLineEdit, QPushButton, 
                           QGroupBox, QTextEdit, QMessageBox,
                           QCheckBox, QFileDialog)
from PyQt5.QtCore import QTimer, pyqtSignal, Qt
from PyQt5.QtGui import QFont


class VideoStreamVisualization(QWidget):
    """Video stream visualization using ffplay, with optional recording via ffmpeg"""
    
    connection_status_changed = pyqtSignal(bool)
    log_message_signal = pyqtSignal(str)  # 线程安全的日志信号
    process_ended_signal = pyqtSignal()  # 进程结束信号
    
    def __init__(self, config=None):
        super().__init__()
        self.config = config or {}
        
        # FFplay and FFmpeg processes
        self.ffplay_process = None
        self.ffmpeg_process = None
        self.is_connected = False
        self.is_closing = False  # 标识是否正在关闭
        
        # 线程锁
        self._process_lock = threading.Lock()
        self._monitor_thread = None
        
        # Default RTSP URL
        self.default_rtsp_url = "rtsp://10.24.20.165:8554/cam"
        
        # Setup UI
        self.setup_ui()
        
        # 连接信号
        self.log_message_signal.connect(self._handle_log_message)
        self.process_ended_signal.connect(self._handle_process_ended)
        
        # Status update timer
        self.status_timer = QTimer()
        self.status_timer.timeout.connect(self.update_status)
        self.status_timer.start(1000)  # Update every second
        
    def setup_ui(self):
        """Setup user interface"""
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        # Connection group
        connection_group = QGroupBox("视频流连接")
        connection_layout = QVBoxLayout()
        
        # RTSP URL input
        url_layout = QHBoxLayout()
        url_layout.addWidget(QLabel("RTSP URL:"))
        
        self.url_input = QLineEdit()
        self.url_input.setText(self.config.get('rtsp_url', self.default_rtsp_url))
        self.url_input.setPlaceholderText("rtsp://ip:port/path")
        url_layout.addWidget(self.url_input)
        
        connection_layout.addLayout(url_layout)
        
        # Control buttons
        button_layout = QHBoxLayout()
        
        self.connect_btn = QPushButton("连接视频流")
        self.connect_btn.clicked.connect(self.connect_stream)
        button_layout.addWidget(self.connect_btn)
        
        self.disconnect_btn = QPushButton("断开连接")
        self.disconnect_btn.clicked.connect(self.disconnect_stream)
        self.disconnect_btn.setEnabled(False)
        button_layout.addWidget(self.disconnect_btn)
        
        connection_layout.addLayout(button_layout)
        connection_group.setLayout(connection_layout)
        layout.addWidget(connection_group)
        
        # Status group
        status_group = QGroupBox("状态信息")
        status_layout = QVBoxLayout()
        
        self.status_label = QLabel("未连接")
        self.status_label.setStyleSheet("QLabel { color: #ff4444; font-weight: bold; }")
        status_layout.addWidget(self.status_label)
        
        # Info text
        self.info_text = QTextEdit()
        self.info_text.setMaximumHeight(150)
        self.info_text.setReadOnly(True)
        self.info_text.setFont(QFont("Consolas", 9))
        status_layout.addWidget(self.info_text)
        
        status_group.setLayout(status_layout)
        layout.addWidget(status_group)
        
        # Recording group
        recording_group = QGroupBox("录制设置")
        recording_layout = QVBoxLayout()
        
        self.record_checkbox = QCheckBox("启用录制 (需要ffmpeg)")
        self.record_checkbox.stateChanged.connect(self.toggle_record_options)
        recording_layout.addWidget(self.record_checkbox)
        
        # Output file path
        file_layout = QHBoxLayout()
        file_layout.addWidget(QLabel("保存路径:"))
        self.output_file_input = QLineEdit()
        self.output_file_input.setPlaceholderText("例如: C:/videos/recording.mp4")
        file_layout.addWidget(self.output_file_input)
        
        self.browse_btn = QPushButton("浏览...")
        self.browse_btn.clicked.connect(self.browse_output_file)
        file_layout.addWidget(self.browse_btn)
        
        recording_layout.addLayout(file_layout)
        recording_group.setLayout(recording_layout)
        layout.addWidget(recording_group)
        
        # Initially disable recording options
        self.toggle_record_options(self.record_checkbox.checkState())
        
        # FFplay parameters info
        params_group = QGroupBox("FFplay/FFmpeg 参数说明")
        params_layout = QVBoxLayout()
        
        params_info = QLabel(
            "播放参数 (ffplay):\n"
            "• -fflags nobuffer: 禁用缓冲以减少延迟\n"
            "• -flags low_delay: 启用低延迟模式\n"
            "• -framedrop: 允许丢帧以保持实时性\n"
            "• -rtsp_transport tcp: 使用TCP传输RTSP\n\n"
            "录制参数 (ffmpeg -c copy):\n"
            "• -c copy: 直接复制流，不重新编码，性能高\n"
            "• -map 0: 映射所有流 (视频、音频等)\n"
            "• -f tee: 使用tee muxer将输出分割到文件和ffplay\n\n"
            "注意: 需要系统安装ffmpeg和ffplay"
        )
        params_info.setWordWrap(True)
        params_info.setStyleSheet("QLabel { color: #666; font-size: 11px; }")
        params_layout.addWidget(params_info)
        
        params_group.setLayout(params_layout)
        layout.addWidget(params_group)
        
        layout.addStretch()
        
    def toggle_record_options(self, state):
        """根据复选框状态启用/禁用录制选项"""
        is_enabled = (state == Qt.Checked)
        self.output_file_input.setEnabled(is_enabled)
        self.browse_btn.setEnabled(is_enabled)

    def browse_output_file(self):
        """打开文件对话框选择保存路径"""
        # 建议一个文件名
        default_filename = f"record_{time.strftime('%Y%m%d_%H%M%S')}.mp4"
        
        filePath, _ = QFileDialog.getSaveFileName(self, "选择保存路径", default_filename, "Video Files (*.mp4 *.ts *.avi *.mkv)")
        if filePath:
            self.output_file_input.setText(filePath)
            
    def connect_stream(self):
        """连接视频流，并根据选项进行录制"""
        try:
            rtsp_url = self.url_input.text().strip()
            
            if not rtsp_url:
                QMessageBox.warning(self, "错误", "请输入RTSP URL")
                return
                
            with self._process_lock:
                if (self.ffplay_process and self.ffplay_process.poll() is None) or \
                   (self.ffmpeg_process and self.ffmpeg_process.poll() is None):
                    QMessageBox.warning(self, "警告", "视频流已在播放或录制中")
                    return

            is_recording = self.record_checkbox.isChecked()

            if is_recording:
                self._start_recording_and_playback(rtsp_url)
            else:
                self._start_playback_only(rtsp_url)
                
        except FileNotFoundError as e:
            self.log_message(f"错误: 未找到所需程序: {e.filename}")
            QMessageBox.critical(self, "错误", f"未找到所需程序: {e.filename}，请确保已安装ffmpeg并将其添加到系统PATH中")
            self._reset_ui_state()
        except Exception as e:
            self.log_message(f"错误: 启动流失败: {e}")
            QMessageBox.critical(self, "错误", f"启动流失败: {e}")
            self._reset_ui_state()
            
    def _start_playback_only(self, rtsp_url):
        """仅启动播放"""
        if not self.check_ffplay_available():
            QMessageBox.critical(self, "错误", 
                               "未找到ffplay程序，请确保已安装ffmpeg并添加到系统PATH中")
            return
            
        self.log_message(f"正在连接到: {rtsp_url} (仅播放)")
        
        ffplay_cmd = [
            "ffplay", "-fflags", "nobuffer", "-flags", "low_delay", 
            "-framedrop", "-rtsp_transport", "tcp", rtsp_url
        ]
        
        self.log_message(f"执行命令: {' '.join(ffplay_cmd)}")
        
        with self._process_lock:
            self.ffplay_process = subprocess.Popen(
                ffplay_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
            )
            self.is_connected = True
        
        self._post_connection_setup()

    def _start_recording_and_playback(self, rtsp_url):
        """启动录制和播放"""
        output_file = self.output_file_input.text().strip()
        if not output_file:
            QMessageBox.warning(self, "错误", "请输入录制文件保存路径")
            return

        if not self.check_ffmpeg_available() or not self.check_ffplay_available():
            QMessageBox.critical(self, "错误", 
                               "需要ffmpeg和ffplay才能进行录制和播放。请确保它们都已安装并添加到系统PATH中。")
            return

        self.log_message(f"准备录制到: {output_file}")
        
        ffmpeg_cmd = [
            "ffmpeg", "-i", rtsp_url, "-c", "copy", "-map", "0",
            "-f", "tee", f"\"{output_file}|[f=nut]pipe:1\""
        ]
        
        ffplay_cmd = ["ffplay", "-i", "pipe:0", "-fflags", "nobuffer", "-flags", "low_delay", "-framedrop"]
        
        self.log_message(f"执行FFmpeg命令: {' '.join(ffmpeg_cmd)}")
        self.log_message(f"执行FFplay命令: {' '.join(ffplay_cmd)}")

        with self._process_lock:
            # shell=True is used here to correctly handle the quoted tee argument, especially on Windows
            self.ffmpeg_process = subprocess.Popen(
                ' '.join(ffmpeg_cmd),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0,
                shell=True
            )
            
            self.ffplay_process = subprocess.Popen(
                ffplay_cmd,
                stdin=self.ffmpeg_process.stdout,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
            )
            self.is_connected = True
            
        self._post_connection_setup()
        
    def _post_connection_setup(self):
        """连接成功后的UI更新和监控启动"""
        # Update UI state
        self.connect_btn.setEnabled(False)
        self.disconnect_btn.setEnabled(True)
        self.url_input.setEnabled(False)
        self.record_checkbox.setEnabled(False)
        
        self.log_message("流处理进程已启动")
        self.connection_status_changed.emit(True)
        
        # Start monitoring thread
        self._monitor_thread = threading.Thread(target=self.monitor_stream_process, daemon=True)
        self._monitor_thread.start()

    def disconnect_stream(self):
        """断开视频流"""
        try:
            self.log_message("正在断开连接...")
            
            with self._process_lock:
                # 终止 ffmpeg 进程 (如果存在)
                if self.ffmpeg_process:
                    self.log_message("正在终止ffmpeg进程...")
                    self._terminate_process(self.ffmpeg_process, "ffmpeg")
                    self.ffmpeg_process = None
            
                # 终止 ffplay 进程
                if self.ffplay_process:
                    self.log_message("正在终止ffplay进程...")
                    self._terminate_process(self.ffplay_process, "ffplay")
                    self.ffplay_process = None
                        
                self.is_connected = False
                
            # Reset UI state
            self._reset_ui_state()
            self.log_message("连接已断开")
            
            # 确保信号在主线程中发出
            if not self.is_closing:
                self.connection_status_changed.emit(False)
                                       
        except Exception as e:
            self.log_message(f"断开连接时出错: {e}")
            self._reset_ui_state()
            
    def _terminate_process(self, process, name="进程"):
        """辅助函数，用于优雅地终止进程"""
        try:
            if process.poll() is None:
                # 在Windows上，对于shell=True的进程，需要终止整个进程树
                if sys.platform == "win32" and name == "ffmpeg": # ffmpeg was started with shell=True
                    subprocess.run(f"taskkill /F /T /PID {process.pid}", check=True, capture_output=True)
                    self.log_message(f"{name} 进程树已终止")
                else:
                    process.terminate() # 尝试正常终止
                
                try:
                    process.wait(timeout=3)
                    self.log_message(f"{name} 进程已正常终止")
                except subprocess.TimeoutExpired:
                    self.log_message(f"强制终止 {name} 进程...")
                    process.kill()
                    try:
                        process.wait(timeout=2)
                        self.log_message(f"{name} 进程已强制终止")
                    except subprocess.TimeoutExpired:
                        self.log_message(f"警告: {name} 进程可能未完全终止")
            else:
                self.log_message(f"{name} 进程已经结束")
        except Exception as e:
            self.log_message(f"终止 {name} 进程时出错: {e}")
            
    def _reset_ui_state(self):
        """重置UI状态"""
        try:
            self.connect_btn.setEnabled(True)
            self.disconnect_btn.setEnabled(False)
            self.url_input.setEnabled(True)
            self.record_checkbox.setEnabled(True)
        except Exception as e:
            self.log_message(f"重置UI状态时出错: {e}")
            

            
    def check_ffplay_available(self):
        """检查ffplay是否可用"""
        try:
            result = subprocess.run(
                ["ffplay", "-version"], 
                capture_output=True, 
                text=True, 
                timeout=5,
                creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
            )
            return result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired, Exception) as e:
            self.log_message(f"检查ffplay可用性时出错: {e}")
            return False

    def check_ffmpeg_available(self):
        """检查ffmpeg是否可用"""
        try:
            result = subprocess.run(
                ["ffmpeg", "-version"], 
                capture_output=True, 
                text=True, 
                timeout=5,
                creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
            )
            return result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired, Exception) as e:
            self.log_message(f"检查ffmpeg可用性时出错: {e}")
            return False
            
    def monitor_stream_process(self):
        """监控流进程状态 (ffmpeg或ffplay)"""
        try:
            self.log_message("开始监控流进程...")
            
            with self._process_lock:
                # 录制时监控ffmpeg，仅播放时监控ffplay
                process = self.ffmpeg_process or self.ffplay_process
                
            if not process:
                self.log_message("监控线程: 没有有效的进程对象")
                return
                
            try:
                # 等待主进程结束
                # 对于ffmpeg+ffplay组合，如果用户关闭ffplay窗口，ffmpeg会收到broken pipe并退出
                stdout, stderr = process.communicate()
                
                # Process has ended
                return_code = process.returncode
                
                log_prefix = "FFmpeg" if self.ffmpeg_process else "FFplay"
                self.log_message(f"{log_prefix}进程结束，返回码: {return_code}")
                
                if return_code != 0 and not self.is_closing:
                    try:
                        error_msg = stderr.decode('utf-8', errors='ignore') if stderr else "未知错误"
                        if error_msg.strip():
                            # 只记录前几行错误信息，避免日志过长
                            error_lines = error_msg.strip().split('\n')
                            if len(error_lines) > 10:
                                error_msg = '\n'.join(error_lines[:10]) + '\n...(更多错误信息已省略)'
                            self.log_message(f"错误信息: {error_msg}")
                        else:
                            self.log_message(f"{log_prefix}异常退出，无详细错误信息")
                    except Exception as decode_error:
                        self.log_message(f"解析错误信息时出错: {decode_error}")
                else:
                    self.log_message(f"{log_prefix}进程正常退出")
                    
            except Exception as comm_error:
                self.log_message(f"等待进程结束时出错: {comm_error}")
                
        except Exception as e:
            self.log_message(f"监控进程时出现未预期错误: {e}")
            traceback.print_exc()
        finally:
            try:
                # Reset connection status in main thread
                if not self.is_closing:
                    with self._process_lock:
                        if self.is_connected:
                            self.is_connected = False
                            
                    # 使用信号确保在主线程中执行UI更新
                    self.process_ended_signal.emit()
                    
            except Exception as e:
                self.log_message(f"清理监控线程时出错: {e}")
                
    def _handle_process_ended(self):
        """处理进程结束后的UI更新（在主线程中执行）"""
        try:
            if not self.is_closing:
                self._reset_ui_state()
                self.connection_status_changed.emit(False)
                self.log_message("进程监控结束，连接状态已重置")
        except Exception as e:
            self.log_message(f"处理进程结束时出错: {e}")
                
    def update_status(self):
        """更新状态显示"""
        try:
            if self.is_closing:
                return
                
            with self._process_lock:
                process = self.ffmpeg_process or self.ffplay_process
                connected = self.is_connected
                
            if connected and process:
                # Check if process is still running
                try:
                    if process.poll() is None:
                        status_text = "已连接 - 正在录制和播放" if self.ffmpeg_process else "已连接 - FFplay运行中"
                        self.status_label.setText(status_text)
                        self.status_label.setStyleSheet("QLabel { color: #44ff44; font-weight: bold; }")
                    else:
                        # Process ended
                        self.status_label.setText("连接已断开")
                        self.status_label.setStyleSheet("QLabel { color: #ff4444; font-weight: bold; }")
                        if connected and not self.is_closing:
                            # 延迟调用disconnect_stream，避免在状态更新中直接调用
                            QTimer.singleShot(100, self.disconnect_stream)
                except Exception as e:
                    self.log_message(f"检查进程状态时出错: {e}")
            else:
                self.status_label.setText("未连接")
                self.status_label.setStyleSheet("QLabel { color: #ff4444; font-weight: bold; }")
                
        except Exception as e:
            self.log_message(f"更新状态时出错: {e}")
             
    def log_message(self, message):
        """记录日志消息（线程安全）"""
        try:
            if not self.is_closing:
                self.log_message_signal.emit(message)
        except Exception as e:
            print(f"发射日志信号时出错: {e}")
            
    def _handle_log_message(self, message):
        """处理日志消息（在主线程中执行）"""
        try:
            if self.is_closing:
                return
                
            timestamp = time.strftime("%H:%M:%S")
            log_entry = f"[{timestamp}] {message}"
            
            # Add to info text (keep last 50 lines)
            current_text = self.info_text.toPlainText()
            lines = current_text.split('\n') if current_text else []
            lines.append(log_entry)
            
            if len(lines) > 50:
                lines = lines[-50:]
                
            self.info_text.setPlainText('\n'.join(lines))
            
            # Scroll to bottom
            try:
                scrollbar = self.info_text.verticalScrollBar()
                if scrollbar:
                    scrollbar.setValue(scrollbar.maximum())
            except Exception as scroll_error:
                print(f"滚动日志时出错: {scroll_error}")
                
        except Exception as e:
            print(f"处理日志消息时出错: {e}")
        
    def get_config(self):
        """获取当前配置"""
        try:
            return {
                'rtsp_url': self.url_input.text(),
                'record_enabled': self.record_checkbox.isChecked(),
                'output_file': self.output_file_input.text()
            }
        except Exception as e:
            self.log_message(f"获取配置时出错: {e}")
            return {}
         
    def closeEvent(self, event):
        """窗口关闭事件"""
        try:
            self.is_closing = True
            self.log_message("正在关闭应用程序...")
            
            # 停止定时器
            if hasattr(self, 'status_timer') and self.status_timer:
                self.status_timer.stop()
                
            # 断开连接
            if self.is_connected:
                self.disconnect_stream()
                
            # 等待监控线程结束
            if self._monitor_thread and self._monitor_thread.is_alive():
                self.log_message("等待监控线程结束...")
                self._monitor_thread.join(timeout=2)
                if self._monitor_thread.is_alive():
                    self.log_message("警告: 监控线程未在超时时间内结束")
                    
            self.log_message("应用程序关闭完成")
            event.accept()
            
        except Exception as e:
            print(f"关闭应用程序时出错: {e}")
            traceback.print_exc()
            event.accept()  # 即使出错也要关闭


def main():
    """测试函数"""
    import sys
    from PyQt5.QtWidgets import QApplication
    
    app = QApplication(sys.argv)
    
    widget = VideoStreamVisualization()
    widget.setWindowTitle("Video Stream - FFplay/FFmpeg模式")
    widget.resize(600, 650)
    widget.show()
    
    sys.exit(app.exec_())


if __name__ == "__main__":
    main() 