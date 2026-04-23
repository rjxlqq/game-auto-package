import os
import time
from datetime import datetime

import cv2
import numpy as np
from PyQt5.QtCore import QThread, pyqtSignal


class globalTargetDetectionThread(QThread):
    """
    目标识别线程
    """
    target_found = pyqtSignal(dict)  # 找到目标信号
    timeout_reached = pyqtSignal()  # 超时信号

    def __init__(self, parent, target_class, timeout_seconds=10, min_confidence=0.5, global_model=None, processing_interval=1):
        super().__init__(parent)
        self.parent = parent
        self.target_class = target_class
        self.timeout_seconds = timeout_seconds
        self.min_confidence = min_confidence
        self.global_model = global_model
        self.running = True
        self.processing_interval = processing_interval

    def run(self):
        """线程执行主循环"""
        self.running = True
        start_time = time.time()
        try:
            while self.running:
                # 1. 检查是否超时
                if (time.time() - start_time) > self.timeout_seconds:
                    self.timeout_reached.emit()
                    break

                frame = self.parent.obs_source.get_frame()
                # 2. 从队列获取帧
                if frame is not None:
                    # 3. 使用严格参考的预处理逻辑
                    # processed_frame = self.preprocess_frame(frame)
                    # self.save_debug_image(frame, frame)
                    results = list(self.global_model(frame, verbose=False, stream=True))
                    # 使用核心结果处理函数
                    best_targets = self.get_best_parsed_results(results, self.min_confidence)
                    # 匹配目标
                    if best_targets and self.target_class in best_targets:
                        self.target_found.emit(best_targets[self.target_class])
                        break
                else:
                    self.msleep(10)  # 队列为空时短休眠
                time.sleep(self.processing_interval)
        except Exception as e:
            print(f" globalTargetDetectionThread线程异常: {e}")
            return None
        self.running = False

    def preprocess_frame(self, frame):
        """统一预处理帧为 YOLO 所需的 3通道 RGB 格式"""
        if frame is None:
            return None
        try:
            # 处理不同通道数的输入
            if len(frame.shape) == 3:
                channels = frame.shape[2]
                if channels == 4:  # BGRA/RGBA → BGR
                    frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)
                elif channels == 3:
                    # OpenCV 默认 BGR，直接转为 RGB
                    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    return frame
                # channels == 1 会在下面处理
            elif len(frame.shape) == 2:  # 灰度图
                frame = cv2.cvtColor(frame, cv2.COLOR_GRAY2BGR)

            # 最后统一确保是 RGB
            if frame.shape[2] == 3:
                # 简单判断是否仍是 BGR（如果还没转）
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

            return frame

        except Exception as e:
            print(f"preprocess_frame 异常: {e}")
            return None

    def get_best_parsed_results(self, results, min_confidence=0.5, offset_x=0, offset_y=0):
        """
        合二为一：解析 YOLO Results 并按类别提取置信度最高的目标
        返回格式: { '类别名': {'class_name':..., 'confidence':..., 'center_x':...}, ... }
        """
        if not results:
            return None
        best_targets = {}
        try:
            # 兼容处理：如果是 stream=True 的生成器或列表，统一进行遍历
            for r in results:
                if not hasattr(r, 'boxes') or r.boxes is None:
                    continue

                for box in r.boxes:
                    conf = float(box.conf.item())

                    # 1. 过滤掉置信度不足的目标
                    if conf < min_confidence:
                        continue

                    class_id = int(box.cls.item())
                    name = r.names[class_id]
                    lx1, ly1, lx2, ly2 = box.xyxy[0].tolist()
                    # 2. 核心逻辑：如果类别不在字典里，或者当前这个比之前的更准，就更新它
                    if name not in best_targets or conf > best_targets[name]["confidence"]:
                        best_targets[name] = {
                            "class_name": name,
                            "confidence": round(conf, 4),
                            "x1": int(lx1 + offset_x),  # 加上偏移量，直接给全局坐标
                            "y1": int(ly1 + offset_y),
                            "x2": int(lx2 + offset_x),
                            "y2": int(ly2 + offset_y),
                            "center_x": int((lx1 + lx2) / 2 + offset_x),
                            "center_y": int((ly1 + ly2) / 2 + offset_y)
                        }

        except Exception as e:
            print(f"❌ 目标解析合并函数异常: {e}")
            return None

        return best_targets if best_targets else None

    def stop(self):
        """停止线程"""
        self.running = False
        if self.isRunning():
            self.wait(500)

    def save_debug_image(self, original, processed):
        """保存处理前后的对比图"""
        try:
            save_dir = "debug_frame"
            if not os.path.exists(save_dir): os.makedirs(save_dir)
            timestamp = datetime.now().strftime("%H%M%S_%f")[:-3]
            # 将原图和处理后的图拼在一起看更直观
            combined = np.hstack((original, processed))
            save_path = os.path.join(save_dir, f"compare_{timestamp}.jpg")
            cv2.imwrite(save_path, combined)
        except Exception as e:
            print(f"保存调试图失败: {e}")
