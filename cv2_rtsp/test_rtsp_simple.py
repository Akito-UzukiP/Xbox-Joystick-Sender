#!/usr/bin/env python3
"""
简化的OpenCV RTSP性能测试脚本
专注于测试RTSP流的读取性能，不显示视频窗口
"""

import cv2
import time
import numpy as np
from collections import deque
import sys
import os

def test_rtsp_performance(rtsp_url, duration=60):
    """测试RTSP性能"""
    print(f"连接到RTSP流: {rtsp_url}")
    
    # 设置OpenCV的FFmpeg选项
    os.environ['OPENCV_FFMPEG_CAPTURE_OPTIONS'] = 'protocol_whitelist;file,rtp,udp,tcp'
    
    # 尝试不同的缓冲区设置
    buffer_sizes = [1, 2, 3]
    
    for buffer_size in buffer_sizes:
        print(f"\n测试缓冲区大小: {buffer_size}")
        print("-" * 60)
        
        cap = cv2.VideoCapture(rtsp_url, cv2.CAP_FFMPEG)
        
        if not cap.isOpened():
            print("错误: 无法连接到RTSP流")
            continue
            
        # 设置缓冲区大小
        cap.set(cv2.CAP_PROP_BUFFERSIZE, buffer_size)
        
        # 获取流信息
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        source_fps = cap.get(cv2.CAP_PROP_FPS)
        actual_buffer = cap.get(cv2.CAP_PROP_BUFFERSIZE)
        
        print(f"流信息: {width}x{height}, 源FPS: {source_fps}, 实际缓冲区: {actual_buffer}")
        
        # 统计变量
        frame_count = 0
        dropped_frames = 0
        total_attempts = 0
        frame_times = deque(maxlen=30)
        fps_history = []
        start_time = time.time()
        last_print_time = start_time
        
        try:
            while time.time() - start_time < duration:
                total_attempts += 1
                ret, frame = cap.read()
                
                if not ret or frame is None:
                    dropped_frames += 1
                    continue
                    
                frame_count += 1
                current_time = time.time()
                frame_times.append(current_time)
                
                # 计算当前FPS
                if len(frame_times) >= 2:
                    time_span = frame_times[-1] - frame_times[0]
                    if time_span > 0:
                        current_fps = (len(frame_times) - 1) / time_span
                        
                # 每5秒打印一次状态
                if current_time - last_print_time >= 5.0:
                    total_time = current_time - start_time
                    avg_fps = frame_count / total_time if total_time > 0 else 0
                    drop_rate = (dropped_frames / total_attempts * 100) if total_attempts > 0 else 0
                    
                    print(f"[{total_time:.1f}s] FPS: {current_fps:.1f} | 平均: {avg_fps:.1f} | "
                          f"帧数: {frame_count} | 丢帧: {dropped_frames} ({drop_rate:.1f}%)")
                    
                    fps_history.append(current_fps)
                    last_print_time = current_time
                    
        except KeyboardInterrupt:
            print("\n用户中断测试")
        except Exception as e:
            print(f"\n错误: {e}")
        finally:
            cap.release()
            
        # 最终统计
        total_time = time.time() - start_time
        avg_fps = frame_count / total_time if total_time > 0 else 0
        drop_rate = (dropped_frames / total_attempts * 100) if total_attempts > 0 else 0
        
        if fps_history:
            fps_array = np.array(fps_history)
            fps_std = np.std(fps_array)
            fps_mean = np.mean(fps_array)
        else:
            fps_std = 0
            fps_mean = avg_fps
            
        print(f"\n缓冲区 {buffer_size} 最终结果:")
        print(f"  运行时间: {total_time:.1f}秒")
        print(f"  总帧数: {frame_count}")
        print(f"  平均FPS: {avg_fps:.2f}")
        print(f"  FPS稳定性: {fps_mean:.2f} ± {fps_std:.2f}")
        print(f"  丢帧率: {drop_rate:.2f}% ({dropped_frames}/{total_attempts})")
        print(f"  读取成功率: {((total_attempts - dropped_frames) / total_attempts * 100):.2f}%")


def main():
    """主函数"""
    # 默认RTSP URL
    default_rtsp_url = "rtsp://10.24.20.165:8554/cam"
    
    # 从命令行参数获取RTSP URL
    if len(sys.argv) > 1:
        rtsp_url = sys.argv[1]
    else:
        rtsp_url = default_rtsp_url
        
    # 测试时长 (秒)
    test_duration = 30
    if len(sys.argv) > 2:
        try:
            test_duration = int(sys.argv[2])
        except ValueError:
            print("警告: 无效的测试时长，使用默认30秒")
    
    print("OpenCV RTSP 性能测试工具")
    print("=" * 60)
    print(f"RTSP URL: {rtsp_url}")
    print(f"每个缓冲区测试时长: {test_duration}秒")
    print("=" * 60)
    
    # 运行测试
    test_rtsp_performance(rtsp_url, test_duration)


if __name__ == "__main__":
    main() 