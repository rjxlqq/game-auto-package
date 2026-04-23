import os
import time
from datetime import datetime

import cv2
import numpy as np
from PyQt5.QtCore import pyqtSignal, QThread


class OCRScanWaitThread(QThread):
    target_found = pyqtSignal(dict)
    timeout_reached = pyqtSignal()

    def __init__(self, parent, target_text, region_params, timeout_seconds=10, min_confidence=0.5, window_target=None, ocr_engine=None, processing_interval=0.5):
        super().__init__(parent)
        self.parent = parent
        self.target_text = target_text
        self.region_params = region_params
        self.timeout_seconds = timeout_seconds
        self.min_confidence = min_confidence
        self.window_target = window_target
        self.ocr_engine = ocr_engine
        self.running = False
        self.processing_interval = processing_interval

    def run(self):
        """独立扫描主循环"""
        self.running = True
        start_time = time.time()
        scan_region = self.calculate_scan_region()
        if not scan_region:
            print("错误: 无法计算扫描区域")
            self.running = False
            return

        x1, y1, x2, y2 = scan_region
        try:
            while self.running:
                if time.time() - start_time > self.timeout_seconds:
                    print(f"OCR等待超时: 未找到文字 '{self.target_text}'")
                    self.timeout_reached.emit()
                    break

                frame = self.parent.obs_source.get_frame()

                if frame is not None:
                    result = self.process_frame(frame, x1, y1, x2, y2)
                    if result:
                        self.target_found.emit(result)
                        break
                else:
                    self.msleep(10)  # 队列为空时短休眠
                time.sleep(self.processing_interval)

        except Exception as e:
            print(f"classifyTargetDetectionThread异常: {e}")
        self.running = False

    def process_frame(self, frame, x1, y1, x2, y2):
        try:
            # 切割感兴趣区域 (ROI)
            # roi = frame[y1:y2, x1:x2]
            # if roi.size == 0:
            #     return None
            # 新增：获取帧实际尺寸用于边界检查
            h, w = frame.shape[:2]

            # 安全裁剪：防止坐标越界
            x1 = max(0, x1)
            y1 = max(0, y1)
            x2 = min(w, x2)
            y2 = min(h, y2)

            if x2 <= x1 or y2 <= y1:
                return None

            roi = frame[y1:y2, x1:x2]
            if roi.size == 0:
                return None
            # self.save_debug_image(roi,roi)
            # OCR 识别
            results = self.ocr_engine.predict(self.ocr_apply_clarity_mask(roi))
            if not results:
                return None

            # --- 在循环外定义三个变量（数组） ---
            all_results = []
            for item in results:
                polys = item.get("dt_polys", [])
                texts = item.get("rec_texts", [])
                scores = item.get("rec_scores", [])

                for poly, text, score in zip(polys, texts, scores):
                    # 1. 过滤置信度
                    if score < self.min_confidence:
                        continue

                    # 2. 如果有特定目标过滤逻辑（可选）
                    # if self.target_text not in text:
                    #     continue

                    # 3. 坐标转换：ROI 内坐标 -> 整图绝对坐标
                    poly_np = np.array(poly, dtype=int)
                    poly_np[:, 0] += x1
                    poly_np[:, 1] += y1

                    # 计算矩形外框 (bbox)
                    curr_bbox = {
                        "x1": int(poly_np[:, 0].min()),
                        "y1": int(poly_np[:, 1].min()),
                        "x2": int(poly_np[:, 0].max()),
                        "y2": int(poly_np[:, 1].max())
                    }
                    all_results.append({
                        "text": text,
                        "score": float(score),
                        "bbox": curr_bbox
                    })
            # --- 循环结束后，统一返回结果 ---
            if not all_results:
                return None

            return {
                "all_results": all_results
            }

        except Exception as e:
            print(f"单帧OCR识别异常: {e}")
            return None

    def calculate_scan_region(self):
        """计算扫描区域"""
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

                print(f"计算后的扫描区域: ({x1},{y1})-({x2},{y2})")
                return (x1, y1, x2, y2)
            else:
                if len(self.region_params) != 4:
                    print("错误: 区域参数必须是4个值的元组")
                    return None
                return self.region_params

        except Exception as e:
            print(f"计算扫描区域错误: {e}")
            return None

    def stop(self):
        """停止线程"""
        self.running = False
        if self.isRunning():
            self.wait(500)

    def ocr_apply_clarity_mask(self, roi):
        """
        增强文字清晰度，并确保输出图像维度与原图一致（3通道），解决拼接和解构报错。
        """
        if roi is None or roi.size == 0:
            return roi

        try:
            # 1. 灰度化：减少色彩干扰
            gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)

            # 2. 自适应直方图均衡化 (CLAHE)：拉开文字与背景对比度
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
            enhanced = clahe.apply(gray)

            # 3. 锐化 (非锐化掩模)：让文字边缘更锋利
            gaussian_blur = cv2.GaussianBlur(enhanced, (0, 0), 3)
            sharpened = cv2.addWeighted(enhanced, 1.5, gaussian_blur, -0.5, 0)

            # 4. 亮度补偿：让画面更干净
            final_gray = cv2.convertScaleAbs(sharpened, alpha=1.1, beta=10)

            # --- 核心修正点：转回 3 通道 BGR ---
            # 虽然看起来还是灰色的，但它现在有 (H, W, 3) 个维度
            # 这样 original 和 processed 的维度就完全一样了
            processed_roi = cv2.cvtColor(final_gray, cv2.COLOR_GRAY2BGR)

            # 保存调试图（现在不会再报维度不匹配的错误了）
            # self.save_debug_image(roi, processed_roi)

            return processed_roi

        except Exception as e:
            print(f"❌ 【ocr_apply_clarity_mask 异常】: {e}")
            return roi

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
