# This Python file uses the following encoding: utf-8
import json
import os
import cv2
import numpy as np
from pathlib import Path
from module.logger import logger


class PatchMatcher:
    """
    百鬼夜行式神增量补丁匹配引擎
    支持多尺度模板匹配、色彩直方图相似度与特征点匹配
    用于免全量重新训练模型即可热插拔识别新上线式神
    """

    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(PatchMatcher, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, patch_dir: str | Path = None):
        if getattr(self, '_initialized', False):
            return
        if patch_dir is None:
            patch_dir = Path(__file__).resolve().parent / 'patches'
        self.patch_dir = Path(patch_dir)
        self.manifest_path = self.patch_dir / 'patch_manifest.json'
        self.gallery_dir = self.patch_dir / 'gallery'
        self.patches: list[dict] = []
        self.patch_samples: dict[str, list[np.ndarray]] = {}
        self.patch_hsv_hists: dict[str, list[np.ndarray]] = {}
        self.reload()
        self._initialized = True

    def reload(self):
        """重新加载补丁清单与样本图库"""
        self.patches.clear()
        self.patch_samples.clear()
        self.patch_hsv_hists.clear()
        if not self.manifest_path.exists():
            logger.info(f'Patch manifest not found at {self.manifest_path}')
            return

        try:
            with open(self.manifest_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if isinstance(data, list):
                    self.patches = [p for p in data if p.get('enabled', True)]
        except Exception as e:
            logger.error(f'Failed to load patch manifest: {e}')
            return

        for p in self.patches:
            p_id = p.get('id')
            if not p_id:
                continue
            samples = []
            hists = []
            # 1. 从 samples 列表加载
            for rel_path in p.get('samples', []):
                full_path = self.patch_dir / rel_path
                if full_path.exists():
                    img = cv2.imdecode(np.fromfile(str(full_path), dtype=np.uint8), cv2.IMREAD_COLOR)
                    if img is not None:
                        samples.append(img)
                        hists.append(self._calc_hsv_hist(img))

            # 2. 从 gallery/<p_id>/ 目录扫描加载
            target_dir = self.gallery_dir / p_id
            if target_dir.exists() and target_dir.is_dir():
                for ext in ('*.png', '*.jpg', '*.jpeg', '*.bmp'):
                    for file in target_dir.glob(ext):
                        img = cv2.imdecode(np.fromfile(str(file), dtype=np.uint8), cv2.IMREAD_COLOR)
                        if img is not None and not any(np.array_equal(img, s) for s in samples):
                            samples.append(img)
                            hists.append(self._calc_hsv_hist(img))

            if samples:
                self.patch_samples[p_id] = samples
                self.patch_hsv_hists[p_id] = hists
                logger.info(f'Loaded patch: {p.get("name")} ({p_id}) with {len(samples)} sample(s)')

    def has_patches(self) -> bool:
        return len(self.patch_samples) > 0

    @staticmethod
    def _calc_hsv_hist(image: np.ndarray) -> np.ndarray:
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        hist = cv2.calcHist([hsv], [0, 1], None, [16, 16], [0, 180, 0, 256])
        cv2.normalize(hist, hist, alpha=0, beta=1, norm_type=cv2.NORM_MINMAX)
        return hist

    def match_roi(self, roi: np.ndarray, min_score: float = 0.65) -> tuple[dict | None, float]:
        """
        在指定 ROI（裁剪出的式神区域）中比对所有补丁
        @return: (最佳匹配补丁元数据, 置信度分数)
        """
        if roi is None or roi.size == 0 or not self.has_patches():
            return None, 0.0

        best_patch = None
        best_score = 0.0

        roi_h, roi_w = roi.shape[:2]
        if roi_h < 20 or roi_w < 20:
            return None, 0.0

        roi_hist = self._calc_hsv_hist(roi)

        for patch in self.patches:
            p_id = patch.get('id')
            samples = self.patch_samples.get(p_id, [])
            hists = self.patch_hsv_hists.get(p_id, [])

            for s_idx, sample in enumerate(samples):
                s_h, s_w = sample.shape[:2]
                # 1. 色彩直方图比对 (巴氏距离/相关性)
                hist_score = cv2.compareHist(roi_hist, hists[s_idx], cv2.HISTCMP_CORREL)
                hist_score = max(0.0, float(hist_score))

                # 2. 多尺度模板匹配
                resized_sample = cv2.resize(sample, (roi_w, roi_h))
                res = cv2.matchTemplate(roi, resized_sample, cv2.TM_CCOEFF_NORMED)
                _, max_val, _, _ = cv2.minMaxLoc(res)
                tmpl_score = max(0.0, float(max_val))

                # 综合打分 (模板结构 70% + 色彩分布 30%)
                composite_score = tmpl_score * 0.7 + hist_score * 0.3

                if composite_score > best_score:
                    best_score = composite_score
                    best_patch = patch

        if best_score >= min_score:
            return best_patch, best_score
        return None, best_score

    def match_boss(self, screen_image: np.ndarray, candidate_idx: int = None, min_score: float = 0.60) -> tuple[dict | None, float]:
        """
        在鬼王选择界面中检测是否匹配某个新式神补丁
        @param screen_image: 1280x720 完整屏幕截图
        @param candidate_idx: 0, 1, 2 分别代表三个候选位置（可选）
        @return: (最佳匹配补丁元数据, 置信度分数)
        """
        if screen_image is None or not self.has_patches():
            return None, 0.0

        # 定义鬼王候选区 ROI 范围 (x, y, w, h)
        candidate_rois = [
            (150, 160, 240, 430),   # 候选 1
            (520, 160, 240, 430),   # 候选 2
            (880, 160, 240, 430),   # 候选 3
        ]

        search_rois = []
        if candidate_idx is not None and 0 <= candidate_idx < len(candidate_rois):
            search_rois = [candidate_rois[candidate_idx]]
        else:
            # 默认搜索中间主展示区或全候选区
            search_rois = candidate_rois + [(300, 150, 680, 450)]

        best_patch = None
        best_score = 0.0

        for rx, ry, rw, rh in search_rois:
            roi = screen_image[ry:ry+rh, rx:rx+rw]
            if roi.size == 0:
                continue

            for patch in self.patches:
                p_id = patch.get('id')
                samples = self.patch_samples.get(p_id, [])

                for sample in samples:
                    s_h, s_w = sample.shape[:2]
                    # 多尺度模板扫描 (0.6x, 0.8x, 1.0x, 1.2x)
                    for scale in (0.6, 0.8, 1.0, 1.2):
                        target_w = int(s_w * scale)
                        target_h = int(s_h * scale)
                        if target_w >= rw or target_h >= rh or target_w <= 10 or target_h <= 10:
                            continue
                        scaled_sample = cv2.resize(sample, (target_w, target_h))
                        res = cv2.matchTemplate(roi, scaled_sample, cv2.TM_CCOEFF_NORMED)
                        _, max_val, _, _ = cv2.minMaxLoc(res)
                        if max_val > best_score:
                            best_score = float(max_val)
                            best_patch = patch

        if best_score >= min_score:
            logger.info(f'PatchMatcher: Detected Boss Patch [{best_patch.get("name")}] (Score: {best_score:.3f})')
            return best_patch, best_score

        return None, best_score


patch_matcher = PatchMatcher()
