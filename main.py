# main.py
import sys
import time

from PyQt5.QtCore import Qt, QPropertyAnimation, QEasingCurve
from PyQt5.QtGui import QPixmap, QIcon
from PyQt5.QtWidgets import QApplication, QSplashScreen, QDialog, QVBoxLayout, QLineEdit, QPushButton, QLabel, QMessageBox

# 导入你现有的样式类
from algoVision.style import StyleManager
from base.layout import layoutWindow


# 1. [核心] 强制限制并行计算库只准开 1 个线程，彻底干掉 libiomp 和 libopenblas 的线程池

# os.environ["OMP_NUM_THREADS"] = "1"
# os.environ["MKL_NUM_THREADS"] = "1"
# os.environ["OPENBLAS_NUM_THREADS"] = "1"
# os.environ["VECLIB_MAXIMUM_THREADS"] = "1"
# os.environ["NUMEXPR_NUM_THREADS"] = "1"
# # 2. [核心] 告诉 Paddle 别在显存里“圈地”
# os.environ['FLAGS_fraction_of_gpu_memory_to_use'] = '0.01'
# # 强制让 Paddle 采用“按需分配”策略，而不是一上来就划走 1% (1%在大内存机器上也不少)
# os.environ['FLAGS_allocator_strategy'] = 'naive_best_fit'
# # 限制单次申请的显存块大小，防止产生巨大的碎片
# os.environ['FLAGS_eager_delete_tensor_gb'] = '0.0'
# # 3. [可选] 解决 OpenSSL 报错
# os.environ['PYTHONHTTPSVERIFY'] = '0'


# -----------加载动画鼠标点击类----------------
class NonClickSplashScreen(QSplashScreen):
    def __init__(self, pixmap, flags):
        super().__init__(pixmap, flags)

    def mousePressEvent(self, event):
        # 重写鼠标按下事件：什么都不做，这样点击就不会消失
        pass

    def mouseDoubleClickEvent(self, event):
        # 同样屏蔽双击
        pass


# ---------------- 登录界面类 ----------------
class LoginDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("绝影 · 系统授权")
        self.setFixedSize(380, 280)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint | Qt.WindowStaysOnTopHint)
        self.setStyleSheet("QDialog { background-color: #1a222a; }")
        try:
            self.setWindowIcon(QIcon("assets/logo.ico"))
        except:
            pass
        layout = QVBoxLayout()
        layout.setSpacing(15)
        layout.setContentsMargins(40, 30, 40, 30)
        self.title_label = QLabel("绝影核心系统验证")
        self.title_label.setStyleSheet("color: #00b4ff; font-size: 18px; font-weight: bold;")
        self.title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.title_label)
        self.account_input = QLineEdit()
        self.account_input.setPlaceholderText("请输入授权账号")
        self.account_input.setStyleSheet(StyleManager.line_edit_style())
        self.account_input.setMinimumHeight(35)
        self.account_input.setText("admin")
        layout.addWidget(self.account_input)
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("请输入授权密码")
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setStyleSheet(StyleManager.line_edit_style())
        self.password_input.setMinimumHeight(35)
        self.password_input.setText("123456")
        layout.addWidget(self.password_input)
        self.login_btn = QPushButton("开启控制台")
        self.login_btn.setStyleSheet(StyleManager.primary_button_style())
        self.login_btn.setDefault(True)
        self.login_btn.clicked.connect(self.handle_login)
        layout.addWidget(self.login_btn)
        self.setLayout(layout)

    def handle_login(self):
        if self.account_input.text() == "admin" and self.password_input.text() == "123456":
            self.accept()
        else:
            QMessageBox.critical(self, "授权失败", "账号或密码错误！")


# ---------------- 动画执行函数 ----------------
def create_splash_animation(msg="绝影系统启动中..."):
    """创建启动页并返回对象，同时启动呼吸动画"""
    pixmap = QPixmap("assets/start.png").scaled(350, 350, Qt.KeepAspectRatio, Qt.SmoothTransformation)
    # --- 修改这里：将 QSplashScreen 换成 NonClickSplashScreen ---
    splash = NonClickSplashScreen(pixmap, Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)
    # -------------------------------------------------------
    splash.show()
    splash.showMessage(f"<font color='#f3d808' size='5'><b>{msg}</b></font>", Qt.AlignBottom | Qt.AlignCenter, Qt.white)
    fade_io = QPropertyAnimation(splash, b"windowOpacity")
    fade_io.setDuration(1500)
    fade_io.setStartValue(0.4)
    fade_io.setStartValue(0.5)
    fade_io.setStartValue(0.6)
    fade_io.setStartValue(0.7)
    fade_io.setStartValue(0.8)
    fade_io.setEndValue(1.0)
    fade_io.setEasingCurve(QEasingCurve.InOutCubic)
    fade_io.setLoopCount(-1)
    fade_io.start()
    # 将动画对象绑定到 splash 上防止被销毁
    splash.animation = fade_io
    return splash


# ---------------- 主程序 ----------------
# main.py
def main():
    app = QApplication(sys.argv)

    # 1. 启动动画
    initial_splash = create_splash_animation("绝影系统启动中...")
    # 将 splash 挂载到 app 方便全局访问
    app.active_splash = initial_splash

    # 强制展示一段时间
    start_time = time.time()
    while time.time() - start_time < 1.5:
        app.processEvents()
        time.sleep(0.01)

    # 2. 准备登录
    login = LoginDialog()

    # --- 核心修改：在弹出登录框前，先隐藏加载动画 ---
    initial_splash.hide()

    # login.exec_() 会阻塞在这里，直到用户登录或关闭
    if login.exec_() == QDialog.Accepted:
        # 登录成功，重新显示加载动画，继续后面的模型初始化过程
        initial_splash.show()
        # 确保动画回到最顶层（可选）
        initial_splash.raise_()

        # 声明全局变量防止 main_win 被回收导致闪退
        global main_win
        main_win = layoutWindow()
        main_win.show()

        sys.exit(app.exec_())
    else:
        # 如果登录取消，彻底关闭
        initial_splash.close()
        sys.exit(0)

if __name__ == "__main__":
    main()
