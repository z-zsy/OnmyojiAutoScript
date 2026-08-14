# This Python file uses the following encoding: utf-8
"""
百鬼夜行式神补丁在线同步与管理工具 (官方真实数据源版)
直接对接《阴阳师》网易官方真实数据源接口 (g37simulator.webapp.163.com)
下载官方高清真实立绘，并自适应生成百鬼游行多角度匹配样本
"""
import sys
import os
import json
import urllib.request
import urllib.error
import cv2
import numpy as np
from pathlib import Path

# 定位当前插件目录与项目根目录
PLUGIN_ROOT = Path(__file__).resolve().parent.parent
PROJECT_ROOT = PLUGIN_ROOT.parent.parent
if str(PLUGIN_ROOT) not in sys.path:
    sys.path.insert(0, str(PLUGIN_ROOT))
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

PATCH_DIR = PLUGIN_ROOT / 'oashya' / 'patches'
MANIFEST_PATH = PATCH_DIR / 'patch_manifest.json'
GALLERY_DIR = PATCH_DIR / 'gallery'

# 网易阴阳师官方式神录 API 与 CDN 资源地址
OFFICIAL_API_URL = "https://g37simulator.webapp.163.com/get_heroid_list?rarity=0&page=1&per_page=500"
OFFICIAL_IMG_CDN = "https://yys.res.netease.com/pc/zt/20161108171335/data/shishen/{id}.png"


def get_local_manifest() -> list[dict]:
    """读取本地已安装的补丁清单"""
    if MANIFEST_PATH.exists():
        try:
            with open(MANIFEST_PATH, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if isinstance(data, list):
                    return data
        except Exception:
            pass
    return []


def save_local_manifest(manifest_data: list[dict]):
    """保存本地补丁清单"""
    PATCH_DIR.mkdir(parents=True, exist_ok=True)
    with open(MANIFEST_PATH, 'w', encoding='utf-8') as f:
        json.dump(manifest_data, f, ensure_ascii=False, indent=2)


def fetch_official_shikigami_list(timeout: int = 6) -> dict | None:
    """从网易官方 API 拉取最新全量式神录"""
    try:
        req = urllib.request.Request(
            OFFICIAL_API_URL,
            headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        )
        with urllib.request.urlopen(req, timeout=timeout) as response:
            if response.status == 200:
                data = json.loads(response.read().decode('utf-8'))
                if data.get('data'):
                    return data['data']
    except Exception:
        pass
    return None


def download_official_avatar(official_id: int | str, save_path: Path, timeout: int = 5) -> bool:
    """从网易官方 CDN 下载式神官方真实立绘头像"""
    url = OFFICIAL_IMG_CDN.format(id=official_id)
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            if resp.status == 200:
                img_data = resp.read()
                if len(img_data) > 500:
                    with open(save_path, 'wb') as f:
                        f.write(img_data)
                    return True
    except Exception:
        pass
    return False


def generate_side_sample_from_front(front_path: Path, side_path: Path):
    """
    基于官方真实正面立绘，自适应构建百鬼游行侧身匹配图：
    - 保持官方真实立绘的色彩、服饰与轮廓
    - 模拟百鬼游行视角的侧向透视与比例
    """
    if not front_path.exists():
        return
    img = cv2.imread(str(front_path), cv2.IMREAD_UNCHANGED)
    if img is None:
        return

    # 百鬼走步侧身透视：水平轻微压缩并保持真实色彩
    h, w = img.shape[:2]
    new_w = max(int(w * 0.82), 10)
    resized = cv2.resize(img, (new_w, h), interpolation=cv2.INTER_AREA)

    # 填充到标准画布
    if len(img.shape) == 3 and img.shape[2] == 4:
        # 带有透明通道
        canvas = np.zeros((h, w, 4), dtype=np.uint8)
        offset_x = (w - new_w) // 2
        canvas[:, offset_x:offset_x + new_w] = resized
    else:
        canvas = np.zeros((h, w, 3), dtype=np.uint8)
        offset_x = (w - new_w) // 2
        canvas[:, offset_x:offset_x + new_w] = resized

    cv2.imwrite(str(side_path), canvas)


def sync_online_patches(timeout: int = 6) -> dict:
    """
    执行网易官方在线增量同步：
    - 获取官方最新全量式神
    - 下载官方高清立绘作为正面样本
    - 基于真实立绘生成侧身游行样本（彻底告别几何占位图）
    - 动态热重载生效
    """
    try:
        from core.logger import logger
    except ImportError:
        import logging
        logger = logging.getLogger('PatchSync')
    logger.info('[PatchSync] Checking official NetEase Onmyoji API for latest shikigami...')

    official_data = fetch_official_shikigami_list(timeout=timeout)
    if official_data is None:
        logger.info('[PatchSync] Official API unreachable or offline, using local cached patches.')
        return {'status': False, 'new_count': 0, 'new_names': [], 'msg': 'Offline / Cached'}

    from oashya import labels
    local_manifest = get_local_manifest()
    local_manifest_names = {p.get('name') for p in local_manifest if p.get('name')}

    rarity_map = {5: 'SP', 4: 'SSR'}
    native_names = set(labels.sp.values()) | set(labels.ssr.values()) | set(labels.sr.values()) | set(labels.r.values())

    sorted_official = sorted(official_data.items(), key=lambda x: int(x[0]))
    new_patches_added = []

    # 统计已有编号
    current_sp_patch_idx = 36
    current_ssr_patch_idx = 47

    for official_id_str, info in sorted_official:
        r_num = info.get('rarity')
        name = info.get('name')
        if not name or r_num not in rarity_map:
            continue

        rarity_str = rarity_map[r_num]

        # 如果原生已收录，跳过
        if name in native_names:
            continue

        # 如果本地补丁清单已存在，只检查/更新样本图完整性
        if name in local_manifest_names:
            patch_item = next((p for p in local_manifest if p.get('name') == name), None)
            if patch_item:
                patch_id = patch_item['id']
                item_gallery = GALLERY_DIR / patch_id
                front_path = item_gallery / 'sample_front.png'
                side_path = item_gallery / 'sample_side.png'
                if not front_path.exists():
                    download_official_avatar(official_id_str, front_path)
                if front_path.exists():
                    generate_side_sample_from_front(front_path, side_path)
            continue

        if rarity_str == 'SP':
            patch_id = f"sp_{current_sp_patch_idx:03d}"
            current_sp_patch_idx += 1
        else:
            patch_id = f"ssr_{current_ssr_patch_idx:03d}"
            current_ssr_patch_idx += 1

        item_gallery = GALLERY_DIR / patch_id
        item_gallery.mkdir(parents=True, exist_ok=True)
        front_path = item_gallery / 'sample_front.png'
        side_path = item_gallery / 'sample_side.png'

        download_official_avatar(official_id_str, front_path, timeout=4)
        if front_path.exists():
            generate_side_sample_from_front(front_path, side_path)

        patch_item = {
            'id': patch_id,
            'name': name,
            'rarity': rarity_str,
            'enabled': True,
            'official_id': int(official_id_str),
            'description': f'{rarity_str}{name} 官方数据同步',
            'samples': [
                f'gallery/{patch_id}/sample_front.png',
                f'gallery/{patch_id}/sample_side.png'
            ]
        }
        local_manifest.append(patch_item)
        local_manifest_names.add(name)
        new_patches_added.append(f"{name} ({rarity_str})")
        logger.info(f'[PatchSync] ✨ Synced official shikigami: [{patch_id}] {name} ({rarity_str}, ID: {official_id_str})')

    if new_patches_added:
        save_local_manifest(local_manifest)
        try:
            from oashya.patch_matcher import patch_matcher
            labels.reload_patches()
            patch_matcher.reload()
        except Exception as e:
            logger.warning(f'[PatchSync] Hot reload warning: {e}')

        logger.info(f'[PatchSync] Official sync complete! Added {len(new_patches_added)} new shikigami.')
        return {'status': True, 'new_count': len(new_patches_added), 'new_names': new_patches_added, 'msg': 'Synced'}
    else:
        logger.info('[PatchSync] All official shikigami patches and samples are up to date.')
        return {'status': True, 'new_count': 0, 'new_names': [], 'msg': 'Already Up to Date'}


if __name__ == '__main__':
    res = sync_online_patches()
    print("Sync Result:", res)
