import os
import subprocess
import sys

# 需要加密的文件夹列表
TARGET_FOLDERS = ["algoVision", "base", "nuoyaStrategy", "tab", "thread"]

def run_cython():
    print(">>> 步骤1: 启动 Cython 编译加密...")
    # 调用你之前写的 build_cy.py
    subprocess.check_call([sys.executable, "build_cy.py"])

def toggle_source_code(hide=True):
    """
    hide=True: 将 .py 改名为 .py.bak (隐藏源码)
    hide=False: 将 .py.bak 改回 .py (恢复源码)
    """
    action = "隐藏" if hide else "恢复"
    print(f">>> 步骤2: {action} 源码文件...")
    for folder in TARGET_FOLDERS:
        for root, dirs, files in os.walk(folder):
            for file in files:
                # 排除 __init__.py，这个必须保留为源码格式
                if file.endswith(".py") and "__init__" not in file and hide:
                    os.rename(os.path.join(root, file), os.path.join(root, file + ".bak"))
                elif file.endswith(".py.bak") and not hide:
                    os.rename(os.path.join(root, file), os.path.join(root, file[:-4]))

if __name__ == "__main__":
    try:
        # 1. 编译为 .pyd
        run_cython()

        # 2. 隐藏 .py 源码
        toggle_source_code(hide=True)

        # 3. 执行你原有的 PyInstaller 打包逻辑
        # 这里可以直接调用你 build_pyinstaller.py 里的 build() 函数
        from build_pyinstaller import build
        build()

    finally:
        # 4. 无论成功失败，一定要恢复源码，方便下次开发
        toggle_source_code(hide=False)