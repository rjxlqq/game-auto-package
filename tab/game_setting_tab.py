#game_setting_tab.py
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QLabel, QGroupBox)


# 游戏设置tab
class gameSetting(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()

    def init_ui(self):
        # 主布局
        layout = QVBoxLayout()

        # 创建分组框
        group_box = QGroupBox("游戏配置注意事项")
        group_layout = QVBoxLayout()

        # 配置说明内容
        content = """
        <h3>游戏运行环境要求</h3>

        <p><b>1. 桌面分辨率：</b>1920 × 1080</p>
        <p><b>2. 桌面缩放：</b>100%（不允许缩放）</p>
        <p><b>3. 游戏分辨率：</b>1280 × 800</p>
        <p><b>4. 输入法：</b>英文模式</p>

        <hr>
        <p style="color: #ff6600; font-weight: bold;">
        ⚠️ 请确保在启动游戏前完成以上配置，否则可能导致异常。
        </p>
        """

        # 创建标签
        label = QLabel(content)
        label.setWordWrap(True)
        label.setAlignment(Qt.AlignLeft)

        # 设置样式
        label.setStyleSheet("""
            QLabel {
                font-size: 13px;
                padding: 15px;
                line-height: 1.6;
            }
        """)

        # 添加到布局
        group_layout.addWidget(label)
        group_box.setLayout(group_layout)

        # 添加到主布局
        layout.addWidget(group_box)
        layout.addStretch()  # 添加弹性空间

        self.setLayout(layout)
