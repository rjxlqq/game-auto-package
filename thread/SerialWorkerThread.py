import threading
import time

import serial
import serial.tools.list_ports


class SerialWorkerThread:
    """
    工业级串口线程化 HID 控制 (增强热插拔与心跳监测版)
    """

    def __init__(self):
        self.port_entry = None
        self.baudrate = 115200
        self.ser = None
        self.is_open = False
        self.running = False
        self.lock = threading.Lock()  # 保证串口写入线程安全

        # 新增/修正初始化变量
        self.last_ping_time = time.time()
        self.heartbeat_interval = 3.0  # 每3秒检查一次

    def _find_port(self):
        """自动查找 USB CDC 串口"""
        for p in serial.tools.list_ports.comports():
            # 兼容更多 ESP32/CDC 设备描述 [cite: 1]
            if any(kw in p.description.upper() for kw in ["USB", "CDC", "CH340", "CP210"]):
                return p.device
        return None

    def _handle_disconnect(self):
        """统一清理失效连接"""
        with self.lock:
            if self.ser:
                try:
                    self.ser.close()
                    print("⚠️ 串口已关闭")
                except:
                    pass
                self.ser = None

    def _monitor_loop(self):
        """核心监控线程：处理自动连接、热插拔、逻辑心跳"""
        while self.running:
            # 状态1：未连接 -> 尝试寻找并连接
            if self.ser is None or not self.ser.is_open:
                port = self._find_port()
                if port:
                    try:
                        self.ser = serial.Serial(port, self.baudrate, timeout=0.1)
                        time.sleep(2)  # 等待硬件初始化 [cite: 4]
                        self.last_ping_time = time.time()
                        print(f"✅ 设备已接入: {port}")
                        self.is_open = True
                    except Exception as e:
                        print(f"❌ 连接失败: {e}")
                        self.ser = None
                        self.is_open = False
            # 状态2：已连接 -> 检查物理和逻辑存活
            else:
                try:
                    # 1. 物理层检查：检查设备是否还在系统列表中
                    current_ports = [p.device for p in serial.tools.list_ports.comports()]
                    if self.ser.port not in current_ports:
                        print("🚨 检测到设备物理拔出")
                        self._handle_disconnect()
                        continue
                    # 2. 逻辑层检查：定时发送心跳
                    if time.time() - self.last_ping_time > self.heartbeat_interval:
                        if self.send_command("PING", wait=True):
                            self.last_ping_time = time.time()
                        else:
                            print("💔 心跳无响应，尝试重连...")
                            self._handle_disconnect()

                except Exception as e:
                    print(f"监控异常: {e}")
                    self._handle_disconnect()

            time.sleep(1)  # 轮询频率

    def start_thread(self):
        """开启监控线程"""
        if not self.running:
            self.running = True
            threading.Thread(target=self._monitor_loop, daemon=True).start()
            print("🚀 串口监控线程已启动")

    def send_command(self, command: str, wait=True):
        """带锁的命令发送"""
        if not self.ser or not self.ser.is_open:
            return False

        with self.lock:
            try:
                # 清除旧的输入缓冲，防止读取到之前的 OK
                self.ser.reset_input_buffer()
                self.ser.write((command + "\n").encode('utf-8'))

                if wait:
                    start_time = time.time()
                    while time.time() - start_time < 1.0:  # 1秒超时
                        if self.ser.in_waiting:
                            line = self.ser.readline().decode(errors='ignore').strip()
                            if "OK" in line or "PONG" in line:
                                return True
                    time.sleep(0.01)
                    return False  # 等待超时
                return True
            except Exception as e:
                print(f"✗ 发送异常: {e}")
                return False

    def stop_thread(self):
        """停止所有逻辑"""
        self.running = False
        self._handle_disconnect()
