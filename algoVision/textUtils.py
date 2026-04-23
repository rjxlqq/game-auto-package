from difflib import SequenceMatcher

import torch


class TextUtils:
    # 根据相对区域计算绝对位置 返回中心点  方便点击=============
    def calc_absolute_coords(self, target_class=None, region_params=None):
        if target_class and region_params:
            x1, y1, x2, y2 = target_class['x1'], target_class['y1'], target_class['x2'], target_class['y2']
            width = x2 - x1
            height = y2 - y1
            # 你提供的点击区域相对比例 (rel_x1, rel_y1, rel_x2, rel_y2)
            rx1, ry1, rx2, ry2 = region_params
            # 计算该相对区域中心点在屏幕上的绝对像素坐标
            # 原理：窗口起点 + (窗口宽度 * 相对比例的中点)
            target_pixel_x = x1 + width * (rx1 + rx2) / 2
            target_pixel_y = y1 + height * (ry1 + ry2) / 2
            return target_pixel_x, target_pixel_y

    # 坐标范围判断===================
    def is_at_location(self, current_pos_str, target_pos_str, offset=10):
        """
        比较两组坐标是否在误差范围内
        current_pos_str: 当前位置，格式 "100,200"
        target_pos_str:  目标位置，格式 "105,205"
        """
        try:
            # 1. 解析当前坐标
            if not current_pos_str or "," not in current_pos_str: return False
            curr_parts = current_pos_str.split(",")
            curr_x = int(float(curr_parts[0].strip()))
            curr_y = int(float(curr_parts[1].strip()))
            # 2. 解析目标坐标
            if not target_pos_str or "," not in target_pos_str:
                return False
            t_parts = target_pos_str.split(",")
            t_x = int(float(t_parts[0].strip()))
            t_y = int(float(t_parts[1].strip()))
            # 3. 计算差距
            diff_x = abs(curr_x - t_x)
            diff_y = abs(curr_y - t_y)
            # print(f"📏 距离比对: 当前({curr_x}, {curr_y}) vs 目标({t_x}, {t_y}) | 偏差:({diff_x}, {diff_y})")
            # 4. 判定
            if diff_x <= offset and diff_y <= offset: return True

        except (ValueError, TypeError, IndexError) as e:
            # print(f"⚠️ 坐标格式错误: {e}")
            pass

        return False

    # 文本存在函数  返回匹配到的值 =================
    def check_text_exists_logic(self, data, target_text, threshold=0.7):
        """
        精准匹配逻辑：
        1. 过滤低于 threshold 置信度的 OCR 结果。
        2. 判断 target_text 是否存在于文本行中。
        3. 如果存在，根据索引位置精确切分出目标文字的坐标。
        """
        if not isinstance(data, dict): return {}

        results_list = data.get('all_results', [])
        if not isinstance(results_list, list): return {}

        matched_results = []

        for item in results_list:
            # --- 新增：置信度过滤 ---
            # 只有 OCR 原始识别置信度达标才处理，确保数据可靠性
            current_conf = item.get('score', 0)
            if current_conf < threshold:
                continue

            current_text = item.get('text', '')

            # 1. 查找目标文字在整行中的起始索引
            start_idx = current_text.find(target_text)

            if start_idx != -1:
                # 2. 获取整行的包围框数据
                full_box = item.get('bbox', {})
                if not full_box:
                    continue

                x1, x2 = full_box['x1'], full_box['x2']
                total_chars = len(current_text)
                target_len = len(target_text)

                # 3. 核心算法：按字符比例切分坐标
                # 计算单个字符占据的物理像素宽度
                char_width = (x2 - x1) / total_chars

                # 计算目标子字符串在行内的起始与结束 X 坐标
                target_x1 = x1 + (start_idx * char_width)
                target_x2 = target_x1 + (target_len * char_width)

                # 4. 构建新的匹配对象
                # 拷贝原对象以保留其他字段，但更新坐标为目标文字的精准坐标
                new_item = item.copy()
                new_item['bbox'] = {
                    'x1': int(target_x1),
                    'y1': full_box['y1'],
                    'x2': int(target_x2),
                    'y2': full_box['y2']
                }
                # 标记匹配置信度为 1.0 (表示包含关系确立)
                new_item['match_confidence'] = 1.0
                matched_results.append(new_item)

        # 5. 调用转换函数返回标准格式
        # 最终返回结果中的 center_x/y 将指向目标文字的正中心而非整行中心
        return self.transform_single_ocr_result(matched_results, target_text)

    # 文本存在函数（支持多关键字匹配 - 顺序优先版） =================
    def check_text_exists_logic_more(self, data, target_texts, threshold=0.7):
        """
        精准匹配逻辑（顺序增强版）：
        1. 严格按照 target_texts 列表中的先后顺序进行全图匹配。
        2. 只有当前一个关键字在全图中都没找到时，才会查找下一个关键字。
        """
        if not isinstance(data, dict): return {}

        # 统一转为列表处理，兼容单字符串输入
        if isinstance(target_texts, str):
            target_texts = [target_texts]

        results_list = data.get('all_results', [])
        if not isinstance(results_list, list): return {}

        # --- 关键修改：外层循环遍历关键字，确保匹配顺序 ---
        for target in target_texts:

            # 内层循环遍历 OCR 识别出的每一行结果
            for item in results_list:
                # 置信度过滤
                current_conf = item.get('score', 0)
                if current_conf < threshold:
                    continue

                current_text = item.get('text', '')

                # 在当前行中查找当前关键字
                start_idx = current_text.find(target)

                if start_idx != -1:
                    # 找到匹配项，计算精准坐标
                    full_box = item.get('bbox', {})
                    if not full_box: continue

                    x1, x2 = full_box['x1'], full_box['x2']
                    total_chars = len(current_text)
                    target_len = len(target)

                    # 按字符比例切分 X 坐标
                    char_width = (x2 - x1) / total_chars
                    target_x1 = x1 + (start_idx * char_width)
                    target_x2 = target_x1 + (target_len * char_width)

                    # 构建匹配对象
                    new_item = item.copy()
                    new_item['bbox'] = {
                        'x1': int(target_x1),
                        'y1': full_box['y1'],
                        'x2': int(target_x2),
                        'y2': full_box['y2']
                    }
                    new_item['match_confidence'] = 1.0

                    print(f"🎯 优先级匹配成功: [{target}] 位于行 [{current_text}]")

                    # 找到当前优先级最高的关键字后，立即返回
                    return self.transform_single_ocr_result([new_item], target)

        # 只有当列表里所有关键字都在全图中找了一遍都没结果，才返回空
        return {}

    # 文本近似匹配函数========
    def find_approximate_targets(self, data, target_text, threshold=0.7):
        """
        高级近似匹配函数：
        1. 相似度检测 (模糊识别兜底)
        2. 字符串切片坐标计算 (精准点击定位)
        3. 全局数据结构安全防护
        """
        if data is None or target_text is None or not isinstance(data, dict):
            return None

        results_list = data.get('all_results', [])
        if not isinstance(results_list, list):
            return None

        matched_results = []

        for item in results_list:
            if not isinstance(item, dict): continue

            current_text = item.get('text', '')
            if not current_text: continue

            # --- 1. 相似度与包含判定 ---
            # 使用 SequenceMatcher 计算 0~1 的相似度
            similarity = SequenceMatcher(None, target_text, current_text).ratio()

            # 记录索引，用于后续切片
            start_idx = current_text.find(target_text)

            if similarity >= threshold or start_idx != -1:
                # 拷贝原对象，准备进行坐标修正
                new_item = item.copy()
                full_box = item.get('bbox', {})

                if full_box and len(current_text) > 0:
                    # --- 2. 核心：字符串切片坐标处理 ---
                    x1, x2 = full_box['x1'], full_box['x2']
                    total_chars = len(current_text)

                    # 如果是包含关系，按实际索引切片；如果是模糊匹配，默认取匹配相似度最高的区域或中心
                    # 这里优先处理包含关系的切片，如果纯相似，则指向原 bbox 中心
                    if start_idx != -1:
                        char_width = (x2 - x1) / total_chars
                        target_len = len(target_text)

                        target_x1 = x1 + (start_idx * char_width)
                        target_x2 = target_x1 + (target_len * char_width)

                        new_item['bbox'] = {
                            'x1': int(target_x1),
                            'y1': full_box['y1'],
                            'x2': int(target_x2),
                            'y2': full_box['y2']
                        }

                    new_item['match_confidence'] = round(similarity, 2)
                    matched_results.append(new_item)

        if not matched_results:
            return None

        # --- 3. 返回转换后的标准格式 ---
        # 返回格式包含: class_name, confidence, x1, y1, x2, y2, center_x, center_y
        return self.transform_single_ocr_result(matched_results, target_text)

    # 将单个 OCR 结果项转换为指定的对象格式=============
    def transform_single_ocr_result(self, ocr_list, class_name):
        """
        将单个 OCR 结果项转换为指定的对象格式
        """
        if not ocr_list or len(ocr_list) == 0:
            return {}

        # 获取列表中的第一个元素
        item = ocr_list[0]
        bbox = item['bbox']

        # 计算中心点坐标
        # 公式: center = (min + max) / 2
        center_x = (bbox['x1'] + bbox['x2']) // 2
        center_y = (bbox['y1'] + bbox['y2']) // 2

        # 构造输出格式
        output = {
            'class_name': class_name,
            'confidence': round(item.get('score', 0), 4),
            'x1': bbox['x1'],
            'y1': bbox['y1'],
            'x2': bbox['x2'],
            'y2': bbox['y2'],
            'center_x': center_x,
            'center_y': center_y
        }
        return output

    # 计算窗口大小
    def get_window_size(self, detection_result):
        """
        根据目标检测结果计算窗口的宽度和高度
        :param detection_result: 包含 x1, y1, x2, y2 的字典
        :return: (width, height)
        """
        # 提取坐标
        x1 = detection_result.get('x1', 0)
        y1 = detection_result.get('y1', 0)
        x2 = detection_result.get('x2', 0)
        y2 = detection_result.get('y2', 0)

        # 计算宽高
        width = x2 - x1
        height = y2 - y1

        return width, height

    # 重置显存 ===============
    def reset_gpu_memory_service(self):
        """
        深度清理 GPU 显存碎片，为高频监测线程腾出空间
        建议在启动线程前、或更换地图后调用
        """
        try:
            # 1.清理 PyTorch 的显存缓存
            # PyTorch 默认会保留已释放的显存以方便下次分配，这会导致“碎片化”
            # empty_cache() 会将这些未使用的显存交还给 GPU
            if torch.cuda.is_available():
                # 记录清理前后的显存情况
                before_mem = torch.cuda.memory_reserved() / 1024 / 1024

                torch.cuda.empty_cache()
                torch.cuda.ipc_collect()  # 清理进程间通信残留的内存

                after_mem = torch.cuda.memory_reserved() / 1024 / 1024
                print(f"✨ 显存碎片清理完成: {before_mem:.1f}MB -> {after_mem:.1f}MB")
            else:
                print("⚠️ 未检测到 CUDA 环境，跳过 GPU 清理")

        except Exception as e:
            print(f"❌ 显存清理过程中出现异常: {e}")
