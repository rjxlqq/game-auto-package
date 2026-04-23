# syncDetectionUtils.py

import gc
from functools import wraps

from PyQt5.QtCore import QTimer, QEventLoop

from thread.OCRScanWaitThread import OCRScanWaitThread  # 区域文字识别线程
from thread.OcrDeskScanThread import OcrDeskScanThread  # 桌面区域识别线程
from thread.RegionScanWaitThread import RegionScanWaitThread  # 区域目标识别线程
from thread.classifyTargetDetectionThread import classifyTargetDetectionThread  # 区域文字识别线程
from thread.globalTargetDetectionThread import globalTargetDetectionThread  # 区域文字识别线程


def auto_cleanup(func):
    """
    清理内存装饰器：
    专门用于 YOLO 识别、OCR 扫描等产生大数组的高频函数。
    """

    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        finally:
            # 1. 显式清理局部变量引用（如果函数内部没写 del）
            # 2. 触发 0 代垃圾回收，回收效率最高且耗时极短
            gc.collect(0)

    return wrapper


class AsyncDetectorMixin:
    # 同步等待目标：返回目标字典或 None
    @auto_cleanup
    def wait_for_target(self, target_class, timeout_seconds=15, min_confidence=0.5):
        """
            target_class:识别目标标签
            timeout_seconds:超时时间
            min_confidence:最小置信度
            本函数返回参数的格式为:{'class_name': '游戏窗口', 'confidence': 0.9097, 'x1': 1, 'y1': 0, 'x2': 1919, 'y2': 1080, 'center_x': 960, 'center_y': 540}
        """
        # 停止可能存在的旧识别线程
        if hasattr(self, 'global_target_detection_thread') and self.global_target_detection_thread and self.global_target_detection_thread.isRunning():
            self.global_target_detection_thread.stop()
            self.global_target_detection_thread.wait(500)

        # 创建事件循环
        event_loop = QEventLoop()
        result = {"target": None}

        # 信号连接回调
        def on_target_found(target):
            result["target"] = target
            event_loop.quit()

        def on_timeout():
            print(f"wait_for_target: 等待 [{target_class}] 超时")
            event_loop.quit()

        # 初始化并启动线程
        self.global_target_detection_thread = globalTargetDetectionThread(
            self, target_class, timeout_seconds, min_confidence, self.global_model
        )
        self.global_target_detection_thread.target_found.connect(on_target_found)
        self.global_target_detection_thread.timeout_reached.connect(on_timeout)
        self.global_target_detection_thread.start()

        # 备用硬件定时器防止极端情况卡死
        timeout_timer = QTimer()
        timeout_timer.setSingleShot(True)
        timeout_timer.timeout.connect(on_timeout)
        timeout_timer.start((timeout_seconds + 2) * 1000)

        # 进入循环，直到 emit quit()
        event_loop.exec_()

        # 善后清理
        timeout_timer.stop()
        if self.global_target_detection_thread.isRunning():
            self.global_target_detection_thread.stop()
            self.global_target_detection_thread.wait(500)

        return result["target"]

    # 同步等待区域目标（整合扫描功能）
    @auto_cleanup
    def wait_for_region_target(self, target_class, region_params, timeout_seconds=10, min_confidence=0.5, window_target=None):
        """
            target_class:识别目标标签
            region_params：相对区域参数，举例,(0.080000, 0.473039, 0.613333, 0.556373)
            timeout_seconds:超时时间
            min_confidence:最小置信度
            window_target:已经识别到的目标窗口，格式如
            本函数返回参数的格式为:{'class_name': '游戏窗口', 'confidence': 0.9097, 'x1': 1, 'y1': 0, 'x2': 1919, 'y2': 1080, 'center_x': 960, 'center_y': 540}
        """
        if self.region_scan_wait_thread and self.region_scan_wait_thread.isRunning():
            self.region_scan_wait_thread.stop()
            self.region_scan_wait_thread.wait(500)

        # 创建事件循环
        event_loop = QEventLoop()
        result = {"target": None}

        def on_target_found(target):
            result["target"] = target
            event_loop.quit()

        def on_timeout():
            event_loop.quit()

        # 创建并启动线程
        self.region_scan_wait_thread = RegionScanWaitThread(
            self,
            target_class,
            region_params,
            timeout_seconds,
            min_confidence,
            window_target,
            self.global_model
        )

        self.region_scan_wait_thread.target_found.connect(on_target_found)
        self.region_scan_wait_thread.timeout_reached.connect(on_timeout)
        self.region_scan_wait_thread.start()

        # 超时保护
        timeout_timer = QTimer()
        timeout_timer.setSingleShot(True)
        timeout_timer.timeout.connect(event_loop.quit)
        timeout_timer.start((timeout_seconds + 2) * 1000)

        # 等待结果
        event_loop.exec_()

        # 清理
        timeout_timer.stop()
        if self.region_scan_wait_thread.isRunning():
            self.region_scan_wait_thread.stop()
            self.region_scan_wait_thread.wait(500)

        return result["target"]

    # 同步等待区域目标（整合扫描功能） 局部识别优化模型 调用小模型
    @auto_cleanup
    def wait_for_region_classify_target(self, target_class, region_params, timeout_seconds=10, min_confidence=0.5, window_target=None):
        """
            target_class:识别目标标签
            region_params：相对区域参数，举例,(0.080000, 0.473039, 0.613333, 0.556373)
            timeout_seconds:超时时间
            min_confidence:最小置信度
            window_target:已经识别到的目标窗口，格式如
            本函数返回参数的格式为:{'class_name': '游戏窗口', 'confidence': 0.9097, 'x1': 1, 'y1': 0, 'x2': 1919, 'y2': 1080, 'center_x': 960, 'center_y': 540}
        """
        if self.classify_target_detection_thread and self.classify_target_detection_thread.isRunning():
            self.classify_target_detection_thread.stop()
            self.classify_target_detection_thread.wait(500)

        # 创建事件循环
        event_loop = QEventLoop()
        result = {"target": None}

        def on_target_found(target):
            result["target"] = target
            event_loop.quit()

        def on_timeout():
            event_loop.quit()

        # 创建并启动线程
        self.classify_target_detection_thread = classifyTargetDetectionThread(
            self,
            target_class,
            region_params,
            timeout_seconds,
            min_confidence,
            window_target,
            self.classify_model
        )

        self.classify_target_detection_thread.target_found.connect(on_target_found)
        self.classify_target_detection_thread.timeout_reached.connect(on_timeout)
        self.classify_target_detection_thread.start()

        # 超时保护
        timeout_timer = QTimer()
        timeout_timer.setSingleShot(True)
        timeout_timer.timeout.connect(event_loop.quit)
        timeout_timer.start((timeout_seconds + 2) * 1000)

        # 等待结果
        event_loop.exec_()

        # 清理
        timeout_timer.stop()
        if self.classify_target_detection_thread.isRunning():
            self.classify_target_detection_thread.stop()
            self.classify_target_detection_thread.wait(500)

        return result["target"]

        # 异步等待区域目标（整合扫描功能）

    # 同步等待区域 OCR 目标
    @auto_cleanup
    def wait_for_ocr_region_target(self, target_text, region_params, timeout_seconds=10, min_confidence=0.5, window_target=None):
        """
            target_text:识别目标文本
            region_params：相对区域参数，举例,(0.080000, 0.473039, 0.613333, 0.556373)
            timeout_seconds:超时时间
            min_confidence:最小置信度
            window_target:已经识别到的目标窗口，格式如
            本函数返回参数的格式为:格式如 {'all_results': [...]}
        """
        if hasattr(self, 'ocr_region_wait_thread') and self.ocr_region_wait_thread and self.ocr_region_wait_thread.isRunning():
            self.ocr_region_wait_thread.stop()
            self.ocr_region_wait_thread.wait(500)

        # 创建事件循环
        event_loop = QEventLoop()
        result = {"target": None}

        def on_target_found(target):
            result["target"] = target
            event_loop.quit()

        def on_timeout():
            event_loop.quit()

        # 创建并启动线程
        self.ocr_region_wait_thread = OCRScanWaitThread(
            self,
            target_text,
            region_params,
            timeout_seconds,
            min_confidence,
            window_target,
            self.ocr_engine
        )
        self.ocr_region_wait_thread.target_found.connect(on_target_found)
        self.ocr_region_wait_thread.timeout_reached.connect(on_timeout)
        self.ocr_region_wait_thread.start()

        # 超时保护
        timeout_timer = QTimer()
        timeout_timer.setSingleShot(True)
        timeout_timer.timeout.connect(event_loop.quit)
        timeout_timer.start((timeout_seconds + 2) * 1000)

        # 等待结果
        event_loop.exec_()

        # 清理
        timeout_timer.stop()
        if self.ocr_region_wait_thread.isRunning():
            self.ocr_region_wait_thread.stop()
            self.ocr_region_wait_thread.wait(500)

        return result["target"]

    # 桌面文字扫描
    @auto_cleanup
    def wait_for_desk_region(self, target_text, region_params, timeout_seconds=10, min_confidence=0.5):
        """
                    target_text:识别目标文本
                    region_params：相对区域参数，举例,(0.080000, 0.473039, 0.613333, 0.556373)
                    timeout_seconds:超时时间
                    min_confidence:最小置信度
                    本函数返回参数的格式为:格式如 {'all_results': [...]}
                """
        if hasattr(self, 'desk_scan_wait_thread') and self.desk_scan_wait_thread and self.desk_scan_wait_thread.isRunning():
            self.desk_scan_wait_thread.stop()
            self.desk_scan_wait_thread.wait(500)

        # 创建事件循环
        event_loop = QEventLoop()
        result = {"target": None}

        def on_target_found(target):
            result["target"] = target
            event_loop.quit()

        def on_timeout():
            event_loop.quit()

        # 创建并启动线程
        self.desk_scan_wait_thread = OcrDeskScanThread(
            self,
            target_text,
            region_params,
            timeout_seconds,
            min_confidence,
            self.ocr_engine
        )

        self.desk_scan_wait_thread.target_found.connect(on_target_found)
        self.desk_scan_wait_thread.timeout_reached.connect(on_timeout)
        self.desk_scan_wait_thread.start()

        # 超时保护
        timeout_timer = QTimer()
        timeout_timer.setSingleShot(True)
        timeout_timer.timeout.connect(event_loop.quit)
        timeout_timer.start((timeout_seconds + 2) * 1000)

        # 等待结果
        event_loop.exec_()

        # 清理
        timeout_timer.stop()
        if self.desk_scan_wait_thread.isRunning():
            self.desk_scan_wait_thread.stop()
            self.desk_scan_wait_thread.wait(500)

        return result["target"]
