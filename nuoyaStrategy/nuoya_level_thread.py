# nuoya_level_thread.py

import gc
import time

from PyQt5.QtCore import QThread
from PyQt5.QtCore import QTimer


# --- 事件驱动型线程 --- --- --- --- ---
class StrategyEventThread(QThread):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.running = True
        self.check_interval = 1
        self.continue_interval = 1
        self.count = 0

    def run(self):
        print("🚀 自动反应线程已启动...")
        while self.running:
            try:
                self.count += 1
                targets = self.parent.detect_all_targets_sync(min_confidence=0.6)
                if not targets:
                    self.parent.last_targets = None
                    time.sleep(self.continue_interval)
                    continue

                print('StrategyEventThread', targets)

                self.parent.last_targets = targets

                if "主线对话窗口" in targets:
                    if self.parent.handle_main_line_dialog(targets['主线对话窗口']):
                        print('主线对话 执行成功')
                    time.sleep(self.continue_interval)
                    continue

                if "跳过电影窗口" in targets:
                    if self.parent.handle_jump_moive_logic(targets['跳过电影窗口']):
                        print('跳过电影窗口 执行成功')
                    time.sleep(5)
                    time.sleep(self.continue_interval)
                    continue

                if "技能确认窗口" in targets and not "NPC对话窗口" in targets:
                    if self.parent.handle_skill_confirm_dialog(targets['技能确认窗口']):
                        print('技能确认 执行成功')
                    time.sleep(self.continue_interval)
                    continue

                if "装备确认窗口" in targets and not "主线对话窗口" in targets:
                    if self.parent.handle_equip_confirm_dialog(targets['装备确认窗口']):
                        print('装备确认 执行成功')
                    time.sleep(self.continue_interval)
                    continue

                if "中间操作窗口" in targets and not "主线对话窗口" in targets:
                    if self.parent.handle_middle_operation_dialog(targets['中间操作窗口']):
                        print('中间操作 执行成功')
                    time.sleep(self.continue_interval)
                    continue

                if "离开副本窗口" in targets and not "主线对话窗口" in targets:
                    if self.parent.handle_exit_dungeon_logic(targets['离开副本窗口']):
                        print('离开副本 执行成功')
                    time.sleep(self.continue_interval)
                    continue

                if "恭喜通关窗口" in targets and not "主线对话窗口" in targets:
                    if self.parent.handle_dungeon_completion(targets['恭喜通关窗口']):
                        print('恭喜通关窗口 执行成功')
                    time.sleep(self.continue_interval)
                    continue

                if "晶体合成窗口" in targets and not "主线对话窗口" in targets:
                    if self.parent.handle_crystal_synthesis_logic(targets['晶体合成窗口']):
                        print('恭喜晶体合成窗口 执行成功')
                    time.sleep(self.continue_interval)
                    continue

                if "确认窗口" in targets and not "合成窗口" in targets and not "角色窗口" in targets:
                    if self.parent.handle_queding_logic(targets['确认窗口']):
                        print('恭喜确认窗口 执行成功')
                    time.sleep(self.continue_interval)
                    continue

                if "设置窗口" in targets and not "主线对话窗口" in targets:
                    if self.parent.handle_back_game(targets['设置窗口']):
                        print('恭喜设置窗口 执行成功')
                    time.sleep(self.continue_interval)
                    continue

                if "NPC对话窗口" in targets and not "主线对话窗口" in targets:
                    ocr_res = self.parent.ocr_scan_sync(
                        (0.026578, 0.125926, 0.970100, 0.908642),
                        min_confidence=0.6,
                        window_target=targets['NPC对话窗口']
                    )
                    if ocr_res:
                        if self.parent.check_text_exists_logic(ocr_res, '联邦任务'):
                            if targets.get("任务窗口"):
                                self.parent.keyboard_quick_click('q')
                            if targets.get("NPC对话窗口"):
                                self.parent.combo_keyboard_quick_click('KEY|ESC')
                            # 🔥 核心修改：不要直接调用 on_toggle_upgrade_clicked
                            # invokeMethod 是最安全的方式，或者简单用 singleShot
                            QTimer.singleShot(0, self.parent.switch_from_upgrade_to_daily)
                            # 停止当前线程的后续逻辑，防止继续扫描
                            self.running = False
                            return

                time.sleep(self.check_interval)

            except Exception as e:
                print(f"⚠️ 反应线程报错: {e}")
                time.sleep(self.check_interval)
            finally:
                if 'targets' in locals():
                    del targets

                if self.count % 60 == 0:
                    gc.collect()

                if self.count % 500 == 0:
                    self.parent.reset_gpu_memory_service()

                if self.count == 10000:
                    self.count = 0

    def stop(self):
        self.running = False
        self.wait()


# --- 角色升级任务线程--- --- --- ---
class MonitorThread(QThread):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.running = True
        self.continue_interval = 1  # 中断事件
        self.check_interval = 1  # 循环时间
        self.count = 0

    def run(self):
        print("🚀 整合版监控引擎启动 (内存锁模式)...")
        self.count = 0
        # continue  跳过当前这一轮循环的剩余代码，直接开始下一次循环
        while self.running:
            try:
                self.count += 1
                targets = self.parent.last_targets

                if not targets:
                    time.sleep(self.continue_interval)
                    continue

                if any(win in targets for win in ["主线对话窗口", "技能确认窗口", "装备确认窗口"]):
                    time.sleep(self.continue_interval)
                    continue

                # 10 合成金色武器
                targets = self.parent.last_targets
                if not targets:
                    time.sleep(self.continue_interval)
                    continue
                if targets.get('合成金色武器窗口') or (targets.get('物品栏窗口') and targets.get('合成窗口')):
                    time.sleep(1)
                    targets = self.parent.last_targets
                    if self.parent.handle_execute_synthetic_mission():
                        print('合成金色武器执行成功')
                    time.sleep(self.continue_interval)
                    continue

                # 14级自动打怪  开启自动打怪后 自动
                targets = self.parent.last_targets
                if not targets:
                    time.sleep(self.continue_interval)
                    continue
                if targets.get("新手试炼场窗口"):
                    self.parent.combo_keyboard_quick_click('COMBO|ALT+a')
                    time.sleep(15)
                    if not targets.get("任务窗口"):
                        self.parent.keyboard_quick_click('q')
                    time.sleep(0.8)
                    targets = self.parent.last_targets
                    region = (0.409274, 0.151786, 0.955645, 0.781250)
                    colors = self.parent.find_color_text_regions_precise(
                        region,
                        'yellow',
                        window_target=targets.get('任务窗口'),
                        isMask=True,
                        blackout_params=[(0.059925, 0.328413, 0.932584, 0.560886)]
                    )
                    if colors:
                        for i, task in enumerate(colors):
                            self.parent.move_mouse_to_target_human_lock(task['center_x'], task['center_y'])
                            self.parent.mouse_quick_click('L')
                            time.sleep(1)
                    time.sleep(self.continue_interval)
                    continue

                # 开始风暴试炼  点击窗口去执行
                targets = self.parent.last_targets
                if not targets:
                    time.sleep(self.continue_interval)
                    continue
                if targets.get("NPC对话窗口"):
                    # 通过NPC对话窗口 判断
                    self.parent.pause = True
                    ocr_res = self.parent.ocr_scan_sync(region_params=(0.026578, 0.125926, 0.970100, 0.908642), window_target=targets.get("NPC对话窗口"))
                    if ocr_res:
                        match = self.parent.check_text_exists_logic(ocr_res, '开始风暴试炼', threshold=0.85)
                        time.sleep(0.3)
                        if match:
                            self.parent.move_mouse_to_target_human_lock(match['center_x'], match['center_y'])
                            time.sleep(0.2)
                            self.parent.mouse_quick_click('L')
                            self.parent.handle_fbsl_logic()
                    time.sleep(self.continue_interval)
                    continue

                # 远古基因计划
                targets = self.parent.last_targets
                if not targets:
                    time.sleep(self.continue_interval)
                    continue
                if targets.get("NPC对话窗口"):
                    ocr_res = self.parent.ocr_scan_sync(region_params=(0.026578, 0.125926, 0.970100, 0.908642), window_target=targets.get("NPC对话窗口"))
                    if ocr_res:
                        match = self.parent.check_text_exists_logic(ocr_res, '继续任务', threshold=0.85)
                        time.sleep(0.3)
                        if match:
                            self.parent.move_mouse_to_target_human_lock(match['center_x'], match['center_y'])
                            time.sleep(0.2)
                            self.parent.mouse_quick_click('L')
                    time.sleep(self.continue_interval)
                    continue

                time.sleep(self.check_interval)
            except Exception as e:
                print(f"⚠️ 整合线程异常: {e}")
                time.sleep(self.check_interval)
            finally:
                if 'targets' in locals():
                    del targets

                if self.count % 60 == 0:
                    gc.collect()

                if self.count == 10000:
                    self.count = 0

    def stop(self):
        self.running = False
        self.wait()


#  ---角色强化线程（技能/技巧/装备/加点） ---
class UpgradeTaskThread(QThread):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.running = True
        self.continue_interval = 1  # 中断事件
        self.check_interval = 4  # 循环时间
        self.count = 0

    def run(self):
        while self.running:
            try:
                self.count += 1
                # 获取主线程缓存的识别结果
                targets = self.parent.last_targets

                if not targets:
                    time.sleep(self.continue_interval)
                    continue

                # 发现需要阻塞窗口后，查看有无任务窗口，如果有则关闭
                option = ["风暴试炼窗口", "密室窗口", "新手试炼场窗口", "远古基因战场窗口", "装备确认窗口", "主线对话窗口", "NPC对话窗口", "合成窗口", "物品栏窗口", "技能确认窗口"]

                if any(win in targets for win in option):
                    time.sleep(self.continue_interval)
                    continue

                if not targets.get('游戏窗口'):
                    time.sleep(self.continue_interval)
                    continue

                current_task = self.parent.ocr_scan_sync(region_params=(0.831131, 0.265152, 0.983847, 0.782828), window_target=targets.get('游戏窗口'))
                if current_task:
                    if self.parent.check_text_exists_logic(current_task, '【角色技能】前往提升', threshold=0.85):
                        self.parent.pause = True
                        if not self.parent.handle_role_skill_upgrade(targets):
                            time.sleep(self.continue_interval)
                            continue

                    if self.parent.check_text_exists_logic(current_task, '【战斗技巧】前往提升', threshold=0.85):
                        self.parent.pause = True
                        if not self.parent.handle_battle_tips_upgrade(targets):
                            time.sleep(self.continue_interval)
                            continue

                    if self.parent.check_text_exists_logic(current_task, '【属性加点】前往加点', threshold=0.85):
                        self.parent.pause = True
                        if not self.parent.handle_role_attribute_points(targets):
                            time.sleep(self.continue_interval)
                            continue

                    if self.parent.find_approximate_targets(current_task, '对身上任意装备进行', threshold=0.85):
                        self.parent.pause = True
                        if not self.parent.handle_zbgaz_logic(targets):
                            time.sleep(self.continue_interval)
                            continue

                time.sleep(self.check_interval)
            except Exception as e:
                print(f"⚠️ 强化线程报错: {e}")
                time.sleep(self.check_interval)
            finally:
                if 'targets' in locals():
                    del targets

                if self.count % 60 == 0:
                    gc.collect()

                if self.count == 10000:
                    self.count = 0

    def stop(self):
        self.running = False
        self.wait()


# --- 任务连接线程：专门负责处理 Q 键打开任务栏并点击黄色任务 ---
class MissionConnectorThread(QThread):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.running = True
        self.continue_interval = 1  # 中断事件
        self.check_interval = 3  # 循环时间
        self.count = 0
        self.last_task_img_hash = None

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

                if self.parent.pause:
                    if targets.get("任务窗口"):
                        self.parent.keyboard_quick_click('q')
                    time.sleep(self.continue_interval)
                    continue

                print('正在执行任务连接线程')

                # 发现需要阻塞窗口后，查看有无任务窗口，如果有则关闭
                option = ["风暴试炼窗口", "密室窗口", "远古基因战场窗口", "装备确认窗口", "主线对话窗口", "NPC对话窗口", "技能确认窗口", "角色窗口"]
                if any(win in targets for win in option):
                    # 发现相关窗口 关闭任务窗口
                    if targets.get("任务窗口"):
                        self.parent.keyboard_quick_click('q')
                    time.sleep(self.continue_interval)
                    continue

                # 1. 如果没开任务窗口，尝试按 Q
                if not targets.get("任务窗口"):
                    if targets.get("游戏窗口"):
                        self.parent.keyboard_quick_click('q')
                        time.sleep(0.5)
                        targets = self.parent.detect_all_targets_sync(min_confidence=0.6)

                # 2. 如果任务窗口已打开，执行颜色识别
                if targets.get("任务窗口"):
                    current_hash = self.parent.get_image_phash(targets.get("任务窗口"))
                    # 比较 当前和之前的汉明值，小于5，才算是有变化
                    if self.last_task_img_hash:
                        dist = self.parent.hamming_distance(current_hash, self.last_task_img_hash)
                        if dist < 5:
                            time.sleep(self.continue_interval)
                            continue
                    self.last_task_img_hash = current_hash

                    colors = self.parent.find_color_text_regions_precise(
                        (0.409274, 0.151786, 0.955645, 0.781250),
                        'yellow',
                        window_target=targets.get('任务窗口'),
                        isMask=True,
                        blackout_params=[(0.003788, 0.586957, 1.000000, 0.996377)]
                    )
                    if colors:
                        for task in colors:
                            targets = self.parent.last_targets  # 重新获取状态
                            self.parent.move_mouse_to_target_human_lock(task['center_x'], task['center_y'])
                            self.parent.mouse_quick_click('L')
                        # self.parent.keyboard_quick_click('q')
                        time.sleep(1)

                time.sleep(self.check_interval)
            except Exception as e:
                print(f"⚠️ 任务连接线程异常: {e}")
                time.sleep(self.check_interval)
            finally:
                if 'targets' in locals():
                    del targets

                if self.count % 60 == 0:
                    gc.collect()

                if self.count == 10000:
                    self.count = 0

    def stop(self):
        self.running = False
        self.wait()
