# driver/device_driver.py - 统合设备驱动管理器 (支持PC客户端与各主流安卓模拟器ADB/NemuIPC)
import time
import subprocess
import cv2
import numpy as np
from typing import Optional, Tuple, List, Dict
from driver.win32_window import Win32Window
from core.logger import logger

class DeviceDriver:
    STANDARD_WIDTH = 1280
    STANDARD_HEIGHT = 720

    def __init__(self, mode: str = "PC 桌面客户端", serial: str = "auto", screenshot_method: str = "window_background", control_method: str = "window_message", window_title: str = "阴阳师-网易游戏"):
        self.mode = mode
        self.serial = serial
        self.screenshot_method = screenshot_method
        self.control_method = control_method
        self.window_title = window_title

        self.win32 = Win32Window(target_title=window_title)
        self.adb_bin: Optional[str] = self._find_adb_binary()
        self.adb_connected = False
        self._init_connection()

    def _find_adb_binary(self, custom_path: str = "auto") -> str:
        """寻找系统中的 adb 可执行文件"""
        if custom_path and custom_path != "auto":
            return custom_path
        for candidate in ["adb", "C:\\Program Files\\Netease\\MuMuPlayer-12.0\\shell\\adb.exe", "D:\\Program Files\\Netease\\MuMuPlayer-12.0\\shell\\adb.exe"]:
            try:
                res = subprocess.run([candidate, "version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=2)
                if res.returncode == 0:
                    return candidate
            except Exception:
                pass
        return "adb"

    @classmethod
    def test_adb_connection(cls, serial: str, custom_path: str = "auto") -> Tuple[bool, str]:
        """立即测试 ADB 端口连接并返回设备详情"""
        adb_bin = "adb"
        if custom_path and custom_path != "auto":
            adb_bin = custom_path
        else:
            for candidate in ["adb", "C:\\Program Files\\Netease\\MuMuPlayer-12.0\\shell\\adb.exe", "D:\\Program Files\\Netease\\MuMuPlayer-12.0\\shell\\adb.exe"]:
                try:
                    res = subprocess.run([candidate, "version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=2)
                    if res.returncode == 0:
                        adb_bin = candidate
                        break
                except Exception:
                    pass

        try:
            # 1. 执行 connect
            conn_res = subprocess.run([adb_bin, "connect", serial], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=3)
            # 2. 查询 devices
            dev_res = subprocess.run([adb_bin, "devices"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=3)
            
            if serial in dev_res.stdout and "device" in dev_res.stdout:
                return True, f"✅ 连接成功！\n\nADB 输出: {conn_res.stdout.strip()}\n在线设备列表:\n{dev_res.stdout.strip()}"
            else:
                return False, f"❌ 未能连接到设备 {serial}。\n\n提示: 请确保模拟器已启动并且开启了 USB/网络调试。\nADB 返回: {conn_res.stdout.strip()} {conn_res.stderr.strip()}"
        except Exception as e:
            return False, f"❌ 执行 ADB 测试出错: {e}\n(请检查 ADB 路径是否正确)"

    def _init_connection(self):
        if "PC" in self.mode:
            self.win32.find_window()
            if self.win32.is_valid():
                logger.info(f"[Driver] 成功绑定 PC 客户端窗口 [HWND: {self.win32.hwnd}]")
        else:
            # 模拟器 ADB 连接
            self._connect_adb()

    def _connect_adb(self):
        if self.serial == "auto":
            # 尝试常见模拟器端口
            ports = ["127.0.0.1:7555", "127.0.0.1:5555", "127.0.0.1:16384", "127.0.0.1:62001", "emulator-5554"]
        else:
            ports = [self.serial]

        for p in ports:
            try:
                subprocess.run([self.adb_bin, "connect", p], stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=2)
                res = subprocess.run([self.adb_bin, "devices"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=2)
                if p in res.stdout and "device" in res.stdout:
                    self.serial = p
                    self.adb_connected = True
                    logger.info(f"[Driver] 成功连接安卓模拟器 ADB: {p}")
                    return
            except Exception:
                pass

        # 尝试通过窗口截屏回退
        self.win32.find_window()

    def is_connected(self) -> bool:
        if "PC" in self.mode:
            return self.win32.is_valid()
        else:
            return self.adb_connected or self.win32.is_valid()

    def screenshot(self) -> Optional[np.ndarray]:
        """抓取画面并返回标准 1280x720 图像"""
        if "PC" in self.mode or "window" in self.screenshot_method.lower() or "bitblt" in self.screenshot_method.lower():
            return self.win32.screenshot()

        # ADB 截图
        if self.adb_connected:
            try:
                res = subprocess.run([self.adb_bin, "-s", self.serial, "exec-out", "screencap", "-p"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=3)
                if res.returncode == 0 and len(res.stdout) > 1000:
                    nparr = np.frombuffer(res.stdout, np.uint8)
                    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                    if img is not None:
                        h, w = img.shape[:2]
                        if w != self.STANDARD_WIDTH or h != self.STANDARD_HEIGHT:
                            img = cv2.resize(img, (self.STANDARD_WIDTH, self.STANDARD_HEIGHT), interpolation=cv2.INTER_AREA)
                        return img
            except Exception as e:
                logger.warning(f"[Driver] ADB 截屏异常，回退至窗口截屏: {e}")

        return self.win32.screenshot()

    def click(self, x: int, y: int, delay: float = 0.05):
        """点击目标坐标 (x, y)"""
        if "PC" in self.mode or "window" in self.control_method.lower():
            self.win32.click(x, y, delay=delay)
            return

        # ADB 点击
        if self.adb_connected:
            try:
                # 默认按 1280x720 发送 tap
                subprocess.Popen([self.adb_bin, "-s", self.serial, "shell", "input", "tap", str(x), str(y)])
                return
            except Exception:
                pass

        self.win32.click(x, y, delay=delay)

    def swipe(self, p1: Tuple[int, int], p2: Tuple[int, int], steps: int = 5, duration: float = 0.3):
        """滑动"""
        if "PC" in self.mode or "window" in self.control_method.lower():
            self.win32.swipe(p1, p2, steps=steps, duration=duration)
            return

        if self.adb_connected:
            try:
                dur_ms = int(duration * 1000)
                subprocess.Popen([self.adb_bin, "-s", self.serial, "shell", "input", "swipe", str(p1[0]), str(p1[1]), str(p2[0]), str(p2[1]), str(dur_ms)])
                return
            except Exception:
                pass

        self.win32.swipe(p1, p2, steps=steps, duration=duration)
