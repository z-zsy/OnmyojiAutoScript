# core/config_manager.py - 全局与设备全量配置管理
import json
from pathlib import Path
from dataclasses import dataclass, field, asdict
from typing import List
from enum import Enum

class ConnectionMode(str, Enum):
    PC_CLIENT = "PC 桌面客户端"
    EMULATOR_ADB = "安卓模拟器 (ADB)"
    EMULATOR_NEMU = "MuMu 模拟器 (NemuIPC 极速)"

class ScreenshotMethod(str, Enum):
    WINDOW_BACKGROUND = "window_background (后台无感)"
    NEMU_IPC = "nemu_ipc (MuMu共享内存)"
    ADB = "ADB (通用安卓截屏)"
    BITBLT = "BitBlt (标准DC抓屏)"

class ControlMethod(str, Enum):
    WINDOW_MESSAGE = "window_message (后台消息点击)"
    MINITOUCH = "minitouch (极速触控)"
    ADB = "ADB (标准触摸)"

class CourtyardType(str, Enum):
    DEFAULT = "默认初代庭院"
    DRAGON = "龙仪星引"
    AUTUMN = "枫赏秋目"
    SPRING = "暖春翠庭"
    OCEAN = "远海航船"
    DREAM = "织梦之庭"

class OnmyojiType(str, Enum):
    SEIMEI = "晴明"
    KAGURA = "神乐"
    HIROMASA = "源博雅"
    YAO_BIKUNI = "八百比丘尼"
    YORIMITSU = "源赖光"
    MICHINAGA = "藤原道长"

@dataclass
class AppConfig:
    # 1. 设备与连接配置
    connection_mode: str = ConnectionMode.PC_CLIENT.value
    window_title: str = "阴阳师-网易游戏"
    adb_host: str = "127.0.0.1"              # ADB 主机地址
    adb_port: int = 7555                     # ADB 端口 (如 7555, 5555, 62001)
    adb_path: str = "auto"                   # ADB 可执行文件路径
    serial: str = "127.0.0.1:7555"           # 完整连接目标 (如 127.0.0.1:7555)
    screenshot_method: str = ScreenshotMethod.WINDOW_BACKGROUND.value
    control_method: str = ControlMethod.WINDOW_MESSAGE.value
    package_name: str = "com.netease.onmyoji" # 游戏包名
    
    # 2. 全局环境与庭院
    courtyard: str = CourtyardType.DEFAULT.value
    onmyoji: str = OnmyojiType.SEIMEI.value

    # 3. 百鬼夜行核心策略
    total_rounds: int = 10                   # 运行轮数
    bean_count: int = 10                     # 每次投掷 10 豆 / 5 豆
    auto_bean: bool = False                  # 智能自适应调豆
    bean_threshold_low: int = 10             # 低于该剩余式神数时切 10 豆
    invite_friend: bool = False              # 是否自动邀请好友
    invite_mode: str = "同服好友"             # 同服好友 / 跨服好友 / 阴阳寮好友

    # 4. 稀有度权重微调 (0.0 ~ 2.0)
    sp_weight: float = 1.0
    ssr_weight: float = 1.0
    sr_weight: float = 0.7
    r_weight: float = 0.3
    n_weight: float = 0.0
    g_weight: float = 0.0

    # 5. BUFF 权重微调
    buff_prob_up: float = 3.5                # 概率UP权重
    buff_friend_up: float = 3.0              # 好友UP权重
    buff_add_beans: float = 2.5              # 增加豆子权重
    buff_speed_up: float = 2.0               # 投速加速
    buff_slow_down: float = 2.0              # 式神减速
    buff_freeze: float = 2.0                 # 式神冰冻

    # 6. 优先式神清单
    priorities: List[str] = field(default_factory=lambda: [
        "龙吟铃鹿御前", "天火命铃彦姬", "时曜泷夜叉姬", "瑶音紧那罗", "晨晖惠比寿",
        "天照", "须佐之男", "神堕八岐大蛇", "因幡辉夜姬", "阿修罗", "千姬", "不知火"
    ])

    # 7. AI 与同步配置
    auto_sync_patches: bool = True           # 启动自动拉取官方最新补丁
    conf_threshold: float = 0.55             # YOLO 置信度阈值
    iou_threshold: float = 0.60              # NMS IOU 阈值
    shot_interval_ms: int = 250              # 投豆间隔 (ms)

class ConfigManager:
    def __init__(self, config_path: Path = None):
        if config_path is None:
            config_path = Path(__file__).parent.parent / "config.json"
        self.config_path = Path(config_path)
        self.config: AppConfig = self.load()

    def load(self) -> AppConfig:
        if self.config_path.exists():
            try:
                with open(self.config_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    # 过滤未知键
                    valid_keys = AppConfig.__annotations__.keys()
                    filtered = {k: v for k, v in data.items() if k in valid_keys}
                    return AppConfig(**filtered)
            except Exception as e:
                print(f"[ConfigManager] 加载配置失败，使用默认配置: {e}")
        return AppConfig()

    def save(self):
        try:
            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump(asdict(self.config), f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"[ConfigManager] 保存配置失败: {e}")
