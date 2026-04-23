# nuoya_layout.py
import threading
import time

from PyQt5.QtCore import QTimer
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QGroupBox, QCheckBox, QGridLayout, QLabel, QMessageBox, QPushButton, QVBoxLayout

from algoVision.style import StyleManager
# 修改导入，使用别名
from nuoyaStrategy import (
    nuoya_chongzu_thread as cz_mod,
    nuoya_lianbang_thread as lb_mod,
    nuoya_shimian_thread as sm_mod,
    nuoya_xunlian_thread as xl_mod,
    nuoya_shangjin_thread as sj_mod)
# 自动升级
from nuoyaStrategy.nuoya_level import NuoyaLevel
from nuoyaStrategy.nuoya_level_thread import MissionConnectorThread
from nuoyaStrategy.nuoya_level_thread import MonitorThread
from nuoyaStrategy.nuoya_level_thread import StrategyEventThread
from nuoyaStrategy.nuoya_level_thread import UpgradeTaskThread


class NuoyaLayout(NuoyaLevel):
    """帧接收器选项卡，包含原有的帧接收器功能"""

    def __init__(self):
        self.TASKS_CONFIG = {
            # 重复随机任务 单人
            "lianbang": {
                "name": "联邦任务",
                "enabled": True,
            },
            "shimianmaifu": {
                "name": "十面埋伏",
                "enabled": True,
            },
            "chongzu": {
                "name": "虫族任务",
                "enabled": True,
            },
            "shangjin": {
                "name": "赏金任务",
                "enabled": True,
            },
            "xunlianying": {
                "name": "训练营",
                "enabled": False,
            },
        }
        # 用来存放生成的UI组件，方便后续访问
        self.task_widgets = {}
        self.task_queue = []
        self.current_task_index = 0
        self.is_task_running = False
        # 添加自动功能全局变量
        self.is_upgrade_running = False  # 状态控制变量
        self.monitor_thread = MonitorThread(self)
        self.strategy_event_thread = StrategyEventThread(self)
        self.mission_connector_thread = MissionConnectorThread(self)
        self.upgrade_task_thread = UpgradeTaskThread(self)
        self.gpu_lock = threading.Lock()  # 核心锁：GPU锁防止并发冲突，Status锁防止数据竞争
        self.action_lock = threading.Lock()  # 动作执行锁
        self.frame_lock = threading.Lock()  # 动作执行锁
        self.last_targets = None  # 最近一次目标识别结果
        self.current_targets = None  # 最近一次目标识别结果
        self.last_dialog_click_time = 0  # 防止主线对话框连续点击
        self.last_equip_click_time = 0  # 防止装备确认连续点击
        self.last_skill_click_time = 0  # 防止技能确认连续点击

        self.pause = False  # TaskStrategyThread停止TaskMissionThread线程标志位
        self.need_buy = None  # 需要购买的物品

    # 从自动升级切换到 日常任务。
    def switch_from_upgrade_to_daily(self):
        """从自动升级安全切换到每日任务"""
        print("🔄 检测到联邦任务，准备切换模式...")
        # 停止自动升级逻辑
        self.is_upgrade_running = False
        self.upgrade_ctrl_btn.setText("开始自动升级")
        self.upgrade_ctrl_btn.setStyleSheet(StyleManager.primary_button_style())
        self.stop_automation()  # 这会停止所有升级相关的子线程

        # 确保任务队列中有联邦任务
        if "lianbang" in self.TASKS_CONFIG:
            self.TASKS_CONFIG["lianbang"]["enabled"] = True

        # 使用 QTimer 延迟触发，确保 stop_automation 彻底回收资源
        QTimer.singleShot(1000, self.on_toggle_task_action)

    # 设置每日任务ui
    def setup_task_group(self):
        # 1. 创建 GroupBox
        task_group = QGroupBox("")
        task_group.setStyleSheet(StyleManager.groupbox_style())

        # 2. 创建布局：改为 QVBoxLayout 实现从上到下排列
        layout = QVBoxLayout()
        layout.setSpacing(10)  # 适当加大垂直间距，防止太挤
        layout.setContentsMargins(15, 15, 15, 15)
        task_group.setLayout(layout)

        # 确保初始化引用字典
        if not hasattr(self, 'task_widgets'):
            self.task_widgets = {}

        checkbox_style = """
            QCheckBox {
                font-size: 16px; 
                font-weight: bold;
                color: #2980b9; 
                font-family: 'Microsoft YaHei';
                spacing: 10px;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
            }
        """

        # --- 1. 动态生成任务行 ---
        for key, info in self.TASKS_CONFIG.items():
            is_enabled = info.get("enabled", False)

            cb = QCheckBox(info["name"])
            cb.setChecked(is_enabled)
            cb.setStyleSheet(checkbox_style)

            self.task_widgets[key] = {"checkbox": cb}
            cb.stateChanged.connect(lambda state, k=key: self.on_any_task_setting_changed(k, state))

            # 直接 addWidget，会自动排在下方
            layout.addWidget(cb)

        # 可以在任务列表和按钮之间加一个弹簧，或者直接按顺序添加
        layout.addSpacing(10)

        # --- 2. 状态显示标签 ---
        self.current_action_label = QLabel("等待任务开始...")
        self.current_action_label.setStyleSheet("color: #3498db; font-weight: bold; margin: 10px 0;")
        self.current_action_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.current_action_label)

        # --- 3. 控制按钮 ---
        self.task_ctrl_btn = QPushButton("开始任务")
        self.task_ctrl_btn.setMinimumHeight(35)  # 稍微加高一点，更好看
        self.task_ctrl_btn.setStyleSheet(StyleManager.primary_button_style())
        self.task_ctrl_btn.clicked.connect(self.on_toggle_task_action)
        layout.addWidget(self.task_ctrl_btn)

        return task_group

    # 每日任务次数和任务状态变化
    def on_any_task_setting_changed(self, task_key, state):
        """当界面上的复选框被点击时，立即更新后台配置字典"""
        is_checked = (state == Qt.Checked)
        if task_key in self.TASKS_CONFIG:
            self.TASKS_CONFIG[task_key]["enabled"] = is_checked
            print(f"⚙️ 任务配置已同步: {task_key} -> {is_checked}")

    # 每日任务状态切换-
    def on_toggle_task_action(self):
        """根据全局变量状态决定是开始还是结束"""
        if not self.is_task_running:
            if self.is_upgrade_running:
                self.show_message("提示", "请先关闭自动升级！", QMessageBox.Information)
                return False
            if not self.serial_worker_thread.ser or not self.serial_worker_thread.is_open:
                self.show_message("提示", "设备被未连接，请先连接设备！", QMessageBox.Information)
                return False
            # if not self.detect_target_sync("游戏窗口", min_confidence=0.6):
            #     self.show_message("提示", "未检测到游戏窗口，请将游戏窗口置顶！", QMessageBox.Information)
            #     return False
            if not self.global_model:
                self.show_message("提示", "模型尚未加载成功！", QMessageBox.Information)
                return False
            if not self.classify_model:
                self.show_message("提示", "模型尚未加载成功！", QMessageBox.Information)
                return False
            if not self.ocr_engine:
                self.show_message("提示", "模型尚未加载成功！", QMessageBox.Information)
                return False
            self.task_queue = []
            for task_id, widgets in self.task_widgets.items():
                checkbox = widgets.get("checkbox")
                if checkbox and checkbox.isChecked():
                    self.task_queue.append(task_id)

            print(f"📋 最终生成的执行队列: {self.task_queue}")

            if not self.task_queue:
                QMessageBox.information(self, "提示", "请至少勾选一个要执行的任务！")
                return False

            # 启动逻辑
            self.is_task_running = True
            self.task_ctrl_btn.setText("结束任务")
            self.task_ctrl_btn.setStyleSheet(StyleManager.warning_button_style())
            self.startTask()
            print('任务线程已开始')
        else:
            self.is_task_running = False
            self.task_ctrl_btn.setText("开始任务")
            self.task_ctrl_btn.setStyleSheet(StyleManager.primary_button_style())
            self.current_action_label.setText("任务已结束")
            self.stopTask()
            print("任务线程已安全停止")

    # 开始每日任务
    def startTask(self):
        """入口函数：初始化队列并触发第一个任务"""
        # 1. 基础配置初始化
        self.task_queue = []
        self.task_map = {
            "lianbang": lb_mod,
            "shangjin": sj_mod,
            "shimianmaifu": sm_mod,
            "xunlianying": xl_mod,
            "chongzu": cz_mod
        }

        # 2. 构建任务队列 (根据勾选框和次数)
        for task_id, config in self.TASKS_CONFIG.items():
            # 检查 enabled 字段是否为 True
            if config.get("enabled", False):
                self.task_queue.append(task_id)

        if not self.task_queue:
            QMessageBox.warning(self, "提示", "请先选择需要执行的任务")
            return

        # 3. 重置索引并更新 UI 状态
        self.current_task_index = 0
        self.is_task_running = True
        self.task_ctrl_btn.setText("停止任务")  # 按钮字体变化 toggle

        print(f"📋 任务清单构建完毕，共 {len(self.task_queue)} 项任务")

        # 4. 启动第一个任务
        self.execute_task_flow()

    # 自动切换下一个任务
    def on_task_auto_next(self):
        """任务完成后的自动跳转槽函数"""
        if not self.is_task_running: return

        print(f"✅ 第 {self.current_task_index + 1} 项任务执行完毕")
        self.current_task_index += 1

        # 短暂延迟，给系统和显存一点喘息时间
        QTimer.singleShot(2000, self.execute_task_flow)

    # 核心调度器 开始下一轮任务
    def execute_task_flow(self):
        """
        自动切换调度器：负责单个任务的启动前置检查和线程实例化
        """
        # 如果用户点击了停止，或者标志位为假，直接退出
        if not self.is_task_running: return

        # 检查是否全部执行完
        if self.current_task_index >= len(self.task_queue):
            print("🏁 所有队列任务处理完毕！")
            self.update_status_bar("全部任务已完成")
            self.stopTask()  # 正常结束
            return

        # 1. 彻底清理旧线程引用 (防止内存溢出和信号重叠)
        self.cleanup_active_threads()

        # 2. 获取当前任务标识
        task_key = self.task_queue[self.current_task_index]
        mod = self.task_map.get(task_key)

        if mod is None:
            print(f"❌ 错误：未找到模块 {task_key}，尝试跳过...")
            self.on_task_auto_next()
            return

        try:
            # ==========================================================
            # 🔥 关键修改：前置动作逻辑 (打开成长手册)
            # ==========================================================
            # 只有返回 True 才会继续启动线程
            print(task_key)
            if task_key == 'lianbang' or task_key == 'shimianmaifu' or task_key == 'chongzu':
                success = self.open_chengzhang(task_key)
                if not success:
                    print(f"⚠️ [中止] 无法打开成长手册执行 {task_key}，为了安全停止所有任务")
                    QMessageBox.critical(self, "执行失败", f"任务 {task_key} 启动环境失败，请检查游戏窗口状态")
                    self.stopTask()  # 彻底停止，不再调用 on_task_auto_next
                    return

            if task_key == 'xunlianying' or task_key == 'shangjin':
                success = self.open_map(task_key)
                if not success:
                    print(f"⚠️ [中止] 无法打开成长手册执行 {task_key}，为了安全停止所有任务")
                    QMessageBox.critical(self, "执行失败", f"任务 {task_key} 启动环境失败，请检查游戏窗口状态")
                    self.stopTask()  # 彻底停止，不再调用 on_task_auto_next
                    return

            # 确保线程类在对应模块中存在
            self.task_mission_thread = mod.TaskMissionThread(self)
            self.task_strategy_thread = mod.TaskStrategyThread(self)

            # 4. 绑定信号
            # finished 信号触发时会自动调用 on_task_auto_next 进入下一个循环
            self.task_strategy_thread.finished.connect(self.on_task_auto_next)

            # 绑定进度更新信号 (如果有)
            if hasattr(self.task_strategy_thread, 'task_progress'):
                self.task_strategy_thread.task_progress.connect(self.update_status_bar)

            # 5. 正式启动
            self.task_mission_thread.start()
            self.task_strategy_thread.start()

        except Exception as e:
            print(f"❌ 启动任务线程发生崩溃: {e}")
            # 发生未知错误时，可以选择停止或者尝试下一个
            self.on_task_auto_next()

    # 停止每日任务
    def stopTask(self):
        """停止所有自动化任务"""
        self.is_task_running = False
        self.task_ctrl_btn.setText("开始任务")
        self.task_ctrl_btn.setStyleSheet(StyleManager.primary_button_style())
        self.cleanup_active_threads()
        if hasattr(self, 'update_status_bar'):
            self.update_status_bar("任务已停止")
        print("🛑 自动化任务已手动或因异常停止")

    # 每日任务线程清理
    def cleanup_active_threads(self):
        """物理级清理"""
        thread_attrs = ['task_mission_thread', 'task_strategy_thread']

        for attr in thread_attrs:
            thread = getattr(self, attr, None)
            if thread:
                # 1. 立即隔离：断开所有信号，让线程变“孤儿”，这样它死时不会连累主界面
                try:
                    thread.disconnect()
                except:
                    pass

                # 2. 停止逻辑循环
                thread.running = False

                # 3. 优雅退出
                if thread.isRunning():
                    thread.quit()
                    # wait 时间减短，配合子线程内部的 self.msleep 响应
                    if not thread.wait(500):
                        thread.terminate()
                        thread.wait()

                # 4. 彻底销毁对象引用
                setattr(self, attr, None)

        self.current_targets = None

    # 打开成长手册 窗口  适用于虫族任务，十面埋伏，联邦任务
    def open_chengzhang(self, task_key):
        try:
            find_text = self.TASKS_CONFIG.get(task_key)
            target_a = self.detect_target_sync("游戏窗口", min_confidence=0.8)
            if not target_a: return False
            if target_a:
                if not self.move_mouse_to_target_human_lock(target_a["center_x"], target_a["center_y"]): return False
                if not self.mouse_quick_click('L'): return False
            time.sleep(0.5)
            pre_target = self.detect_target_sync("成长手册窗口", min_confidence=0.8)
            if not pre_target:
                if not self.keyboard_quick_click('r'): return False
                time.sleep(0.5)
            target_b = self.detect_target_sync("成长手册窗口", min_confidence=0.8)
            if not target_b: return False
            current_task = self.ocr_scan_sync(region_params=(0.102830, 0.145759, 0.200000, 0.587814), window_target=target_b)
            if not current_task: return False
            matches = self.check_text_exists_logic(current_task, find_text['name'], threshold=0.8)
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

    # 打开世界地图窗口 适用于 训练营，赏金任务
    def open_map(self, task_key):
        try:

            target = self.detect_target_sync("游戏窗口", min_confidence=0.8)
            if not target: return False
            if not self.move_mouse_to_target_human_lock(target["center_x"], target["center_y"]): return False
            time.sleep(0.1)
            if not self.mouse_quick_click('L'): return False
            if not self.combo_keyboard_quick_click('KEY|TAB'): return False
            time.sleep(0.5)

            map_target_a = self.detect_target_sync("地图窗口", min_confidence=0.8)
            if not map_target_a: return False
            center_x, center_y = self.calc_absolute_coords(map_target_a, (0.852552, 0.010294, 0.963138, 0.069118))
            if not self.move_mouse_to_target_human_lock(center_x, center_y): return False
            time.sleep(0.1)
            if not self.mouse_quick_click('L'): return False
            time.sleep(0.5)
            map_target_b_ = self.detect_target_sync("地图窗口", min_confidence=0.8)
            if not map_target_b_: return False
            center_x, center_y = self.calc_absolute_coords(map_target_b_, (0.756833, 0.732064, 0.839774, 0.797950))
            if not self.move_mouse_to_target_human_lock(center_x, center_y): return False
            time.sleep(0.1)
            if not self.mouse_quick_click('L'): return False
            time.sleep(0.5)
            if task_key == 'xunlianying':
                map_target_c = self.detect_target_sync("地图窗口", min_confidence=0.8)
                if not map_target_c: return False
                center_x, center_y = self.calc_absolute_coords(map_target_c, (0.328622, 0.574312, 0.349823, 0.605505))
                if not self.move_mouse_to_target_human_lock(center_x, center_y): return False
                time.sleep(0.1)
                if not self.mouse_quick_click('L'): return False
                time.sleep(0.5)
            elif task_key == 'shangjin':
                map_target_c = self.detect_target_sync("地图窗口", min_confidence=0.8)
                if not map_target_c: return False
                # todo 这里的相对区域是假的，需要标注 马龙位置
                center_x, center_y = self.calc_absolute_coords(map_target_c, (0.328622, 0.574312, 0.349823, 0.605505))
                if not self.move_mouse_to_target_human_lock(center_x, center_y): return False
                time.sleep(0.1)
                if not self.mouse_quick_click('L'): return False
                time.sleep(0.5)
            else:
                map_target_c = self.detect_target_sync("地图窗口", min_confidence=0.8)
                if not map_target_c: return False
                center_x, center_y = self.calc_absolute_coords(map_target_c, (0.271226, 0.367459, 0.303066, 0.404022))
                if not self.move_mouse_to_target_human_lock(center_x, center_y): return False
                time.sleep(0.1)
                if not self.mouse_quick_click('L'): return False
                time.sleep(0.5)

            if not self.combo_keyboard_quick_click('KEY|TAB'): return False
            return True
        except Exception as e:
            print(f"⚠️ 开启{task_key}任务报错: {e}")
            return False

    # 更新每日任务ui显示
    def update_status_bar(self, name):
        """
        更新 UI 的状态文字和进度显示
        name: 任务名称 (来自信号)
        curr: 当前第几个任务 (来自信号)
        total: 总任务数 (来自信号)
        """
        msg = f"当前执行: {name}"
        # print(f"DEBUG UI: {msg}")  # 在控制台打印，方便调试
        # 确保你的类里有这个 Label，如果没有，请替换为你自己的 Label 变量名
        try:
            if hasattr(self, 'current_action_label'):
                self.current_action_label.setText(msg)
        except Exception as e:
            print(f"⚠️ 更新状态栏失败: {e}")

    # 自动升级按钮点击事件
    def on_toggle_upgrade_clicked(self):
        """绑定函数：处理自动升级按钮点击逻辑"""
        if not self.is_upgrade_running:
            # 切换为运行状态
            if self.is_task_running:
                self.show_message("提示", "请先关闭每日任务！", QMessageBox.Information)
                return False
            if not self.serial_worker_thread.ser or not self.serial_worker_thread.is_open:
                self.show_message("提示", "设备被未连接，请先连接设备！", QMessageBox.Information)
                return False
            # if not self.detect_target_sync("游戏窗口", min_confidence=0.6):
            #     self.show_message("提示", "未检测到游戏窗口，请将游戏窗口置顶！", QMessageBox.Information)
            #     return False
            if not self.global_model:
                self.show_message("提示", "模型尚未加载成功！", QMessageBox.Information)
                return False
            if not self.classify_model:
                self.show_message("提示", "模型尚未加载成功！", QMessageBox.Information)
                return False
            if not self.ocr_engine:
                self.show_message("提示", "模型尚未加载成功！", QMessageBox.Information)
                return False
            self.is_upgrade_running = True
            self.upgrade_ctrl_btn.setText("停止自动升级")
            self.upgrade_ctrl_btn.setStyleSheet(StyleManager.warning_button_style())
            self.start_automation()
            print('开始自动升级')
        else:
            # 切换为停止状态
            self.is_upgrade_running = False
            self.upgrade_ctrl_btn.setText("开始自动升级")
            self.upgrade_ctrl_btn.setStyleSheet(StyleManager.primary_button_style())
            self.stop_automation()
            print("停止自动升级")

    # 开始自动升级任务
    def start_automation(self):
        """
        统一管理自动化线程的启动。
        """
        # 开始任务钱鼠标移动到游戏窗口
        game_win = self.detect_target_sync("游戏窗口", min_confidence=0.8)
        if not game_win: return False
        if not self.move_mouse_to_target_human_lock(game_win['center_x'], game_win['center_y']): return False
        if not self.mouse_quick_click('L'): return False
        # --- 1. 处理状态监控线程 (MonitorThread) ---
        if self.monitor_thread is None or not self.monitor_thread.isRunning():
            print("🔄 监控线程已停止或未创建，正在重新实例化...")
            self.monitor_thread = MonitorThread(self)
            self.monitor_thread.running = True
            self.monitor_thread.start()

        # --- 2. 处理点击策略线程 (StrategyEventThread) ---
        if self.strategy_event_thread is None or not self.strategy_event_thread.isRunning():
            print("🔄 策略线程已停止，正在重启...")
            self.strategy_event_thread = StrategyEventThread(self)
            self.strategy_event_thread.running = True
            self.strategy_event_thread.start()

        # --- 3. 任务重连线程 (MissionConnectorThread) ---
        if self.mission_connector_thread is None or not self.mission_connector_thread.isRunning():
            print("🔄 任务重连线程已停止，正在重启...")
            self.mission_connector_thread = MissionConnectorThread(self)
            self.mission_connector_thread.running = True
            self.mission_connector_thread.start()

        # --- 4. 角色强化线程 (UpgradeTaskThread) ---
        if self.upgrade_task_thread is None or not self.upgrade_task_thread.isRunning():
            print("🔄 角色强化线程已停止，正在重启...")
            self.upgrade_task_thread = UpgradeTaskThread(self)
            self.upgrade_task_thread.running = True
            self.upgrade_task_thread.start()

        return True

    # 结束自动升级任务
    def stop_automation(self):
        if self.monitor_thread:
            self.monitor_thread.running = False
            self.monitor_thread.wait(200)
            print("🛑状态监控线程已结束")
        if self.strategy_event_thread:
            self.strategy_event_thread.running = False
            self.strategy_event_thread.wait(200)
            print("🛑重要窗口点击线程已结束")
        if self.mission_connector_thread:
            self.mission_connector_thread.running = False
            self.mission_connector_thread.wait(200)
            print("🛑任务重连线程已结束")
        if self.upgrade_task_thread:
            self.upgrade_task_thread.running = False
            self.upgrade_task_thread.wait(200)
            print("🛑角色强化线程已结束")
        return True

    # 设置自动升级ui
    def setup_upgrade_group(self):
        """创建角色自动升级分组框 (集成等级、坐标、地图实时显示)"""
        upgrade_group = QGroupBox("")
        upgrade_group.setStyleSheet(StyleManager.groupbox_style())
        layout = QGridLayout(upgrade_group)
        layout.setSpacing(10)  # 增加控件间距，避免拥挤
        # 设置布局内边距：左=15, 上=30(加大), 右=15, 下=15
        layout.setContentsMargins(10, 10, 10, 10)

        # --- 3. 执行控制区 ---
        self.upgrade_ctrl_btn = QPushButton("开始自动升级")
        self.upgrade_ctrl_btn.setMinimumHeight(35)  # 稍微增加高度方便点击
        self.upgrade_ctrl_btn.setStyleSheet(StyleManager.primary_button_style())
        self.upgrade_ctrl_btn.clicked.connect(self.on_toggle_upgrade_clicked)
        layout.addWidget(self.upgrade_ctrl_btn, 5, 0, 1, 2)

        return upgrade_group

    # 提示框样式
    def show_message(self, title, message, icon=QMessageBox.Information, buttons=None):
        """显示自定义样式的消息框"""
        msg = QMessageBox(self)
        msg.setWindowTitle(title)
        msg.setText(message)
        msg.setIcon(icon)

        if buttons:
            msg.setStandardButtons(buttons)

        return msg.exec_()
