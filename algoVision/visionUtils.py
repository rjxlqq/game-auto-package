import gc
import os
from datetime import datetime
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


class VisionUtils:

    # 区域扫描 模板匹配方案 带相对区域
    @auto_cleanup
    def detect_region_template_match_sync(self, template_img, region_params, threshold=0.8, window_target=None):
        """
        仿照 detect_region_target_classify_sync 编写的模板匹配函数
        :param template_img: image路径
        :param region_params: 扫描区域比例 (rx1, ry1, rx2, ry2)
        :param threshold: 相似度阈值 (0-1)
        :param window_target: 游戏窗口的基础坐标字典 (含有 x1, y1, x2, y2)
        :return: 类似 YOLO 格式的标准坐标字典
        """
        print('区域扫描 模板匹配方案 带相对区域-')
        # 1. 计算扫描区域坐标 (复用你现有的计算逻辑)
        scan_region = self.calculate_scan_region_sync(region_params, window_target)
        if not scan_region: return None
        roi_x1, roi_y1, roi_x2, roi_y2 = scan_region
        image = cv2.imread(template_img)
        # 2. 获取当前帧并裁剪 ROI
        frame = self.obs_source.get_frame()
        if frame is None or image is None: return None
        # 边界安全检查并裁剪
        roi = frame[roi_y1:roi_y2, roi_x1:roi_x2]
        if roi.size == 0: return None
        try:
            # 3. 执行模板匹配 (使用归一化相关系数匹配法)
            res = cv2.matchTemplate(roi, image, cv2.TM_CCOEFF_NORMED)
            min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)

            # 4. 判断是否超过阈值
            if max_val >= threshold:
                th, tw = image.shape[:2]

                # 5. 坐标还原：将 ROI 内的局部坐标还原为全局屏幕坐标
                # max_loc 是匹配到的左上角在 ROI 里的位置
                abs_x1 = max_loc[0] + roi_x1
                abs_y1 = max_loc[1] + roi_y1
                abs_x2 = abs_x1 + tw
                abs_y2 = abs_y1 + th

                # 6. 构造与你的脚本兼容的标准返回格式
                result = {
                    "class_name": "template_match",
                    "confidence": round(float(max_val), 4),
                    "x1": int(abs_x1),
                    "y1": int(abs_y1),
                    "x2": int(abs_x2),
                    "y2": int(abs_y2),
                    "center_x": int((abs_x1 + abs_x2) / 2),
                    "center_y": int((abs_y1 + abs_y2) / 2)
                }

                # 可选：保存调试图（复用你现有的 save_debug_image）
                # self.save_debug_image_single(roi)
                return result

        except Exception as e:
            print(f"❌ 模板匹配运行异常: {e}")
            return None
        finally:
            # --- 内存优化：显式销毁当前帧 ---
            if 'frame' in locals():
                del frame
            # ---------------------------

    # 窗口全域扫描 模板匹配方案
    @auto_cleanup
    def detect_window_template_match_sync(self, template_img, threshold=0.8, window_target=None):
        """
        在指定的窗口全范围内执行模板匹配
        :param template_img: image路径
        :param threshold: 相似度阈值 (0-1)
        :param window_target: 游戏窗口的坐标字典 (含有 x1, y1, x2, y2)
        :return: 兼容标准格式的坐标字典
        """
        print('窗口全域扫描 模板匹配方案')
        image = cv2.imread(template_img)
        frame = self.obs_source.get_frame()
        if frame is None or image is None: return None

        # 1. 确定扫描边界：如果没有传 window_target，则默认使用全屏
        if window_target:
            wx1 = max(0, int(window_target.get('x1', 0)))
            wy1 = max(0, int(window_target.get('y1', 0)))
            wx2 = min(frame.shape[1], int(window_target.get('x2', frame.shape[1])))
            wy2 = min(frame.shape[0], int(window_target.get('y2', frame.shape[0])))
        else:
            # 如果没传，则搜索整个当前帧
            wx1, wy1, wx2, wy2 = 0, 0, frame.shape[1], frame.shape[0]

        # 2. 裁剪窗口区域 ROI
        roi = frame[wy1:wy2, wx1:wx2]
        if roi.size == 0: return None
        # self.save_debug_image_single(roi)
        # 获取尺寸用于安全检查
        roi_h, roi_w = roi.shape[:2]
        tpl_h, tpl_w = image.shape[:2]

        # 【安全检查】防止模板比窗口还大导致崩溃
        if roi_h < tpl_h or roi_w < tpl_w:
            print(f"⚠️ 窗口区域({roi_w}x{roi_h})小于模板({tpl_w}x{tpl_h})")
            return None
        try:
            # 3. 执行模板匹配
            res = cv2.matchTemplate(roi, image, cv2.TM_CCOEFF_NORMED)
            _, max_val, _, max_loc = cv2.minMaxLoc(res)

            if max_val >= threshold:
                # 4. 还原坐标到全局屏幕
                abs_x1 = max_loc[0] + wx1
                abs_y1 = max_loc[1] + wy1
                abs_x2 = abs_x1 + tpl_w
                abs_y2 = abs_y1 + tpl_h

                # 5. 返回标准结果格式
                return {
                    "class_name": "window_template_match",
                    "confidence": round(float(max_val), 4),
                    "x1": int(abs_x1),
                    "y1": int(abs_y1),
                    "x2": int(abs_x2),
                    "y2": int(abs_y2),
                    "center_x": int((abs_x1 + abs_x2) / 2),
                    "center_y": int((abs_y1 + abs_y2) / 2)
                }

        except Exception as e:
            print(f"❌ 窗口模板匹配异常: {e}")
            return None
        finally:
            # --- 内存优化：显式销毁当前帧 ---
            if 'frame' in locals():
                del frame
            # ---------------------------

    # 图片区域涂黑操作
    @auto_cleanup
    def apply_blackout_masks(self, image, blackout_params):
        """
        对给定的图像进行多区域涂黑遮盖。
        :param image: numpy 数组 (ROI 图像)
        :param blackout_params: 支持以下格式:
            1. 单个比例坐标元组: (x1, y1, x2, y2)
            2. 比例坐标列表/数组: [(x1, y1, x2, y2), [x1, y1, x2, y2], ...]
        :return: 处理后的图像副本
        """
        if blackout_params is None:
            return image

        # 确保操作的是副本，不影响原始帧流
        processed_img = image.copy()
        rh, rw = processed_img.shape[:2]

        # --- 核心改进：标准格式化输入 ---
        # 如果传入的是单个元组 (x1,y1,x2,y2)，转为列表格式进行统一迭代
        if isinstance(blackout_params, (list, tuple)) and len(blackout_params) > 0:
            # 检查第一个元素是不是数字，如果是，说明传的是单个区域
            if not isinstance(blackout_params[0], (list, tuple)):
                blackout_list = [blackout_params]
            else:
                blackout_list = blackout_params
        else:
            return processed_img

        # 遍历数组中的每一个遮罩区域
        for box in blackout_list:
            if len(box) == 4:
                bx1, by1, bx2, by2 = box

                # 比例转像素坐标并进行边界限位 (0.0 - 1.0 -> 像素)
                start_x = max(0, int(rw * bx1))
                start_y = max(0, int(rh * by1))
                end_x = min(rw, int(rw * bx2))
                end_y = min(rh, int(rh * by2))

                # 只有当计算出的区域合法时才执行切片操作
                if end_x > start_x and end_y > start_y:
                    # NumPy 切片快速涂黑 (0,0,0) 代表 BGR 黑色
                    processed_img[start_y:end_y, start_x:end_x] = 0

        return processed_img

    # 查找特定颜色字体  加强文字字快的识别 - 返回多个色块  blackout_params 是截取的图片的相对位置\
    @auto_cleanup
    def find_color_text_regions_precise(self, region_params, color_name='yellow', window_target=None, isMask=False, blackout_params=None):
        try:
            # 1. 常规 ROI 截取 (沿用你原有的逻辑)
            scan_region = self.calculate_scan_region_sync(region_params, window_target)
            if not scan_region: return []
            rx1, ry1, rx2, ry2 = scan_region
            frame = self.obs_source.get_frame()
            if frame is None: return []
            roi = frame[int(ry1):int(ry2), int(rx1):int(rx2)]
            if roi.size == 0: return []

            # 2. 颜色提取
            hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
            if color_name == 'yellow':
                lower = np.array([28, 60, 60])
                upper = np.array([38, 255, 255])
            elif color_name == 'red':
                lower = np.array([0, 70, 15])
                upper = np.array([5, 201, 240])
            else:
                return []

            mask = cv2.inRange(hsv, lower, upper)

            # 3. 掩码遮盖
            if isMask:
                mask = self.apply_blackout_masks(mask, blackout_params)
            # self.save_debug_image_single(mask)
            # 4. 【精准形态学】专治长条文字
            # 先用横向长条核进行闭运算，连接间断的字
            h_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (40, 2))
            mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, h_kernel)

            # 再进行轻微膨胀，加固边缘
            mask = cv2.dilate(mask, np.ones((2, 2), np.uint8), iterations=1)

            # 5. 轮廓筛选
            contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            results = []

            for cnt in contours:
                x, y, w, h = cv2.boundingRect(cnt)
                aspect_ratio = w / float(h)
                area = cv2.contourArea(cnt)

                # --- 精准过滤闸门 ---
                # 过滤1: 面积太小不是字
                if area < 40: continue
                # 过滤2: 必须是横向长条状 (宽度至少是高度的 1.5 倍)
                if aspect_ratio < 1.5: continue
                # 过滤3: 物理尺寸限制 (防止误判巨大的黄色背景块)
                if h > 60 or w < 20: continue

                results.append({
                    'class_name': f"{color_name}_text",
                    'x1': int(rx1 + x),
                    'y1': int(ry1 + y),
                    'x2': int(rx1 + x + w),
                    'y2': int(ry1 + y + h),
                    'center_x': int(rx1 + x + w / 2),
                    'center_y': int(ry1 + y + h / 2),
                    'w': w,
                    'h': h,
                    'ratio': round(aspect_ratio, 2)
                })

            # 按从上到下排序，符合人类阅读习惯
            results.sort(key=lambda x: x['y1'])
            return results

        except Exception as e:
            print(f"❌ 精准多色块定位异常: {e}")
            return []

    # 保存图片
    @auto_cleanup
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

    # 保存图片
    @auto_cleanup
    def save_debug_image_single(self, original):
        """仅保存原始图像文件"""
        try:
            save_dir = "debug_frame"
            # 1. 确保目录存在
            if not os.path.exists(save_dir):
                os.makedirs(save_dir)
            # 2. 生成精确到毫秒的时间戳作为文件名
            timestamp = datetime.now().strftime("%H%M%S_%f")[:-3]
            # 3. 设置保存路径
            save_path = os.path.join(save_dir, f"{timestamp}.jpg")
            # 4. 执行写入
            cv2.imwrite(save_path, original)

        except Exception as e:
            print(f"❌ 保存图片失败: {e}")

    # 计算汉明距离 ，值越小表示图片越相似
    @auto_cleanup
    def get_hamming_distance(self, h1, h2):
        """计算汉明距离，值越小表示图片越相似"""
        if not h1 or not h2: return 999
        return sum(c1 != c2 for c1, c2 in zip(h1, h2))

    # 当前帧截取目标区域并计算感知哈希
    @auto_cleanup
    def get_image_phash(self, target):
        """
        从当前帧截取目标区域并计算感知哈希 (pHash)
        :param target: 包含 y1, y2, x1, x2 坐标的字典
        :return: 64位哈希字符串 或 None
        """
        try:
            # 1. 直接从 OBS 源获取最新的全屏帧
            frame = self.obs_source.get_frame()
            if frame is None: return None

            # 2. 核心：根据传入的 target 坐标进行物理截取 (ROI)
            # 注意：Numpy 索引是 [y_start:y_end, x_start:x_end]
            roi_img = frame[target['y1']:target['y2'], target['x1']:target['x2']]

            if roi_img.size == 0:
                return None

            # 3. 计算 pHash 算法流程
            img = cv2.resize(roi_img, (32, 32))
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            dct = cv2.dct(np.float32(gray))
            dct_low = dct[0:8, 0:8]
            avg = dct_low.mean()
            return ''.join(['1' if x > avg else '0' for x in dct_low.flatten()])
        except Exception as e:
            print(f"提取图像哈希失败: {e}")
            return None
