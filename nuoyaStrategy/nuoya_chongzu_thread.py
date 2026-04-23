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

    def run(self):
        print("🚀 自动反应线程已启动...")
        while self.running:
            try:
                self.task_progress.emit("虫族任务")
                self.count += 1

                # 判断任务是否可以结束
                if self.finished_flag >= 2:
                    self.parent.is_task_running = False
                    self.finished_flag = 0
                    self.parent.on_task_auto_next()
                    break

                # 识别所有的目标
                targets = self.parent.detect_all_targets_sync(min_confidence=0.6)

                print(targets, 'TaskStrategyThread')

                if not targets:
                    self.parent.last_targets = None
                    time.sleep(self.continue_interval)
                    continue

                self.parent.last_targets = targets

                if "NPC对话窗口" in targets:
                    self.npc_ocr_scan(targets.get('NPC对话窗口'), ['虫族任务-组队', '接受任务', '重返副本'])
                    time.sleep(self.continue_interval)
                    continue

                if "死亡窗口" in targets:
                    self.fuhuo(targets.get('死亡窗口'))
                    time.sleep(self.continue_interval)
                    continue

                if "离开副本窗口" in targets:
                    if self.handle_exit_dungeon_logic(targets['离开副本窗口']):
                        self.finished_flag += 1
                        time.sleep(2.6)
                        self.open_chengzhang('虫族任务')
                    time.sleep(self.continue_interval)
                    continue

                time.sleep(self.check_interval)

            except Exception as e:
                print(f"⚠️ 反应线程报错: {e}")
                time.sleep(self.check_interval)
            finally:
                if 'targets' in locals():
                    del targets

                # 清理内存碎片
                if self.count % 60 == 0:
                    gc.collect()

                # 清除gpu碎片
                if self.count % 500 == 0:
                    self.parent.reset_gpu_memory_service()

                # count重置
                if self.count == 10000:
                    self.count = 0

    def stop(self):
        self.running = False
        self.wait()

    # 死亡复活
    def fuhuo(self, target):
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
            return False
        finally:
            print('复活暂停结束')

    # NPC对话窗口执行逻辑
    def npc_ocr_scan(self, target, jugde):
        try:
            ocr_res = self.parent.ocr_scan_sync((0.010204, 0.112195, 1.006803, 0.997561), min_confidence=0.6, window_target=target)
            if not ocr_res: return False
            matches = self.parent.check_text_exists_logic_more(ocr_res, jugde, threshold=0.75)
            if not matches: return False
            if not self.parent.move_mouse_to_target_human_lock(matches["center_x"], matches["center_y"]): return False
            if not self.parent.mouse_quick_click('L'): return False
            return True
        except Exception as e:
            print(f'NPC对话窗口执行失败{e}')
            return False
        finally:
            print('NPC对话窗口暂停结束')

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

    # 打开成长手册 窗口  适用于虫族任务，十面埋伏，联邦任务
    def open_chengzhang(self, task_name):
        try:
            target = self.parent.detect_target_sync("游戏窗口", min_confidence=0.8)
            if not target: return False
            if target:
                if not self.parent.move_mouse_to_target_human_lock(target["center_x"], target["center_y"]): return False
                if not self.parent.mouse_quick_click('L'): return False
            time.sleep(0.5)
            pre_target = self.parent.detect_target_sync("成长手册窗口", min_confidence=0.8)
            if not pre_target:
                if not self.parent.keyboard_quick_click('r'): return False
                time.sleep(0.5)
            target = self.parent.detect_target_sync("成长手册窗口", min_confidence=0.8)
            if not target: return False
            current_task = self.parent.ocr_scan_sync(region_params=(0.094607, 0.149218, 0.207190, 0.557160), window_target=target)
            if not current_task: return False
            matches = self.parent.check_text_exists_logic(current_task, task_name, threshold=0.8)
            if not matches: return False
            if not self.parent.move_mouse_to_target_human_lock(matches["center_x"], matches["center_y"]): return False
            if not self.parent.mouse_quick_click('L'): return False
            time.sleep(1)
            if not self.parent.keyboard_quick_click('r'): return False
            return True
        except Exception as e:
            print(f"❌ 打开成长手册窗口报错: {e}")
            return False


# --- 任务连接线程 ---
class TaskMissionThread(QThread):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.running = True
        self.continue_interval = 1  # 中断事件
        self.check_interval = 1  # 循环时间
        self.count = 0
        self.last_coord = None

    def run(self):
        print("🚀 任务连接线程已启动 (Q键任务逻辑)...")
        while self.running:
            try:
                self.count += 1

                # 获取最新的识别结果
                targets = self.parent.last_targets

                if not targets:
                    time.sleep(self.continue_interval)
                    continue

                status = self.check_comprehensive_status(targets.get('游戏窗口'))
                if status.get('map') == '巨兽之窟' and status.get('coord'):
                    print('进入了巨兽之窟，执行打怪逻辑')
                    current_coord = status["coord"]
                    if not self.parent.is_at_location(status.get("coord"), '60,89', 8):
                        if current_coord != self.last_coord:
                            if self.open_map((0.332160, 0.522059, 0.346244, 0.536765)):
                                time.sleep(self.continue_interval)
                                continue
                        self.last_coord = current_coord
                    else:
                        self.auto_fight(targets.get('游戏窗口'))

                if status.get('map') == '血池' and status.get('coord'):
                    print('血池，，执行打怪逻辑')
                    current_coord = status["coord"]
                    if not self.parent.is_at_location(status.get("coord"), '62,60', 8):
                        if current_coord != self.last_coord:
                            if self.open_map((0.415385, 0.376384, 0.427219, 0.398524)):
                                time.sleep(self.continue_interval)
                                continue
                        self.last_coord = current_coord
                    else:
                        self.auto_fight(targets.get('游戏窗口'))

                if status.get('map') == '母虫之穴' and status.get('coord'):
                    print('母虫之穴,执行打怪逻辑')
                    current_coord = status["coord"]
                    if not self.parent.is_at_location(status.get("coord"), '30,50', 8):
                        if current_coord != self.last_coord:
                            if self.open_map((0.182783, 0.330309, 0.198113, 0.355717)):
                                time.sleep(self.continue_interval)
                                continue
                            self.last_coord = current_coord
                    else:
                        self.auto_fight(targets.get('游戏窗口'))

                time.sleep(self.check_interval)

            except Exception as e:
                print(f"⚠️ 任务连接线程异常: {e}")
                time.sleep(self.check_interval)
            finally:
                if 'targets' in locals():
                    del targets

                # 清理内存碎片
                if self.count % 60 == 0:
                    gc.collect()

                # count重置
                if self.count == 10000:
                    self.count = 0

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
            return status
        except Exception as e:
            print(f"⚠️ 坐标识别异常: {e}")
            return None

    # 到达地图指定点位
    def open_map(self, region):
        try:
            if not self.parent.combo_keyboard_quick_click('KEY|TAB'): return False
            time.sleep(1)
            map_targe = self.parent.detect_target_sync('地图窗口', min_confidence=0.7)
            if not map_targe: return False
            center_x, center_y = self.parent.calc_absolute_coords(map_targe, region)
            if not self.parent.move_mouse_to_target_human_lock(center_x, center_y): return False
            time.sleep(0.4)
            if not self.parent.mouse_quick_click('L'): return False
            if not self.parent.mouse_quick_click('L'): return False
            if not self.parent.combo_keyboard_quick_click('KEY|TAB'): return False
            return True
        except Exception as e:
            print(f"⚠️ 地图找人报错: {e}")
            return False

    # 开启自动打怪
    def auto_fight(self, target):
        zddg = self.detect_region_target_classify_sync("自动打怪", (0.367361, 0.157267, 0.624306, 0.723427), min_confidence=0.6, window_target=target)
        if not zddg:
            if not self.parent.combo_keyboard_quick_click('COMBO|ALT+a'): return False
        return True
