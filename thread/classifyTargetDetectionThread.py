import os
import time
from datetime import datetime

import cv2
import numpy as np
from PyQt5.QtCore import QThread, pyqtSignal


class classifyTargetDetectionThread(QThread):
    """
    区域目标识别线程（支持绝对/相对区域）
    已修复：检测结果坐标现在正确转换为全图绝对坐标
    """
    target_found = pyqtSignal(dict)  # 找到目标信号
    timeout_reached = pyqtSignal()  # 超时信号

    def __init__(self, parent, target_class, region_params, timeout_seconds=10, min_confidence=0.5, window_target=None, classify_model=None, processing_interval=0.5):
        super().__init__(parent)
        self.parent = parent
        self.target_class = target_class
        self.timeout_seconds = timeout_seconds
        self.min_confidence = min_confidence
        self.classify_model = classify_model
        self.window_target = window_target
        self.region_params = region_params
        self.running = True
        self.processing_interval = processing_interval

        # 用于保存当前扫描区域的左上角偏移（ROI偏移）
        self.current_roi_x1 = 0
        self.current_roi_y1 = 0

    def run(self):
        """线程执行主循环"""
        start_time = time.time()
        self.running = True

        # 计算扫描区域
        scan_region = self.calculate_scan_region()
        if not scan_region:
            print("错误: 无法计算扫描区域")
            self.running = False
            return

        x1, y1, x2, y2 = scan_region

        # 保存当前 ROI 偏移，用于后续坐标转换
        self.current_roi_x1 = int(x1)
        self.current_roi_y1 = int(y1)
        try:
            while self.running:
                # 1. 检查是否超时
                if (time.time() - start_time) > self.timeout_seconds:
                    self.timeout_reached.emit()
                    break

                frame = self.parent.obs_source.get_frame()
                # 2. 从队列获取帧
                if frame is not None:
                    # 3. 在指定区域执行 YOLO 识别
                    results = self.scan_single_frame_region(frame, x1, y1, x2, y2)
                    # 4. 处理检测结果（这里会自动加上 ROI 偏移，得到全图坐标）
                    best_targets = self.get_best_parsed_results(results, self.min_confidence, offset_x=int(x1), offset_y=int(y1))
                    # 5. 匹配目标
                    if best_targets and self.target_class in best_targets:
                        self.target_found.emit(best_targets[self.target_class])
                        break
                else:
                    self.msleep(10)  # 队列为空时短休眠

                time.sleep(self.processing_interval)

        except Exception as e:
            print(f"classifyTargetDetectionThread异常: {e}")

        self.running = False

    def scan_single_frame_region(self, frame, x1, y1, x2, y2):
        """在单个帧的指定区域执行YOLO识别"""
        try:
            h, w = frame.shape[:2]

            # 安全裁剪坐标
            x1, y1 = max(0, int(x1)), max(0, int(y1))
            x2, y2 = min(w, int(x2)), min(h, int(y2))

            if x2 <= x1 or y2 <= y1:
                return None

            # 提取 ROI
            region = frame[y1:y2, x1:x2]
            if region.size == 0:
                return None
            # self.save_debug_image(region,region)
            # YOLO 识别（使用较小 imgsz 加速）
            if self.classify_model:
                results = list(self.classify_model(region, verbose=False, stream=True, imgsz=416))
                if results and len(results) > 0:
                    return results
            return None

        except Exception as e:
            print(f"单帧区域扫描错误: {e}")
            return None

    def calculate_scan_region(self):
        """计算扫描区域（支持相对窗口坐标）"""
        try:
            if self.window_target:
                if not self.window_target or len(self.region_params) != 4:
                    print("错误: 窗口目标或相对区域参数不正确")
                    return None

                window_x1 = self.window_target.get("x1", 0)
                window_y1 = self.window_target.get("y1", 0)
                window_x2 = self.window_target.get("x2", 0)
                window_y2 = self.window_target.get("y2", 0)

                rel_x1, rel_y1, rel_x2, rel_y2 = self.region_params
                width = window_x2 - window_x1
                height = window_y2 - window_y1

                x1 = window_x1 + int(width * rel_x1)
                y1 = window_y1 + int(height * rel_y1)
                x2 = window_x1 + int(width * rel_x2)
                y2 = window_y1 + int(height * rel_y2)

                print(f"计算后的扫描区域（相对）: ({x1},{y1})-({x2},{y2})")
                return (x1, y1, x2, y2)
            else:
                if len(self.region_params) != 4:
                    print("错误: 区域参数必须是4个值的元组")
                    return None
                return self.region_params

        except Exception as e:
            print(f"计算扫描区域错误: {e}")
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
            if not os.path.exists(save_dir):
                os.makedirs(save_dir)
            timestamp = datetime.now().strftime("%H%M%S_%f")[:-3]
            # 将原图和处理后的图拼在一起看更直观
            combined = np.hstack((original, processed))
            save_path = os.path.join(save_dir, f"compare_{timestamp}.jpg")
            cv2.imwrite(save_path, combined)
        except Exception as e:
            print(f"保存调试图失败: {e}")
