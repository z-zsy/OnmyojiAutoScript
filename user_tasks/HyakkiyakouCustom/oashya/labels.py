# This Python file uses the following encoding: utf-8
# @author runhey
# github https://github.com/runhey
from dataclasses import dataclass

# sp
sp = {
    'sp_001': '少羽大天狗',
    'sp_002': '炼狱茨木童子',
    'sp_003': '稻荷神御馔津',
    'sp_004': '苍风一目连',
    'sp_005': '赤影妖刀姬',
    'sp_006': '御怨般若',
    'sp_007': '骁浪荒川之主',
    'sp_008': '烬天玉澡前',
    'sp_009': '鬼王酒吞童子',
    'sp_010': '天剑韧心鬼切',
    'sp_011': '聆海金鱼姬',
    'sp_012': '浮世青行灯',
    'sp_013': '缚骨清姬',
    'sp_014': '待宵姑获鸟',
    'sp_015': '麓铭大岳丸',
    'sp_016': '初翎山风',
    'sp_017': '夜溟彼岸花',
    'sp_018': '蝉冰雪女',
    'sp_019': '空相面灵气',
    'sp_020': '绘世花鸟卷',
    'sp_021': '因幡辉夜姬',
    'sp_022': '梦寻山兔',
    'sp_023': '神堕八岐大蛇',
    'sp_024': '大夜摩天阎魔',
    'sp_025': '心狩鬼女红叶',
    'sp_026': '神启荒',
    'sp_027': '禅心云外镜',
    'sp_028': '流光追月神',
    'sp_029': '修罗鬼童丸',
    'sp_030': '寻森小鹿男',
    'sp_031': '纺愿缘结神',
    'sp_032': '渺念萤草',
    'sp_033': '本真三尾狐',
    'sp_034': '鲸汐千姬',
    'sp_035': '福悦座敷童子', }

# ssr
ssr = {
    'ssr_001': '大天狗',
    'ssr_002': '酒吞童子',
    'ssr_003': '荒川之主',
    'ssr_004': '阎魔',
    'ssr_005': '两面佛',
    'ssr_006': '小鹿男',
    'ssr_007': '茨木童子',
    'ssr_008': '青行灯',
    'ssr_009': '妖刀姬',
    'ssr_010': '一目连',
    'ssr_011': '花鸟卷',
    'ssr_012': '辉夜姬',
    'ssr_013': '荒',
    'ssr_014': '彼岸花',
    'ssr_015': '雪童子',
    'ssr_016': '山风',
    'ssr_017': '玉澡前',
    'ssr_018': '御馔津',
    'ssr_019': '面灵气',
    'ssr_020': '鬼切',
    'ssr_021': '白藏主',
    'ssr_022': '八岐大蛇',
    'ssr_023': '不知火',
    'ssr_024': '大岳丸',
    'ssr_025': '泷夜叉姬',
    'ssr_026': '云外镜',
    'ssr_027': '鬼童丸',
    'ssr_028': '缘结神',
    'ssr_029': '铃鹿御前',
    'ssr_030': '紧那罗',
    'ssr_031': '千姬',
    'ssr_032': '帝释天',
    'ssr_033': '阿修罗',
    'ssr_034': '食灵',
    'ssr_035': '饭筒',
    'ssr_036': '铃彦姬',
    'ssr_037': '不见岳',
    'ssr_038': '须佐之男',
    'ssr_039': '寻香行',
    'ssr_040': '季',
    'ssr_041': '月读',
    'ssr_042': '言灵',
    'ssr_043': '孔雀明王',
    'ssr_044': '天照',
    'ssr_045': '伊邪那美',
    'ssr_046': '泷'}

# sr
sr = {
    'sr_001': '桃花妖',
    'sr_002': '雪女',
    'sr_003': '鬼使白',
    'sr_004': '鬼使黑',
    'sr_005': '孟婆',
    'sr_006': '犬神',
    'sr_007': '骨女',
    'sr_008': '鬼女红叶',
    'sr_009': '跳跳哥哥',
    'sr_010': '傀儡师',
    'sr_011': '海坊主',
    'sr_012': '判官',
    'sr_013': '凤凰火',
    'sr_014': '吸血姬',
    'sr_015': '妖狐',
    'sr_016': '妖琴师',
    'sr_017': '食梦貘',
    'sr_018': '清姬',
    'sr_019': '镰铀',
    'sr_020': '姑获鸟',
    'sr_021': '二口女',
    'sr_022': '白狼',
    'sr_023': '樱花妖',
    'sr_024': '惠比寿',
    'sr_025': '络新妇',
    'sr_026': '般若',
    'sr_027': '青坊主',
    'sr_028': '万年竹',
    'sr_029': '夜叉',
    'sr_030': '黑童子',
    'sr_031': '白童子',
    'sr_032': '烟烟罗',
    'sr_033': '金鱼姬',
    'sr_034': '档鸩',
    'sr_035': '以津真天',
    'sr_036': '匣中少女',
    'sr_037': '小松丸',
    'sr_038': '书翁',
    'sr_039': '百目鬼',
    'sr_040': '追月神',
    'sr_041': '日和坊',
    'sr_042': '熏',
    'sr_043': '奕',
    'sr_044': '猫掌柜',
    'sr_045': '人面树',
    'sr_046': '於菊虫',
    'sr_047': '一反木绵',
    'sr_048': '入殓师',
    'sr_049': '化鲸',
    'sr_050': '海忍',
    'sr_051': '久次良',
    'sr_052': '蟹姬',
    'sr_053': '纸舞',
    'sr_054': '星熊童子',
    'sr_055': '风狸',
    'sr_056': '蝎女',
    'sr_057': '入内雀',
    'sr_058': '怡细工',
    'sr_059': '川猿',
    'sr_060': '迦楼罗',
    'sr_061': '灵海蝶',
    'sr_062': '粉婆婆',
    'sr_063': '天逆每',
    'sr_064': '慧明灯',
    'sr_065': '盗人神'}

# r
r = {
    'r_001': '三尾狐',
    'r_002': '座敷童子',
    'r_003': '鲤鱼精',
    'r_004': '九命猫',
    'r_005': '狸猫',
    'r_006': '河童',
    'r_007': '童男',
    'r_008': '童女',
    'r_009': '饿鬼',
    'r_010': '巫师',
    'r_011': '鸦天狗',
    'r_012': '食发鬼',
    'r_013': '武士之灵',
    'r_014': '雨女',
    'r_015': '跳跳弟弟',
    'r_016': '跳跳妹妹',
    'r_017': '兵俑',
    'r_018': '丑时之女',
    'r_019': '独眼小僧',
    'r_020': '铁鼠',
    'r_021': '椒图',
    'r_022': '管狐',
    'r_023': '山兔',
    'r_024': '萤草',
    'r_025': '蝴蝶精',
    'r_026': '山童',
    'r_027': '首无',
    'r_028': '觉',
    'r_029': '青蛙瓷器',
    'r_030': '古笼火',
    'r_031': '免丸',
    'r_032': '数珠',
    'r_033': '小袖之手',
    'r_034': '电师',
    'r_035': '天井下',
    'r_036': '垢尝',
    'r_037': '影鳄'}

# n 卡
n = {
    'n_001': '灯笼鬼',
    'n_002': '提灯小僧',
    'n_003': '赤舌',
    'n_004': '盗墓小鬼',
    'n_005': '寄生魂',
    'n_006': '唐纸伞妖',
    'n_007': '天邪鬼绿',
    'n_008': '天邪鬼赤',
    'n_009': '天邪鬼黄',
    'n_010': '天邪鬼青',
    'n_011': '帚神',
    'n_012': '涂壁'}

# 呱太
g = {
    'g_001': '大天狗呱',
    'g_002': '酒吞呱',
    'g_003': '荒川呱',
    'g_004': '阎魔呱',
    'g_005': '两面佛呱',
    'g_006': '小鹿男呱',
    'g_007': '茨木呱',
    'g_008': '青行灯呱',
    'g_009': '妖刀姬呱',
    'g_010': '一目连呱',
    'g_011': '花鸟卷呱',
    'g_012': '辉夜姬呱',
    'g_013': '荒呱',
    'g_014': '彼岸花呱',
    'g_015': '雪童子呱',
    'g_016': '玉藻前呱',
    'g_017': '御馒津呱'}

buff = {
    'buff_001': '式神灯笼',
    'buff_002': '式神减速',
    'buff_003': '砸豆加速',
    'buff_004': '豆子获取',
    'buff_005': '式神冰冻',
    'buff_006': '概率UP',
    'buff_007': '好友UP',
}


import json
from pathlib import Path

# 补丁映射注册表
PATCH_REGISTRY: dict[int, dict] = {}
PATCH_ID_TO_CLASS_ID: dict[str, int] = {}


def load_patches() -> list[dict]:
    """从 patches/patch_manifest.json 加载增量补丁"""
    manifest_path = Path(__file__).resolve().parent / 'patches' / 'patch_manifest.json'
    if not manifest_path.exists():
        return []
    try:
        with open(manifest_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            if isinstance(data, list):
                return [p for p in data if p.get('enabled', True)]
    except Exception:
        pass
    return []


def gen_classify() -> list[dict]:
    result = []
    id_index: int = 0
    # 基础 219 个类别 (0 ~ 218) 严格固定顺序，保证 ONNX 输出不错位
    for i in [buff, n, g, r, sr, ssr, sp]:
        for k, v in i.items():
            result.append({'name': v,  # 中文
                           'class': k,  # label
                           'id': id_index})  # int
            id_index += 1

    # 动态追加补丁类别 (从 219 开始顺延)
    PATCH_REGISTRY.clear()
    PATCH_ID_TO_CLASS_ID.clear()
    patches = load_patches()
    for p in patches:
        p_id = p.get('id', f'patch_{id_index}')
        p_name = p.get('name', p_id)
        p_rarity = p.get('rarity', 'SSR').upper()
        p_entry = {
            'name': p_name,
            'class': p_id,
            'id': id_index,
            'rarity': p_rarity,
            'is_patch': True,
            'patch_data': p
        }
        result.append(p_entry)
        PATCH_REGISTRY[id_index] = p_entry
        PATCH_ID_TO_CLASS_ID[p_id] = id_index
        id_index += 1

    return result


CLASSIFY = gen_classify()


@dataclass
class CLASSINDEX:
    MIN_BUFF: int = 0
    MAX_BUFF: int = 6
    MIN_N: int = 7
    MAX_N: int = 18
    MIN_G: int = 19
    MAX_G: int = 35
    MIN_R: int = 36
    MAX_R: int = 72
    MIN_SR: int = 73
    MAX_SR: int = 137
    MIN_SSR: int = 138
    MAX_SSR: int = 183
    MIN_SP: int = 184
    MAX_SP: int = 218
    BUFF_001: int = 0
    BUFF_002: int = 1
    BUFF_003: int = 2
    BUFF_004: int = 3
    BUFF_005: int = 4
    BUFF_006: int = 5
    BUFF_007: int = 6
    R_007: int = 42
    R_008: int = 43


def reload_patches():
    """热重载补丁配置"""
    global CLASSIFY
    CLASSIFY = gen_classify()


def get_class_rarity(class_id: int) -> str:
    """获取指定 class_id 的稀有度（兼容原生 218 类别与补丁）"""
    if class_id in PATCH_REGISTRY:
        return PATCH_REGISTRY[class_id].get('rarity', 'SSR')
    if CLASSINDEX.MIN_SP <= class_id <= CLASSINDEX.MAX_SP:
        return 'SP'
    if CLASSINDEX.MIN_SSR <= class_id <= CLASSINDEX.MAX_SSR:
        return 'SSR'
    if CLASSINDEX.MIN_SR <= class_id <= CLASSINDEX.MAX_SR:
        return 'SR'
    if CLASSINDEX.MIN_R <= class_id <= CLASSINDEX.MAX_R:
        return 'R'
    if CLASSINDEX.MIN_N <= class_id <= CLASSINDEX.MAX_N:
        return 'N'
    if CLASSINDEX.MIN_G <= class_id <= CLASSINDEX.MAX_G:
        return 'G'
    if CLASSINDEX.MIN_BUFF <= class_id <= CLASSINDEX.MAX_BUFF:
        return 'BUFF'
    return 'UNKNOWN'


def id2label(idd: int) -> str:
    if 0 <= idd < len(CLASSIFY):
        return CLASSIFY[idd]['class']
    return f'unknown_{idd}'


def id2name(idd: int) -> str:
    if 0 <= idd < len(CLASSIFY):
        return CLASSIFY[idd]['name']
    return f'未知式神_{idd}'


def label2id(label: str) -> int:
    """支持通过 label (如 sp_001) 或 中文名称 (如 少羽大天狗) 查询 id"""
    for i in CLASSIFY:
        if i['class'] == label or i['name'] == label:
            return i['id']
    raise ValueError(f'Unknown label or name: {label}')


def get_all_names() -> set[str]:
    """获取本地所有已收录式神的名称集合"""
    return {i['name'] for i in CLASSIFY}


def is_known_shikigami(name: str) -> bool:
    """判断式神名称是否已在本地库或补丁库中收录（支持子串与模糊匹配）"""
    if not name:
        return False
    for i in CLASSIFY:
        known_name = i['name']
        if name == known_name or (len(name) >= 3 and (name in known_name or known_name in name)):
            return True
    return False

