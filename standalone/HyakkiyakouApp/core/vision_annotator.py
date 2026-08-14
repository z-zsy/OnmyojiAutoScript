# core/vision_annotator.py - 百鬼夜行 AI 视觉与 HUD 标注渲染引擎
import os
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from typing import List, Dict, Tuple, Optional, Any

class VisionAnnotator:
    """
    负责在游戏实时画面上叠加绘制：
    1. 式神稀有度色彩边界框 (SP / SSR / SR / R / N / BUFF)
    2. 中文名称、稀有度角标与相似度百分比
    3. 目标移动速度向量与预测轨迹箭头
    4. 提前量预判瞄准打击十字准星 (Crosshair)
    """

    # 稀有度颜色表 (BGR / RGB)
    COLOR_MAP = {
        "SP": (247, 166, 203),    # 浅洋红 / 高亮紫 (BGR: 203, 166, 247)
        "SSR": (135, 179, 250),   # 琥珀金橙 (BGR: 135, 179, 250)
        "SR": (235, 220, 137),    # 浅海蓝 (BGR: 235, 220, 137)
        "R": (200, 200, 200),     # 银灰
        "N": (160, 160, 160),     # 灰
        "BUFF": (161, 227, 166),  # 增益翡翠绿 (BGR: 161, 227, 166)
        "UNKNOWN": (180, 180, 180)
    }

    def __init__(self):
        self.font = self._load_chinese_font(13)
        self.font_small = self._load_chinese_font(11)

    def _load_chinese_font(self, size: int):
        font_paths = [
            "C:/Windows/Fonts/msyh.ttc",
            "C:/Windows/Fonts/msyhbd.ttc",
            "C:/Windows/Fonts/simhei.ttf",
            "C:/Windows/Fonts/simsun.ttc",
            "/System/Library/Fonts/PingFang.ttc"
        ]
        for p in font_paths:
            if os.path.exists(p):
                try:
                    return ImageFont.truetype(p, size)
                except Exception:
                    pass
        return ImageFont.load_default()

    def annotate(
        self,
        frame: np.ndarray,
        targets: List[Dict[str, Any]],
        aim_point: Optional[Tuple[int, int]] = None,
        focus_name: Optional[str] = None,
        options: Optional[Dict[str, bool]] = None
    ) -> np.ndarray:
        """
        在给定的 BGR 帧上绘制所有标注并返回渲染后的 BGR 帧
        """
        if frame is None:
            return None

        if options is None:
            options = {
                "show_box": True,
                "show_label": True,
                "show_trajectory": True,
                "show_aim": True
            }

        canvas = frame.copy()
        h, w = canvas.shape[:2]

        # 1. 绘制 OpenCV 几何图形（边框、速度向量、瞄准线）
        for tgt in targets:
            bbox = tgt.get("bbox")  # (x1, y1, x2, y2)
            if not bbox or len(bbox) < 4:
                continue

            x1, y1, x2, y2 = [int(v) for v in bbox]
            rarity = tgt.get("rarity", "R").upper()
            color = self.COLOR_MAP.get(rarity, (180, 180, 180))

            # 绘制外边框
            if options.get("show_box", True):
                thickness = 2 if rarity in ["SP", "SSR", "BUFF"] else 1
                cv2.rectangle(canvas, (x1, y1), (x2, y2), color, thickness)
                # 绘制四角高亮重音
                corner_len = min(12, (x2 - x1) // 3, (y2 - y1) // 3)
                cv2.line(canvas, (x1, y1), (x1 + corner_len, y1), color, thickness + 1)
                cv2.line(canvas, (x1, y1), (x1, y1 + corner_len), color, thickness + 1)
                cv2.line(canvas, (x2, y1), (x2 - corner_len, y1), color, thickness + 1)
                cv2.line(canvas, (x2, y1), (x2, y1 + corner_len), color, thickness + 1)
                cv2.line(canvas, (x1, y2), (x1 + corner_len, y2), color, thickness + 1)
                cv2.line(canvas, (x1, y2), (x1, y2 - corner_len), color, thickness + 1)
                cv2.line(canvas, (x2, y2), (x2 - corner_len, y2), color, thickness + 1)
                cv2.line(canvas, (x2, y2), (x2, y2 - corner_len), color, thickness + 1)

            # 绘制速度向量 / 预测轨迹
            if options.get("show_trajectory", True):
                vx = tgt.get("vx", 0)
                vy = tgt.get("vy", 0)
                if abs(vx) > 0.5 or abs(vy) > 0.5:
                    cx = (x1 + x2) // 2
                    cy = (y1 + y2) // 2
                    arrow_x = int(cx + vx * 8)
                    arrow_y = int(cy + vy * 8)
                    cv2.arrowedLine(canvas, (cx, cy), (arrow_x, arrow_y), color, 1, tipLength=0.3)

        # 2. 绘制打击提前量瞄准十字准星
        if options.get("show_aim", True) and aim_point is not None:
            ax, ay = aim_point
            if 0 <= ax < w and 0 <= ay < h:
                # 瞄准环
                cv2.circle(canvas, (ax, ay), 18, (0, 0, 255), 2)
                cv2.circle(canvas, (ax, ay), 6, (0, 255, 255), -1)
                # 十字准星线
                cv2.line(canvas, (ax - 26, ay), (ax - 10, ay), (0, 0, 255), 2)
                cv2.line(canvas, (ax + 10, ay), (ax + 26, ay), (0, 0, 255), 2)
                cv2.line(canvas, (ax, ay - 26), (ax, ay - 10), (0, 0, 255), 2)
                cv2.line(canvas, (ax, ay + 10), (ax, ay + 26), (0, 0, 255), 2)

        # 3. 绘制中文文本标签 (转为 PIL 绘制以支持高质量中文字体)
        if options.get("show_label", True) and targets:
            pil_img = Image.fromarray(cv2.cvtColor(canvas, cv2.COLOR_BGR2RGB))
            draw = ImageDraw.Draw(pil_img)

            for tgt in targets:
                bbox = tgt.get("bbox")
                if not bbox:
                    continue
                x1, y1, x2, y2 = [int(v) for v in bbox]
                name = tgt.get("name", "未知")
                rarity = tgt.get("rarity", "R").upper()
                score = tgt.get("score", 0.0)

                label_str = f"[{rarity}] {name}"
                if score > 0:
                    label_str += f" {int(score * 100)}%"

                # 计算文本尺寸
                bg_color = (24, 24, 37, 210)  # 半透明深色胶囊
                text_color = (255, 255, 255)
                if rarity == "SP":
                    text_color = (255, 180, 230)
                elif rarity == "SSR":
                    text_color = (255, 220, 150)
                elif rarity == "BUFF":
                    text_color = (180, 255, 180)

                tag_x = max(2, x1)
                tag_y = max(2, y1 - 20)
                draw.rectangle([tag_x, tag_y, tag_x + len(label_str) * 11 + 8, tag_y + 18], fill=bg_color)
                draw.text((tag_x + 4, tag_y + 1), label_str, font=self.font, fill=text_color)

            # 如果有锁定目标名称，在准星旁绘制指示
            if options.get("show_aim", True) and aim_point is not None and focus_name:
                ax, ay = aim_point
                draw.text((ax + 24, ay - 10), f"🎯 锁定: {focus_name}", font=self.font, fill=(255, 215, 0))

            canvas = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)

        return canvas
