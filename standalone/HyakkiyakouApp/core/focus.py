# core/focus.py - 单目标跟踪与落点决策
import numpy as np
from typing import List, Tuple
from oashya.labels import id2label, id2name, get_class_rarity, CLASSINDEX as CI
from core.logger import logger

class Focus:
    def __init__(self, inputs: list):
        self._id: int = inputs[0]
        self._class: int = inputs[1]
        self._conf: float = inputs[2]
        self._cx: int = int(inputs[3])
        self._cy: int = int(inputs[4])
        self._w: int = int(inputs[5])
        self._h: int = int(inputs[6])
        self._v: float = float(inputs[7])
        self._omega: float = 0.0
        self._omega_buff: float = 0.0

    def __eq__(self, o):
        return self._id == o._id or o._class == self._class

    def omega(self, z):
        cy = min(max(self._cy, 0), 719)
        cx = min(max(self._cx, 0), 1279)
        self._omega = float(z[cy, cx])
        return self._omega

    def set_omega(self, value):
        self._omega = value

    def update(self, focus):
        self._id = focus._id
        self._class = focus._class
        self._conf = focus._conf
        self._cx = focus._cx
        self._cy = focus._cy
        self._w = focus._w
        self._h = focus._h
        self._v = focus._v

    def omega_buff(self, tracks: list, invite_friend: bool = False, has_prob_up: bool = False) -> Tuple[float, int, int, float, int]:
        """
        计算屏幕上飞过的 BUFF 的收益权重与落点
        """
        buff_omega = 0.0
        buff_cx, buff_cy, buff_v = 0, 0, 0.0
        buff_class = -1

        for track in tracks:
            _id, _class, _conf, _cx, _cy, _w, _h, _v = track
            rarity = get_class_rarity(_class)
            if rarity != 'BUFF':
                continue

            current_buff_omega = 0.0
            if _class == CI.BUFF_PROB_UP:
                current_buff_omega = 3.5  # 概率UP最高优先级
            elif _class == CI.BUFF_FRIEND_UP and invite_friend:
                current_buff_omega = 3.0
            elif _class == CI.BUFF_ADD_BEANS:
                current_buff_omega = 2.5
            elif _class == CI.BUFF_SPEED_UP:
                current_buff_omega = 2.0
            elif _class in (CI.BUFF_SLOW_DOWN, CI.BUFF_FREEZE):
                current_buff_omega = 2.0

            if current_buff_omega > buff_omega:
                buff_omega = current_buff_omega
                buff_cx = int(_cx)
                buff_cy = int(_cy)
                buff_v = float(_v)
                buff_class = _class

        return buff_omega, buff_cx, buff_cy, buff_v, buff_class

    def decision(self, tracks: list, strategy: dict, state: list) -> Tuple[int, int, bool, int]:
        """
        根据当前状态决策是否投掷以及目标坐标与豆数
        返回: (target_x, target_y, throw_bool, bean_count)
        """
        invite_friend = strategy.get('invite_friend', False)
        buff_omega, buff_cx, buff_cy, buff_v, buff_class = self.omega_buff(tracks, invite_friend)

        # 判断是优先砸 BUFF 还是优先砸式神
        if buff_omega > self._omega:
            # 砸 BUFF
            target_x = int(buff_cx + buff_v * 100)
            target_y = max(int(buff_cy - 40), 50)
            target_class = buff_class
            is_buff = True
        else:
            # 砸当前锁定的式神 (计算提前量: 考虑移动速度)
            target_x = int(self._cx + self._v * 100 - (self._w // 4))
            target_y = max(int(self._cy - 30), 50)
            target_class = self._class
            is_buff = False

        target_rarity = get_class_rarity(target_class)
        is_rare = (target_rarity in ('SSR', 'SP')) and (not is_buff)

        # 只要位于有效射击区 (200 < target_x < 1150)，且权重 > 0 则投掷
        throw = (150 <= target_x <= 1180) and (self._omega > 0.05 or is_buff)
        
        # 默认 10 豆 (用户配置)
        bean = strategy.get('bean_count', 10)
        if not is_rare and not is_buff and self._omega < 0.2:
            # 对于低价值目标且非稀有，若开启省豆可减少
            pass

        return (target_x, target_y, throw, bean)
