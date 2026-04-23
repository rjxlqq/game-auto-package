# layout.py
import time

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import (QMainWindow, QVBoxLayout, QTabWidget, QMessageBox, QWidget)
# from PyQt5.QtCore import QEvent
from PyQt5.QtWidgets import QMenu, QAction, QApplication
from PyQt5.QtWidgets import QSystemTrayIcon

from algoVision.style import StyleManager
from base.communicator import bus  # 导入总线
from tab.game_setting_tab import gameSetting
from tab.main_tab import mainTab

version = "录屏小助手V5.2"


class layoutWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(version)
        self.setFixedSize(288, 466)
        self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint)
        self.setWindowOpacity(0.95)
        # 1. 必须创建一个中心部件
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        # 2. 所有的布局都加在 central_widget 上，而不是 self 上
        main_layout = QVBoxLayout(self.central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        self.setWindowIcon(QIcon("assets/logo.ico"))
        self.move(10, 10)
        # 4. 创建选项卡并添加到布局
        self.tab_widget = QTabWidget()
        # 2. 创建选项卡
        self.tab_widget = QTabWidget()
        self.tab_widget.setStyleSheet(StyleManager.tab_widget_style())
        # --- 关键点：FrameReceiverTab 现在内部自己会跑 OBS 采集逻辑 ---
        self.main_tab = mainTab()
        self.gameSetting_tab = gameSetting()
        self.tab_widget.addTab(self.main_tab, "设置")
        self.tab_widget.addTab(self.gameSetting_tab, "说明")
        main_layout.addWidget(self.tab_widget)
        # 绑定全局错误处理逻辑
        bus.error_occurred.connect(self.show_global_error)
        self.last_error_time = 0
        self.last_error_msg = ""
        # 默认最小化启动（可选）
        self.showMinimized()
        # self.init_tray()

    def show_global_error(self, title, message):
        current_time = time.time()

        # 核心逻辑：如果消息相同 且 间隔小于 5 秒，则不弹窗
        if message == self.last_error_msg and (current_time - self.last_error_time) < 5:
            print(f"检测到重复错误，已拦截显示: {message}")
            return

        self.last_error_time = current_time
        self.last_error_msg = message
        QMessageBox.critical(self, title, message)

    def init_tray(self):
        """新增：初始化系统托盘"""
        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setIcon(QIcon("assets/logo.ico"))  # 保持你的图标路径
        self.tray_icon.setToolTip("绝影录屏助手")
        # 托盘右键菜单
        tray_menu = QMenu()
        show_action = QAction("显示主界面", self)
        quit_action = QAction("彻底退出", self)
        quit_action.triggered.connect(self.close)
        show_action.triggered.connect(self.showNormal)
        quit_action.triggered.connect(QApplication.instance().quit)

        tray_menu.addAction(show_action)
        tray_menu.addSeparator()
        tray_menu.addAction(quit_action)

        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.activated.connect(self._on_tray_activated)
        self.tray_icon.show()

    def _on_tray_activated(self, reason):
        """新增：双击恢复窗口"""
        if reason == QSystemTrayIcon.DoubleClick:
            self.showNormal()
            self.activateWindow()

    # def changeEvent(self, event):
    #     """核心：监听最小化状态，实现缩小到右下角"""
    #     if event.type() == QEvent.WindowStateChange:
    #         if self.isMinimized():
    #             self.hide()  # 隐藏窗口，让任务栏图标消失
    #             event.ignore()
    #             return
    #     super().changeEvent(event)  # 保持原有的事件处理

    def closeEvent(self, event):
        """当用户点击关闭或托盘点退出时"""
        # 触发你 main_tab 里的清理逻辑
        if hasattr(self, 'main_tab'):
            self.main_tab.cleanup()
        print("资源清理完毕，正在退出...")
        event.accept()
        QApplication.instance().quit()
