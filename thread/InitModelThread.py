import logging
import os
import sys
import warnings

from PyQt5.QtCore import QThread, pyqtSignal
from paddleocr import PaddleOCR
from ultralytics import YOLO


class InitModelThread(QThread):
    done = pyqtSignal(object, object, object)
    error_occurred = pyqtSignal(str)

    def run(self):
        try:
            print('开始加载模型')
            # --- 1. OCR 加载 (你的核心逻辑) ---
            logging.getLogger("paddlex").setLevel(logging.ERROR)
            logging.getLogger("paddleocr").setLevel(logging.ERROR)
            warnings.filterwarnings("ignore", category=UserWarning)
            det_path = self.resource_path("textDetection/PP-OCRv5_server_det/PP-OCRv5_server_det_infer")
            rec_path = self.resource_path("textDetection/PP-OCRv5_server_rec/PP-OCRv5_server_rec_infer")
            ocr = PaddleOCR(
                ocr_version='PP-OCRv5',  # 指定模型版本，v5 是目前精度与速度平衡最好的版本
                precision='fp16',
                det_model_dir=det_path,  # 文本检测模型路径，负责定位画面中的文字区域
                rec_model_dir=rec_path,  # 文本识别模型路径，负责将区域图片转为文字内容
                text_detection_model_name='PP-OCRv5_server_det',  # 指定使用 Server 版检测模型（精度高但内存占用大）
                text_recognition_model_name='PP-OCRv5_server_rec',  # 指定使用 Server 版识别模型（参数量多，适合复杂场景）
                use_doc_orientation_classify=False,  # 关闭文档方向分类，挂机画面固定不需要此功能，可省内存
                use_doc_unwarping=False,  # 关闭文本矫正，处理非扫描件时关闭可减少计算开销
                use_textline_orientation=False,  # 关闭行方向检测，防止与角度分类冲突并降低复杂度
                device='gpu',  # 强制指定推理设备为 GPU，减轻 CPU 负担
                # rec_batch_num=10,  # 限制识别批次为1，强制单行处理以压低显存/内存峰值
            )
            print('加载模型a成功')
            # --- 2. YOLO 加载 (你的核心逻辑) ---
            # 这里可以放你那段 find_local_yolo_model 的路径搜索逻辑
            # 简化演示直接加载
            global_yolo_path = self.resource_path("detection/global_model.pt")
            classify_yolo_path = self.resource_path("detection/classify_model.pt")
            # global_yolo_path = self.resource_path("detection/global_model.onnx")
            # classify_yolo_path = self.resource_path("detection/classify_model.onnx")
            global_yolo = YOLO(global_yolo_path, task='detect')
            classify_yolo = YOLO(classify_yolo_path, task='detect')
            self.done.emit(global_yolo, classify_yolo, ocr)
            print('加载模型b成功')
        except Exception as e:
            error_msg = f"模型加载失败详细原因: {str(e)}"
            print(f"❌ {error_msg}")
            # 发送错误信号
            self.error_occurred.emit(error_msg)

    def resource_path(self, relative_path):
        """ 获取资源绝对路径，兼容开发环境和 PyInstaller 打包环境 """
        if hasattr(sys, '_MEIPASS'):
            # PyInstaller 打包后的临时解压目录
            base_path = sys._MEIPASS
        else:
            # 开发环境下，可执行文件或脚本所在的绝对路径
            base_path = os.path.dirname(os.path.abspath(sys.argv[0]))

        # 直接拼接，不要用 os.walk 模糊查找
        path = os.path.join(base_path, relative_path)

        if not os.path.exists(path):
            # 最后的保底检查：如果拼接路径不存在，再尝试在当前工作目录查找
            path = os.path.join(os.getcwd(), relative_path)

        if not os.path.exists(path):
            raise FileNotFoundError(f"找不到资源文件: {path}")

        return path
