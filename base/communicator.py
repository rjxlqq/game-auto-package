# communicator.py
from PyQt5.QtCore import QObject, pyqtSignal

class GlobalBus(QObject):
    # 错误信号：(标题, 内容)
    error_occurred = pyqtSignal(str, str)
    # 状态栏消息信号：内容
    message_sent = pyqtSignal(str)

# 导出单例
bus = GlobalBus()