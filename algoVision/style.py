# style_manager.py
class StyleManager:

    @staticmethod
    def primary_button_style():
        return """
        QPushButton {
            background-color: qlineargradient(
                x1:0, y1:0, x2:0, y2:1,
                stop:0 #00b4ff,
                stop:0.5 #0099e6,
                stop:1 #0077cc
            );
            color: #ffffff;
            border: 1px solid #00aaff;
            padding: 8px 18px;
            border-radius: 4px;
            font-weight: bold;
            font-size: 12px;
            font-family: "Microsoft YaHei", "Segoe UI";
        }
        QPushButton:hover {
            background-color: qlineargradient(
                x1:0, y1:0, x2:0, y2:1,
                stop:0 #33ccff,
                stop:1 #00aaff
            );
            border: 1px solid #66ddff;
        }
        QPushButton:pressed {
            background-color: qlineargradient(
                x1:0, y1:0, x2:0, y2:1,
                stop:0 #005599,
                stop:1 #003366
            );
            border: 1px solid #0088cc;
        }
        """

    @staticmethod
    def warning_button_style():
        return """
        QPushButton {
            background-color: qlineargradient(
                x1:0, y1:0, x2:0, y2:1,
                stop:0 #ff5555,
                stop:0.5 #ff3333,
                stop:1 #ff0000
            );
            color: #ffffff;
            border: 1px solid #ff6666;
            padding: 8px 18px;
            border-radius: 4px;
            font-weight: bold;
            font-size: 12px;
            font-family: "Microsoft YaHei", "Segoe UI";
        }
        QPushButton:hover {
            background-color: qlineargradient(
                x1:0, y1:0, x2:0, y2:1,
                stop:0 #ff7777,
                stop:1 #ff5555
            );
            border: 1px solid #ff9999;
        }
        QPushButton:pressed {
            background-color: qlineargradient(
                x1:0, y1:0, x2:0, y2:1,
                stop:0 #cc0000,
                stop:1 #990000
            );
            border: 1px solid #ff3333;
        }
        """

    @staticmethod
    def groupbox_style():
        return """
        QGroupBox {
            font-weight: bold;
            font-size: 13px;
            color: #e0f0ff;
            border: 1px solid #334455;
            border-radius: 6px;
            margin-top: 14px;
            background-color: rgba(40, 50, 65, 0.9);
            padding: 2px;
            font-family: "Microsoft YaHei", "Segoe UI";
        }

        QGroupBox::title {
            subcontrol-origin: margin;
            subcontrol-position: top center;
            padding: 2px 6px;
            color: #ffffff;
            background-color: qlineargradient(
                x1:0, y1:0, x2:1, y2:0,
                stop:0 #2a6ea5,
                stop:1 #1e4a75
            );
            border: 1px solid #3a7bb5;
            border-radius: 4px;
        }

        QLabel {
            color: #c0d0e0;
            font-size: 12px;
            font-family: "Microsoft YaHei", "Segoe UI";
            background: transparent;
        }

        QCheckBox {
            color: #c0d0e0;
            spacing: 8px;
            font-size: 12px;
            font-family: "Microsoft YaHei", "Segoe UI";
            background: transparent;
        }

        QCheckBox::indicator {
            width: 14px;
            height: 14px;
            border-radius: 3px;
            border: 1px solid #5a6b7c;
            background-color: #2a3440;
        }

        QCheckBox::indicator:checked {
            background-color: qlineargradient(
                x1:0, y1:0, x2:0, y2:1,
                stop:0 #00b4ff,
                stop:1 #0077cc
            );
            border: 1px solid #00aaff;
        }
        """

    @staticmethod
    def frame_style():
        return """
        QFrame {
            background-color: rgba(30, 40, 50, 0.8);
            border: none;
            padding: 0px;
        }
        """

    @staticmethod
    def tab_widget_style():
        return """
        QTabWidget::pane {
            background-color: #2a3440;
            border: 1px solid #445566;
            border-radius: 6px;
        }

        QTabWidget QWidget {
            background-color: #2a3440;
            color: #e0f0ff;
        }

        QTabBar::tab {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                       stop:0 #3a4a5a, stop:1 #2a3a4a);
            border: 1px solid #556677;
            border-bottom: none;
            color: #c0d0e0;
            padding: 4px 4px;  /* 增加内边距 */
            margin: 2px 1px 0px 1px;  /* 上 右 下 左 */
            font-weight: bold;
            font-size: 12px;
            font-family: "Microsoft YaHei", "Segoe UI";
            min-width: 80px;  /* 设置最小宽度 */
        }

        QTabBar::tab:first {
            margin-left: 2px;  /* 第一个tab左边距 */
        }

        QTabBar::tab:last {
            margin-right: 2px;  /* 最后一个tab右边距 */
        }

        QTabBar::tab:selected {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                       stop:0 #00b4ff, stop:1 #0077cc);
            color: #ffffff;
            border-color: #00aaff;
            margin-bottom: -1px;  /* 选中tab向下延伸 */
            padding-bottom: 9px;   /* 底部增加padding补偿margin */
        }

        QTabBar::tab:hover:!selected {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                       stop:0 #4a5a6a, stop:1 #3a4a5a);
            color: #ffffff;
        }

        QTabBar::tab:disabled {
            background: #333333;
            color: #666666;
        }

        /* 针对不同tab数量的调整 */
        QTabBar::tab:only-one {
            min-width: 120px;  /* 只有一个tab时宽度更大 */
        }

        /* 小尺寸tab（当tab数量较多时） */
        QTabBar::tab:small {
            padding: 6px 12px;
            min-width: 60px;
            font-size: 11px;
        }
        """

    @staticmethod
    def combo_box_style():
        return """
        QComboBox {
            background-color: #2a3440;
            border: 1px solid #556677;
            border-radius: 4px;
            padding: 1px 2px;
            font-size: 12px;
            color: #e0f0ff;
            min-width: 120px;
            font-family: "Microsoft YaHei", "Segoe UI";
        }

        QComboBox:hover {
            border: 1px solid #00aaff;
            background-color: #344050;
        }

        QComboBox:focus {
            border: 2px solid #00b4ff;
            background-color: #3a4555;
        }

        QComboBox::drop-down {
            subcontrol-origin: padding;
            subcontrol-position: top right;
            width: 20px;
            border-left: 1px solid #556677;
            border-top-right-radius: 3px;
            border-bottom-right-radius: 3px;
            background-color: #3a4555;
        }

        QComboBox::down-arrow {
            image: none;
            border-left: 4px solid transparent;
            border-right: 4px solid transparent;
            border-top: 5px solid #c0d0e0;
            width: 0px;
            height: 0px;
        }

        QComboBox::down-arrow:hover {
            border-top: 5px solid #ffffff;
        }

        QComboBox QAbstractItemView {
            background-color: #2a3440;
            border: 1px solid #556677;
            border-radius: 4px;
            selection-background-color: #00b4ff;
            outline: none;
            font-size: 12px;
            color: #e0f0ff;
        }

        QComboBox QAbstractItemView::item {
            padding: 2px 3px;
            color: #e0f0ff;
            border-bottom: 1px solid #445566;
        }

        QComboBox QAbstractItemView::item:hover {
            background-color: #344050;
            color: #ffffff;
        }

        QComboBox QAbstractItemView::item:selected {
            background-color: #00b4ff;
            color: #ffffff;
        }
        """

    @staticmethod
    def window_background_style():
        return """
        QMainWindow, QDialog {
            background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 1,
                                       stop: 0 #1a2530, stop: 1 #0f1720);
        }
        """

    @staticmethod
    def list_widget_style():
        return """
        QListWidget {
            background-color: #2a3440;
            border: 1px solid #445566;
            border-radius: 4px;
            color: #e0f0ff;
            font-family: "Microsoft YaHei", "Segoe UI";
            outline: none;
        }

        QListWidget::item {
            padding: 2px;
            border-bottom: 1px solid #445566;
            background-color: transparent;
        }

        QListWidget::item:selected {
            background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                            stop:0 #00b4ff, stop:1 #0077cc);
            color: #ffffff;
        }

        QListWidget::item:hover {
            background-color: #344050;
        }
        """

    @staticmethod
    def line_edit_style():
        return """
        QLineEdit {
            background-color: #2a3440;
            border: 1px solid #556677;
            border-radius: 4px;
            padding: 1px;
            color: #e0f0ff;
            font-family: "Microsoft YaHei", "Segoe UI";
            selection-background-color: #00b4ff;
        }

        QLineEdit:hover {
            border: 1px solid #00aaff;
            background-color: #344050;
        }

        QLineEdit:focus {
            border: 2px solid #00b4ff;
            background-color: #3a4555;
        }

        QLineEdit:disabled {
            background-color: #333333;
            color: #666666;
            border: 1px solid #555555;
        }
        """
