# syncDetectionUtils.py
import gc
from functools import wraps


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


global_size = 800
classify_size = 448


class SyncDetectorMixin:
    # 扫描所有目标 返回所有目标-----------
    @auto_cleanup
    def detect_all_targets_sync(self, min_confidence=0.5):
        frame = self.obs_source.get_frame()
        if frame is None: return None
        try:
            # self.save_debug_image_single(frame)
            results = list(self.global_model(frame, verbose=False, stream=True, imgsz=global_size, device=0))
            best_targets = self.get_best_parsed_results(results, min_confidence)
            return best_targets
        except Exception as e:
            print(f"❌ 目标检测流程异常: {e}")
            return None
        finally:
            # --- 内存优化：显式销毁当前帧 ---
            if 'frame' in locals():
                del frame
            # ---------------------------

    # 窗口内 全局扫描 返回最优目标--------
    @auto_cleanup
    def detect_target_sync(self, target_class, min_confidence=0.5):
        frame = self.obs_source.get_frame()
        if frame is None: return None
        try:
            # self.save_debug_image_single(frame)
            results = list(self.global_model(frame, verbose=False, stream=True, imgsz=global_size, device=0))
            best_targets = self.get_best_parsed_results(results, min_confidence)
            if best_targets and target_class in best_targets:
                return best_targets[target_class]
        except Exception as e:
            print(f"❌ 目标检测流程异常: {e}")
            return None
        finally:
            # --- 内存优化：显式销毁当前帧 ---
            if 'frame' in locals():
                del frame
            # ---------------------------

    # 区域扫描  小目标 返回所有目标-----------
    @auto_cleanup
    def detect_region_all_targets_sync(self, region_params, min_confidence=0.5, window_target=None):
        # 1. 计算扫描区域
        scan_region = self.calculate_scan_region_sync(region_params, window_target)
        if not scan_region: return None
        roi_x1, roi_y1, roi_x2, roi_y2 = scan_region
        # 2. 获取并裁剪帧
        frame = self.obs_source.get_frame()
        if frame is None: return None
        roi = frame[roi_y1:roi_y2, roi_x1:roi_x2]
        try:
            # self.save_debug_image_single(roi)
            results = list(self.classify_model(roi, verbose=False, stream=True, imgsz=classify_size, device=0))
            # 4. 解析结果
            best_targets = self.get_best_parsed_results(results, min_confidence)
            return best_targets
        except Exception as e:
            print(f"detect_region_all_targets_sync 运行异常: {e}")
            return None
        finally:
            # --- 内存优化：显式销毁当前帧 ---
            if 'frame' in locals():
                del frame
            # ---------------------------

    # 区域扫描  小目标 返回最优目标-----------
    @auto_cleanup
    def detect_region_target_classify_sync(self, target_class, region_params, min_confidence=0.5, window_target=None):
        # 1. 计算扫描区域
        scan_region = self.calculate_scan_region_sync(region_params, window_target)
        if not scan_region: return None
        roi_x1, roi_y1, roi_x2, roi_y2 = scan_region
        # 2. 获取并裁剪帧
        frame = self.obs_source.get_frame()
        if frame is None: return None
        roi = frame[roi_y1:roi_y2, roi_x1:roi_x2]
        try:
            # self.save_debug_image_single(roi)
            results = list(self.classify_model(roi, verbose=False, stream=True, imgsz=classify_size, device=0))
            # 4. 解析结果
            best_targets = self.get_best_parsed_results(results, min_confidence, offset_x=roi_x1, offset_y=roi_y1)
            if best_targets and target_class in best_targets:
                return best_targets[target_class]
        except Exception as e:
            print(f"detect_region_target_classify_sync 运行异常: {e}")
            return None
        finally:
            # --- 内存优化：显式销毁当前帧 ---
            if 'frame' in locals():
                del frame
            # ---------------------------

    # 区域扫描 小目标  返回所有的同一类型的目标-----------
    @auto_cleanup
    def detect_region_targets_classify_sync(self, target_class, region_params, min_confidence=0.5, window_target=None):
        # 1. 计算扫描区域
        scan_region = self.calculate_scan_region_sync(region_params, window_target)
        if not scan_region: return None
        roi_x1, roi_y1, roi_x2, roi_y2 = scan_region
        # 2. 获取并裁剪帧
        frame = self.obs_source.get_frame()
        if frame is None: return None
        roi = frame[roi_y1:roi_y2, roi_x1:roi_x2]
        try:
            # self.save_debug_image_single(roi)
            results = list(self.classify_model(roi, verbose=False, stream=True, imgsz=classify_size, device=0))
            # 4. 解析结果
            all_targets = self.get_all_parsed_results(results, target_class, min_confidence, offset_x=roi_x1, offset_y=roi_y1)
            return all_targets
        except Exception as e:
            print(f"detect_region_target_classify_sync 运行异常: {e}")
            return None
        finally:
            # --- 内存优化：显式销毁当前帧 ---
            if 'frame' in locals():
                del frame
            # ---------------------------

    # 区域扫描 小目标 返回当前界面frame上的小目标
    @auto_cleanup
    def detect_region_targets_classify_frame_sync(self, target_class, region_params=(0.001573, 0.857545, 0.477189, 1.001874), min_confidence=0.5):
        """
        同步识别指定比例区域内的特定类型目标。
        region_params: (x1_ratio, y1_ratio, x2_ratio, y2_ratio) 如 (0.0, 0.055, 0.028, 0.08)
        """
        # 1. 获取当前帧
        frame = self.obs_source.get_frame()
        if frame is None:
            return None

        # 2. 将归一化比例转换为像素坐标
        h, w = frame.shape[:2]
        roi_x1 = int(region_params[0] * w)
        roi_y1 = int(region_params[1] * h)
        roi_x2 = int(region_params[2] * w)
        roi_y2 = int(region_params[3] * h)

        # 3. 边界检查（防止比例越界或切片错误）
        roi_x1, roi_x2 = max(0, roi_x1), min(w, roi_x2)
        roi_y1, roi_y2 = max(0, roi_y1), min(h, roi_y2)

        if roi_x2 <= roi_x1 or roi_y2 <= roi_y1:
            return None

        # 4. 裁切 ROI
        roi = frame[roi_y1:roi_y2, roi_x1:roi_x2]

        try:
            # self.save_debug_image_single(roi)
            results = list(self.classify_model(roi, verbose=False, stream=True, imgsz=classify_size, device=0))
            # 6. 解析结果
            # 传入 target_class 过滤，同时传入还原坐标所需的像素偏移
            all_targets = self.get_all_parsed_results(
                results,
                target_class=target_class,
                min_confidence=min_confidence,
                offset_x=roi_x1,
                offset_y=roi_y1
            )
            return all_targets

        except Exception as e:
            print(f"detect_region_all_targets_sync 运行异常: {e}")
            return None
        finally:
            # --- 内存优化 ---
            if 'frame' in locals():
                del frame
            if 'roi' in locals():
                del roi

    # 获取单个最优目标 去重--------
    @auto_cleanup
    def get_best_parsed_results(self, results, min_confidence=0.5, offset_x=0, offset_y=0):
        """
        合二为一：解析 YOLO Results 并按类别提取置信度最高的目标
        返回格式: { '类别名': {'class_name':..., 'confidence':..., 'center_x':...}, ... }
        """
        if not results: return None
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

    # 返回多个目标，不去重--------------
    @auto_cleanup
    def get_all_parsed_results(self, results, target_class, min_confidence=0.5, offset_x=0, offset_y=0):
        """
        不去重解析：返回所有满足置信度条件的目标列表
        返回格式: [ {'class_name': '...', 'confidence': ...}, {...}, ... ]
        """
        if not results: return []
        all_targets = []
        try:
            # 遍历所有结果页 (兼容 stream=True)
            for r in results:
                if not hasattr(r, 'boxes') or r.boxes is None:
                    continue

                for box in r.boxes:
                    conf = float(box.conf.item())

                    # 1. 置信度过滤
                    if conf < min_confidence:
                        continue

                    class_id = int(box.cls.item())
                    name = r.names[class_id]
                    if target_class and name != target_class:
                        continue
                    # 2. 提取局部坐标
                    lx1, ly1, lx2, ly2 = box.xyxy[0].tolist()

                    # 3. 构造结果并直接 append 到列表 (不做类别判断，不覆盖)
                    item = {
                        "class_name": name,
                        "confidence": round(conf, 4),
                        "x1": int(lx1 + offset_x),  # 加上偏移量，直接给全局坐标
                        "y1": int(ly1 + offset_y),
                        "x2": int(lx2 + offset_x),
                        "y2": int(ly2 + offset_y),
                        "center_x": int((lx1 + lx2) / 2 + offset_x),
                        "center_y": int((ly1 + ly2) / 2 + offset_y)
                    }
                    all_targets.append(item)

        except Exception as e:
            print(f"❌ 目标全解析函数异常: {e}")
            return []

        return all_targets

    # yolo识别 计算相对区域 返回区域的位置 方便裁剪 --------------------
    @auto_cleanup
    def calculate_scan_region_sync(self, region_params, window_target):
        try:
            if not window_target or len(region_params) != 4: return None
            w_x1, w_y1 = window_target.get("x1", 0), window_target.get("y1", 0)
            width = window_target.get("x2", 0) - w_x1
            height = window_target.get("y2", 0) - w_y1
            r_x1, r_y1, r_x2, r_y2 = region_params
            return (w_x1 + int(width * r_x1), w_y1 + int(height * r_y1),
                    w_x1 + int(width * r_x2), w_y1 + int(height * r_y2))
        except Exception as e:
            print(f"计算区域异常: {e}")
            return None
