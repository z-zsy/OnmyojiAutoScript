# This Python file uses the following encoding: utf-8
# @author runhey
# github https://github.com/runhey
import time
import random
import re
from cached_property import cached_property
from datetime import datetime, timedelta
from module.atom.click import RuleClick

from module.base.timer import Timer
from module.atom.image_grid import ImageGrid
from module.atom.image import RuleImage
from module.base.utils import point2str
from module.logger import logger
from module.exception import TaskEnd, GameStuckError
from tasks.KekkaiUtilize.page import page_guild_realm, page_guild_realm_growth, page_guild_card

from tasks.KekkaiUtilize.script_task import ScriptTask as KU
from tasks.KekkaiUtilize.utils import CardClass
from user_tasks.KekkaiActivationSelf.assets import KekkaiActivationSelfAssets
from user_tasks.KekkaiActivationSelf.utils import parse_rule
from user_tasks.KekkaiActivationSelf.config import ActivationConfigSelf, CardType
from tasks.Utils.config_enum import ShikigamiClass
from tasks.GameUi.page import page_main, page_guild

""" 结界挂卡-self """
class ScriptTask(KU, KekkaiActivationSelfAssets):

    def run(self):
        con = self.config.kekkai_activation_self.activation_config
        # 进入寮结界
        self.goto_page(page_guild_realm)

        if con.exchange_before:
            self.check_max_lv(con.shikigami_class, con.auto_fill)
        # 收取经验
        self.harvest_card()

        # 如果找不到卡超过设定次数
        if con.card_not_found_count >= 5:
            logger.info("未找到卡超过5次, 默认执行一次挂卡逻辑")
            self.goto_page(page_guild_card)
            # 点击全选
            self.ui_click_until_disappear(self.I_A_CARD_ALL)
            # 找到点击的按钮后就一直点
            self.ui_click_until_disappear(self.I_A_ACTIVATE_YELLOW)
            # 再次找到红色确认按钮
            self.ui_click_until_disappear(self.I_A_ACTIVATE_YELLOW)

            # 是否勾选自动下太鼓和斗鱼
            if con.exchange_max:
                if self.check_exchange_max():
                    logger.info("自动下卡成功！，将次数重置为 0")
                    con.card_not_found_count = 0
            else:
                logger.info("手动下卡成功！，将次数重置为 0")
                con.card_not_found_count = 0

            self.set_next_run("KekkaiActivationSelf", target=datetime.now() + timedelta(days=1))
            raise TaskEnd("KekkaiActivationSelf")

        self.goto_page(page_guild_card)

        # 挂卡点击过滤按钮
        if con.card_type == CardType.TAIKO:
            self.ui_click_until_disappear(self.I_A_CARD_TAIKO)
        elif con.card_type == CardType.FISH:
            self.ui_click_until_disappear(self.I_A_CARD_FISH)

        # 找到要挂的结界卡
        click_target = self.check_card_num()

        if click_target is None:
            logger.error("未找到可以激活的结界卡!")
            con.card_not_found_count += 1
            logger.info(f"没找到结界卡加一:{con.card_not_found_count}")
            self.set_next_run("KekkaiActivationSelf", target=datetime.now() + timedelta(days=1))
            raise TaskEnd("KekkaiActivationSelf")

        self.ui_click_until_disappear(click_target)
        # 激活结界卡
        self.ui_click_until_disappear(self.I_A_ACTIVATE_YELLOW)
        # 再次确认
        self.ui_click_until_disappear(self.I_A_ACTIVATE_YELLOW)

        # 自动下太鼓和斗鱼逻辑
        if con.exchange_max:
            if self.check_exchange_max():
                logger.info("置换高收益成功！")

        self.set_next_run("KekkaiActivationSelf", target=datetime.now() + timedelta(days=1))
        raise TaskEnd("KekkaiActivationSelf")

    def parse_star_priority(self, priority_str: str) -> list[int]:
        priority = []
        if priority_str:
            for item in re.findall(r'\d+', priority_str):
                star = int(item)
                if 1 <= star <= 6 and star not in priority:
                    priority.append(star)
        for star in [6, 5, 4, 3, 2, 1]:
            if star not in priority:
                priority.append(star)
        return priority

    def check_card_num(self):
        conf = self.config.kekkai_activation_self.activation_config
        rule = conf.card_type
        star_priority_str = conf.star_priority
        star_order = self.parse_star_priority(star_priority_str)
        logger.info(f"星级优先级排序规则: {star_order}")

        if rule == CardType.TAIKO:
            min_card_num = conf.min_taiko_num
            check_card = "勾玉"
        elif rule == CardType.FISH:
            min_card_num = conf.min_fish_num
            check_card = "体力"
        else:
            logger.error('Unknown utilize rule')
            raise ValueError('Unknown utilize rule')

        ocr_count = 0
        while 1:
            self.screenshot()
            results = self.O_CHECK_CARD_NUMBER.detect_and_ocr(self.device.image)
            ocr_count += 1
            filtered_results = [result for result in results if check_card in result.ocr_text]
            logger.info(f"识别到卡: {[result.ocr_text for result in filtered_results]}")

            candidate_cards = []
            for result in filtered_results:
                t = result.ocr_text
                numbers = [int(num) for num in re.findall(r'\d+', t)]
                if numbers:
                    yield_num = numbers[0]
                    if yield_num < min_card_num:
                        continue
                    star_match = re.search(r'([1-6])\s*星', t)
                    if star_match:
                        card_star = int(star_match.group(1))
                    elif len(numbers) > 1 and 1 <= numbers[1] <= 6:
                        card_star = numbers[1]
                    else:
                        card_star = 0

                    if card_star in star_order:
                        star_priority_index = star_order.index(card_star)
                    else:
                        star_priority_index = 99

                    priority_key = (-star_priority_index, yield_num)
                    candidate_cards.append((priority_key, card_star, yield_num, result))

            if candidate_cards:
                sorted_results = sorted(candidate_cards, key=lambda x: x[0], reverse=True)
                selected = sorted_results[0]
                max_result = selected[3]
                sel_star = selected[1]
                sel_yield = selected[2]

                box = max_result.box
                x_min = self.O_CHECK_CARD_NUMBER.roi[0] + box[0][0]
                y_min = self.O_CHECK_CARD_NUMBER.roi[1] + box[0][1]
                width = box[1][0] - box[0][0]
                height = box[2][1] - box[1][1]
                roi = int(x_min), int(y_min), int(width), int(height)

                target = RuleClick(roi_front=roi, roi_back=roi, name="tmpclick")
                logger.info(f"优先选择挂卡: [{max_result.ocr_text}] (星级: {sel_star}星, 收益: {sel_yield}) ROI: {roi}")
                return target
            else:
                if ocr_count > 3:
                    logger.error('多次未找到符合条件的结果, 退出')
                    return None
                logger.warning("未找到符合条件的结果, 准备往上滑动")
                duration = 2
                safe_pos_x = random.randint(200, 400)
                safe_pos_y = random.randint(580, 600)
                p1 = (safe_pos_x, safe_pos_y)
                p2 = (safe_pos_x, safe_pos_y - 410)
                logger.info('Swipe %s -> %s, %sS ' % (point2str(*p1), point2str(*p2), duration))
                self.device.swipe_adb(p1, p2, duration=duration)
                time.sleep(1)
                continue
