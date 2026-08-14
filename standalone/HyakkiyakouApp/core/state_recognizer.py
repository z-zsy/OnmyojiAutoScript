# core/state_recognizer.py - 百鬼夜行全界面状态识别器 (纯 OpenCV 实现，零 OAS 依赖)
import cv2
import numpy as np
from pathlib import Path
from typing import Optional, Tuple, List, Dict
from enum import Enum
from oashya.patch_matcher import patch_matcher
from oashya.labels import is_sp, is_ssr
from core.logger import logger

class GameState(Enum):
    UNKNOWN = "未知界面"
    IN_ROOM = "百鬼准备大厅"
    BOSS_SELECT = "选择鬼王界面"
    IN_GAME = "百鬼砸豆进行中"
    SETTLEMENT = "百鬼结算界面"
    INVITING = "邀请好友界面"

class StateRecognizer:
    def __init__(self, assets_dir: Path = None):
        if assets_dir is None:
            assets_dir = Path(__file__).parent.parent / "resources" / "assets" / "hya"
        self.assets_dir = Path(assets_dir)
        self.templates: Dict[str, np.ndarray] = {}
        self.load_templates()

    def load_templates(self):
        """
        预加载百鬼夜行核心界面模板
        """
        template_files = {
            "start_btn": "hya_hstart.png",
            "end_title": "hya_hend.png",
            "title_txt": "hya_htitle.png",
            "invite_btn": "hya_hinvite.png",
            "selected_mark": "hya_hselected.png",
            "bean_10": "hya_bean10.png",
            "bean_05": "hya_bean05.png",
            "access_btn": "hya_haccess.png",
        }
        for name, fname in template_files.items():
            fpath = self.assets_dir / fname
            if fpath.exists():
                img = cv2.imread(str(fpath))
                if img is not None:
                    self.templates[name] = img

    def match_template(self, image: np.ndarray, template_name: str, threshold: float = 0.75, roi: Tuple[int, int, int, int] = None) -> Optional[Tuple[int, int, float]]:
        """
        在目标图 (或 ROI) 中寻找模板
        返回: (center_x, center_y, max_val) 或 None
        """
        if template_name not in self.templates or image is None:
            return None

        template = self.templates[template_name]
        th, tw = template.shape[:2]
        h, w = image.shape[:2]

        if roi is not None:
            rx, ry, rw, rh = roi
            rx1 = max(0, rx)
            ry1 = max(0, ry)
            rx2 = min(w, rx + rw)
            ry2 = min(h, ry + rh)
            search_img = image[ry1:ry2, rx1:rx2]
            offset_x, offset_y = rx1, ry1
        else:
            search_img = image
            offset_x, offset_y = 0, 0

        if search_img.shape[0] < th or search_img.shape[1] < tw:
            return None

        res = cv2.matchTemplate(search_img, template, cv2.TM_CCOEFF_NORMED)
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)

        if max_val >= threshold:
            cx = offset_x + max_loc[0] + tw // 2
            cy = offset_y + max_loc[1] + th // 2
            return (cx, cy, float(max_val))

        return None

    def recognize_state(self, image: np.ndarray) -> Tuple[GameState, dict]:
        """
        识别当前游戏画面状态
        """
        if image is None:
            return GameState.UNKNOWN, {}

        # 1. 检查是否在结算页面 (hya_hend.png 或大字 "获得奖励")
        end_match = self.match_template(image, "end_title", threshold=0.72, roi=(300, 30, 680, 200))
        if end_match:
            return GameState.SETTLEMENT, {"center": (end_match[0], end_match[1])}

        # 2. 检查是否在选鬼王界面 (顶部有“选择本局鬼王”或中间有3个候选卡片)
        # 选鬼王特征：底部有 "开始" 按钮 (位于约 (1000~1180, 580~680)) 并且顶部出现鬼王选择提示
        start_match = self.match_template(image, "start_btn", threshold=0.75, roi=(950, 550, 300, 160))
        selected_match = self.match_template(image, "selected_mark", threshold=0.70)
        
        # 选鬼王中间 3 个卡片位置
        card_rois = [
            (180, 160, 280, 380),  # 左
            (500, 160, 280, 380),  # 中
            (820, 160, 280, 380),  # 右
        ]

        if selected_match or (start_match and not self.match_template(image, "invite_btn", threshold=0.70)):
            return GameState.BOSS_SELECT, {"start_btn": start_match, "card_rois": card_rois}

        # 3. 检查是否在百鬼准备大厅 (有邀请好友按钮 或 进入百鬼夜行标题)
        invite_match = self.match_template(image, "invite_btn", threshold=0.70)
        title_match = self.match_template(image, "title_txt", threshold=0.70)
        access_match = self.match_template(image, "access_btn", threshold=0.70)
        if invite_match or title_match or access_match:
            return GameState.IN_ROOM, {"start_btn": start_match, "invite_btn": invite_match, "access_btn": access_match}

        # 4. 检查是否在砸豆进行中 (底部有豆子槽 10豆/5豆，或者上方有黑色长条/倒计时)
        bean10_match = self.match_template(image, "bean_10", threshold=0.65, roi=(0, 580, 300, 140))
        bean05_match = self.match_template(image, "bean_05", threshold=0.65, roi=(0, 580, 300, 140))
        if bean10_match or bean05_match:
            return GameState.IN_GAME, {"bean_10": bean10_match, "bean_05": bean05_match}

        return GameState.UNKNOWN, {}

    def pick_best_boss(self, image: np.ndarray, priorities: List[str] = None) -> Tuple[int, str]:
        """
        在选鬼王界面自动分析 3 张卡片，选出最高优先级的鬼王：
        返回: (boss_index 0~2, 选中的式神名称)
        """
        card_rois = [
            (180, 160, 280, 380),  # 左 (0)
            (500, 160, 280, 380),  # 中 (1)
            (820, 160, 280, 380),  # 右 (2)
        ]
        priorities = priorities or []
        card_scores = []

        for idx, (rx, ry, rw, rh) in enumerate(card_rois):
            card_img = image[ry:ry+rh, rx:rx+rw]
            # 1. 尝试使用 PatchMatcher 匹配
            patch_name, match_score = patch_matcher.match_boss(card_img)
            
            score = 0
            if patch_name:
                if patch_name in priorities:
                    score = 1000 - priorities.index(patch_name)  # 越靠前分越高
                elif is_sp(patch_name):
                    score = 500
                elif is_ssr(patch_name):
                    score = 400
                else:
                    score = 100
            else:
                patch_name = f"候选鬼王_{idx+1}"
                score = 50

            card_scores.append((idx, patch_name, score, (rx + rw // 2, ry + rh // 2)))

        # 选出分数最高的一张卡
        best = max(card_scores, key=lambda x: x[2])
        logger.info(f"[StateRecognizer] 自动选鬼王决策: 第 {best[0]+1} 位 [{best[1]}] (Score: {best[2]})")
        return best[0], best[1]
