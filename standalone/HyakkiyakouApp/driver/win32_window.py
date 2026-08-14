# win32_window.py - 轻量级 Windows 游戏窗口驱动 (支持阴阳师PC桌面版与主流模拟器)
import time
import ctypes
import numpy as np
import cv2
import win32gui
import win32ui
import win32con
from typing import Optional, Tuple, List, Dict

# DPI Awareness
try:
    ctypes.windll.user32.SetProcessDPIAware()
except Exception:
    pass

class Win32Window:
    STANDARD_WIDTH = 1280
    STANDARD_HEIGHT = 720

    def __init__(self, target_title: str = "阴阳师-网易游戏"):
        self.target_title = target_title
        self.hwnd: Optional[int] = None
        self.find_window()

    def find_window(self) -> Optional[int]:
        """
        查找游戏窗口句柄 (优先精准匹配，其次模糊匹配)
        """
        self.hwnd = None
        
        # 1. 尝试精确查找
        hwnd = win32gui.FindWindow(None, self.target_title)
        if hwnd and win32gui.IsWindow(hwnd):
            self.hwnd = hwnd
            return self.hwnd

        # 2. 尝试模糊查找 (含 '阴阳师' 或 'MuMu' 或 '夜神' 或 '雷电')
        candidates = []
        def enum_cb(h, _):
            if win32gui.IsWindowVisible(h):
                title = win32gui.GetWindowText(h)
                if any(kw in title for kw in ["阴阳师", "MuMu", "夜神", "雷电", "LDPlayer", "Nox"]):
                    # 过滤极小窗口
                    rect = win32gui.GetClientRect(h)
                    w, h_ = rect[2] - rect[0], rect[3] - rect[1]
                    if w > 300 and h_ > 200:
                        candidates.append((h, title))
            return True

        try:
            win32gui.EnumWindows(enum_cb, None)
        except Exception:
            pass

        if candidates:
            # 优先选择标题含阴阳师的
            for h, title in candidates:
                if "阴阳师" in title:
                    self.hwnd = h
                    return self.hwnd
            self.hwnd = candidates[0][0]
            return self.hwnd

        return None

    @classmethod
    def list_all_game_windows(cls) -> List[Dict[str, any]]:
        """
        列出当前系统中所有可能的游戏窗口
        """
        windows = []
        def enum_cb(h, _):
            if win32gui.IsWindowVisible(h):
                title = win32gui.GetWindowText(h)
                if title:
                    rect = win32gui.GetClientRect(h)
                    w, h_ = rect[2] - rect[0], rect[3] - rect[1]
                    if w > 300 and h_ > 200:
                        windows.append({"hwnd": h, "title": title, "width": w, "height": h_})
            return True
        try:
            win32gui.EnumWindows(enum_cb, None)
        except Exception:
            pass
        return windows

    def is_valid(self) -> bool:
        if self.hwnd and win32gui.IsWindow(self.hwnd):
            return True
        return self.find_window() is not None

    def get_client_rect(self) -> Tuple[int, int, int, int]:
        if not self.is_valid():
            return (0, 0, 1280, 720)
        try:
            left, top, right, bottom = win32gui.GetClientRect(self.hwnd)
            w = max(right - left, 1)
            h = max(bottom - top, 1)
            return (left, top, w, h)
        except Exception:
            return (0, 0, 1280, 720)

    def screenshot(self) -> Optional[np.ndarray]:
        """
        后台高性能截屏，并自动缩放到标准 1280x720 坐标系
        """
        if not self.is_valid():
            return None

        hwnd = self.hwnd
        _, _, width, height = self.get_client_rect()
        if width <= 0 or height <= 0:
            return None

        # 使用 PrintWindow / BitBlt 从窗口 DC 抓取
        hwnd_dc = win32gui.GetWindowDC(hwnd)
        mfc_dc = win32ui.CreateDCFromHandle(hwnd_dc)
        save_dc = mfc_dc.CreateCompatibleDC()
        save_bitmap = win32ui.CreateBitmap()
        save_bitmap.CreateCompatibleBitmap(mfc_dc, width, height)
        save_dc.SelectObject(save_bitmap)

        img_bgr = None
        try:
            # PrintWindow Flag: 2 = PW_RENDERFULLCONTENT (Win8.1+)
            result = ctypes.windll.user32.PrintWindow(hwnd, save_dc.GetSafeHdc(), 2)
            if not result:
                # 回退方案: BitBlt
                save_dc.BitBlt((0, 0), (width, height), mfc_dc, (0, 0), win32con.SRCCOPY)

            bmpinfo = save_bitmap.GetInfo()
            bmpstr = save_bitmap.GetBitmapBits(True)
            img = np.frombuffer(bmpstr, dtype=np.uint8).reshape((bmpinfo['bmHeight'], bmpinfo['bmWidth'], 4))
            img_bgr = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
        except Exception:
            pass
        finally:
            win32gui.DeleteObject(save_bitmap.GetHandle())
            save_dc.DeleteDC()
            mfc_dc.DeleteDC()
            win32gui.ReleaseDC(hwnd, hwnd_dc)

        if img_bgr is not None and (width != self.STANDARD_WIDTH or height != self.STANDARD_HEIGHT):
            img_bgr = cv2.resize(img_bgr, (self.STANDARD_WIDTH, self.STANDARD_HEIGHT), interpolation=cv2.INTER_AREA)

        return img_bgr

    def click(self, x: int, y: int, delay: float = 0.05):
        """
        后台向目标坐标 (x, y) 发送鼠标左键点击 (以 1280x720 为基准自动映射至实际窗口分辨率)
        """
        if not self.is_valid():
            return

        _, _, real_w, real_h = self.get_client_rect()
        scale_x = real_w / self.STANDARD_WIDTH
        scale_y = real_h / self.STANDARD_HEIGHT

        target_x = int(x * scale_x)
        target_y = int(y * scale_y)

        lParam = win32api_lParam(target_x, target_y)
        win32gui.PostMessage(self.hwnd, win32con.WM_LBUTTONDOWN, win32con.MK_LBUTTON, lParam)
        if delay > 0:
            time.sleep(delay)
        win32gui.PostMessage(self.hwnd, win32con.WM_LBUTTONUP, 0, lParam)

    def swipe(self, p1: Tuple[int, int], p2: Tuple[int, int], steps: int = 5, duration: float = 0.3):
        """
        后台模拟滑动 (以 1280x720 为基准)
        """
        if not self.is_valid():
            return

        _, _, real_w, real_h = self.get_client_rect()
        scale_x = real_w / self.STANDARD_WIDTH
        scale_y = real_h / self.STANDARD_HEIGHT

        x1, y1 = int(p1[0] * scale_x), int(p1[1] * scale_y)
        x2, y2 = int(p2[0] * scale_x), int(p2[1] * scale_y)

        lParam_start = win32api_lParam(x1, y1)
        win32gui.PostMessage(self.hwnd, win32con.WM_LBUTTONDOWN, win32con.MK_LBUTTON, lParam_start)
        time.sleep(0.05)

        for i in range(1, steps + 1):
            curr_x = int(x1 + (x2 - x1) * (i / steps))
            curr_y = int(y1 + (y2 - y1) * (i / steps))
            lParam = win32api_lParam(curr_x, curr_y)
            win32gui.PostMessage(self.hwnd, win32con.WM_MOUSEMOVE, win32con.MK_LBUTTON, lParam)
            time.sleep(duration / steps)

        lParam_end = win32api_lParam(x2, y2)
        win32gui.PostMessage(self.hwnd, win32con.WM_LBUTTONUP, 0, lParam_end)


def win32api_lParam(x: int, y: int) -> int:
    return (int(y) << 16) | (int(x) & 0xFFFF)
