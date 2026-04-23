# nuoya_level.py
import gc
import time
from functools import wraps


# 清理内存装饰器，注意 要放在类外边
def auto_cleanup(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            # 执行原函数
            result = func(*args, **kwargs)
            return result
        except Exception as e:
            raise e
        finally:
            # 1. 强制清理 0 代垃圾（新生代对象）
            gc.collect(0)
            # 2. 如果你的 target 对象包含大型 numpy 数组或显存引用，
            # 装饰器其实很难精准 del 它们，因为它拿不到函数内部的变量名。
            # print(f"执行完毕并触发小规模回收: {func.__name__}")

    return wrapper


class NuoyaLevel:
    # 合成金色武器 ******
    @auto_cleanup
    def handle_execute_synthetic_mission(self):
        try:
            if not self.keyboard_quick_click('h'): return False
            time.sleep(1)
            synth_win = self.detect_target_sync("合成窗口", min_confidence=0.6)
            if not synth_win: return False
            # 点击切换到合成页签
            ocr_res = self.ocr_scan_sync((0.111399, 0.054422, 0.344560, 0.156463), min_confidence=0.6, window_target=synth_win)
            if not ocr_res: return False
            matches = self.check_text_exists_logic(ocr_res, '装备')
            if not matches: return False
            if not self.move_mouse_to_target_human_lock(matches['center_x'], matches['center_y']): return False
            time.sleep(0.2)
            if not self.mouse_quick_click('L'): return False
            # 识别物品栏并放入材料 (保持你的顺序点击逻辑)
            bag_win = self.detect_target_sync("物品栏窗口", min_confidence=0.6)
            if not bag_win: return False
            time.sleep(0.8)
            # 1. 识别多个装备
            zhuangbei_list = self.detect_region_targets_classify_sync("十级装备合成", (0.026667, 0.154206, 0.986667, 0.813084), min_confidence=0.6, window_target=bag_win)
            if zhuangbei_list:
                # 设置一个行阈值。
                # 如果是归一化坐标(0-1)，通常 0.03 ~ 0.05 对应一行的高度
                # 如果是像素坐标，通常设为格子高度的一半（例如 30 像素）
                row_threshold = 0.04

                def sort_logic(item):
                    # 将 Y 坐标除以阈值并取整，这样同一行的项会得到相同的 'row_index'
                    row_index = item['center_y'] // row_threshold
                    return (row_index, item['center_x'])

                zhuangbei_list.sort(key=sort_logic)
                print(f"✅ 严谨排序完成，共 {len(zhuangbei_list)} 个目标")
            # 2. 识别图纸
            tuzhi = self.detect_region_target_classify_sync("装备设计图纸", (0.026667, 0.154206, 0.986667, 0.813084), min_confidence=0.6, window_target=bag_win)
            if zhuangbei_list is None: zhuangbei_list = []
            # 3. 插入图纸逻辑
            if tuzhi:
                zhuangbei_list.insert(1, tuzhi)
                print(f"📍 图纸已插入到点击序列的第 2 位")

            # 按照顺序执行右键点击
            for item in zhuangbei_list:
                print(f"正在处理: {item.get('class_name', '未知')} 坐标: ({item['center_x']}, {item['center_y']})")
                # 移动鼠标并锁定
                if self.move_mouse_to_target_human_lock(item['center_x'], item['center_y']):
                    time.sleep(0.5)
                    # 右键快速点击
                    self.mouse_quick_click('R')
                    # 适当增加一点点间隔，防止点击过快游戏 UI 没反应
                    time.sleep(0.5)

            # 点击合成按钮
            synth_win = self.detect_target_sync("合成窗口", min_confidence=0.6)
            if not synth_win: return False
            center_x, center_y = self.calc_absolute_coords(synth_win, (0.241645, 0.900000, 0.444730, 0.977778))
            if not self.move_mouse_to_target_human_lock(center_x, center_y): return False
            time.sleep(0.1)
            if not self.mouse_quick_click('L'): return False
            time.sleep(1)

            # 点击装备合成确认
            gold_win = self.detect_target_sync("合成金色武器窗口", min_confidence=0.6)
            game_win = self.detect_target_sync("游戏窗口", min_confidence=0.6)
            target = None
            if gold_win:
                target = gold_win
            if game_win:
                target = game_win
            print(target)
            ocr_queding = self.ocr_scan_sync((0.428047, 0.502532, 0.498532, 0.565823), min_confidence=0.6, window_target=target)
            if not ocr_queding: return False
            matches_queding = self.check_text_exists_logic(ocr_queding, '确定')
            if not self.move_mouse_to_target_human_lock(matches_queding['center_x'], matches_queding['center_y']): return False
            time.sleep(0.1)
            if not self.mouse_quick_click('L'): return False
            time.sleep(0.5)

            # 关闭合成窗口
            center_x, center_y = self.calc_absolute_coords(synth_win, (0.893401, 0.006682, 0.989848, 0.084633))
            if not self.move_mouse_to_target_human_lock(center_x, center_y): return False
            time.sleep(0.5)
            if not self.mouse_quick_click('L'): return False

            # 装备新武器 (右键)
            gaoliang10 = self.wait_for_region_classify_target("十级装备合成高亮", (0.026667, 0.154206, 0.986667, 0.813084), min_confidence=0.6, window_target=bag_win)
            if not self.move_mouse_to_target_human_lock(gaoliang10['center_x'], gaoliang10['center_y']): return False
            time.sleep(0.1)
            if not self.mouse_quick_click('R'): return False
            time.sleep(1)

            # 关闭物品栏 (左键)
            center_x, center_y = self.calc_absolute_coords(bag_win, (0.863636, 0.009238, 0.987013, 0.085450))
            if not self.move_mouse_to_target_human_lock(center_x, center_y): return False
            time.sleep(1)
            if not self.mouse_quick_click('L'): return False
            # OCR 寻找‘尼德霍格’
            gold_win = self.detect_target_sync("合成金色武器窗口", min_confidence=0.6)
            game_win = self.detect_target_sync("游戏窗口", min_confidence=0.6)
            target = None
            if gold_win:
                target = gold_win
            if game_win:
                target = game_win
            ocr_res = self.ocr_scan_sync((0.833211, 0.299242, 0.986832, 0.500000), min_confidence=0.6, window_target=target)
            if not ocr_res: return False
            matches = self.check_text_exists_logic(ocr_res, "尼德霍")
            if not matches: return False
            time.sleep(0.4)
            if not self.move_mouse_to_target_human_lock(matches["center_x"], matches["center_y"]): return False
            time.sleep(0.1)
            if not self.mouse_quick_click('L'): return False
            time.sleep(50)
            return True
        except Exception as e:
            print(f"❌ 10级装备合成 执行异常: {e}")
            return False

    # 风暴试炼 ******
    @auto_cleanup
    def handle_fbsl_logic(self):
        try:
            game_win = self.detect_target_sync("游戏窗口", min_confidence=0.7)
            if not game_win: return False
            jinru = self.detect_region_target_classify_sync("进入", (0.211299, 0.300505, 0.420396, 0.781566), min_confidence=0.6, window_target=game_win)
            if jinru:
                if not self.move_mouse_to_target_human_lock(jinru['center_x'], jinru['center_y']): return False
                time.sleep(0.1)
                if not self.mouse_quick_click('L'): return False
                time.sleep(1)
                game_win_again = self.detect_target_sync("游戏窗口", min_confidence=0.7)
                if not game_win_again: return False
                ksgq = self.detect_region_target_classify_sync("开始关卡", (0.596916, 0.500634, 0.788546, 0.946768), min_confidence=0.6, window_target=game_win_again)
                if not ksgq: return False
                if not self.move_mouse_to_target_human_lock(ksgq['center_x'], ksgq['center_y']): return False
                time.sleep(0.1)
                if not self.mouse_quick_click('L'): return False
            else:
                time.sleep(1)
                ksgq = self.detect_region_target_classify_sync("开始关卡", (0.596916, 0.500634, 0.788546, 0.946768), min_confidence=0.6, window_target=game_win)
                if not ksgq: return False
                if not self.move_mouse_to_target_human_lock(ksgq['center_x'], ksgq['center_y']): return False
                time.sleep(0.1)
                if not self.mouse_quick_click('L'): return False
            time.sleep(6)

            # --- 点位 A 操作  ---
            if not self.combo_keyboard_quick_click('KEY|TAB'): return False
            map_win_a = self.wait_for_target("地图窗口")
            time.sleep(0.5)
            if not map_win_a: return False
            center_x, center_y = self.calc_absolute_coords(map_win_a, (0.101775, 0.416514, 0.132544, 0.455046))
            if not self.move_mouse_to_target_human_lock(center_x, center_y): return False
            time.sleep(1)
            print('执行点击')
            if not self.mouse_quick_click('L'): return False
            if not self.mouse_quick_click('L'): return False
            if not self.mouse_quick_click('L'): return False
            time.sleep(6)
            if not self.combo_keyboard_quick_click('KEY|TAB'): return False
            if not self.combo_keyboard_quick_click('COMBO|ALT+a'): return False
            time.sleep(40)

            # --- 点位 B 操作  ---
            if not self.combo_keyboard_quick_click('KEY|TAB'): return False
            map_win_b = self.wait_for_target("地图窗口")
            time.sleep(0.5)
            if not map_win_b: return False
            center_x, center_y = self.calc_absolute_coords(map_win_b, (0.386256, 0.416364, 0.411137, 0.450909))
            if not self.move_mouse_to_target_human_lock(center_x, center_y): return False
            if not self.mouse_quick_click('L'): return False
            if not self.mouse_quick_click('L'): return False
            if not self.mouse_quick_click('L'): return False
            time.sleep(7)
            if not self.combo_keyboard_quick_click('KEY|TAB'): return False
            if not self.combo_keyboard_quick_click('COMBO|ALT+a'): return False
            time.sleep(40)

            # --- 点位 C 操作  ---
            if not self.combo_keyboard_quick_click('KEY|TAB'): return False
            map_win_c = self.wait_for_target("地图窗口")
            if not map_win_c: return False
            center_x, center_y = self.calc_absolute_coords(map_win_c, (0.611307, 0.612132, 0.647821, 0.663603))
            if not self.move_mouse_to_target_human_lock(center_x, center_y): return False
            time.sleep(1)
            if not self.mouse_quick_click('L'): return False
            if not self.mouse_quick_click('L'): return False
            if not self.mouse_quick_click('L'): return False
            time.sleep(7)
            if not self.combo_keyboard_quick_click('KEY|TAB'): return False
            if not self.combo_keyboard_quick_click('COMBO|ALT+a'): return False
            time.sleep(50)
            return True

        except Exception as e:
            print(f"❌ 21级风暴试炼 第一步 执行异常: {e}")
            return False
        finally:
            self.pause = False

    # 自动点击主线对话框按钮
    @auto_cleanup
    def handle_main_line_dialog(self, target):
        try:
            current_time = time.time()
            if current_time - getattr(self, 'last_dialog_click_time', 0) < 0.8: return False
            if not target: return False
            print('开始执行自动点击主线对话窗口')
            target_pixel_x, target_pixel_y = self.calc_absolute_coords(target, (0.810767, 0.735000, 0.986949, 0.920000))
            if not self.move_mouse_to_target_human_lock(target_pixel_x, target_pixel_y): return False
            re_check = self.detect_target_sync("主线对话窗口", min_confidence=0.8)
            if not re_check: return False
            if self.mouse_quick_click('L'): self.last_dialog_click_time = time.time()
            return True
        except Exception as e:
            print(f"❌ 自动点击主线对话框按钮 执行异常: {e}")
            return False

    # 自动技能确认
    @auto_cleanup
    def handle_skill_confirm_dialog(self, target):
        try:
            current_time = time.time()
            if current_time - getattr(self, 'last_skill_click_time', 0) < 0.8: return False
            if not target: return False
            print('开始执行自动技能确认窗口')
            target_pixel_x, target_pixel_y = self.calc_absolute_coords(target, (0.387273, 0.653153, 0.625455, 0.887387))
            if not self.move_mouse_to_target_human_lock(target_pixel_x, target_pixel_y): return False
            re_check = self.detect_target_sync("技能确认窗口", min_confidence=0.8)
            if not re_check: return False
            if self.mouse_quick_click('L'): self.last_skill_click_time = time.time()
            return True
        except Exception as e:
            print(f"❌ 自动技能确认窗口按钮 执行异常: {e}")
            return False

    # 自动装备确认窗口按钮
    @auto_cleanup
    def handle_equip_confirm_dialog(self, target):
        try:
            current_time = time.time()
            if current_time - getattr(self, 'last_equip_click_time', 0) < 0.8: return False
            if not target: return False
            print('开始执行自动装备确认窗口')
            time.sleep(1)
            target_pixel_x, target_pixel_y = self.calc_absolute_coords(target, (0.353191, 0.813953, 0.753191, 0.953488))
            if not self.move_mouse_to_target_human_lock(target_pixel_x, target_pixel_y): return False
            # re_check = self.detect_target_sync("装备确认窗口", min_confidence=0.8)
            # if not re_check: return False
            time.sleep(0.1)
            if self.mouse_quick_click('L'): self.last_equip_click_time = time.time()
            return True
        except Exception as e:
            print(f"❌ 自动装备确认窗口按钮 执行异常: {e}")
            return False

    # 自动点击中间操作窗口
    @auto_cleanup
    def handle_middle_operation_dialog(self, target):
        try:
            current_time = time.time()
            if current_time - getattr(self, 'last_middle_click_time', 0) < 0.8: return False
            if not target: return False
            print('开始执行自动点击中间操作窗口')
            re_check_again = self.detect_target_sync("中间操作窗口", min_confidence=0.8)
            if not re_check_again: return False
            target_pixel_x, target_pixel_y = self.calc_absolute_coords(re_check_again, (0.107527, 0.141414, 0.881720, 0.909091))
            if not self.move_mouse_to_target_human_lock(target_pixel_x, target_pixel_y): return False
            # re_check = self.detect_target_sync("中间操作窗口", min_confidence=0.8)
            # if not re_check: return False
            time.sleep(0.1)
            if self.mouse_quick_click('L'): self.last_middle_click_time = time.time()
            return True
        except Exception as e:
            print(f"❌ 自动点击中间操作窗口 执行异常: {e}")
            return False

    # 自动点击 离开副本窗口
    @auto_cleanup
    def handle_exit_dungeon_logic(self, target):
        try:
            if not target: return False
            print('开始执行离开副本窗口窗口')
            target_pixel_x, target_pixel_y = self.calc_absolute_coords(target, (0.293040, 0.663366, 0.725275, 0.920792))
            if not self.move_mouse_to_target_human_lock(target_pixel_x, target_pixel_y): return False
            re_check = self.detect_target_sync("离开副本窗口", min_confidence=0.8)
            if not re_check: return False
            if not self.mouse_quick_click('L'): return False
            return True
        except Exception as e:
            print(f"❌ 自动点击离开副本窗口 执行异常: {e}")
            return False

    # 返回游戏  -----
    @auto_cleanup
    def handle_back_game(self, target):
        try:
            if not target: return False
            print('开始执行返回游戏')
            ocr_res = self.ocr_scan_sync((0.142857, 0.087819, 0.843750, 0.917847), 0.8, target)
            if not ocr_res: return False
            queding = self.check_text_exists_logic_more(ocr_res, ['返回游戏'])
            if not queding: return False
            if not self.move_mouse_to_target_human_lock(queding["center_x"], queding["center_y"]): return False
            time.sleep(0.1)
            if not self.mouse_quick_click('L'): return False
            return True
        except Exception as e:
            print(f"❌ 处理返回游戏 执行异常: {e}")
            return False

    # 自动点击恭喜通关窗口
    @auto_cleanup
    def handle_dungeon_completion(self, target):
        try:
            if not target: return False
            print('开始执行离开恭喜通关窗口')
            target_pixel_x, target_pixel_y = self.calc_absolute_coords(target, (0.429032, 0.853659, 0.567742, 0.919512))
            if not self.move_mouse_to_target_human_lock(target_pixel_x, target_pixel_y): return False
            re_check = self.detect_target_sync("恭喜通关窗口", min_confidence=0.8)
            if not re_check: return False
            if not self.mouse_quick_click('L'): return False
            print('恭喜通关执行点击成功')
            return True
        except Exception as e:
            print(f"❌ 自动点击恭喜通关窗口 执行异常: {e}")
            return False

    # 自动点击晶体合成窗口
    @auto_cleanup
    def handle_crystal_synthesis_logic(self, target):
        try:
            if not target: return False
            print('开始执行晶体合成窗口')
            target_pixel_x, target_pixel_y = self.calc_absolute_coords(target, (0.241117, 0.923937, 0.436548, 0.975391))
            if not self.move_mouse_to_target_human_lock(target_pixel_x, target_pixel_y): return False
            re_check = self.detect_target_sync("晶体合成窗口", min_confidence=0.8)
            if not re_check: return False
            if not self.mouse_quick_click('L'): return False
            return True
        except Exception as e:
            print(f"❌ 自动点击晶体合成窗口 执行异常: {e}")
            return False

    # 自动点击确认窗口
    @auto_cleanup
    def handle_queding_logic(self, target):
        try:
            if not target: return False
            print('开始执行确定窗口')
            ocr_res = self.ocr_scan_sync((0.114114, 0.495726, 0.879880, 0.888889), 0.8, target)
            if not ocr_res: return False
            queding = self.check_text_exists_logic_more(ocr_res, ['确定', '自动加点'])
            if not queding: return False
            if not self.move_mouse_to_target_human_lock(queding["center_x"], queding["center_y"]): return False
            time.sleep(0.1)
            if not self.mouse_quick_click('L'): return False
            return True
        except Exception as e:
            print(f"❌ 自动点击确定窗口 执行异常: {e}")
            return False

    # 自动点击跳过电影窗口
    @auto_cleanup
    def handle_jump_moive_logic(self, target):
        try:
            if not target: return False
            print('开始执行跳过电影窗口')
            ocr_res = self.ocr_scan_sync((0.780702, 0.813836, 0.975146, 0.978616), 0.8, target)
            if not ocr_res: return False
            matches = self.check_text_exists_logic(ocr_res, '跳过电影', threshold=0.7)
            if not matches: return False
            if not self.move_mouse_to_target_human_lock(matches["center_x"], matches["center_y"]): return False
            time.sleep(0.1)
            if not self.mouse_quick_click('L'): return False
            return True
        except Exception as e:
            print(f"❌ 自动点击跳过电影窗口 执行异常: {e}")
            return False

    # 技能加点
    @auto_cleanup
    def handle_role_skill_upgrade(self, targets):
        try:
            if "主线对话窗口" in targets: return False
            if not targets.get('技能加点窗口'):
                game_win = self.detect_target_sync("游戏窗口", min_confidence=0.7)
                current_task = self.ocr_scan_sync(region_params=(0.831131, 0.265152, 0.983847, 0.782828), window_target=game_win)
                if not current_task: return False
                matches = self.check_text_exists_logic(current_task, '【角色技能】前往提升', threshold=0.8)
                if not matches: return False
                if not self.move_mouse_to_target_human_lock(matches['center_x'] + 20, matches['center_y']): return False
                time.sleep(0.1)
                if not self.mouse_quick_click('L'): return False
                time.sleep(0.8)
                skill_win = self.detect_target_sync("技能加点窗口", min_confidence=0.8)
                if not skill_win: return False
                qr_ocr = self.ocr_scan_sync(region_params=(0.381511, 0.512626, 0.616288, 0.580808), window_target=game_win)
                if qr_ocr:
                    matches = self.check_text_exists_logic(qr_ocr, '确定', threshold=0.8)
                    if matches:
                        self.move_mouse_to_target_human_lock(matches['center_x'], matches['center_y'])
                        time.sleep(0.1)
                        self.mouse_quick_click('L')

            fail_count = 0  # 连续未发现按钮的计数
            max_fails = 2  # 允许连续 2 次检测不到，防止单帧漏检

            while True:
                skill_win = self.detect_target_sync("技能加点窗口", min_confidence=0.8)
                if not skill_win: break
                # 🔥 核心判断点：寻找加点按钮
                target = self.detect_region_target_classify_sync(
                    target_class="加点按钮",
                    region_params=(0.062500, 0.160194, 0.888158, 0.900485),
                    min_confidence=0.6,
                    window_target=skill_win
                )
                if target:
                    fail_count = 0  # 只要找到按钮，就清空失败计数
                    if not self.move_mouse_to_target_human_lock(target['center_x'], target['center_y']): break
                    time.sleep(0.1)
                    if not self.mouse_quick_click('L'): break
                    # 处理可能出现的二级确认框
                    time.sleep(0.3)
                    game_win = self.detect_target_sync("游戏窗口", min_confidence=0.8)
                    confirm_ocr = self.ocr_scan_sync(region_params=(0.373538, 0.515152, 0.623538, 0.589646), window_target=game_win)
                    confirm_btn = self.check_text_exists_logic(confirm_ocr, "确定", threshold=0.5)
                    if confirm_btn:
                        self.move_mouse_to_target_human_lock(confirm_btn['center_x'], confirm_btn['center_y'])
                        time.sleep(0.1)
                        self.mouse_quick_click('L')
                else:
                    # 找不到按钮了
                    fail_count += 1
                    print(f"🔎 未发现加点按钮 (第 {fail_count} 次检查)")
                    if fail_count >= max_fails:
                        print("✅ 确认所有技能已加满，准备关闭窗口。")
                        break

            final_win = self.detect_target_sync("技能加点窗口", 0.8)
            if final_win:
                if not self.keyboard_quick_click('v'): return False
            time.sleep(2)
            final_win = self.detect_target_sync("技能加点窗口", 0.8)
            if final_win:
                if not self.keyboard_quick_click('v'): return False
            return True

        except Exception as e:
            print(f"❌ handle_role_skill_upgrade 异常: {e}")
            return False
        finally:
            self.pause = False

    # 战斗技巧
    @auto_cleanup
    def handle_battle_tips_upgrade(self, targets):
        try:
            if "主线对话窗口" in targets: return False
            if not targets.get('战斗技巧窗口'):
                game_win = self.detect_target_sync("游戏窗口", min_confidence=0.7)
                current_task = self.ocr_scan_sync(region_params=(0.831131, 0.265152, 0.983847, 0.782828), window_target=game_win)
                if not current_task: return False
                matches = self.check_text_exists_logic(current_task, '【战斗技巧】前往提升', threshold=0.8)
                if not matches: return False
                if not self.move_mouse_to_target_human_lock(matches["center_x"] + 20, matches["center_y"]): return False
                time.sleep(0.1)
                if not self.mouse_quick_click('L'): return False
                # if not self.keyboard_quick_click('a'): return False
                time.sleep(0.5)
                win_battle = self.detect_target_sync("战斗技巧窗口", min_confidence=0.7)
                if not win_battle: return False
            time.sleep(0.5)
            win_battle = self.detect_target_sync("战斗技巧窗口", min_confidence=0.7)
            if not win_battle: return False
            print("📍点击训练按钮")
            center_x, center_y = self.calc_absolute_coords(target_class=win_battle, region_params=(0.538168, 0.880488, 0.670483, 0.980488))
            self.move_mouse_to_target_human_lock(center_x, center_y)
            final_check = self.detect_target_sync("战斗技巧窗口", min_confidence=0.7)
            if not final_check: return False
            if not self.mouse_quick_click('L'): return False
            time.sleep(0.2)
            if not self.keyboard_quick_click('a'): return False
            time.sleep(3)
            final_win = self.detect_target_sync("战斗技巧窗口", 0.8)
            if final_win:
                if not self.keyboard_quick_click('a'): return False
            return True
        except Exception as e:
            print(f"❌ 战斗技巧逻辑执行异常: {e}")
            return False
        finally:
            self.pause = False

    # 属性加点  -----
    @auto_cleanup
    def handle_role_attribute_points(self, targets):
        try:
            print('开始属性加点')
            if "主线对话窗口" in targets: return False
            game_win = self.detect_target_sync("游戏窗口", min_confidence=0.7)
            current_task = self.ocr_scan_sync(region_params=(0.831131, 0.265152, 0.983847, 0.782828), window_target=game_win)
            if not current_task: return False
            matches = self.check_text_exists_logic(current_task, '【属性加点】前往加点', threshold=0.8)
            if not matches: return False
            if not self.move_mouse_to_target_human_lock(matches["center_x"] + 20, matches["center_y"] + 0): return False
            time.sleep(0.1)
            if not self.mouse_quick_click('L'): return False
            time.sleep(1)
            jusse = self.detect_target_sync("角色窗口", min_confidence=0.7)
            if not jusse: return False
            time.sleep(1)
            xzk1 = self.wait_for_region_classify_target("属性加点选择框", (0.619141, 0.317073, 0.998047, 0.689579), min_confidence=0.6, window_target=jusse)
            if not xzk1:
                if self.detect_target_sync("角色窗口", min_confidence=0.6):
                    return self.combo_keyboard_quick_click('KEY|ESC')
            if not self.move_mouse_to_target_human_lock(xzk1['center_x'], xzk1['center_y']): return False
            time.sleep(0.1)
            if not self.mouse_quick_click('L'): return False
            time.sleep(0.8)
            game = self.detect_target_sync("游戏窗口", min_confidence=0.7)
            if not game: return False
            ocr_res = self.ocr_scan_sync((0.380220, 0.518939, 0.628571, 0.616162), window_target=game)
            print(ocr_res)
            if not ocr_res: return False
            matches = self.check_text_exists_logic(ocr_res, '自动加点', threshold=0.5)
            if not matches: return False
            if not self.move_mouse_to_target_human_lock(matches["center_x"], matches["center_y"]): return False
            time.sleep(0.2)
            if not self.mouse_quick_click('L'): return False
            time.sleep(1)
            jusse = self.detect_target_sync("角色窗口", min_confidence=0.7)
            if not jusse: return False
            if not self.keyboard_quick_click('c'): return False
            time.sleep(4)
            jusse = self.detect_target_sync("角色窗口", min_confidence=0.7)
            if not jusse: return False
            if not self.keyboard_quick_click('c'): return False
            return True

        except Exception as e:
            print(f"❌ 属性加点执行异常: {e}")
            return False
        finally:
            self.pause = False

    # 装备改造 -----
    @auto_cleanup
    def handle_zbgaz_logic(self, targets=None):
        try:
            if "主线对话窗口" in targets: return False
            # --- 优化点 1: 绝对状态检测 ---
            refine_win = targets.get('装备改造窗口')
            if not refine_win:
                print("尝试打开装备改造窗口...")
                self.keyboard_quick_click('o')
                time.sleep(1.2)  # 增加等待窗口弹出的时间
                refine_win = self.detect_target_sync("装备改造窗口", min_confidence=0.7)
            if not refine_win:
                print("❌ 无法打开装备改造窗口")
                return False
            weigaizao_ocr = self.ocr_scan_sync((0.487080, 0.050847, 0.968992, 0.559322), min_confidence=0.6, window_target=refine_win)
            if not weigaizao_ocr: return False
            highlight_tag = self.check_text_exists_logic(weigaizao_ocr, '未改造')
            if not highlight_tag: return False
            if not self.move_mouse_to_target_human_lock(highlight_tag['center_x'], highlight_tag['center_y']): return False
            time.sleep(0.8)
            if not self.mouse_quick_click('L'): return False
            # 1. 处理 一级劳尔晶体
            refine_win = self.detect_target_sync("装备改造窗口", min_confidence=0.7)
            if refine_win:
                crystals = self.detect_region_targets_classify_sync(
                    "一级劳尔晶体",
                    (0.479896, 0.565878, 0.981842, 0.978041),
                    min_confidence=0.6,
                    window_target=refine_win
                )
                if crystals:
                    print(f"💎 发现 {len(crystals)} 个 一级劳尔晶体，依次右键点击")
                    for crystal in crystals:  # 这里的循环用于处理同名多个目标，主逻辑已扁平
                        if not self.detect_target_sync("装备改造窗口", min_confidence=0.7): break
                        self.move_mouse_to_target_human_lock(crystal['center_x'], crystal['center_y'])
                        time.sleep(0.1)
                        self.mouse_quick_click('R')
                else:
                    print("未发现 一级劳尔晶体，跳过")
            # 2. 处理 二级劳尔晶体
            refine_win = self.detect_target_sync("装备改造窗口", min_confidence=0.7)
            if refine_win:
                crystals = self.detect_region_targets_classify_sync(
                    "二级劳尔晶体",
                    (0.479896, 0.565878, 0.981842, 0.978041),
                    min_confidence=0.6,
                    window_target=refine_win
                )
                if crystals:
                    print(f"💎 发现 {len(crystals)} 个 二级劳尔晶体，依次右键点击")
                    for crystal in crystals:
                        if not self.detect_target_sync("装备改造窗口", min_confidence=0.7): break
                        self.move_mouse_to_target_human_lock(crystal['center_x'], crystal['center_y'])
                        time.sleep(0.1)
                        self.mouse_quick_click('R')
                else:
                    print("未发现 二级劳尔晶体，跳过")
            # # 3. 处理 三级劳尔晶体
            # refine_win = self.detect_target_sync("装备改造窗口", min_confidence=0.7)
            # if refine_win:
            #     crystals = self.detect_region_targets_classify_sync("三级劳尔晶体", crystal_region, min_confidence=0.6, window_target=refine_win)
            #     if crystals:
            #         print(f"💎 发现 {len(crystals)} 个 三级劳尔晶体，依次右键点击")
            #         for crystal in crystals:
            #             if not self.detect_target_sync("装备改造窗口", min_confidence=0.7): break
            #             self.move_mouse_to_target_human_lock(crystal['center_x'], crystal['center_y'])
            #             self.mouse_quick_click('R')
            #     else:
            #         print("未发现 三级劳尔晶体，跳过")
            # 4. 处理 四级劳尔晶体
            # refine_win = self.detect_target_sync("装备改造窗口", min_confidence=0.7)
            # if refine_win:
            #     crystals = self.detect_region_targets_classify_sync("四级劳尔晶体", crystal_region, min_confidence=0.6, window_target=refine_win)
            #     if crystals:
            #         print(f"💎 发现 {len(crystals)} 个 四级劳尔晶体，依次右键点击")
            #         for crystal in crystals:
            #             if not self.detect_target_sync("装备改造窗口", min_confidence=0.7): break
            #             self.move_mouse_to_target_human_lock(crystal['center_x'], crystal['center_y'])
            #             self.mouse_quick_click('R')
            #     else:
            #         print("未发现 四级劳尔晶体，跳过")
            # --- 步骤 4: 执行最终改造按钮 ---
            refine_win = self.detect_target_sync("装备改造窗口", min_confidence=0.7)
            if not refine_win: return False
            # 计算并点击改造按钮
            gaizao_ocr = self.ocr_scan_sync((0.211414, 0.915398, 0.311284, 0.978003), min_confidence=0.8, window_target=refine_win)
            if not gaizao_ocr: return False
            gaizao_matches = self.check_text_exists_logic(gaizao_ocr, '改造')
            if not self.move_mouse_to_target_human_lock(gaizao_matches["center_x"] + 10, gaizao_matches["center_y"]): return False
            time.sleep(0.2)
            if not self.mouse_quick_click('L'): return False
            # --- 步骤 5: 收尾（关闭窗口） ---
            time.sleep(1)  # 给改造动画一点时间
            refine_win_final = self.detect_target_sync("装备改造窗口", min_confidence=0.7)
            if not refine_win_final: return False
            if not self.keyboard_quick_click('o'): return False
            time.sleep(3)
            final_win = self.detect_target_sync("装备改造窗口", 0.8)
            if final_win:
                if not self.keyboard_quick_click('o'): return False
            return True

        except Exception as e:
            print(f"❌ 装备改造异常: {e}")
            return False
        finally:
            self.pause = False

    # 自动一键接受  -----
    @auto_cleanup
    def handle_one_btn_dialog_actions(self, targets):
        try:
            yjjs = self.detect_region_target_classify_sync("一键接受", (0.679176, 0.221519, 0.840324, 0.508861), min_confidence=0.6, window_target=targets['游戏窗口'])
            if not yjjs: return False
            if not self.move_mouse_to_target_human_lock(yjjs['center_x'], yjjs['center_y']): return False
            time.sleep(0.1)
            if not self.mouse_quick_click('L'): return False
            return True
        except Exception as e:
            print(f"❌ 处理一键接受 执行异常: {e}")
            return False
