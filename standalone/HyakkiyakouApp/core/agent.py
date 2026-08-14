# core/agent.py - 全局多目标态势评估与热力图决策 Agent
import numpy as np
from typing import List, Tuple, Optional
from datetime import datetime
from oashya.labels import get_class_rarity, id2name, id2label, CLASSINDEX as CI
from oashya.patch_matcher import patch_matcher
from core.focus import Focus
from core.logger import logger

def generate_gaussian_patch(size=(300, 300), mean=0, std_dev=60):
    x = np.linspace(-150, 150, size[1])
    y = np.linspace(-150, 150, size[0])
    x, y = np.meshgrid(x, y)
    z = np.exp(-(((x - mean) ** 2 + (y - mean) ** 2) / (2 * std_dev ** 2)))
    return z

class Agent:
    GAUSSIAN = generate_gaussian_patch()

    def __init__(self, strategy: dict = None):
        self.z = np.zeros((720, 1280), dtype=np.float32)
        self.focus: Optional[Focus] = None
        self.strategy = strategy or {}
        self.weights = self.strategy.get('weights', [1.0, 1.0, 0.7, 0.3, 0.0, 0.0])  # SP, SSR, SR, R, N, G
        self.priorities: List[str] = self.strategy.get('priorities', [])

    def update_strategy(self, strategy: dict):
        self.strategy = strategy
        self.weights = self.strategy.get('weights', [1.0, 1.0, 0.7, 0.3, 0.0, 0.0])
        self.priorities = self.strategy.get('priorities', [])

    def gamma(self, tracks: list, current_image: np.ndarray = None) -> np.ndarray:
        """
        根据屏幕上所有式神/目标的位置与稀有度/优先级构建全屏价值热力图
        """
        z = np.zeros((720, 1280), dtype=np.float32)
        canvas_h, canvas_w = 720, 1280
        pw, ph = 300, 300

        for track in tracks:
            _id, _class, _conf, _cx, _cy, _w, _h, _v = track
            name = id2name(_class)
            rarity = get_class_rarity(_class)

            # 基础权重
            if rarity == 'SP':
                weight = self.weights[0]
            elif rarity == 'SSR':
                weight = self.weights[1]
            elif rarity == 'SR':
                weight = self.weights[2]
            elif rarity == 'R':
                weight = self.weights[3]
            elif rarity == 'N':
                weight = self.weights[4]
            elif rarity == 'BUFF':
                weight = 1.5
            else:
                weight = 0.0

            # 优先式神清单加权 (顶格权重)
            if name in self.priorities:
                weight = max(weight, 2.0)

            # 靠近屏幕中间及黄金投掷区 (x=500~800) 时加权
            pos_factor = 1.0 - abs(_cx - 640) / 1280.0
            total_weight = weight * pos_factor

            if total_weight <= 0:
                continue

            # 贴高斯热力斑
            cx, cy = int(_cx), int(_cy)
            x1 = max(0, cx - pw // 2)
            y1 = max(0, cy - ph // 2)
            x2 = min(canvas_w, cx + pw // 2)
            y2 = min(canvas_h, cy + ph // 2)

            patch_x1 = (pw // 2) - (cx - x1)
            patch_y1 = (ph // 2) - (cy - y1)
            patch_x2 = patch_x1 + (x2 - x1)
            patch_y2 = patch_y1 + (y2 - y1)

            if (x2 > x1) and (y2 > y1):
                z[y1:y2, x1:x2] += self.GAUSSIAN[patch_y1:patch_y2, patch_x1:patch_x2] * total_weight

        return z

    def step(self, tracks: list, current_image: np.ndarray = None, state: list = None) -> Tuple[int, int, bool, int]:
        """
        每帧单步决策：
        1. 融合 PatchMatcher 识别未被原生 YOLO 命中的式神
        2. 生成全屏热力图
        3. 锁定价值最高的 Focus 目标
        4. 计算投豆动作 (x, y, throw, bean)
        """
        # 1. 补丁目标补充识别
        if current_image is not None and patch_matcher.has_patches():
            tracks = patch_matcher.match_tracks(current_image, tracks)

        # 2. 生成热力图
        self.z = self.gamma(tracks, current_image)

        # 3. 寻找全屏最高价值目标
        best_focus = None
        max_omega = 0.0

        for track in tracks:
            _id, _class, _conf, _cx, _cy, _w, _h, _v = track
            rarity = get_class_rarity(_class)
            if rarity == 'BUFF':
                continue  # BUFF 另行在 Focus 中仲裁

            f = Focus(track)
            omega_val = f.omega(self.z)
            if omega_val > max_omega:
                max_omega = omega_val
                best_focus = f

        if best_focus is not None:
            self.focus = best_focus
            self.focus.set_omega(max_omega)

        # 4. 如果有锁定目标，执行决策
        if self.focus is not None:
            action = self.focus.decision(tracks, self.strategy, state or [250, 36, 10])
            return action

        return (0, 0, False, 10)
