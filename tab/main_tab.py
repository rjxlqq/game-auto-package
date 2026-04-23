# main_tab.py
import sys
import threading
import time

import cv2
import dxcam
from PyQt5.QtCore import Qt, QTimer, QPropertyAnimation
from PyQt5.QtWidgets import (QApplication, QSplashScreen, QVBoxLayout, QSplitter, QWidget, QScrollArea, QFrame, QMessageBox)

from algoVision.asyncDetectionUtils import AsyncDetectorMixin
from algoVision.mouseKeyUtils import MouseKeyUtils
from algoVision.style import StyleManager
from algoVision.syncDetectionUtils import SyncDetectorMixin
from algoVision.syncOcrUtils import SyncOcrUtils
from algoVision.textUtils import TextUtils
from algoVision.visionUtils import VisionUtils
from nuoyaStrategy.nuoya_layout import NuoyaLayout  # 策略
from thread.InitModelThread import InitModelThread  # 初始化模型线程
from thread.SerialWorkerThread import SerialWorkerThread  # 硬件线程


# self.obs_source.get_frame()
class ObsSharedMemorySource:
    def __init__(self):
        self.camera = dxcam.create(device_idx=0, output_idx=0)
        self.region = (0, 0, 1920, 1080)

        # 全局最新帧（存放处理好的 BGR 图像）
        self.latest_bgr_frame = None

        # 启动 DXCam 的 C++ 底层异步抓取，限制 30 FPS 足矣，降低显卡压力
        self.camera.start(target_fps=30)

        # 启动 Python 后台处理线程
        self.running = True
        self.process_thread = threading.Thread(target=self._background_process_loop, daemon=True)
        self.process_thread.start()

    def _background_process_loop(self):
        """
        极致精简的后台采图：仅搬运原始数据，不做任何额外计算。
        """
        while self.running:
            try:
                # 1. 直接获取 DXCam 缓冲区的原始 RGB 数据 (非阻塞)
                # 这是最原始、未经任何处理的 NumPy 数组
                raw_frame = self.camera.get_latest_frame()
                if raw_frame is not None:
                    # 2. 直接赋值给全局变量
                    self.latest_bgr_frame = cv2.cvtColor(raw_frame, cv2.COLOR_RGB2BGR)
                    # 3. 极短的休眠，防止单核 CPU 占用过高
                time.sleep(0.001)

            except Exception as e:
                print(f"⚠️ 原始帧采集异常: {e}")
                time.sleep(0.5)

    def get_frame(self):
        """
        业务线程调用接口：极其轻量！直接返回内存中的变量，0 延迟，0 阻塞。
        """
        return self.latest_bgr_frame

    def release(self):
        """退出程序时调用"""
        self.running = False
        if self.camera:
            self.camera.stop()


# 帧接收器选项卡，包含原有的帧接收器功能   核心代码 + 初始化变量 + 页面ui
class mainTab(QWidget, NuoyaLayout, AsyncDetectorMixin, SyncDetectorMixin, SyncOcrUtils, VisionUtils, MouseKeyUtils, TextUtils):
    def __init__(self, parent=None):
        super().__init__(parent)
        # 初始化继承
        NuoyaLayout.__init__(self)
        # 获取虚拟摄像头 画面
        self.obs_source = ObsSharedMemorySource()
        # 初始化 全局模型
        self.global_model = None
        # 初始化 分类模型
        self.classify_model = None
        # 初始化ocr 模型
        self.ocr_engine = None
        # 区域扫描线程
        self.region_scan_wait_thread = None
        # 目标识别线程
        self.global_target_detection_thread = None
        # 目标识别线程
        self.classify_target_detection_thread = None
        # 区域文字扫描线程
        self.ocr_region_wait_thread = None
        # 区域区域扫描线程
        self.desk_scan_wait_thread = None
        # 任务开始和结束
        self.is_task_running = False

        if hasattr(self, 'serial_worker_thread') and self.serial_worker_thread and self.serial_worker_thread.isRunning():
            self.serial_worker_thread.stop()
            self.serial_worker_thread.wait(200)
        self.serial_worker_thread = SerialWorkerThread()
        self.serial_worker_thread.start_thread()
        # 设置UI
        self.setup_ui()
        # 先加载配置

    def showEvent(self, event):
        super().showEvent(event)
        # 标志位防止重复触发
        if not hasattr(self, 'init_started'):
            self.init_started = True
            QTimer.singleShot(100, self.start_init)

    def start_init(self):
        self.t = InitModelThread()

        def on_finished(global_yolo, classify_yolo, ocr):
            self.global_model, self.classify_model, self.ocr_engine = global_yolo, classify_yolo, ocr
            # 在 main.py 中挂载的 active_splash
            splash = getattr(QApplication.instance(), 'active_splash', None)
            if splash:
                if hasattr(splash, 'animation'):
                    splash.animation.stop()
                splash.close()  # 此时才真正关闭动画

        def on_init_failed(error_message):
            QMessageBox.critical(self, "加载错误",
                                 f"程序核心加载失败，无法继续运行。\n\n{error_message}")
            for widget in QApplication.allWidgets():
                for anim in widget.findChildren(QPropertyAnimation):
                    anim.stop()
                if isinstance(widget, QSplashScreen):
                    widget.close()
                    break
            sys.exit()

        self.t.error_occurred.connect(on_init_failed)
        self.t.done.connect(on_finished)
        self.t.start()

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        splitter = QSplitter(Qt.Vertical)
        # 上半部分
        top_widget = QWidget()
        splitter.addWidget(top_widget)
        # 下半部分（滚动区域）
        settings_group = self.setup_settings_group()
        splitter.addWidget(settings_group)
        splitter.setSizes([0, 888])
        main_layout.addWidget(splitter)

    def setup_settings_group(self):
        # 使用QFrame，可以设置边框样式
        settings_frame = QFrame()
        settings_frame.setStyleSheet(StyleManager.frame_style())
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.addWidget(self.setup_upgrade_group())
        scroll_layout.addWidget(self.setup_task_group())
        scroll_layout.addStretch(1)
        scroll_area.setWidget(scroll_content)
        group_layout = QVBoxLayout(settings_frame)
        group_layout.addWidget(scroll_area)
        group_layout.setContentsMargins(0, 0, 0, 0)
        group_layout.setSpacing(1)
        return settings_frame

    def cleanup(self):
        try:
            print(">>> 启动全局资源清理流程...")
            # 停止目标检测线程
            if hasattr(self, 'global_target_detection_thread') and self.global_target_detection_thread:
                if self.global_target_detection_thread.isRunning():
                    self.global_target_detection_thread.stop()
                    self.global_target_detection_thread.wait(100)
                print("✓ 目标检测线程已清理")

            # 停止分类检测线程
            if hasattr(self, 'classify_target_detection_thread') and self.classify_target_detection_thread:
                if self.classify_target_detection_thread.isRunning():
                    self.classify_target_detection_thread.stop()
                    self.classify_target_detection_thread.wait(100)
                print("✓ OCR分类线程已清理")

            # 停止区域扫描线程
            if hasattr(self, 'region_scan_wait_thread') and self.region_scan_wait_thread:
                if self.region_scan_wait_thread.isRunning():
                    self.region_scan_wait_thread.stop()
                    self.region_scan_wait_thread.wait(100)
                print("✓ 区域扫描线程已清理")

            # 停止OCR区域扫描线程
            if hasattr(self, 'ocr_region_wait_thread') and self.ocr_region_wait_thread:
                if self.ocr_region_wait_thread.isRunning():
                    self.ocr_region_wait_thread.stop()
                    self.ocr_region_wait_thread.wait(100)
                print("✓ OCR扫描线程已清理")

            # 停止桌面扫描线程
            if hasattr(self, 'desk_scan_wait_thread') and self.desk_scan_wait_thread:
                if self.desk_scan_wait_thread.isRunning():
                    self.desk_scan_wait_thread.stop()
                    self.desk_scan_wait_thread.wait(100)
                print("✓ 桌面扫描线程已清理")

            # 清理 NuoyaLayout 内部的特定线程 ---
            self.stop_automation()
            # 强制打断可能的同步事件循环
            if hasattr(self, 'loop') and self.loop.isRunning():
                self.loop.quit()
                print("✓ 强制打断同步等待循环")

            # 停止本地采集定时器
            if hasattr(self, 'local_capture_timer'):
                self.local_capture_timer.stop()
                print("✓ 采集定时器已停止")

            print("<<< 所有后台资源清理完毕，程序安全退出")
        except Exception as e:
            print(f"退出程序报错: {e}")
