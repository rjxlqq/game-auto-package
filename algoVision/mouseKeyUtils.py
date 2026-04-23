import gc
import random
import time
from functools import wraps

from PyQt5.QtGui import QCursor


def auto_cleanup(func):
    """
    清理内存装饰器：
    专门用于 YOLO 识别、OCR 扫描等产生大数组的高频函数。
    """

    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        finally:
            # 1. 显式清理局部变量引用（如果函数内部没写 del）
            # 2. 触发 0 代垃圾回收，回收效率最高且耗时极短
            gc.collect(0)

    return wrapper


class MouseKeyUtils:
    # 移动后点击 有锁
    @auto_cleanup
    def smart_move_click_lock(self, target_x, target_y, mouse_type='L', threshold=3, max_attempts=5):
        with self.action_lock:
            self.smart_move_click(self, target_x, target_y, mouse_type, threshold, max_attempts)

    # 移动后点击 无锁
    @auto_cleanup
    def smart_move_click(self, target_x, target_y, mouse_type='L', threshold=3, max_attempts=5):
        """
        智能微调点击：
        如果不满足 threshold，则进行微调补偿，直到到位后再点击。
        """
        try:
            SCREEN_WIDTH, SCREEN_HEIGHT = 1920, 1080
            for i in range(max_attempts):
                # 1. 获取当前实时位置
                curr = QCursor.pos()
                curr_x, curr_y = curr.x(), curr.y()

                # 2. 计算距离
                distance = ((target_x - curr_x) ** 2 + (target_y - curr_y) ** 2) ** 0.5

                # 3. 核心判断：如果到位了，直接点击并退出
                if distance < threshold:
                    btn = 'L' if mouse_type == 'L' else 'R'
                    if self.serial_worker_thread.send_command(f'MB|{btn},1'):
                        return self.serial_worker_thread.send_command(f'MB|{btn},0')
                    return True

                # 如果没到位，进行补偿移动
                # 映射坐标并发送 MM (对于硬件来说，重复发送 MM 会进行位置修正)
                abs_x = int(max(0, min((target_x / SCREEN_WIDTH) * 32767, 32767)))
                abs_y = int(max(0, min((target_y / SCREEN_HEIGHT) * 32767, 32767)))
                self.serial_worker_thread.send_command(f"MM|{abs_x},{abs_y}", wait=False)
                # 给硬件一点物理反应时间（微调等待）
                time.sleep(0.02)

            print(f"⚠️ 微调 {max_attempts} 次后仍未到位，放弃点击。")
            return False

        except Exception as e:
            print(f"❌ smart_move_click 异常: {e}")
            return False

    # ---鼠标移动函数 --------------------
    @auto_cleanup
    def move_mouse_to_target_human_lock(self, target_x, target_y):
        """
        带锁的拟人移动入口。
        """
        with self.action_lock:
            return self.move_mouse_to_target_human(target_x, target_y)

    # --- 核心算法函数：负责高速移动 -----------------
    @auto_cleanup
    def move_mouse_to_target_human(self, target_x, target_y):
        """
        自适应拟人移动：处理快速 / 超近 / 超远 三种场景（优化版 - 防卡顿/防爆炸）
        - 超远 (>600px)：大步 + 轻微变速 + 少量曲线感
        - 中距离：平衡速度与自然
        - 超近 (<50px)：小步、无扰动、极致精准
        """
        try:
            # 1. 设定你的屏幕分辨率
            SCREEN_WIDTH = 1920
            SCREEN_HEIGHT = 1080
            # 2. 将像素坐标映射到 HID 绝对坐标范围 (0 - 32767)
            # 算法：(当前坐标 / 屏幕总宽) * 32767
            abs_x = int((target_x / SCREEN_WIDTH) * 32767)
            abs_y = int((target_y / SCREEN_HEIGHT) * 32767)
            # 3. 边界限制
            abs_x = max(0, min(abs_x, 32767))
            abs_y = max(0, min(abs_y, 32767))
            # 4. 一次性发送指令
            # 使用 MA 命令，瞬间到达，无需循环计算偏移 MA直接瞬间移动 MM带轨迹移动。
            # success = self.serial_worker_thread.send_command(f"MA|{abs_x},{abs_y}", wait=False)
            success = self.serial_worker_thread.send_command(f"MM|{abs_x},{abs_y}", wait=False)
            return success
        except Exception as e:
            print(f"❌ 鼠标移动异常: {e}")
            return False

    # 鼠标快速点击----------------------
    @auto_cleanup
    def mouse_quick_click(self, mouse_type):
        with self.action_lock:
            if mouse_type == 'L':
                mouse_on_l = self.serial_worker_thread.send_command('MB|L,1')
                mouse_off = self.serial_worker_thread.send_command('MB|L,0')
                if mouse_on_l and mouse_off:
                    return True
            if mouse_type == 'R':
                mouse_on_r = self.serial_worker_thread.send_command('MB|R,1')
                mouse_off_r = self.serial_worker_thread.send_command('MB|R,0')
                if mouse_on_r and mouse_off_r:
                    return True
            return False

    # 键盘快速点击---------------
    @auto_cleanup
    def keyboard_quick_click(self, key_type):
        with self.action_lock:
            after_delay = random.uniform(0.05, 0.1)
            key_on = self.serial_worker_thread.send_command(f'KD|{key_type}')
            time.sleep(after_delay)
            key_off = self.serial_worker_thread.send_command(f'KU|{key_type}')
            if key_on and key_off: return True
            print('键盘点击失败')
            return False

    # 特殊键盘点击---------------------
    @auto_cleanup
    def combo_keyboard_quick_click(self, key_type):
        with self.action_lock:
            if self.serial_worker_thread.send_command(f'{key_type}'): return True
            return False
