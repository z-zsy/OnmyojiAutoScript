# app.py - 百鬼夜行独立版桌面程序入口
import sys
import os
from pathlib import Path

# 确保本应用根目录在 sys.path 首位
APP_DIR = Path(__file__).resolve().parent
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

# 适配 PyInstaller 打包环境
if hasattr(sys, '_MEIPASS'):
    os.chdir(sys._MEIPASS)

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt
from gui.main_window import MainWindow

def main():
    # 启用高 DPI 支持
    QApplication.setHighDpiScaleFactorRoundingPolicy(Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)
    
    app = QApplication(sys.argv)
    app.setApplicationName("Hyakkiyakou Standalone")
    app.setOrganizationName("OnmyojiAutoScript")
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())

if __name__ == '__main__':
    main()
