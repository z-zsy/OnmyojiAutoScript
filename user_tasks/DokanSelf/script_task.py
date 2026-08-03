# This Python file uses the following encoding: utf-8
# @author runhey
# github https://github.com/runhey
import re
from time import sleep
from module.logger import logger
from tasks.Dokan.script_task import ScriptTask as BaseDokanTask, position_offset
from user_tasks.DokanSelf.assets import DokanSelfAssets
from user_tasks.DokanSelf.config import DokanSelf


class ScriptTask(BaseDokanTask, DokanSelfAssets):
    """
    道馆突破-鑫 专属逻辑：
    在寻馆阶段，硬性校验是否带有【鑫】字寮徽标志或【鑫】字名称。
    已被他人击破识别、赏金/人数下限、御魂与阵容分级切换等全套逻辑 100% 完美继承。
    """

    def find_dokan(self, score=4.6):
        dokan_conf = getattr(self.config.dokan_self, 'dokan_config', None)
        if not dokan_conf:
            dokan_conf = getattr(self.config.dokan, 'dokan_config', None)

        only_target_icon = getattr(dokan_conf, 'only_attack_target_icon', True)
        fallback_random = getattr(dokan_conf, 'fallback_random_if_not_found', False)

        num_fresh = 0
        backup = {
            'i_point_bounty': self.I_RIGHTPAD_POINT_BOUNTY.roi_back,
            'i_point_people_num': self.I_CENTER_POINT_PEOPLE_NUMBER.roi_back
        }

        def restore_roi():
            self.I_RIGHTPAD_POINT_BOUNTY.roi_back = backup['i_point_bounty']
            self.I_CENTER_POINT_PEOPLE_NUMBER.roi_back = backup['i_point_people_num']

        def check_target_icon(item_roi) -> bool:
            """
            检测指定候选道馆 item 是否包含【鑫】字图标或名称
            """
            if not only_target_icon:
                return True

            # 1. OCR 核心识别：扫描卡片行的文字（高精度命中 '鑫' 字）
            self.screenshot()
            try:
                self.O_DOKAN_CENTER_PEOPLE_NUMBER.roi = position_offset(item_roi, (-260, -15, 320, 50))
                text = self.O_DOKAN_CENTER_PEOPLE_NUMBER.detect_text(self.device.image)
                if '鑫' in text:
                    logger.info(f"[DokanSelf] PaddleOCR 成功识别到【鑫】字! 识别结果: {text}")
                    return True
            except Exception as e:
                logger.debug(f"[DokanSelf] OCR scanning error: {e}")

            # 2. 图像模板辅助识别
            icon_area = position_offset(item_roi, (-250, -40, 200, 80))
            self.I_XIN_ICON.roi_front = icon_area
            self.I_XIN_ICON.roi_back = icon_area

            if self.appear(self.I_XIN_ICON):
                logger.info(f"[DokanSelf] 模板匹配到【鑫】字寮徽标志! ROI={icon_area}")
                return True

            logger.warning(f"[DokanSelf] 该道馆未包含【鑫】字标志，自动跳过!")
            return False

        def find_challengeable(ignore_score=False):
            restore_roi()
            self.screenshot()
            bounty_list = self.find_all_element(self.I_RIGHTPAD_POINT_BOUNTY, (0, 0, 0, 50))
            logger.info(f'find elements list:{bounty_list}')
            min_score = 10
            idx_selected = -1

            for idx, item in enumerate(bounty_list):
                self.device.click_record_clear()
                logger.info(f"------start no.{idx} =={item}-----------")

                if not ignore_score and not check_target_icon(item):
                    continue

                self.screenshot()
                while self.appear(self.I_CENTER_CHALLENGE):
                    self.click(self.C_DOKAN_CANCEL_SELECT_DOKAN, interval=1.5)
                    self.wait_animate_stable(self.C_DOKAN_CANCEL_SELECT_DOKAN_CHECK_ANIMATE, interval=0.5, timeout=1.5)

                self.O_DOKAN_RIGHTPAD_BOUNTY.roi = position_offset(item, (0, 0, 100, 0))
                bounty = self.O_DOKAN_RIGHTPAD_BOUNTY.ocr(self.device.image)
                tmp = re.search(r'(\d+)', bounty)
                if not tmp:
                    logger.warning(f"can't find bounty,item = {item},ocr bounty={bounty}")
                    continue
                bounty = float(tmp.group())

                self.I_RIGHTPAD_POINT_BOUNTY.roi_back = position_offset(item, (-10, -10, 20, 20))
                if not self.ui_click_until_appear_or_timeout(self.I_RIGHTPAD_POINT_BOUNTY, self.I_CENTER_CHALLENGE,
                                                             interval=1.5, timeout=8):
                    logger.info(f"can't find challenge button (可能已被他人先击破), idx={idx} item={item}")
                    continue

                self.screenshot()
                if not self.appear(self.I_CENTER_POINT_PEOPLE_NUMBER):
                    logger.warning(f"can't find point people number image, item={item}")
                    continue

                self.O_DOKAN_CENTER_PEOPLE_NUMBER.roi = position_offset(
                    self.I_CENTER_POINT_PEOPLE_NUMBER.roi_front,
                    (0, 0, 0, 30))
                p_num = self.O_DOKAN_CENTER_PEOPLE_NUMBER.detect_text(self.device.image)
                tmp = re.search(r"(\d+)", p_num)
                if not tmp:
                    logger.warning(f"can't find people number in ocr result,item={item}, p_num={p_num}")
                    continue
                p_num = float(tmp.group())
                logger.info(f"bounty:{bounty},people_num:{p_num},score:{bounty / p_num}")

                item_score = bounty / p_num
                if item_score < min_score:
                    min_score = item_score
                    idx_selected = idx

                if item_score > score or item_score < 1.5:
                    logger.info("click to making challenge disappear")
                    continue
                if p_num < dokan_conf.min_people_num:
                    logger.info("people num too small")
                    continue
                if bounty < dokan_conf.min_bounty:
                    logger.info("bounty too small")
                    continue
                if not self.appear(self.I_CENTER_GUANZHU_XIUXI):
                    continue

                logger.info(f"find_dokan: 【鑫】字道馆匹配成功! bounty:{bounty},people_num:{p_num},score:{bounty / p_num}")
                return True

            if ignore_score and fallback_random and idx_selected >= 0:
                x, y, w, h = bounty_list[idx_selected]
                while 1:
                    self.screenshot()
                    if self.appear(self.I_CENTER_CHALLENGE):
                        return True
                    self.device.click(x, y)
                    sleep(0.5)
            return False

        max_refresh = getattr(dokan_conf, 'find_dokan_refresh_count', 7)
        while num_fresh < max_refresh:
            for i in range(3):
                sleep(3)
                if find_challengeable():
                    logger.info("find challengeable 【鑫】 dokan")
                    self.ui_click(self.I_CENTER_CHALLENGE, self.I_CHALLENGE_ENSURE, interval=1)
                    self.ui_click_until_disappear(self.I_CHALLENGE_ENSURE, interval=1)
                    self.config.dokan_self.attack_count_config.del_attack_count(1, self.config.save)
                    restore_roi()
                    return True
                self.swipe(self.S_DOKAN_LIST_UP)

            restore_roi()
            logger.info("=========refresh dokan list=========")
            self.ui_click(self.C_DOKAN_REFRESH, self.I_REFRESH_ENSURE, interval=1)
            self.ui_click_until_disappear(self.I_REFRESH_ENSURE, interval=1)
            logger.info("Refresh Done")
            num_fresh += 1

        if fallback_random and find_challengeable(ignore_score=True):
            logger.warning("刷新上限已用完, 开启了保底随机打其他道馆")
            self.ui_click(self.I_CENTER_CHALLENGE, self.I_CHALLENGE_ENSURE, interval=1)
            self.ui_click_until_disappear(self.I_CHALLENGE_ENSURE, interval=1)
            self.config.dokan_self.attack_count_config.del_attack_count(1, self.config.save)
            return True

        logger.warning("未找到任何带有【鑫】字标志的道馆，结束本次寻找。")
        return False
