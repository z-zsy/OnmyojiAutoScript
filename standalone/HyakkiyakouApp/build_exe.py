# build_exe.py - 百鬼夜行独立版一键 PyInstaller 编译打包脚本
import os
import sys
import shutil
import subprocess
from pathlib import Path

def build():
    root_dir = Path(__file__).resolve().parent
    dist_dir = root_dir / "dist"
    build_dir = root_dir / "build"
    app_entry = root_dir / "app.py"

    print("==================================================")
    print("🔨 开始编译百鬼夜行独立版 EXE...")
    print(f"📁 工作目录: {root_dir}")
    print("==================================================")

    # 1. 组装 PyInstaller 参数
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--noconfirm",
        "--onedir",                  # 编译为便携式文件夹 (启动秒开，便于补丁热插拔更新)
        "--windowed",                # 窗口化运行 (无黑色控制台窗口)
        "--name=百鬼夜行独立版",
        f"--distpath={dist_dir}",
        f"--workpath={build_dir}",
        f"--paths={root_dir}",
        # 收集必要模块与排除无用模块
        "--copy-metadata=onnxruntime",
        "--collect-submodules=onnxruntime",
        "--collect-binaries=onnxruntime",
        "--hidden-import=PySide6.QtCore",
        "--hidden-import=PySide6.QtGui",
        "--hidden-import=PySide6.QtWidgets",
        "--exclude-module=PySide6.QtWebEngineCore",
        "--exclude-module=PySide6.QtWebEngineWidgets",
        "--exclude-module=PySide6.Qt3DCore",
        "--exclude-module=PySide6.Qt3DRender",
        "--exclude-module=PySide6.QtQuick",
        "--exclude-module=PySide6.QtSpatialAudio",
        # 打包关键数据文件与模型
        f"--add-data={root_dir / 'oashya' / 'oashya_fp32.onnx'}{os.pathsep}oashya",
        f"--add-data={root_dir / 'oashya' / 'tracker.cp310-win_amd64.pyd'}{os.pathsep}oashya",
        f"--add-data={root_dir / 'oashya' / 'patches'}{os.pathsep}oashya/patches",
        f"--add-data={root_dir / 'resources' / 'assets'}{os.pathsep}resources/assets",
        str(app_entry)
    ]

    print("🚀 执行 PyInstaller 命令:")
    print(" ".join(cmd))
    print()

    ret = subprocess.call(cmd, cwd=str(root_dir))
    if ret != 0:
        print(f"❌ 打包失败，退出码: {ret}")
        sys.exit(ret)

    # 2. 将默认配置文件复制到打包目录
    output_app_dir = dist_dir / "百鬼夜行独立版"
    config_src = root_dir / "config.json"
    if config_src.exists():
        shutil.copy2(config_src, output_app_dir / "config.json")

    print("\n==================================================")
    print("🎉 恭喜！百鬼夜行独立版 EXE 打包编译成功！")
    print(f"📦 输出路径: {output_app_dir.resolve()}")
    print("🚀 双击运行: 百鬼夜行独立版.exe 即可直接使用！")
    print("==================================================")

if __name__ == '__main__':
    build()
