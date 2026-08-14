# This Python file uses the following encoding: utf-8
"""
百鬼夜行新式神增量补丁快捷录入工具
用法：
  python dev_tools/hyakkiyakou/add_patch.py --name "新SP式神" --rarity "SP" --images path/to/sample1.png path/to/sample2.png
或者直接交互式运行：
  python dev_tools/hyakkiyakou/add_patch.py
"""
import argparse
import json
import os
import shutil
import sys
from pathlib import Path

# 添加插件根目录与项目根目录到 sys.path
PLUGIN_ROOT = Path(__file__).resolve().parent.parent
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
if str(PLUGIN_ROOT) not in sys.path:
    sys.path.insert(0, str(PLUGIN_ROOT))
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def get_next_patch_id(rarity: str, manifest_data: list[dict]) -> str:
    """根据稀有度和已存在补丁自动生成下一个 ID，例如 sp_036, ssr_047"""
    rarity_lower = rarity.lower()
    existing_nums = []
    # 检查现有 manifest 中的 ID
    for item in manifest_data:
        item_id = item.get('id', '')
        if item_id.startswith(f'{rarity_lower}_'):
            try:
                num = int(item_id.split('_')[-1])
                existing_nums.append(num)
            except ValueError:
                pass

    # 检查 labels.py 原生已有 ID 的最大值
    try:
        from oashya import labels
        dict_map = {
            'sp': labels.sp,
            'ssr': labels.ssr,
            'sr': labels.sr,
            'r': labels.r,
            'n': labels.n,
            'g': labels.g,
        }
        target_dict = dict_map.get(rarity_lower, {})
        for k in target_dict.keys():
            if k.startswith(f'{rarity_lower}_'):
                try:
                    num = int(k.split('_')[-1])
                    existing_nums.append(num)
                except ValueError:
                    pass
    except Exception:
        pass

    next_num = max(existing_nums, default=0) + 1
    return f'{rarity_lower}_{next_num:03d}'


def add_shikigami_patch(name: str, rarity: str, patch_id: str = None, image_paths: list[str | Path] = None, desc: str = ""):
    rarity = rarity.upper()
    valid_rarities = ['SP', 'SSR', 'SR', 'R', 'N', 'G']
    if rarity not in valid_rarities:
        print(f"❌ 错误：稀有度必须是 {valid_rarities} 之一")
        return False

    patch_dir = PLUGIN_ROOT / 'oashya' / 'patches'
    manifest_path = patch_dir / 'patch_manifest.json'
    gallery_dir = patch_dir / 'gallery'
    patch_dir.mkdir(parents=True, exist_ok=True)
    gallery_dir.mkdir(parents=True, exist_ok=True)

    manifest_data = []
    if manifest_path.exists():
        try:
            with open(manifest_path, 'r', encoding='utf-8') as f:
                manifest_data = json.load(f)
                if not isinstance(manifest_data, list):
                    manifest_data = []
        except Exception as e:
            print(f"⚠️ 读取现有清单失败，将创建新清单: {e}")
            manifest_data = []

    if not patch_id:
        patch_id = get_next_patch_id(rarity, manifest_data)

    target_gallery = gallery_dir / patch_id
    target_gallery.mkdir(parents=True, exist_ok=True)

    sample_relative_paths = []
    if image_paths:
        for idx, img_p in enumerate(image_paths, start=1):
            src_path = Path(img_p)
            if src_path.is_file() and src_path.exists():
                dst_name = f'sample_{idx:02d}{src_path.suffix.lower()}'
                dst_path = target_gallery / dst_name
                shutil.copy2(src_path, dst_path)
                sample_relative_paths.append(f'gallery/{patch_id}/{dst_name}')
                print(f"  📷 已复制样本图: {src_path.name} -> {dst_path.name}")
            elif src_path.is_dir() and src_path.exists():
                for dir_idx, file in enumerate(src_path.glob('*.*'), start=1):
                    if file.suffix.lower() in ('.png', '.jpg', '.jpeg', '.bmp'):
                        dst_name = f'sample_{dir_idx:02d}{file.suffix.lower()}'
                        dst_path = target_gallery / dst_name
                        shutil.copy2(file, dst_path)
                        sample_relative_paths.append(f'gallery/{patch_id}/{dst_name}')
                        print(f"  📷 已从目录复制样本图: {file.name} -> {dst_path.name}")

    # 检查是否已存在同 ID 补丁，若存在则更新，否则新增
    existing_index = None
    for i, item in enumerate(manifest_data):
        if item.get('id') == patch_id:
            existing_index = i
            break

    patch_entry = {
        "id": patch_id,
        "name": name,
        "rarity": rarity,
        "enabled": True,
        "description": desc or f"{rarity}式神 {name} 识别补丁",
        "samples": sample_relative_paths
    }

    if existing_index is not None:
        manifest_data[existing_index] = patch_entry
        print(f"🔄 更新现有补丁项: [{patch_id}] {name}")
    else:
        manifest_data.append(patch_entry)
        print(f"✨ 添加新补丁项: [{patch_id}] {name}")

    # 写入清单
    with open(manifest_path, 'w', encoding='utf-8') as f:
        json.dump(manifest_data, f, ensure_ascii=False, indent=2)

    print("\n🎉 补丁创建成功！")
    print(f"  - 式神名称: {name}")
    print(f"  - 稀有度:   {rarity}")
    print(f"  - 补丁 ID:  {patch_id}")
    print(f"  - 样本数量: {len(sample_relative_paths)}")
    print(f"  - 样本目录: {target_gallery}")

    # 测试重载验证
    try:
        from oashya import labels
        from oashya.patch_matcher import patch_matcher
        labels.reload_patches()
        patch_matcher.reload()
        new_class_id = labels.label2id(patch_id)
        print(f"✅ 验证成功：系统已动态分配 Class ID = {new_class_id}，可在任务配置的优先式神中直接填写 '{name}'！\n")
    except Exception as e:
        print(f"⚠️ 自动重载验证提示: {e}\n")

    return True


def main():
    parser = argparse.ArgumentParser(description="百鬼夜行式神增量补丁快捷录入工具")
    parser.add_argument("--name", type=str, help="式神中文名称 (例如: 泷 / 神启荒)")
    parser.add_argument("--rarity", type=str, choices=['SP', 'SSR', 'SR', 'R', 'N', 'G'], help="式神稀有度 (SP/SSR/SR/R/N/G)")
    parser.add_argument("--id", type=str, default=None, help="自定义补丁ID (可选，默认自动递增)")
    parser.add_argument("--images", nargs='+', default=[], help="式神样本图片路径 (1~3张截图或包含截图的目录)")
    parser.add_argument("--desc", type=str, default="", help="补丁描述 (可选)")

    args = parser.parse_args()

    if not args.name or not args.rarity:
        print("=" * 60)
        print(" 🌸 百鬼夜行 - 式神增量补丁生成助手 🌸 ")
        print("=" * 60)
        name = input("请输入式神中文名称 (如 '纺愿缘结神'): ").strip()
        if not name:
            print("❌ 名称不能为空！")
            return
        rarity = input("请输入稀有度 [SP/SSR/SR/R/N/G] (默认: SP): ").strip().upper() or "SP"
        imgs_input = input("请输入样本图片路径 (多个路径空格隔开，或直接拖入图片): ").strip()
        image_paths = []
        if imgs_input:
            image_paths = [p.strip(' "\'') for p in imgs_input.split() if p.strip(' "\'')]
        add_shikigami_patch(name=name, rarity=rarity, patch_id=args.id, image_paths=image_paths)
    else:
        add_shikigami_patch(name=args.name, rarity=args.rarity, patch_id=args.id, image_paths=args.images, desc=args.desc)


if __name__ == '__main__':
    main()
