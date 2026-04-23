--------------------------------------------------------------------------------------------------------------------------------------------------------------------------

# labelstudio

# 安装

conda create -n labelstudio python=3.10

pip install label-studio

pip install "label-studio<2.0"  安装低版本的 不然报错了

# 启动

conda activate labelstudio

label-studio start

# 仓库迁移

在 “用户变量”（上方那个框）点击 “新建”：

变量名：LABEL_STUDIO_BASE_DATA_DIR

变量值：D:\project\yolo-ocr\label-studio（或者你想要的 D 盘具体路径）。

#重置密码
label-studio reset_password --username rjxlqq@163.com

docker版本：
搜索镜像 heartexlabs/label-studio:develop
安装好镜像后，启动容器就好了


--------------------------------------------------------------------------------------------------------------------------------------------------------------------------

# 依赖安装：

# 导入到 requirements.txt 生成全部的依赖

pip freeze > requirements.txt

pip install pipreqs

# 生成引用的依赖

pipreqs ./ --encoding=utf8 --force

模型名字：
global_model
classify_model

--------------------------------------------------------------------------------------------------------------------------------------------------------------------------

# 首先 激活虚拟环境 重要

conda activate XXX

# 激活全局变量 添加全局变量

# C:\ProgramData\anaconda3

# C:\ProgramData\anaconda3\Scripts

# C:\ProgramData\anaconda3\Library\bin

# 对于 Windows 命令提示符 (cmd)  在 C:\ProgramData\anaconda3 文件夹中执行命令

conda init cmd.exe

# 对于 Windows PowerShell

conda init powershell

# 复制环境

conda create --name yolo-ocr --clone yolo_ocr

# 删除环境

conda remove --name myenv --all

# 项目目录

tree /f

# 清除缓存

pip cache purge

# 批量卸载依赖包 谨慎使用！！！！

pip freeze | Select-String -NotMatch "^(pip|setuptools)" | ForEach-Object { pip uninstall -y ($_ -split "==")[0] }

--------------------------------------------------------------------------------------------------------------------------------------------------------------------------

# yolo-ocr环境 yolo_ocr_package

pip install torch==2.7.1 torchvision==0.22.1 torchaudio==2.7.1 --index-url https://download.pytorch.org/whl/cu118

pip install ultralytics==8.3.196

pip install paddlepaddle-gpu==3.2.2 -i https://www.paddlepaddle.org.cn/packages/stable/cu118/

pip install paddleocr==3.2.0

# 只需要一种  opencv-contrib-python  如果有干扰执行以下命令

pip uninstall opencv-python opencv-contrib-python opencv-python-headless -y

pip install opencv-contrib-python==4.8.1.78 -i https://pypi.tuna.tsinghua.edu.cn/simple

pip install numpy==1.26.4

pip install pyqt5

pip install pyserial

# 打包工具安装

pip installl PyInstaller
--------------------------------------------------------------------------------------------------------------------------------------------------------------------------

# yolo-train 环境

# 完全卸载当前版本

pip uninstall torch torchvision torchaudio -y

# 清除pip缓存（重要！）

pip cache purge

# 不要相信依赖包文件 一定要手动安装！

pip install torch==2.7.1 torchvision==0.22.1 torchaudio==2.7.1 --index-url https://download.pytorch.org/whl/cu118
pip install ultralytics==8.3.196
pip install numpy==2.2.6

# 这俩可以为最新，否则报错

pip install opencv-python 4.12.0.88
pip install opencv-python-headless 4.12.0.88

--------------------------------------------------------------------------------------------------------------------------------------------------------------------------

# 本地训练安装

# crnn 文本识别

# db_net 文本检测

原图 → DBNet检测 → 文本区域裁剪 → CRNN识别

# ocr-train环境  Python 3.9.25

pip install paddlepaddle-gpu==3.2.2 -i https://www.paddlepaddle.org.cn/packages/stable/cu118/

pip install paddleocr==3.2.0

pip install numpy==1.26.4

pip install opencv-python==4.8.1.78

pip install opencv-python-headless==4.8.1.78

# 可能缺少以下依赖包

pip install scikit-image

pip install albumentations

pip install lmdb

pip install rapidfuzz

# 脚本训练,导出的为训练格式

# crnn脚本训练

# python tools/train.py -c configs/rec/my_rec_crnn.yml

# db_net脚本训练

# python tools/train.py -c configs/det/my_det_db.yml

# 转换识别模型-由训练类型转为推理类型

# python tools/export_model.py -c configs/rec/my_rec_crnn.yml -o Global.pretrained_model=./my_train/output/crnn/best_model/model Global.save_inference_dir=./my_train/output/crnn_inference/

# 转换检测模型-由训练类型转为推理类型

# python tools/export_model.py -c configs/det/my_det_db.yml -o Global.pretrained_model=./my_train/output/db_net/latest Global.save_inference_dir=./my_train/output/db_net_inference/

--------------------------------------------------------------------------------------------------------------------------------------------------------------------------

# pplabel环境   Python 3.9.25

pip install paddlepaddle-gpu

pip install paddlepaddle

pip install paddleocr

pip install PPOCRLabel

pip install "paddlex[ocr]"

# 启动   PPOCRLabel

PPOCRLabel --lang ch

--------------------------------------------------------------------------------------------------------------------------------------------------------------------------

# paddocr实例传参：

参数名称,参数说明,参数类型,默认值
doc_orientation_classify_model_name,文档方向分类模型的名称。如果设置为 None，将会使用产线默认模型。,str/None,None
doc_orientation_classify_model_dir,文档方向分类模型的目录路径。如果设置为 None，将会下载并加载模型。,str/None,None
doc_unwarping_model_name,文本切图矫正模型的名称。如果设置为 None，将会使用产线默认模型。,str/None,None
doc_unwarping_model_dir,文本切图矫正模型的目录路径。如果设置为 None，将会下载并加载模型。,str/None,None
text_detection_model_name,文本检测模型的名称。如果设置为 None，将会使用产线默认模型。,str/None,None
text_detection_model_dir,文本检测模型的目录路径。如果设置为 None，将会下载并加载模型。,str/None,None
textline_orientation_model_name,文本行方向检测模型的名称。如果设置为 None，将会使用产线默认模型。,str/None,None
textline_orientation_model_dir,文本行方向检测模型的目录路径。如果设置为 None，将会下载并加载模型。,str/None,None
textline_orientation_batch_size,文本行方向检测的 batch size。如果设置为 None，将默认使用 batch_size=1。,int/None,None
text_recognition_model_name,文本识别模型的名称。如果设置为 None，将会使用产线默认模型。,str/None,None
text_recognition_model_dir,文本识别模型的目录路径。如果设置为 None，将会下载并加载模型。,str/None,None
text_recognition_batch_size,文本识别预测的 batch size。如果设置为 None，将默认使用 batch_size=10。,int/None,None
is_doc_orientation_classify,是否启用文档方向分类功能。如果设置为 None，将依据产线的默认配置确定其数值，默认设定为 True。,bool/None,None
is_doc_unwarping,是否启用矫正文本切图的功能。如果设置为 None，将依据产线的默认配置确定其数值，默认设定为 True。,bool/None,None
is_textline_orientation,是否启用对文本行进行方向检测。如果设置为 None，将依据产线的默认配置确定其数值，默认设定为 True。,bool/None,None
text_det_limit_side_len,文本检测器的边长限制：• int: 大于 0 的任意整数；• None: 如果设置为 None，将采用产线初始化的参数数值，默认设定为 960。,int/None,None
text_det_limit_type,文本检测器的边长限制类型：• min: 表示 min_side_len，表示小的边长不能够小于 text_det_limit_side_len，但是其较大的边长并不会大于 limit_side_len；• None: 如果设置为
None，将采用产线初始化的参数数值，默认设定为 max。,str/None,None
text_det_thresh,文本检测阈值。如果设置为 None，将从对应产线的预测逻辑中去读取。,float/None,None
text_det_box_thresh,文本检测框的阈值。如果设置为 None，将从对应产线的预测逻辑中去读取。,float/None,None
text_det_unclip_ratio,文本检测框的膨胀系数。如果设置为 None，将从对应产线的预测逻辑中去读取。,float/None,None
text_det_input_shape,文本检测的输入形状。,tuple/None,None
text_rec_score_thresh,文本识别阈值。得分大于该阈值的文本结果会被保留。• float: 大于 0 的任意浮点数；• None: 如果设置为 None，将采用产线初始化的参数数值，默认设定为 0.5。,float/None,None
text_rec_input_shape,文本识别的输入形状。,tuple/None,None
lang,使用的模型对应的语言种类。具体的参数请参考官网文档。,str/None,None
ocr_version,OCR 模型的版本。主要包括：• PP-OCRv2: 使用 PP-OCRv2 的系列模型；• PP-OCRv3: 使用 PP-OCRv3 的系列模型；• PP-OCRv4: 使用 PP-OCRv4 的系列模型。,str/None,None
device,表示预测的设备，其支持设定如下名称：• gpu: 用 gpu 表示使用 GPU 进行推理；• gpu:0: 用 gpu:0 表示使用第 1 块 GPU 进行推理；• npu: 用 npu 表示使用 NPU 进行推理；• xpu: 用 xpu 表示使用 XPU 进行推理；•
mlu: 用 mlu 表示使用 MLU 进行推理；• dcu: 用 dcu 表示使用 DCU 进行推理；• None: 如果设置为 None，将其从使用产线初始化的参数数值，默认设定为：优先检测本地环境的 GPU 设备，如果没有，则使用 CPU
设备。,str/None,None
enable_mkldnn,是否启用 MKLDNN。,bool,True
cpu_threads,在 CPU 上进行推理时使用的线程数。,int,10
paddleocr_config,PaddleOCR 的配置文件路径。,str/None,None
--------------------------------------------------------------------------------------------------------------------------------------------------------------------------

# paddocr训练文件配置参数

# PaddleOCR v3.2 CRNN 文本识别全参数配置词典 (Full Reference)

本文件详细记录了 PaddleOCR v3.2 识别配置文件（YAML）中所有可配置变量及其功能含义。

--------------------------------------------------------------------------------------------------------------------------------------------------------------------------

## 1. Global (全局配置模块)

控制训练、评估、保存和日志的核心环境参数。

- **use_gpu**: [bool] 是否使用 GPU。如果是 CPU 环境请设为 false。
- **epoch_num**: [int] 训练总轮数。
- **log_smooth_window**: [int] 训练日志打印 Loss 的平滑窗口大小。
- **print_batch_step**: [int] 每隔多少个 iter 打印一次训练日志。
- **save_model_dir**: [str] 模型保存、日志保存的根目录。
- **save_epoch_step**: [int] 每隔多少个 epoch 保存一次检查点（checkpoint）。
- **eval_batch_step**: [list/int] 进行验证（Eval）的频率。如 `[0, 2000]` 表示从 0 次开始，每 2000 次 iter 验证一次。
- **cal_metric_during_train**: [bool] 训练过程中是否计算准确率等指标。
- **pretrained_model**: [str] 加载预训练模型的路径（不需要后缀名）。
- **checkpoints**: [str] 断点续训模型路径，加载后会同步 epoch 和优化器状态。
- **save_inference_dir**: [str] 导出推理模型（inference model）的默认路径。
- **use_visualdl**: [bool] 是否启动 VisualDL 记录训练曲线。
- **infer_img**: [str] 预测时使用的单张图片路径。
- **character_dict_path**: [str] 字典文件路径（.txt），每行一个字符。
- **max_text_length**: [int] 模型能识别的最大字符长度。
- **use_space_char**: [bool] 是否识别空格符。
- **use_distillation**: [bool] 是否开启蒸馏（通常在 PP-OCR 系列中使用）。

---

## 2. Optimizer & Lr (优化器与学习率模块)

控制梯度更新逻辑。

### Lr (学习率策略)

- **name**: [str] 策略名称。常用 `Cosine` (余弦衰减), `Linear` (线性衰减), `Piecewise` (分段衰减)。
- **learning_rate**: [float] 初始学习率。
- **warmup_epoch**: [int] 热身阶段轮数。初期以极小学习率缓慢上升。

### Optimizer (优化器)

- **name**: [str] 算法名称。CRNN 常用 `Adam` 或 `Momentum`。
- **beta1**: [float] Adam 参数。
- **beta2**: [float] Adam 参数。
- **weight_decay**: [float] L2 正则化系数，防止过拟合。

---

## 3. Architecture (模型组网模块)

定义 CRNN 的三大件：Backbone, Neck, Head。

### Backbone (骨干网络)

- **name**: [str] 常用 `MobileNetV3` (轻量化) 或 `ResNet` (高精度)。
- **model_name**: [str] MobileNetV3 可选 `small` 或 `large`。
- **scale**: [float] 模型宽度缩放倍数。
- **last_conv_stride**: [int] 最后一层卷积步长，通常设为 1 以保证特征分辨率。

### Neck (序列编码)

- **name**: [str] CRNN 必须使用 `SequenceEncoder`。
- **encoder_type**: [str] 必须设为 `rnn`。
- **hidden_size**: [int] RNN 隐藏层神经元数量，常见 `96` 或 `256`。

### Head (预测输出)

- **name**: [str] CRNN 对应 `CTCHead`。
- **fc_decay**: [float] 输出层（全连接层）的权重衰减。

---

## 4. Loss (损失函数)

- **name**: [str] 对于 CRNN，必须设为 `CTCLoss`。

---

## 5. PostProcess (后处理)

- **name**: [str] `CTCLabelDecode`。
- **character_dict_path**: [str] 再次确认字典路径，与 Global 保持一致。
- **use_space_char**: [bool] 是否输出空格。

---

## 6. Train/Eval Dataset (数据集与数据加载)

定义数据的输入流水线。

- **name**: [str] `SimpleDataSet` (文本行格式) 或 `LMDBDataSet`。
- **data_dir**: [str] 图片存储的根目录。
- **label_file_list**: [list] 标注文件列表。
- **ratio_list**: [list] 多个数据集混合训练时的采样权重。

### DataLoader (读取器)

- **batch_size_per_card**: [int] 每张显卡的 Batch 大小。
- **drop_last**: [bool] 是否丢弃最后一个不完整的 batch。
- **num_workers**: [int] 数据读取的多线程数。

### Transforms (数据增强/算子)

1. **DecodeImage**:
    - `img_mode`: BGR/RGB
    - `channel_first`: False
2. **IAAAugment**: 图像增强算子（模糊、抖动等）。
3. **RecAug**: 针对识别任务的专用增强。
4. **CTCLabelEncode**: 文本转数字索引。
5. **RecResizeImg**:
    - `image_shape`: [通道, 高, 宽]，CRNN 默认为 `[3, 32, 320]`。
6. **KeepKeys**: 传递给模型的 Key 列表，通常包含 `['image', 'label', 'length']`。

---

## 📝 核心调参逻辑 (Dictionary Reference)

| 场景             | 调整方向                                                  |
|:---------------|:------------------------------------------------------|
| **显存溢出 (OOM)** | 调小 `batch_size_per_card` 或 `RecResizeImg` 的宽度。        |
| **字典不匹配**      | 检查 `character_dict_path` 和 `PostProcess` 中的字典是否一致。    |
| **识别极短/极长文本**  | 修改 `max_text_length` 和 `RecResizeImg` 中的宽度。           |
| **精度提升**       | 将 `Backbone` 换为 `ResNet34_vd` 并加载 `pretrained_model`。 |

# self.serial_worker_thread.send_command('COMBO|ALT+a')

# self.serial_worker_thread.send_command('COMBO|CTRL+ESC')

# self.serial_worker_thread.send_command('KEY|TAB')

# self.serial_worker_thread.send_command('KD|r')

# self.serial_worker_thread.send_command('KU|r')

# self.serial_worker_thread.send_command('KP|r')

# self.serial_worker_thread.send_command('KEY|TAB')

# self.serial_worker_thread.send_command('KEY|BACKSPACE')

# self.serial_worker_thread.send_command('KEY|ESC')

# self.serial_worker_thread.send_command('MB|L,1')

# self.serial_worker_thread.send_command('MB|L,0')

# self.serial_worker_thread.send_command('MB|R,1')

# self.serial_worker_thread.send_command('MB|R,0')

# self.serial_worker_thread.send_command('TYPE|AAAAAQWQFQWF')

================ 串口 HID 控制协议 =================

所有命令格式统一为：
CMD|ARG\n

ESP32 执行完成后会返回：
OK
心跳命令返回：
PONG

---------------------------------------------------
一、键盘相关命令
---------------------------------------------------
注意大小写
1️⃣ KP（Key Print）
功能：
发送一个可打印字符（立即按下并释放）
底层实现：
Keyboard.write(char)

    示例：
        KP|A
        KP|1
        KP|@

---------------------------------------------------

2️⃣ KD（Key Down）
功能：
按下某个按键并保持不放
底层实现：
Keyboard.press(char)

    示例：
        KD|W        # 常用于游戏移动
        KD|A

---------------------------------------------------

3️⃣ KU（Key Up）
功能：
释放某个已按下的按键
底层实现：
Keyboard.release(char)

    示例：
        KU|W
        KU|A

---------------------------------------------------

4️⃣ TYPE（Text Input）
功能：
连续输入一段文本
底层实现：
Keyboard.print(text)

    示例：
        TYPE|Hello World
        TYPE|123456

---------------------------------------------------

5️⃣ KEY（特殊功能键）
功能：
发送单个“非字符键”
底层实现：
Keyboard.press(KEY_xxx) + release

    支持的键名：
        ENTER
        TAB
        ESC

        SPACE

    示例：
        KEY|ENTER
        KEY|TAB
        KEY|ESC

---------------------------------------------------

6️⃣ COMBO（组合键）
功能：
发送组合键（修饰键 + 主键）
底层实现：
Keyboard.press(修饰键)
Keyboard.press(主键)
Keyboard.releaseAll()

    支持修饰键：
        CTRL
        ALT
        SHIFT

    示例：
        COMBO|CTRL+C     # 复制
        COMBO|ALT+TAB    # 切换窗口
        COMBO|SHIFT+A

⚠️ 限制说明：
- 仅支持：一个修饰键 + 一个主键
- 不支持 CTRL+SHIFT+A 这种多修饰键（可扩展）

---------------------------------------------------
二、鼠标相关命令
---------------------------------------------------

7️⃣ MM（Mouse Move）
功能：
鼠标相对移动（非屏幕绝对坐标）
底层实现：
Mouse.move(dx, dy)

    示例：
        MM|10,-5     # 向右 10，向上 5
        MM|-20,0

---------------------------------------------------

8️⃣ MS（Mouse Scroll）
功能：
鼠标滚轮滚动
底层实现：
Mouse.move(0, 0, wheel)

    示例：
        MS|1         # 向上滚
        MS|-3        # 向下滚 3 格

---------------------------------------------------

9️⃣ MB（Mouse Button）
功能：
鼠标按键按下或释放
底层实现：
Mouse.press(button)
Mouse.release(button)

    按键定义：
        L = 左键
        M = 中键
        R = 右键

    状态定义：
        1 = 按下
        0 = 释放

    示例：
        MB|L,1       # 左键按下
        MB|L,0       # 左键释放
        MB|R,1       # 右键按下

---------------------------------------------------
三、心跳与安全机制
---------------------------------------------------

🔁 PING（心跳）
功能：
保持 ESP32 与 PC 通信在线
防止键盘/鼠标卡死
示例：
PING

    ESP32 返回：
        PONG

🛡 安全策略：
- ESP32 10 秒未收到 PING：
自动 Keyboard.releaseAll()
- PC 掉线后：
自动重连 CDC 串口






