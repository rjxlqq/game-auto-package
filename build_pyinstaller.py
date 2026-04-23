import importlib.metadata
import os
import shutil
import subprocess
import sys

import paddlex

# ================= 配置区（路径已根据你的环境写死） =================
# 主程序入口文件路径
MAIN_FILE = r"D:\project\game-auto\main.py"

# 输出目录名称
DIST_NAME = "jueying"

# 修改为你的图标文件路径
ICON_FILE = r"D:\project\game-auto\assets\logo.ico"

# =================================================================
EXTRA_RESOURCES = [
    "assets",  # 图标
    "detection",  # YOLO模型文件
    "textDetection",  # ocr模型文件
]


def copy_extra_resources():
    """将额外资源文件复制到打包目录"""
    print(">>> 正在复制额外资源文件...")

    dist_path = os.path.join("dist", DIST_NAME)
    project_root = os.path.dirname(MAIN_FILE)

    for resource in EXTRA_RESOURCES:
        src_path = os.path.join(project_root, resource)
        dst_path = os.path.join(dist_path, resource)

        if os.path.exists(src_path):
            if os.path.isdir(src_path):
                if os.path.exists(dst_path):
                    shutil.rmtree(dst_path)
                shutil.copytree(src_path, dst_path)
                print(f"✅ 已复制文件夹: {resource}")
            else:
                shutil.copy2(src_path, dst_path)
                print(f"✅ 已复制文件: {resource}")
        else:
            print(f"⚠️  警告: 资源文件不存在 - {src_path}")


def build():
    print(f">>> 正在分析 PaddleX 依赖并准备元数据...")

    # 自动获取环境内所有包名
    user_deps = [dist.metadata["Name"] for dist in importlib.metadata.distributions()]
    # 获取 PaddleX 官方要求的依赖列表
    deps_all = list(paddlex.utils.deps.DEP_SPECS.keys())
    # 筛选重合部分，用于拷贝 metadata（解决 .version 找不到的问题）
    deps_need = [dep for dep in user_deps if dep in deps_all]

    # 构建 PyInstaller 命令
    cmd = [
        sys.executable, "-m", "PyInstaller",
        MAIN_FILE,
        "--name", DIST_NAME,
        "--onedir",  # 生成文件夹模式，方便手动补全
        # "--onefile",  # 打包为一个文件
        "--noconfirm",  # 自动覆盖现有 dist 目录
        "--noconsole",  # 不带控制台
        "--clean",  # 清理缓存
        "--icon", ICON_FILE,
        "--collect-data", "paddlex",
        "--collect-binaries", "paddle",
        "--collect-binaries", "nvidia",
        "--collect-submodules", "paddleocr",
        "--collect-data", "ultralytics",
        "--collect-submodules", "cv2",
    ]

    # 自动注入元数据拷贝参数，修复 paddlex 运行时版本检查
    for dep in deps_need:
        cmd += ["--copy-metadata", dep]

    print(f">>> 启动 PyInstaller，命令详情: {' '.join(cmd)}")

    try:
        # 清理旧目录
        if os.path.exists("dist"): shutil.rmtree("dist")
        if os.path.exists("build"): shutil.rmtree("build")
        # 执行打包过程
        subprocess.run(cmd, check=True)
        copy_extra_resources()
        print("\n✅ 打包任务顺利结束！")
    except subprocess.CalledProcessError as e:
        print(f"❌ PyInstaller 运行失败: {e}")
    except Exception as e:
        print(f"❌ 后处理文件拷贝失败: {e}")


if __name__ == "__main__":
    build()
