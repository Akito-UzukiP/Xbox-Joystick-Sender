"""
消息总线可视化模块 - PyQt版本
用于显示和管理消息总线的topics和消息
"""

import json
import time
import threading
from datetime import datetime
from collections import defaultdict, deque

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, 
                            QTreeWidget, QTreeWidgetItem, QTextEdit, 
                            QLabel, QPushButton, QCheckBox, QSplitter)
from PyQt5.QtCore import QTimer, Qt, pyqtSignal
from PyQt5.QtGui import QFont


class MessageBusVisualization(QWidget):
    """消息总线可视化组件"""
    
    # 信号定义
    message_added = pyqtSignal(str, float, dict)  # topic, timestamp, data
    
    def __init__(self):
        super().__init__()
        
        # 消息存储 - 每个topic保留最新的100条消息
        self.topic_messages = defaultdict(lambda: deque(maxlen=100))
        self.topic_stats = defaultdict(lambda: {
            'count': 0, 
            'last_time': 0, 
            'rate': 0,
            'rate_window': deque(maxlen=20),  # 用于更准确的频率计算
            'last_display_update': 0
        })
        self.selected_topic = None
        
        # 锁用于线程安全
        self.lock = threading.Lock()
        
        # 界面更新控制
        self.last_tree_update = 0
        self._last_msg_count = 0
        
        # 创建界面
        self.setup_layout()
        
        # 启动更新定时器
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_display)
        self.update_timer.start(200)  # 每200ms更新一次
        
    def setup_layout(self):
        """设置消息总线可视化布局"""
        layout = QVBoxLayout(self)
        
        # 主分割器
        main_splitter = QSplitter(Qt.Horizontal)
        layout.addWidget(main_splitter)
        
        # 左侧面板 - Topic列表
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        
        # Topic列表标题
        topic_label = QLabel("Topics")
        topic_label.setFont(QFont("Arial", 12, QFont.Bold))
        left_layout.addWidget(topic_label)
        
        # Topic树视图
        self.topic_tree = QTreeWidget()
        self.topic_tree.setHeaderLabels(['Topic', '消息数', '频率(Hz)'])
        self.topic_tree.setColumnWidth(0, 200)
        self.topic_tree.setColumnWidth(1, 80)
        self.topic_tree.setColumnWidth(2, 80)
        self.topic_tree.itemSelectionChanged.connect(self.on_topic_select)
        left_layout.addWidget(self.topic_tree)
        
        # 清除按钮
        clear_btn = QPushButton("清除所有消息")
        clear_btn.clicked.connect(self.clear_all_messages)
        left_layout.addWidget(clear_btn)
        
        main_splitter.addWidget(left_widget)
        
        # 右侧面板 - 消息详情
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        
        # 消息详情标题
        header_layout = QHBoxLayout()
        
        self.selected_topic_label = QLabel("Select a topic to view messages")
        self.selected_topic_label.setFont(QFont("Arial", 12, QFont.Bold))
        header_layout.addWidget(self.selected_topic_label)
        
        header_layout.addStretch()
        
        # 自动滚动复选框
        self.auto_scroll_checkbox = QCheckBox("自动滚动")
        self.auto_scroll_checkbox.setChecked(True)
        header_layout.addWidget(self.auto_scroll_checkbox)
        
        right_layout.addLayout(header_layout)
        
        # 消息显示区域
        self.message_text = QTextEdit()
        self.message_text.setFont(QFont("Consolas", 9))
        self.message_text.setReadOnly(True)
        right_layout.addWidget(self.message_text)
        
        main_splitter.addWidget(right_widget)
        
        # 设置分割器比例
        main_splitter.setSizes([300, 700])
        
    def add_message(self, topic, timestamp, data):
        """添加新消息到topic"""
        with self.lock:
            # 存储消息
            message = {
                'timestamp': timestamp,
                'data': data,
                'formatted_time': datetime.fromtimestamp(timestamp).strftime("%H:%M:%S.%f")[:-3]
            }
            self.topic_messages[topic].append(message)
            
            # 更新统计
            stats = self.topic_stats[topic]
            stats['count'] += 1
            
            # 计算频率使用滑动窗口
            current_time = time.time()
            stats['rate_window'].append(current_time)
            
            # 从窗口计算频率
            if len(stats['rate_window']) >= 2:
                time_span = stats['rate_window'][-1] - stats['rate_window'][0]
                if time_span > 0:
                    stats['rate'] = (len(stats['rate_window']) - 1) / time_span
                else:
                    stats['rate'] = 0
            
            stats['last_time'] = current_time
            
            # 如果当前选中的就是这个topic，立即追加消息并滚动
            is_selected_topic = (self.selected_topic == topic)
        
        # 在锁外处理UI更新，避免死锁
        if is_selected_topic and self.auto_scroll_checkbox.isChecked():
            # 使用QTimer.singleShot确保在主线程中执行
            QTimer.singleShot(0, lambda: self.update_message_display_realtime(message))
    
    def on_topic_select(self):
        """处理topic选择"""
        current_item = self.topic_tree.currentItem()
        if current_item:
            self.selected_topic = current_item.text(0)
            self._last_msg_count = 0  # 重置消息计数以强制更新
            self.update_message_display(force_update=True)
    
    def update_message_display(self, force_update=False):
        """更新选中topic的消息显示"""
        if not self.selected_topic:
            return
            
        current_time = time.time()
        stats = self.topic_stats[self.selected_topic]
        
        # 对于高频topic，限制显示更新频率以避免界面卡顿
        if not force_update and current_time - stats.get('last_display_update', 0) < 0.2:
            return
            
        with self.lock:
            messages = list(self.topic_messages[self.selected_topic])
        
        self.selected_topic_label.setText(f"Topic: {self.selected_topic} ({len(messages)} messages)")
        
        # 只有在强制更新或消息数量变化很大时才完全重建显示
        current_msg_count = len(messages)
        if not force_update and hasattr(self, '_last_msg_count'):
            # 如果消息数量变化不大，不重建显示（让实时追加处理）
            if abs(self._last_msg_count - current_msg_count) < 5:
                return
        
        self._last_msg_count = current_msg_count
        
        # 清除并更新消息显示
        self.message_text.clear()
        
        # 只显示最新的消息以提高性能
        display_messages = messages[-20:] if len(messages) > 20 else messages
        
        for msg in display_messages:
            self.insert_formatted_message(msg)
        
        # 自动滚动到底部
        if self.auto_scroll_checkbox.isChecked():
            self.force_scroll_to_end()
            
        stats['last_display_update'] = current_time
    
    def update_message_display_realtime(self, message):
        """实时更新消息显示（仅追加新消息）"""
        try:
            # 只追加新消息，不重建整个显示
            self.insert_formatted_message(message)
            # 强制滚动到底部
            self.force_scroll_to_end()
            # 限制显示的消息数量
            document = self.message_text.document()
            if document.blockCount() > 100:  # 如果超过100行，删除前面的内容
                cursor = self.message_text.textCursor()
                cursor.movePosition(cursor.Start)
                cursor.movePosition(cursor.Down, cursor.KeepAnchor, 50)
                cursor.removeSelectedText()
        except:
            pass
    
    def insert_formatted_message(self, message):
        """插入格式化的消息到文本区域"""
        # 时间戳
        self.message_text.setTextColor(Qt.blue)
        self.message_text.insertPlainText(f"[{message['formatted_time']}] ")
        
        # 数据（格式化JSON）
        try:
            if isinstance(message['data'], dict):
                # 如果数据很大，使用紧凑格式
                if len(str(message['data'])) > 200:
                    formatted_data = json.dumps(message['data'], ensure_ascii=False, separators=(',', ':'))
                else:
                    formatted_data = json.dumps(message['data'], ensure_ascii=False, indent=2)
            else:
                formatted_data = str(message['data'])
        except:
            formatted_data = str(message['data'])
        
        # 限制单条消息的长度
        if len(formatted_data) > 500:
            formatted_data = formatted_data[:500] + "... (截断)"
        
        self.message_text.setTextColor(Qt.black)
        self.message_text.insertPlainText(f"{formatted_data}\n\n")
    
    def force_scroll_to_end(self):
        """强制滚动到底部"""
        try:
            scrollbar = self.message_text.verticalScrollBar()
            scrollbar.setValue(scrollbar.maximum())
        except:
            pass
    
    def update_display(self):
        """更新topic树和消息显示"""
        current_time = time.time()
        
        # 更频繁地更新树视图以显示高频topic的实时统计
        if current_time - self.last_tree_update >= 0.5:  # 每0.5秒更新一次树视图
            with self.lock:
                topics_to_update = []
                for topic in self.topic_stats.keys():
                    stats = self.topic_stats[topic]
                    rate_str = f"{stats['rate']:.1f}" if stats['rate'] > 0 else "0.0"
                    topics_to_update.append((topic, stats['count'], rate_str))
            
            # 更新或创建树视图项目
            existing_items = {}
            root = self.topic_tree.invisibleRootItem()
            
            # 收集现有项目
            for i in range(root.childCount()):
                item = root.child(i)
                existing_items[item.text(0)] = item
            
            # 更新或添加topic
            for topic, count, rate_str in topics_to_update:
                if topic in existing_items:
                    # 更新现有项目
                    item = existing_items[topic]
                    item.setText(1, str(count))
                    item.setText(2, rate_str)
                else:
                    # 创建新项目
                    item = QTreeWidgetItem([topic, str(count), rate_str])
                    self.topic_tree.addTopLevelItem(item)
                    existing_items[topic] = item
            
            # 删除不再存在的topic
            topics_to_remove = []
            for topic, item in existing_items.items():
                if topic not in self.topic_stats:
                    topics_to_remove.append(item)
            
            for item in topics_to_remove:
                index = self.topic_tree.indexOfTopLevelItem(item)
                if index >= 0:
                    self.topic_tree.takeTopLevelItem(index)
                
            self.last_tree_update = current_time
        
        # 更新消息显示如果有topic被选中
        if self.selected_topic and self.selected_topic in self.topic_stats:
            self.update_message_display()
    
    def clear_all_messages(self):
        """清除所有消息"""
        with self.lock:
            self.topic_messages.clear()
            self.topic_stats.clear()
        
        # 清理树视图
        self.topic_tree.clear()
        
        self.selected_topic = None
        self.selected_topic_label.setText("Select a topic to view messages")
        self.message_text.clear()
        self._last_msg_count = 0 