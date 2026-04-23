import gc
import re
import time

from PyQt5.QtCore import QThread, pyqtSignal


# --- 任务执行主线程 ---
class TaskStrategyThread(QThread):
    task_progress = pyqtSignal(str)

    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.running = True  # 线程是否在运行
        self.check_interval = 1  # 循环时间
        self.continue_interval = 0.5  # 中断事件
        self.count = 0  # 线程执行计数器
        self.finished_flag = 0  # 结束标志
        self.isCoord = False  # 是否开启坐标扫描
        self.status = None  # 坐标 地图信息

    def run(self):
        print("🚀 自动反应线程已启动...")
        while self.running:
            try:
                self.task_progress.emit("训练营")
                self.count += 1

                # 判断任务是否可以结束
                if self.finished_flag >= 5:
                    self.parent.is_task_running = False
                    self.finished_flag = 0
                    break

                # 识别所有的目标
                targets = self.parent.detect_all_targets_sync(min_confidence=0.6)

                print(targets, 'TaskStrategyThread', '训练营')

                if not targets:
                    self.parent.last_targets = None
                    time.sleep(self.continue_interval)
                    continue

                self.parent.last_targets = targets

                self.status = self.check_comprehensive_status(targets.get('游戏窗口'))
                if self.status["map"] == '魔族基地':
                    print('进入了魔族基地，执行打怪逻辑')
                    pass

                if self.status["map"] == '钢铁囚牢':
                    print('钢铁囚牢，，执行打怪逻辑')
                    pass

                # 发现联邦任务 即调用 on_toggle_upgrade_clicked函数
                if "NPC对话窗口" in targets:
                    self.parent.pause = True
                    self.npc_ocr_scan(targets.get('NPC对话窗口'))
                    time.sleep(self.continue_interval)
                    continue

                if "死亡窗口" in targets:
                    self.parent.pause = True
                    self.revive(targets.get('死亡窗口'))
                    time.sleep(self.continue_interval)
                    continue

                if "离开副本窗口" in targets:
                    self.parent.pause = True
                    if self.handle_exit_dungeon_logic(targets['离开副本窗口']):
                        self.finished_flag += 1
                    time.sleep(self.continue_interval)
                    continue

                if "雷恩" in targets:
                    self.parent.pause = True
                    self.click_npc(targets['雷恩'])
                    time.sleep(self.continue_interval)
                    continue

                time.sleep(self.check_interval)
            except Exception as e:
                print(f"⚠️ 反应线程报错: {e}")
                time.sleep(1)
            finally:
                if 'targets' in locals():
                    del targets

                if self.count % 60 == 0:
                    gc.collect()

                # 清除gpu碎片
                if self.count % 500 == 0:
                    self.parent.reset_gpu_memory_service()

                # 防止卡死
                if self.count == 1000:
                    self.parent.pause = False

                # count重置
                if self.count == 10000:
                    self.count = 0

    def stop(self):
        self.running = False
        self.wait()

    # 死亡后回城复活继续任务
    def revive(self, target):
        try:
            fh_ocr_res = self.parent.ocr_scan_sync((0.026578, 0.125926, 0.970100, 0.908642), min_confidence=0.6, window_target=target)
            if not fh_ocr_res: return False
            fh_matches = self.parent.check_text_exists_logic(fh_ocr_res, '回城复活')
            if not fh_matches: return False
            if not self.parent.move_mouse_to_target_human_lock(fh_matches['center_x'], fh_matches['center_y']): return False
            if not self.parent.mouse_quick_click('L'): return False
            return True
        except Exception as e:
            print(f'复活失败{e}')
        finally:
            print('复活暂停结束')
            self.parent.pause = False

    # NPC对话窗口执行逻辑
    def npc_ocr_scan(self, target):
        try:
            ocr_res = self.parent.ocr_scan_sync((0.010000, 0.087591, 1.006667, 0.990268), min_confidence=0.6, window_target=target)
            if not ocr_res: return False
            jugde = ['进入训练营', '接受任务']
            matches = self.parent.check_text_exists_logic_more(ocr_res, jugde, threshold=0.75)
            if not matches: return False
            if not self.parent.move_mouse_to_target_human_lock(matches["center_x"], matches["center_y"]): return False
            if not self.parent.mouse_quick_click('L'): return False
            return True
        except Exception as e:
            print(f'NPC对话窗口执行失败{e}')
        finally:
            print('NPC对话窗口暂停结束')
            self.parent.pause = False

    # 离开副本窗口
    def handle_exit_dungeon_logic(self, target):
        try:
            if not target: return False
            print('开始执行离开副本窗口窗口')
            target_pixel_x, target_pixel_y = self.parent.calc_absolute_coords(target, (0.293040, 0.663366, 0.725275, 0.920792))
            if not self.parent.move_mouse_to_target_human_lock(target_pixel_x, target_pixel_y): return False
            re_check = self.parent.detect_target_sync("离开副本窗口", min_confidence=0.8)
            if not re_check: return False
            if not self.parent.mouse_quick_click('L'): return False
            return True
        except Exception as e:
            print(f"❌ 自动点击离开副本窗口 执行异常: {e}")
            return False
        finally:
            print('自动点击离开副本窗口暂停结束')
            self.parent.pause = False

    # 找 npc 雷恩
    def click_npc(self, target):
        try:
            if not self.parent.move_mouse_to_target_human_lock(target['center_x'], target['center_y']): return False
            time.sleep(0.1)
            if not self.parent.mouse_quick_click('L'): return False
            return True
        except Exception as e:
            print(f"⚠️ 找人函数报错: {e}")
        finally:
            print('找人函数报错暂停结束')
            self.parent.pause = False


# --- 任务连接线程 ---
class TaskMissionThread(QThread):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.running = True
        self.continue_interval = 1  # 中断事件
        self.check_interval = 2  # 循环时间
        self.count = 0
        self.isCoord = True

    def run(self):
        print("🚀 任务连接线程已启动 (Q键任务逻辑)...")
        while self.running:
            try:
                if self.parent.pause:
                    time.sleep(self.continue_interval)
                    continue

                self.count += 1

                # 获取最新的识别结果
                targets = self.parent.last_targets

                if not targets:
                    time.sleep(self.continue_interval)
                    continue

                # 判断角色是否到达点位，如果到了则isCoord置为False,如果没有到则开始地图找人
                if self.isCoord:
                    status = self.check_comprehensive_status(targets.get('游戏窗口'))
                    if self.parent.is_at_location(status["coord"], '292,499', 10):
                        self.isCoord = False
                        time.sleep(self.continue_interval)
                        continue
                    else:
                        self.open_map()

                time.sleep(self.check_interval)

                if self.count % 100 == 0:
                    self.parent.reset_gpu_memory_service()

            except Exception as e:
                print(f"⚠️ 任务连接线程异常: {e}")
                time.sleep(1)
            finally:

                if 'targets' in locals():
                    del targets

                if self.count % 10 == 0:
                    gc.collect()

    def stop(self):
        self.running = False
        self.wait()

    # 坐标检测
    def check_comprehensive_status(self, target):
        try:
            # 默认状态池
            status = {
                "map": "未知",
                "coord": "0,0",
            }
            if target is None: return status

            region = [(0.900392, 0.063599, 0.949020, 0.092016), (0.851330, 0.032432, 0.983568, 0.064865)]
            ocr_text = self.parent.ocr_pure_predict(self.parent.get_combined_roi_image_horizontal(region, target))
            if ocr_text and "all_results" in ocr_text:
                results = ocr_text['all_results']
                # 初始化
                found_coord = None
                found_map = None
                for item in results:
                    text = item.get('text', '').strip()
                    if not text:
                        continue
                    # 1. 判断是否为【坐标】：特征是包含数字且必须有分隔符（逗号或点）
                    # 正则含义：匹配 数字+分隔符+数字 (如 123,456)
                    if re.search(r'\d+[,\.]\d+', text):
                        cleaned_coord = text.replace('.', ',')
                        found_coord = re.sub(r'[^\d,]', '', cleaned_coord)
                        continue
                    # 2. 判断是否为【级别】：特征是纯数字，且数值通常在合理范围内 (如 1-150)
                    # 我们先提取出字符串中的数字部分
                    nums = re.findall(r'\d+', text)
                    if nums:
                        # 如果字符串是纯数字，或者是 "10" 这种短字符
                        # 增加数值范围判断（假设等级不会超过 200），防止误抓大额坐标数字
                        val = int(nums[0])
                        if val < 200 and (text.isdigit() or "级" in text or "lv" in text.lower()):
                            found_level = val
                            continue
                    # 3. 判断是否为【地图名字】：特征是包含中文字符或英文字母，且不全是数字
                    # 排除掉已经被认定的等级和坐标后，剩下的长文本即为地图
                    if not text.isdigit() and len(text) > 1:
                        found_map = text
                if found_coord is not None:
                    status["coord"] = found_coord
                if found_map is not None:
                    status["map"] = found_map
            print(status)
            return status
        except Exception as e:
            print(f"⚠️ 坐标识别异常: {e}")
            return None

    # 地图寻人
    def open_map(self):
        try:
            target = self.parent.detect_target_sync("游戏窗口", min_confidence=0.8)
            if not target: return False
            if not self.parent.move_mouse_to_target_human_lock(target["center_x"], target["center_y"]): return False
            time.sleep(0.1)
            if not self.parent.mouse_quick_click('L'): return False
            if not self.parent.combo_keyboard_quick_click('KEY|TAB'): return False
            time.sleep(0.5)

            map_target_a = self.parent.detect_target_sync("地图窗口", min_confidence=0.8)
            if not map_target_a: return False
            center_x, center_y = self.parent.calc_absolute_coords(map_target_a, (0.852552, 0.010294, 0.963138, 0.069118))
            if not self.parent.move_mouse_to_target_human_lock(center_x, center_y): return False
            time.sleep(0.1)
            if not self.parent.mouse_quick_click('L'): return False
            time.sleep(0.5)
            map_target_b_ = self.parent.detect_target_sync("地图窗口", min_confidence=0.8)
            if not map_target_b_: return False
            center_x, center_y = self.parent.calc_absolute_coords(map_target_b_, (0.756833, 0.732064, 0.839774, 0.797950))
            if not self.parent.move_mouse_to_target_human_lock(center_x, center_y): return False
            time.sleep(0.1)
            if not self.parent.mouse_quick_click('L'): return False
            time.sleep(0.5)
            map_target_c = self.parent.detect_target_sync("地图窗口", min_confidence=0.8)
            if not map_target_c: return False

            center_x, center_y = self.parent.calc_absolute_coords(map_target_c, (0.328622, 0.574312, 0.349823, 0.605505))
            if not self.parent.move_mouse_to_target_human_lock(center_x, center_y): return False
            time.sleep(0.1)
            if not self.parent.mouse_quick_click('L'): return False
            time.sleep(0.5)
            if not self.parent.combo_keyboard_quick_click('KEY|TAB'): return False
            return True
        except Exception as e:
            print(f"⚠️ 地图找人报错: {e}")
            return False
