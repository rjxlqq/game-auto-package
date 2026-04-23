import base64
import gc
import re
import time
from hashlib import md5

import cv2
import requests
from PyQt5.QtCore import QThread, pyqtSignal


# --- 任务执行主线程 ---
class TaskStrategyThread(QThread):
    task_progress = pyqtSignal(str)

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
                self.task_progress.emit("赏金任务")
                self.count += 1

                # 识别所有的目标
                targets = self.parent.detect_all_targets_sync(min_confidence=0.6)

                print(targets, 'TaskStrategyThread')

                if not targets:
                    self.parent.last_targets = None
                    time.sleep(self.continue_interval)
                    continue

                self.parent.last_targets = targets

                # 发现联邦任务 即调用 on_toggle_upgrade_clicked函数
                if "NPC对话窗口" in targets:
                    self.parent.pause = True
                    self.npc_ocr_scan(targets.get('NPC对话窗口'))
                    time.sleep(self.continue_interval)
                    continue

                if "绑银装备窗口" in targets:
                    self.parent.pause = True
                    self.goumaizhuangbei(targets.get('绑银装备窗口'))
                    time.sleep(self.continue_interval)
                    continue

                if "绑银首饰窗口" in targets:
                    self.parent.pause = True
                    self.goumaizhuangbei(targets.get('绑银首饰窗口'))
                    time.sleep(self.continue_interval)
                    continue

                if "死亡窗口" in targets:
                    self.parent.pause = True
                    self.fuhuo(targets.get('死亡窗口'))
                    time.sleep(self.continue_interval)
                    continue

                if "商会管理员" in targets:
                    self.parent.pause = True
                    if self.parent.find_npc:
                        self.click_npc(targets.get('商会管理员'))
                    time.sleep(self.continue_interval)
                    continue

                if "反外挂答窗口" in targets:
                    self.parent.pause = True
                    if self.process_captcha_blocking(targets.get('反外挂答窗口')):
                        time.sleep(0.3)
                        self.open_chengzhang()
                    time.sleep(self.continue_interval)
                    continue

                if "提交物品窗口" in targets and "物品栏窗口" in targets:
                    self.parent.pause = True
                    self.tijiaowuin(targets.get('物品栏窗口'))
                    time.sleep(self.continue_interval)
                    continue

                if "提交物品窗口" in targets and "物品栏窗口" not in targets:
                    self.parent.pause = True
                    self.closetjwp(targets.get('提交物品窗口'))
                    time.sleep(self.continue_interval)
                    continue

                if "商店窗口" in targets:
                    self.parent.pause = True
                    pass

                if self.parent.need_buy:
                    # 需要购买的物品
                    pass

                time.sleep(self.check_interval)

            except Exception as e:
                print(f"⚠️ 反应线程报错: {e}")
                time.sleep(1)
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

    # 点击人物
    def click_npc(self, target):
        try:
            if not self.parent.move_mouse_to_target_human_lock(target["center_x"], target["center_y"]): return False
            time.sleep(0.2)
            if not self.parent.mouse_quick_click('L'): return False
            return True
        except Exception as e:
            print(f"点击人物失败{e}")
        finally:
            print('点击人物暂停结束')
            self.parent.pause = False
            self.parent.find_npc = False

    # 打开地图 到达相应位置  商会管理员
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

            center_x, center_y = self.parent.calc_absolute_coords(map_target_c, (0.358156, 0.260949, 0.379433, 0.286496))
            if not self.parent.move_mouse_to_target_human_lock(center_x, center_y): return False
            time.sleep(0.1)
            if not self.parent.mouse_quick_click('L'): return False
            time.sleep(0.5)
            if not self.parent.combo_keyboard_quick_click('KEY|TAB'): return False
            return True
        except Exception as e:
            print(f"⚠️ 地图找人报错: {e}")
            return False

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

    # NPC对话窗口执行逻辑
    def npc_ocr_scan(self, target):
        try:
            ocr_res = self.parent.ocr_scan_sync((0.026578, 0.125926, 0.970100, 0.908642), min_confidence=0.6, window_target=target)
            if not ocr_res: return False
            jugde_over = ['接受了20次联邦任务']
            matches_over = self.parent.check_text_exists_logic_more(ocr_res, jugde_over, threshold=0.75)
            if matches_over:
                self.parent.pause = True
                self.running = False
                self.parent.on_task_auto_next()
                return False
            jugde = ['请送我到需要战斗的地方', '请送我到采集地点', '联邦任务', '我已经完成了', '购买装备', '离开', '我来接受联邦检测', '购买东西']
            matches = self.parent.check_text_exists_logic_more(ocr_res, jugde, threshold=0.75)
            if not matches: return False
            if not self.parent.move_mouse_to_target_human_lock(matches["center_x"], matches["center_y"]): return False
            if not self.parent.mouse_quick_click('L'): return False
            self.parent.pause = False
            return True
        except Exception as e:
            print(f"npc对话窗口执行失败{e}")
        finally:
            self.parent.pause = False

    # 购买装备
    def goumaizhuangbei(self, target):
        try:
            glzb = self.parent.detect_region_targets_classify_sync("高亮装备", (0.046647, 0.158151, 0.962099, 0.851582), min_confidence=0.6, window_target=target)
            if not glzb: return False
            for task in glzb[:1]:
                self.parent.move_mouse_to_target_human_lock(task['center_x'], task['center_y'])
                time.sleep(1)
                self.parent.mouse_quick_click('R')
            center_x, center_y = self.parent.calc_absolute_coords(target, (0.917647, 0.017327, 0.979412, 0.071782))
            if not self.parent.move_mouse_to_target_human_lock(center_x, center_y): return False
            time.sleep(0.5)
            if not self.parent.mouse_quick_click('L'): return False
            wp_win = self.parent.detect_target_sync("物品栏窗口", min_confidence=0.8)
            center_x, center_y = self.parent.calc_absolute_coords(wp_win, (0.915584, 0.020930, 0.961039, 0.051163))
            if not self.parent.move_mouse_to_target_human_lock(center_x, center_y): return False
            if not self.parent.mouse_quick_click('L'): return False
            return True

        except Exception as e:
            print(f"⚠️ 购买装备: {e}")
            time.sleep(1)
        finally:
            self.parent.pause = False

    # 提交物品
    def tijiaowuin(self, target):
        try:
            print(target, '执行提交物品')
            gaoliang = self.parent.detect_region_target_classify_sync("高亮装备", (0.034483, 0.170686, 0.976127, 0.805195), min_confidence=0.6, window_target=target)
            if not gaoliang: return False
            if not self.parent.move_mouse_to_target_human_lock(gaoliang['center_x'], gaoliang['center_y']): return False
            time.sleep(0.5)
            if not self.parent.mouse_quick_click('R'): return False
            time.sleep(0.5)
            tijiao_win = self.parent.detect_target_sync("提交物品窗口", min_confidence=0.6)
            if not tijiao_win: return False
            # 点击切换到合成页签
            ocr_res = self.parent.ocr_scan_sync((0.048544, 0.541667, 0.961165, 0.986111), min_confidence=0.6, window_target=tijiao_win)
            if not ocr_res: return False
            matches = self.parent.check_text_exists_logic(ocr_res, '确定')
            if not matches: return False
            if not self.parent.move_mouse_to_target_human_lock(matches['center_x'], matches['center_y']): return False
            if not self.parent.mouse_quick_click('L'): return False
            wp_win = self.parent.detect_target_sync("物品栏窗口", min_confidence=0.8)
            center_x, center_y = self.parent.calc_absolute_coords(wp_win, (0.915584, 0.020930, 0.961039, 0.051163))
            if not self.parent.move_mouse_to_target_human_lock(center_x, center_y): return False
            if not self.parent.mouse_quick_click('L'): return False
            time.sleep(2)
            return True
        except Exception as e:
            print(f"⚠️ 提交物品: {e}")
            time.sleep(1)
        finally:
            print('提交物品暂停结束')
            self.parent.pause = False

    # 关闭提交物品
    def closetjwp(self, target):
        try:
            # 点击切换到合成页签
            ocr_res = self.parent.ocr_scan_sync((0.048544, 0.541667, 0.961165, 0.986111), min_confidence=0.6, window_target=target)
            if not ocr_res: return False
            matches = self.parent.check_text_exists_logic(ocr_res, '取消')
            if not matches: return False
            if not self.parent.move_mouse_to_target_human_lock(matches['center_x'], matches['center_y']): return False
            if not self.parent.mouse_quick_click('L'): return False
        except Exception as e:
            print(f"⚠️ 关闭提交物品: {e}")
            time.sleep(1)
        finally:
            print('关闭提交物品暂停结束')
            self.parent.pause = False

    # 联邦任务后死亡后回城复活 寻找尼尔 继续任务
    def fuhuo(self, target):
        try:
            fh_ocr_res = self.parent.ocr_scan_sync((0.026578, 0.125926, 0.970100, 0.908642), min_confidence=0.6, window_target=target)
            if not fh_ocr_res: return False
            fh_matches = self.parent.check_text_exists_logic(fh_ocr_res, '回城复活')
            if not fh_matches: return False
            if not self.parent.move_mouse_to_target_human_lock(fh_matches['center_x'], fh_matches['center_y']): return False
            if not self.parent.mouse_quick_click('L'): return False
            if not self.keyboard_quick_click('r'): return False
            time.sleep(3)
            target = self.detect_target_sync("成长手册窗口", min_confidence=0.8)
            czsc_ocr = self.ocr_scan_sync(region_params=(0.094607, 0.149218, 0.207190, 0.557160), window_target=target)
            if not czsc_ocr: return False
            czsc_matches = self.check_text_exists_logic(czsc_ocr, '联邦任务', threshold=0.8)
            if not czsc_matches: return False
            if not self.move_mouse_to_target_human_lock(czsc_matches["center_x"], czsc_matches["center_y"]): return False
            if not self.mouse_quick_click('L'): return False
            return True
        except Exception as e:
            print(f'复活失败{e}')
        finally:
            print('复活暂停结束')
            self.parent.pause = False

    # 处理验证码
    def process_captcha_blocking(self, target):
        """
        阻塞式验证码处理：截图 -> 识别 -> 点击 -> 确认
        返回 True 表示处理成功，False 表示失败或跳过
        """
        # 记录起始总时间
        start_total = time.perf_counter()

        print("🛡️ [验证码] 正在处理，脚本逻辑暂停...")

        try:
            # --- 步骤 1: 图像截取 ---
            t1 = time.perf_counter()
            frame = self.parent.obs_source.get_frame()
            if frame is None: return False

            wx1, wy1, wx2, wy2 = target['x1'], target['y1'], target['x2'], target['y2']
            roi = frame[wy1:wy2, wx1:wx2]

            ok, buf = cv2.imencode('.png', roi)
            if not ok: return False
            base64_img = base64.b64encode(buf).decode('utf-8')
            t_image = time.perf_counter() - t1

            # --- 步骤 2: API 请求 ---
            t2 = time.perf_counter()
            params = {
                'user': '123456qq',
                'pass2': md5('123456qq'.encode('utf-8')).hexdigest(),
                'softid': '974891',
                'codetype': 5000,
                'file_base64': base64_img
            }

            # 增加 headers 模拟浏览器，有时能加快响应
            response = requests.post(
                "http://upload.chaojiying.net/Upload/Processing.php",
                data=params,
                timeout=30
            )
            res = response.json()
            t_api = time.perf_counter() - t2
            # --- 结果打印 ---
            total_duration = time.perf_counter() - start_total
            print(f"✅ [验证码识别完毕]")
            print(f"📊 耗时统计: [总计:{total_duration:.2f}s] [图片处理:{t_image:.2f}s] [接口响应:{t_api:.2f}s]")
            print(f"📝 识别结果: {res.get('pic_str', '识别失败')}")
            # {'err_no': 0, 'err_str': 'OK', 'pic_id': '2321214000476440147', 'pic_str': '3', 'md5': '087858b001142815491d0942bfac5356'}
            if res.get('pic_str') == '1':
                center_x, center_y = self.parent.calc_absolute_coords(target_class=target, region_params=(0.095628, 0.381703, 0.174863, 0.482650))
                self.parent.move_mouse_to_target_human_lock(center_x, center_y)
                time.sleep(0.1)
                if not self.parent.mouse_quick_click('L'): return False
            elif res.get('pic_str') == '2':
                center_x, center_y = self.parent.calc_absolute_coords(target_class=target, region_params=(0.104839, 0.479233, 0.182796, 0.575080))
                self.parent.move_mouse_to_target_human_lock(center_x, center_y)
                time.sleep(0.1)
                if not self.parent.mouse_quick_click('L'): return False
            elif res.get('pic_str') == '3':
                center_x, center_y = self.parent.calc_absolute_coords(target_class=target, region_params=(0.103825, 0.574132, 0.188525, 0.675079))
                self.parent.move_mouse_to_target_human_lock(center_x, center_y)
                time.sleep(0.1)
                if not self.parent.mouse_quick_click('L'): return False
            elif res.get('pic_str') == '4':
                center_x, center_y = self.parent.calc_absolute_coords(target_class=target, region_params=(0.105121, 0.701923, 0.169811, 0.791667))
                self.parent.move_mouse_to_target_human_lock(center_x, center_y)
                time.sleep(0.1)
                if not self.parent.mouse_quick_click('L'): return False
            else:
                # 啥都没有 执行2
                center_x, center_y = self.parent.calc_absolute_coords(target_class=target, region_params=(0.104839, 0.479233, 0.182796, 0.575080))
                self.parent.move_mouse_to_target_human_lock(center_x, center_y)
                time.sleep(0.1)
                if not self.parent.mouse_quick_click('L'): return False

            ocr_check = self.parent.ocr_scan_sync((0.072193, 0.755418, 0.435829, 0.953560), 0.8, target)
            if not ocr_check: return False
            check = self.parent.check_text_exists_logic_more(ocr_check, ['确定'])
            if not check: return False
            if not self.parent.move_mouse_to_target_human_lock(check["center_x"], check["center_y"]): return False
            time.sleep(0.1)
            if not self.parent.mouse_quick_click('L'): return False
            return True

        except Exception as e:
            print(f"⚠️ [验证码] 异常: {e}")
            return False
        finally:
            print('验证码暂停结束')
            self.parent.pause = False

    # 验证码后调用函数  需要寻找尼尔
    def open_chengzhang(self):
        try:
            target = self.detect_target_sync("游戏窗口", min_confidence=0.8)
            if not target: return False
            if target:
                if not self.move_mouse_to_target_human_lock(target["center_x"], target["center_y"]): return False
                if not self.mouse_quick_click('L'): return False
            time.sleep(0.5)
            pre_target = self.detect_target_sync("成长手册窗口", min_confidence=0.8)
            if not pre_target:
                if not self.keyboard_quick_click('r'): return False
                time.sleep(0.5)
            target = self.detect_target_sync("成长手册窗口", min_confidence=0.8)
            if not target: return False
            current_task = self.ocr_scan_sync(region_params=(0.094607, 0.149218, 0.207190, 0.557160), window_target=target)
            if not current_task: return False
            matches = self.check_text_exists_logic(current_task, '联邦任务', threshold=0.8)
            if not matches: return False
            if not self.move_mouse_to_target_human_lock(matches["center_x"], matches["center_y"]): return False
            if not self.mouse_quick_click('L'): return False
            time.sleep(1)
            if not self.keyboard_quick_click('r'): return False
            return True
        except Exception as e:
            print(f"❌ 打开成长手册窗口报错: {e}")
            # 发生未知错误时，可以选择停止或者尝试下一个
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
                    print('TaskMissionThread暂停')
                    if targets.get("任务窗口"):
                        self.parent.keyboard_quick_click('q')
                    time.sleep(self.continue_interval)
                    continue

                # 如果没开任务窗口，尝试按 Q
                if not targets.get("任务窗口"):
                    if targets.get("游戏窗口"):
                        self.parent.keyboard_quick_click('q')
                        time.sleep(0.5)
                        if self.task_ocr_scan(targets.get("任务窗口")):
                            self.yellow_task()
                # 如果已经打开任务窗口，直接点击
                else:
                    if self.task_ocr_scan(targets.get("任务窗口")):
                        self.yellow_task()

                time.sleep(self.check_interval)

            except Exception as e:
                print(f"⚠️ 任务连接线程异常: {e}")
                time.sleep(1)
            finally:
                if 'targets' in locals():
                    del targets

                if self.count % 60 == 0:
                    import gc
                    gc.collect()

                if self.count == 10000:
                    self.count = 0

    def stop(self):
        self.running = False
        self.wait()

    # 打开任务栏
    def task_ocr_scan(self, target):
        ocr_res = self.parent.ocr_scan_sync((0.029364, 0.142857, 0.355628, 0.907143), min_confidence=0.6, window_target=target)
        if not ocr_res: return False
        cg_matches = self.parent.check_text_exists_logic_more(ocr_res, ['常规任务'], threshold=0.75)
        lb_matches = self.parent.check_text_exists_logic_more(ocr_res, ['联邦任务'], threshold=0.75)
        if cg_matches and lb_matches:
            # 如果常规任务存在且联邦任务存在，只点击联邦任务
            if not self.parent.move_mouse_to_target_human_lock(lb_matches["center_x"], lb_matches["center_y"]): return False
            if not self.parent.mouse_quick_click('L'): return False
            return True
        elif cg_matches and not lb_matches:
            # 常规任务存在但是联邦任务不存在，先点击常规任务 再次识别 如果没有 联邦任务则退出 如果有则点击
            if not self.parent.move_mouse_to_target_human_lock(cg_matches["center_x"], cg_matches["center_y"]): return False
            if not self.parent.mouse_quick_click('L'): return False
            lb_ocr_res = self.parent.ocr_scan_sync((0.029364, 0.142857, 0.355628, 0.907143), min_confidence=0.6, window_target=target)
            if not lb_ocr_res: return False
            lb_matches = self.parent.check_text_exists_logic_more(lb_ocr_res, ['联邦任务'], threshold=0.75)
            if not lb_matches: return False
            if not self.parent.move_mouse_to_target_human_lock(lb_matches["center_x"], lb_matches["center_y"]): return False
            if not self.parent.mouse_quick_click('L'): return False
            return True

    # 点击黄色字体
    def yellow_task(self):
        targets = self.parent.last_targets  # 重新获取状态
        # 2. 如果任务窗口已打开，执行颜色识别
        if targets and targets.get("任务窗口"):
            zb_ocr_res = self.parent.ocr_scan_sync((0.409274, 0.151786, 0.955645, 0.781250), min_confidence=0.6, window_target=targets.get("任务窗口"))
            zb_matches = self.parent.check_text_exists_logic_more(zb_ocr_res, ['罗宾', '镇静药水', '狂暴药水', '冥想药水', '忍耐药水'])
            if (zb_matches["class_name"] == '镇静药水' or zb_matches["class_name"] == '狂暴药水' or
                zb_matches["class_name"] == '冥想药水' or zb_matches["class_name"] == '忍耐药水' or
                zb_matches["活化药水"]) and zb_matches:
                self.parent.need_buy = zb_matches["class_name"]

            if zb_matches and zb_matches["class_name"] == '罗宾':
                if not self.parent.move_mouse_to_target_human_lock(zb_matches["center_x"], zb_matches["center_y"]): return False
                if not self.parent.mouse_quick_click('L'): return False
                return True
            else:
                colors1 = self.parent.find_color_text_regions_precise(
                    (0.409274, 0.151786, 0.955645, 0.781250),
                    'yellow',
                    window_target=targets.get('任务窗口'),
                )
                colors2 = self.parent.find_color_text_regions_precise(
                    (0.409274, 0.151786, 0.955645, 0.781250),
                    'red',
                    window_target=targets.get('任务窗口'),
                )
                colors = colors1 + colors2
                if colors:
                    print(f"🔍 [MissionThread] 发现 {len(colors)} 个颜色疑似点")
                    for task in colors:
                        self.parent.move_mouse_to_target_human_lock(task['center_x'], task['center_y'])
                        if not self.parent.mouse_quick_click('L'): return False
                        time.sleep(0.5)
                    return True
