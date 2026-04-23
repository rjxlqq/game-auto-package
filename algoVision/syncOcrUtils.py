import gc
from functools import wraps

import cv2
import numpy as np


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


class SyncOcrUtils:

    # OCR识别 带掩码 apply_mask================
    @auto_cleanup
    def ocr_scan_sync(self, region_params, min_confidence=0.5, window_target=None, pre_frame=2):
        """
        合二为一：计算区域 -> 截取ROI -> 掩码预处理 -> PaddleOCR预测 -> 坐标还原
        严格保留原代码逻辑，仅增加外层超时控制
        """
        try:
            # 1. 获取最新帧 (增加队列超时，防止推流断开导致永久阻塞)
            frame = self.obs_source.get_frame()
            if frame is None: return None

            # 2. 计算扫描区域
            scan_region = self.calculate_scan_region_ocr(region_params, window_target)
            if not scan_region: return None

            x1, y1, x2, y2 = scan_region
            h, w = frame.shape[:2]

            # 3. 核心逻辑：强制转换为 int，确保切片下标合法
            ix1, iy1 = int(max(0, x1)), int(max(0, y1))
            ix2, iy2 = int(min(w, x2)), int(min(h, y2))

            # 4. 截取 ROI 并应用掩码
            roi = frame[iy1:iy2, ix1:ix2]
            if roi.size == 0:
                return None

            processed_roi = None
            if pre_frame == 1:
                processed_roi = self.ocr_apply_mask(roi)
            elif pre_frame == 2:
                processed_roi = self.ocr_apply_clarity_mask(roi)
            elif pre_frame == 3:
                processed_roi = self.ocr_apply_color_mask(roi)

            results = self.ocr_engine.predict(processed_roi)
            if not results:
                return None

            all_results = []
            for item in results:
                # 严格保留 PaddleOCR 默认返回格式处理逻辑
                polys = item.get("dt_polys", [])
                texts = item.get("rec_texts", [])
                scores = item.get("rec_scores", [])

                for poly, text, score in zip(polys, texts, scores):
                    if score < min_confidence:
                        continue

                    poly_np = np.array(poly, dtype=int)
                    # 坐标还原：严格保留原有的起始偏移量加法
                    res_x1 = int(poly_np[:, 0].min() + ix1)
                    res_y1 = int(poly_np[:, 1].min() + iy1)
                    res_x2 = int(poly_np[:, 0].max() + ix1)
                    res_y2 = int(poly_np[:, 1].max() + iy1)

                    all_results.append({
                        "text": text,
                        "score": float(score),
                        "bbox": {"x1": res_x1, "y1": res_y1, "x2": res_x2, "y2": res_y2}
                    })

            if all_results:
                return {"all_results": all_results}

            # 如果没识别到，会在 while 循环内继续，直到超时
        except Exception as e:
            print(f"OCR识别异常: {e}")
            # 异常时稍微休息避免 CPU 飙升
            return None
        finally:
            # --- 内存优化：显式销毁当前帧 ---
            if 'frame' in locals():
                del frame
            # ---------------------------

    # 1。提高清晰度带锐化 ocr滤镜====================
    @auto_cleanup
    def ocr_apply_mask(self, roi):
        """
        核心预处理：使用简单卷积核进行图像锐化，增强清晰度
        """
        try:
            if roi is None or roi.size == 0:
                return roi

            # 定义一个简单的锐化卷积核
            # 中心值 5 减去四周的 1，保持能量守恒的同时增强边缘
            kernel = np.array([[0, -1, 0],
                               [-1, 5, -1],
                               [0, -1, 0]])

            # 使用 filter2D 进行卷积操作
            # -1 表示输出图像深度与原图一致
            sharpened_roi = cv2.filter2D(roi, -1, kernel)

            # 保存调试图像观察锐化效果
            # self.save_debug_image(roi, sharpened_roi)

            return sharpened_roi

        except Exception as e:
            print(f"【DEBUG】简单锐化预处理报错: {e}")
            return roi

    # 2。提高清晰度带锐化  黑白 ocr滤镜==============
    @auto_cleanup
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

            # 保存调试图
            # self.save_debug_image(roi, processed_roi)

            return processed_roi

        except Exception as e:
            print(f"❌ 【ocr_apply_clarity_mask 异常】: {e}")
            return roi

    # 3。特定颜色过滤 ocr滤镜
    @auto_cleanup
    def ocr_apply_color_mask(self, roi, color_name='yellow'):
        """
        使用调试工具导出的精确值进行颜色过滤。
        支持红色双色域合并，解决识别不全问题。
        """
        if roi is None or roi.size == 0:
            return roi

        try:
            # 1. 转换到 HSV 空间
            hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)

            # 2. 应用调试工具导出的值
            if color_name == 'yellow':
                lower = np.array([21, 26, 96])
                upper = np.array([39, 167, 255])
                mask = cv2.inRange(hsv, lower, upper)

            elif color_name == 'red':
                lower = np.array([0, 70, 15])
                upper = np.array([5, 201, 240])
                mask = cv2.inRange(hsv, lower, upper)
            else:
                return roi

            # 4. 应用掩码并亮度补偿
            # 只保留 mask 区域的颜色，背景变黑
            res = cv2.bitwise_and(roi, roi, mask=mask)

            # 亮度补偿：alpha 是对比度，beta 是亮度
            # 这一步能让抠出来的字在 OCR 引擎眼里更“显眼”
            processed_roi = cv2.convertScaleAbs(res, alpha=1.3, beta=15)

            return processed_roi

        except Exception as e:
            print(f"❌ 【ocr_apply_color_mask 异常】: {e}")
            return roi

    # 单纯的ocr识别=================
    @auto_cleanup
    def ocr_pure_predict(self, image_obj, min_confidence=0.5, pre_frame=2):
        """
        纯粹 OCR 识别：接收图片对象，返回识别结果。
        格式严格对标原 ocr_scan_sync，方便直接对接原有的分拣逻辑。
        """
        if image_obj is None or image_obj.size == 0:
            return None

        try:
            # 1. 应用预处理 (保留原逻辑，pre_frame=3 效果最好)
            processed_img = image_obj
            if pre_frame == 1:
                processed_img = self.ocr_apply_mask(image_obj)
            elif pre_frame == 2:
                processed_img = self.ocr_apply_clarity_mask(image_obj)
            # 2. 执行 OCR 引擎预测
            # with self.gpu_lock:
            #     # 假设你的引擎是 PaddleOCR 或类似的 predict 接口
            #     results = self.ocr_engine.predict(processed_img)
            results = self.ocr_engine.predict(processed_img)
            if not results:
                return None

            all_results = []
            for item in results:
                texts = item.get("rec_texts", [])
                scores = item.get("rec_scores", [])
                polys = item.get("dt_polys", [])

                for poly, text, score in zip(polys, texts, scores):
                    if score < min_confidence:
                        continue

                    # 计算局部坐标
                    poly_np = np.array(poly, dtype=int)

                    # 严格按照你原来的格式：all_results 列表 -> 字典 -> text/score/bbox
                    all_results.append({
                        "text": str(text),
                        "score": float(score),
                        "bbox": {
                            "x1": int(poly_np[:, 0].min()),
                            "y1": int(poly_np[:, 1].min()),
                            "x2": int(poly_np[:, 0].max()),
                            "y2": int(poly_np[:, 1].max())
                        }
                    })

            # 严格保留原代码返回格式
            if all_results:
                return {"all_results": all_results}

            return None

        except Exception as e:
            print(f"❌ 纯粹OCR识别异常: {e}")
            return None

    # ocr识别图片拼接函数 横向拼接=================
    @auto_cleanup
    def get_combined_roi_image_horizontal(self, regions, window_target):
        """
        根据 regions 自动计算基准高度并水平拼接，严格对齐 location.py 标注精度。
        """
        frame = self.obs_source.get_frame()
        if frame is None or not window_target: return None

        # 1. 获取窗口物理属性
        wx1, wy1 = window_target['x1'], window_target['y1']
        ww = window_target['x2'] - wx1
        wh = window_target['y2'] - wy1
        h_img, w_img = frame.shape[:2]

        raw_rois = []

        # --- 第一步：提取所有原始 ROI 并记录坐标 ---
        for reg in regions:
            # 使用 location.py 的逆运算逻辑进行纠偏
            # 公式：起点 + round(比例 * 跨度)
            rx1 = wx1 + round(reg[0] * ww)
            ry1 = wy1 + round(reg[1] * wh)
            rx2 = wx1 + round(reg[2] * ww)
            ry2 = wy1 + round(reg[3] * wh)

            # 边界安全限位
            ix1, iy1 = int(max(0, rx1)), int(max(0, ry1))
            ix2, iy2 = int(min(w_img, rx2)), int(min(h_img, ry2))

            roi = frame[iy1:iy2, ix1:ix2].copy()
            if roi.size > 0:
                raw_rois.append(roi)

        if not raw_rois:
            return None

        # --- 第二步：动态确定基准高度 ---
        # 取所有截块中最高的那一个作为拼接基准高度
        max_h = max(roi.shape[0] for roi in raw_rois)

        # 限制一个最小基准高度（可选，防止全是细长条导致显示太小）
        base_h = max(32, max_h)

        processed_rois = []
        # 定义自适应宽度的隔离带（黑色像素）
        separator_w = 15
        separator = np.zeros((base_h, separator_w, 3), dtype=np.uint8)

        # --- 第三步：等比例缩放并对齐高度 ---
        for i, roi in enumerate(raw_rois):
            orig_h, orig_w = roi.shape[:2]

            # 计算等比例缩放后的宽度：新宽 = 原始宽 * (基准高 / 原始高)
            aspect_ratio = orig_w / orig_h
            target_w = int(base_h * aspect_ratio)

            # 缩放至基准高度
            resized = cv2.resize(roi, (target_w, base_h), interpolation=cv2.INTER_CUBIC)
            processed_rois.append(resized)

            # 插入隔离带
            if i < len(raw_rois) - 1:
                processed_rois.append(separator)

        # --- 第四步：最终拼接 ---
        combined_img = np.hstack(processed_rois)
        return combined_img

    # ocr识别图片拼接函数 纵向拼接 =================
    @auto_cleanup
    def get_combined_roi_image_vertical(self, regions, window_target):
        """
        纵向拼接优化版：
        1. 严格对齐 location.py 的 round 纠偏逻辑。
        2. 自动获取 regions 中最宽的 ROI 作为画布基准宽度，防止文字被切断。
        """
        frame = self.obs_source.get_frame()
        if frame is None or not window_target:
            return None

        # 1. 获取窗口物理属性
        wx1, wy1 = window_target['x1'], window_target['y1']
        ww = window_target['x2'] - wx1
        wh = window_target['y2'] - wy1
        h_img, w_img = frame.shape[:2]

        raw_rois = []

        # --- 第一步：按照 location.py 逻辑精准提取 ROI ---
        for reg in regions:
            # 逆运算逻辑：起点 + round(比例 * 跨度)
            rx1 = wx1 + round(reg[0] * ww)
            ry1 = wy1 + round(reg[1] * wh)
            rx2 = wx1 + round(reg[2] * ww)
            ry2 = wy1 + round(reg[3] * wh)

            # 转换为整数切片坐标并做边界限位
            ix1, iy1 = int(max(0, rx1)), int(max(0, ry1))
            ix2, iy2 = int(min(w_img, rx2)), int(min(h_img, ry2))

            roi = frame[iy1:iy2, ix1:ix2].copy()
            if roi.size > 0:
                raw_rois.append(roi)

        if not raw_rois:
            return None

        # --- 第二步：计算基准宽度 ---
        # 动态获取所有截块中的最大宽度，确保没有任何文字被裁剪
        max_w = max(roi.shape[1] for roi in raw_rois)
        base_w = max(180, max_w)  # 至少保证 180 宽，或者以最宽的为准

        processed_rois = []
        # 定义自适应高度的隔离带（黑色像素线）
        separator_h = 5
        separator = np.zeros((separator_h, base_w, 3), dtype=np.uint8)

        # --- 第三步：对齐宽度并贴入画布 ---
        for i, roi in enumerate(raw_rois):
            roi_h, roi_w = roi.shape[:2]

            # 创建一个与基准宽度一致的黑色画布
            canvas = np.zeros((roi_h, base_w, 3), dtype=np.uint8)

            # 将原图贴入画布左侧（保留 100% 原始像素，不拉伸）
            # 这样处理比 cv2.resize 更好，因为 OCR 识别原始像素最准
            copy_w = min(roi_w, base_w)
            canvas[0:roi_h, 0:copy_w] = roi[:, 0:copy_w]

            processed_rois.append(canvas)

            # 插入隔离带
            if i < len(raw_rois) - 1:
                processed_rois.append(separator)

        # --- 第四步：垂直拼接 ---
        # 所有块的宽度现在都是 base_w，可以直接 vstack
        combined_img = np.vstack(processed_rois)
        return combined_img

    # ocr计算相对区域====================
    @auto_cleanup
    def calculate_scan_region_ocr(self, region_params, window_target):
        """
        根据当前识别到的目标进行物理还原。
        """
        if not window_target: return None

        # 1. 获取实时目标的物理位置 (YOLO给出的准基准)
        wx1, wy1 = window_target['x1'], window_target['y1']
        ww = window_target['x2'] - wx1
        wh = window_target['y2'] - wy1

        # 2. 核心：基于实时宽高的像素级还原
        # 比例参数 region_params 是 (rx1, ry1, rx2, ry2)
        # 必须先乘比例再 round，最后加起点，防止误差累积
        res_x1 = wx1 + round(region_params[0] * ww)
        res_y1 = wy1 + round(region_params[1] * wh)
        res_x2 = wx1 + round(region_params[2] * ww)
        res_y2 = wy1 + round(region_params[3] * wh)

        return int(res_x1), int(res_y1), int(res_x2), int(res_y2)
