# core/logger.py - 独立线程安全日志系统 (支持控制台输出与 GUI 实时信号推送)
import sys
import logging
from datetime import datetime
from pathlib import Path
from PySide6.QtCore import QObject, Signal

class LogEmitter(QObject):
    log_signal = Signal(str, str, str)  # (time_str, level, message)

emitter = LogEmitter()

class GuiLogHandler(logging.Handler):
    def emit(self, record):
        try:
            msg = self.format(record)
            time_str = datetime.fromtimestamp(record.created).strftime("%H:%M:%S")
            emitter.log_signal.emit(time_str, record.levelname, record.getMessage())
        except Exception:
            pass

def setup_logger(log_dir: Path = None) -> logging.Logger:
    logger = logging.getLogger("HyakkiApp")
    logger.setLevel(logging.INFO)
    logger.handlers.clear()

    # 控制台输出
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(logging.Formatter("[%(asctime)s] [%(levelname)s] %(message)s", "%H:%M:%S"))
    logger.addHandler(console_handler)

    # GUI 信号输出
    gui_handler = GuiLogHandler()
    logger.addHandler(gui_handler)

    # 文件输出
    if log_dir:
        log_dir.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(str(log_dir / "hyakki.log"), encoding="utf-8")
        file_handler.setFormatter(logging.Formatter("[%(asctime)s] [%(levelname)s] %(message)s", "%Y-%m-%d %H:%M:%S"))
        logger.addHandler(file_handler)

    return logger

logger = setup_logger(Path(__file__).parent.parent / "log")
