#!/usr/bin/env python3
"""
独立的OpenCV RTSP测试脚本
用于测试RTSP流的读取性能和帧率稳定性
支持帧缓冲区清理，防止帧堆积
"""

import cv2
import time
import threading
import numpy as np
from collections import deque
import sys
import os

class RTSPTester:
    def __init__(self, rtsp_url):
        self.rtsp_url = rtsp_url
        self.cap = None
        self.running = False
        
        # 统计信息
        self.frame_count = 0
        self.start_time = None
        self.fps_history = deque(maxlen=100)  # 保存最近100个FPS值
        self.frame_times = deque(maxlen=30)   # 保存最近30帧的时间戳
        self.dropped_frames = 0
        self.total_read_attempts = 0
        self.flushed_frames = 0  # 被丢弃的堆积帧数量
        
        # 显示相关
        self.show_video = True
        self.last_stats_time = time.time()
        
        # 帧缓冲区管理
        self.enable_frame_flush = True  # 是否启用帧缓冲区清理
        self.max_buffer_frames = 2      # 最大允许的缓冲帧数
        
    def connect(self):
        """连接到RTSP流"""
        print(f"连接到RTSP流: {self.rtsp_url}")
        
        self.cap = cv2.VideoCapture(self.rtsp_url, cv2.CAP_MSMF)
        
        if not self.cap.isOpened():
            print("错误: 无法连接到RTSP流")
            return False
            
        # 设置较小的缓冲区大小以减少延迟
        self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        
        # 尝试设置其他属性来减少延迟
        # self.cap.set(cv2.CAP_PROP_FPS, 30)
        
        # 获取流信息
        width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        source_fps = self.cap.get(cv2.CAP_PROP_FPS)
        buffer_size = self.cap.get(cv2.CAP_PROP_BUFFERSIZE)
        
        print(f"流信息:")
        print(f"  Resolution: {width}x{height}")
        print(f"  FPS: {source_fps}")
        print(f"  BufferSize: {buffer_size}")
        print(f"  Frame Flush: {'启用' if self.enable_frame_flush else '禁用'}")
        
        return True
        
    def flush_buffer(self):
        """清理缓冲区中的旧帧，保留最新帧"""
        if not self.enable_frame_flush or not self.cap:
            return None
            
        frame = None
        flush_count = 0
        
        # 连续读取帧直到缓冲区为空或达到最大清理数量
        while flush_count < self.max_buffer_frames:
            ret, temp_frame = self.cap.read()
            if not ret or temp_frame is None:
                break
                
            frame = temp_frame  # 保留最后一个有效帧
            flush_count += 1
            
        if flush_count > 1:
            self.flushed_frames += (flush_count - 1)  # 记录被丢弃的帧数
            
        return frame
        
    def read_latest_frame(self):
        """读取最新帧，丢弃堆积的旧帧"""
        self.total_read_attempts += 1
        
        # 首先尝试读取一帧
        ret, frame = self.cap.read()
        
        if not ret or frame is None:
            self.dropped_frames += 1
            return None
            
        # 如果启用了帧缓冲区清理，尝试获取更新的帧
        if self.enable_frame_flush:
            latest_frame = self.flush_buffer()
            if latest_frame is not None:
                frame = latest_frame
                
        return frame
        
    def disconnect(self):
        """断开连接"""
        self.running = False
        if self.cap:
            self.cap.release()
        cv2.destroyAllWindows()
        
    def calculate_fps(self):
        """计算当前FPS"""
        current_time = time.time()
        self.frame_times.append(current_time)
        
        if len(self.frame_times) >= 2:
            time_span = self.frame_times[-1] - self.frame_times[0]
            if time_span > 0:
                fps = (len(self.frame_times) - 1) / time_span
                self.fps_history.append(fps)
                return fps
        return 0
        
    def get_stats(self):
        """获取统计信息"""
        current_time = time.time()
        
        if self.start_time:
            total_time = current_time - self.start_time
            avg_fps = self.frame_count / total_time if total_time > 0 else 0
        else:
            avg_fps = 0
            
        current_fps = self.calculate_fps()
        
        # 计算FPS稳定性
        if len(self.fps_history) > 1:
            fps_array = np.array(list(self.fps_history))
            fps_std = np.std(fps_array)
            fps_mean = np.mean(fps_array)
        else:
            fps_std = 0
            fps_mean = current_fps
            
        drop_rate = (self.dropped_frames / self.total_read_attempts * 100) if self.total_read_attempts > 0 else 0
        
        return {
            'current_fps': current_fps,
            'avg_fps': avg_fps,
            'fps_std': fps_std,
            'fps_mean': fps_mean,
            'frame_count': self.frame_count,
            'dropped_frames': self.dropped_frames,
            'drop_rate': drop_rate,
            'total_read_attempts': self.total_read_attempts,
            'flushed_frames': self.flushed_frames
        }
        
    def print_stats(self, stats):
        """打印统计信息"""
        print(f"\r统计信息 - "
              f"Current FPS: {stats['current_fps']:.1f} | "
              f"Average FPS: {stats['avg_fps']:.1f} | "
              f"FPS Mean: {stats['fps_mean']:.1f}±{stats['fps_std']:.1f} | "
              f"Frame Count: {stats['frame_count']} | "
              f"Dropped: {stats['dropped_frames']} | "
              f"Flushed: {stats['flushed_frames']}", 
              end='', flush=True)
        
    def add_info_overlay(self, frame, stats):
        """在视频帧上添加信息覆盖层"""
        height, width = frame.shape[:2]
        
        # 设置字体
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 0.6
        thickness = 2
        color = (0, 255, 0)  # 绿色
        
        # 信息文本
        info_lines = [
            f"Current FPS: {stats['current_fps']:.1f}",
            f"Average FPS: {stats['avg_fps']:.1f}",
            f"FPS Stability: {stats['fps_mean']:.1f}±{stats['fps_std']:.1f}",
            f"Total Frame Count: {stats['frame_count']}",
            f"Dropped Frames: {stats['dropped_frames']} ({stats['drop_rate']:.1f}%)",
            f"Flushed Frames: {stats['flushed_frames']}",
            f"Read Attempts: {stats['total_read_attempts']}"
        ]
        
        # 绘制半透明背景
        overlay = frame.copy()
        cv2.rectangle(overlay, (5, 5), (450, 25 * len(info_lines) + 10), (0, 0, 0), -1)
        cv2.addWeighted(overlay, 0.7, frame, 0.3, 0, frame)
        
        # 绘制信息文本
        y_offset = 25
        for line in info_lines:
            cv2.putText(frame, line, (10, y_offset), font, font_scale, color, thickness)
            y_offset += 25
            
        return frame
        
    def run_test(self, duration=None, show_video=True, enable_flush=True):
        """运行RTSP测试"""
        self.show_video = show_video
        self.enable_frame_flush = enable_flush
        
        if not self.connect():
            return
            
        self.running = True
        self.start_time = time.time()
        
        print(f"开始RTSP测试...")
        if duration:
            print(f"测试时长: {duration}秒")
        print(f"帧缓冲区清理: {'启用' if self.enable_frame_flush else '禁用'}")
        print("按 'q' 键退出, 按 'f' 键切换帧清理模式")
        print("-" * 80)
        
        try:
            while self.running:
                # 使用新的读取方法获取最新帧
                frame = self.read_latest_frame()
                
                if frame is None:
                    print(f"\n警告: 读取帧失败 (尝试 {self.total_read_attempts})")
                    continue
                    
                self.frame_count += 1
                
                # 获取统计信息
                stats = self.get_stats()
                
                # 每秒打印一次统计信息
                current_time = time.time()
                if current_time - self.last_stats_time >= 1.0:
                    self.print_stats(stats)
                    self.last_stats_time = current_time
                
                # 显示视频
                if self.show_video:
                    display_frame = self.add_info_overlay(frame.copy(), stats)
                    cv2.imshow('RTSP测试 - 防堆积模式', display_frame)
                    
                    # 检查键盘输入
                    key = cv2.waitKey(1) & 0xFF
                    if key == ord('q'):
                        break
                    elif key == ord('f'):
                        self.enable_frame_flush = not self.enable_frame_flush
                        print(f"\n帧缓冲区清理: {'启用' if self.enable_frame_flush else '禁用'}")
                        
                # 检查测试时长
                if duration and (current_time - self.start_time) >= duration:
                    break
                    
                # 小延迟避免过度消耗CPU
                time.sleep(0.001)
                
        except KeyboardInterrupt:
            print("\n用户中断测试")
        except Exception as e:
            print(f"\n错误: {e}")
        finally:
            self.disconnect()
            
        # 打印最终统计
        print("\n" + "=" * 80)
        print("测试完成 - 最终统计:")
        final_stats = self.get_stats()
        print(f"Total Running Time: {time.time() - self.start_time:.1f} seconds")
        print(f"Total Frame Count: {final_stats['frame_count']}")
        print(f"Average FPS: {final_stats['avg_fps']:.2f}")
        print(f"FPS Stability: {final_stats['fps_mean']:.2f} ± {final_stats['fps_std']:.2f}")
        print(f"Dropped Frames: {final_stats['dropped_frames']}")
        print(f"Flushed Frames: {final_stats['flushed_frames']}")
        print(f"Drop Rate: {final_stats['drop_rate']:.2f}%")
        print(f"Read Success Rate: {((final_stats['total_read_attempts'] - final_stats['dropped_frames']) / final_stats['total_read_attempts'] * 100):.2f}%")
        if final_stats['flushed_frames'] > 0:
            print(f"Buffer Flush Rate: {(final_stats['flushed_frames'] / final_stats['frame_count'] * 100):.2f}%")


def main():
    """主函数"""
    # 默认RTSP URL (您可以修改为您的RTSP地址)
    default_rtsp_url = "rtsp://10.24.20.165:8554/cam"
    
    # 从命令行参数获取RTSP URL
    if len(sys.argv) > 1:
        rtsp_url = sys.argv[1]
    else:
        rtsp_url = default_rtsp_url
        
    # 测试时长 (秒，None为无限制)
    test_duration = None
    if len(sys.argv) > 2:
        try:
            test_duration = int(sys.argv[2])
        except ValueError:
            print("警告: 无效的测试时长，使用无限制模式")
    
    print("OpenCV RTSP 测试工具 - 防帧堆积版本")
    print("=" * 50)
    print(f"RTSP URL: {rtsp_url}")
    print(f"测试时长: {'无限制' if test_duration is None else f'{test_duration}秒'}")
    print("=" * 50)
    
    # 创建并运行测试
    tester = RTSPTester(rtsp_url)
    tester.run_test(duration=test_duration, show_video=True, enable_flush=True)


if __name__ == "__main__":
    main() 