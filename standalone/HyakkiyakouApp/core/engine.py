# core/engine.py - 百鬼夜行核心自动化工作引擎 (QThread 后台线程)
import time
import cv2
import numpy as np
from pathlib import Path
from typing import Optional
from PySide6.QtCore import QThread, Signal

from driver.device_driver import DeviceDriver
from oashya.tracker import Tracker
from oashya.patch_matcher import patch_matcher
from oashya.sync_patches import sync_online_patches
from oashya.labels import id2name, get_class_rarity
from core.agent import Agent
from core.state_recognizer import StateRecognizer, GameState
from core.config_manager import AppConfig
from core.logger import logger

class HyakkiWorker(QThread):
    status_signal = Signal(str)                   # 运行状态简述
    round_signal = Signal(int, int)               # (当前轮次, 目标轮次)
    target_signal = Signal(str, int, int)         # (锁定的式神名, x, y)
    frame_signal = Signal(object, list, object, object) # (img, targets_info, aim_point, focus_name) 实时画面与AI标注
    finished_signal = Signal(bool, str)           # (成功与否, 结束消息)

    def __init__(self, config: AppConfig):
        super().__init__()
        self.config = config
        self._is_running = True
        self.current_round = 0
        self.total_rounds = config.total_rounds
        self.driver = DeviceDriver(
            mode=config.connection_mode,
            serial=config.serial,
            screenshot_method=config.screenshot_method,
            control_method=config.control_method,
            window_title=config.window_title
        )
        self.recognizer = StateRecognizer()
        self.tracker: Optional[Tracker] = None
        self.agent: Optional[Agent] = None

    def stop(self):
        self._is_running = False
        logger.info("[Engine] 收到停止指令，正在退出工作线程...")

    def run(self):
        logger.info("==================================================")
        logger.info(f"🚀 百鬼夜行独立版启动中... (连接模式: {self.config.connection_mode})")
        logger.info(f"🏯 庭院设置: [{self.config.courtyard}], 阴阳师: [{self.config.onmyoji}]")
        logger.info("==================================================")

        # 1. 检查或自动同步网易官方最新式神补丁
        if self.config.auto_sync_patches:
            self.status_signal.emit("正在同步官方最新式神...")
            try:
                sync_online_patches()
            except Exception as e:
                logger.warning(f"在线同步式神补丁提示: {e}")

        # 2. 检查设备/游戏窗口连接
        self.status_signal.emit("正在连接游戏设备/窗口...")
        if not self.driver.is_connected():
            logger.error("❌ 未能连接到游戏设备或窗口！请检查《阴阳师》桌面版或模拟器连接端口。")
            self.finished_signal.emit(False, "未找到游戏窗口或模拟器端口连接失败")
            return

        logger.info(f"✅ 游戏设备连接就绪！")

        # 3. 初始化 AI Tracker 与 Agent
        self.status_signal.emit("加载 AI 深度模型与跟踪器...")
        try:
            tracker_args = {
                'conf_threshold': self.config.conf_threshold,
                'iou_threshold': self.config.iou_threshold,
                'precision': 'fp32',
                'inference_engine': 'onnxruntime',
                'debug': False,
            }
            self.tracker = Tracker(args=tracker_args)
            strategy = {
                'weights': [
                    self.config.sp_weight,
                    self.config.ssr_weight,
                    self.config.sr_weight,
                    self.config.r_weight,
                    self.config.n_weight,
                    self.config.g_weight
                ],
                'priorities': self.config.priorities,
                'invite_friend': self.config.invite_friend,
                'bean_count': self.config.bean_count,
                'auto_bean': self.config.auto_bean,
                'bean_threshold_low': self.config.bean_threshold_low,
            }
            self.agent = Agent(strategy=strategy)
            logger.info("✅ AI 模型与优先策略加载就绪！")
        except Exception as e:
            logger.error(f"❌ 初始化 AI 引擎失败: {e}")
            self.finished_signal.emit(False, f"AI 初始化失败: {e}")
            return

        # 4. 主任务状态机循环
        self.current_round = 0
        last_action = [0, 0, False, 10]
        unknown_state_count = 0

        while self._is_running and self.current_round < self.total_rounds:
            self.round_signal.emit(self.current_round + 1, self.total_rounds)

            # 抓屏
            img = self.driver.screenshot()
            if img is None:
                time.sleep(0.5)
                continue

            state, info = self.recognizer.recognize_state(img)

            if state == GameState.IN_ROOM:
                unknown_state_count = 0
                self.frame_signal.emit(img, [], None, None)
                self.status_signal.emit(f"准备大厅 (第 {self.current_round + 1}/{self.total_rounds} 轮)")
                logger.info(f"📍 处于百鬼夜行准备大厅，准备开始第 {self.current_round + 1} 轮...")
                time.sleep(0.5)

                # 点击“进入/开始”
                start_btn = info.get("start_btn")
                if start_btn:
                    self.driver.click(start_btn[0], start_btn[1])
                else:
                    self.driver.click(1050, 610)
                time.sleep(2.0)

            elif state == GameState.BOSS_SELECT:
                unknown_state_count = 0
                self.frame_signal.emit(img, [], None, None)
                self.status_signal.emit("正在分析并选择最优鬼王...")
                # 智能识别 3 个候选并挑选最高分
                boss_idx, boss_name = self.recognizer.pick_best_boss(img, self.config.priorities)
                card_rois = info.get("card_rois", [(320, 350), (640, 350), (960, 350)])
                if boss_idx < len(card_rois):
                    rx, ry, rw, rh = card_rois[boss_idx]
                    click_x = rx + rw // 2
                    click_y = ry + rh // 2
                else:
                    click_x, click_y = 640, 350

                logger.info(f"👑 选中鬼王: [{boss_name}]，点击坐标 ({click_x}, {click_y})")
                self.driver.click(click_x, click_y)
                time.sleep(0.8)

                # 点击右下角“开始”
                start_btn = info.get("start_btn")
                if start_btn:
                    self.driver.click(start_btn[0], start_btn[1])
                else:
                    self.driver.click(1080, 620)
                time.sleep(2.5)

            elif state == GameState.IN_GAME:
                unknown_state_count = 0
                self.status_signal.emit(f"砸豆进行中 (第 {self.current_round + 1} 轮)")

                # 运行 YOLO 检测与 ByteTrack 运动跟踪
                tracks = self.tracker(image=img, response=last_action)

                # 运行 Agent 决策
                action = self.agent.step(tracks, current_image=img)
                last_action = action
                target_x, target_y, throw, bean = action

                target_name = "未知式神"
                if self.agent.focus:
                    target_name = id2name(self.agent.focus._class)

                # 提取目标列表用于界面实时渲染
                targets_info = []
                for t in tracks:
                    cls_id = getattr(t, '_class', 0)
                    name = id2name(cls_id)
                    rarity = get_class_rarity(cls_id)
                    bbox = getattr(t, 'tlbr', None)
                    if bbox is None and hasattr(t, 'tlwh'):
                        tlwh = t.tlwh
                        bbox = (tlwh[0], tlwh[1], tlwh[0] + tlwh[2], tlwh[1] + tlwh[3])
                    vx, vy = 0.0, 0.0
                    if hasattr(t, 'mean') and len(t.mean) >= 6:
                        vx, vy = float(t.mean[4]), float(t.mean[5])
                    elif hasattr(t, 'velocity'):
                        vx, vy = float(t.velocity[0]), float(t.velocity[1])

                    targets_info.append({
                        "bbox": bbox,
                        "name": name,
                        "rarity": rarity,
                        "score": getattr(t, 'score', 0.9),
                        "vx": vx,
                        "vy": vy,
                        "track_id": getattr(t, 'track_id', 0)
                    })

                aim_point = (target_x, target_y) if throw else None
                focus_name = target_name if throw else None
                self.frame_signal.emit(img, targets_info, aim_point, focus_name)

                if throw:
                    self.target_signal.emit(target_name, target_x, target_y)
                    self.driver.click(target_x, target_y)
                    time.sleep(self.config.shot_interval_ms / 1000.0)
                else:
                    time.sleep(0.04)

            elif state == GameState.SETTLEMENT:
                unknown_state_count = 0
                self.frame_signal.emit(img, [], None, None)
                self.current_round += 1
                self.status_signal.emit(f"第 {self.current_round} 轮结算完成")
                logger.info(f"🎉 第 {self.current_round} 轮百鬼夜行顺利结束！")
                
                # 点击屏幕空白处退出结算
                self.driver.click(640, 620)
                time.sleep(1.5)
                self.driver.click(640, 620)
                time.sleep(1.5)

            else:
                # UNKNOWN
                self.frame_signal.emit(img, [], None, None)
                unknown_state_count += 1
                if unknown_state_count % 10 == 0:
                    logger.info("⏳ 正在等待进入百鬼夜行相关界面...")
                time.sleep(0.3)

        if not self._is_running:
            self.status_signal.emit("已手动停止")
            self.finished_signal.emit(True, "用户手动停止")
            logger.info("⏹ 百鬼夜行任务已手动停止。")
        else:
            self.status_signal.emit(f"已完成全部 {self.total_rounds} 轮")
            self.finished_signal.emit(True, f"已顺利完成全部 {self.total_rounds} 轮百鬼夜行！")
            logger.info(f"🏆 全部 {self.total_rounds} 轮百鬼夜行任务圆满完成！")
