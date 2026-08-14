# gui/main_window.py - 百鬼夜行独立版多标签页现代化主界面 (含实时画面与AI透视HUD)
import sys
import time
import cv2
import numpy as np
from pathlib import Path
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QSpinBox, QDoubleSpinBox, QComboBox, QCheckBox,
    QTextEdit, QGroupBox, QProgressBar, QTabWidget, QLineEdit,
    QMessageBox, QFormLayout, QFrame, QSizePolicy
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QTextCursor, QKeySequence, QShortcut, QImage, QPixmap

from core.config_manager import (
    ConfigManager, AppConfig, ConnectionMode, ScreenshotMethod,
    ControlMethod, CourtyardType, OnmyojiType
)
from core.engine import HyakkiWorker
from core.logger import emitter, logger
from core.vision_annotator import VisionAnnotator
from driver.device_driver import DeviceDriver
from driver.win32_window import Win32Window
from gui.priority_dialog import PriorityDialog
from oashya.sync_patches import sync_online_patches

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("百鬼夜行独立版 - Hyakkiyakou Standalone v2.0 (实时视觉版)")
        self.resize(1060, 780)
        self.setMinimumSize(960, 700)

        self.config_manager = ConfigManager()
        self.config = self.config_manager.config
        self.worker: HyakkiWorker = None
        self.annotator = VisionAnnotator()

        # 待机预览抓屏驱动与定时器
        self.preview_driver: DeviceDriver = None
        self.preview_timer = QTimer(self)
        self.preview_timer.timeout.connect(self._on_preview_tick)
        self._is_previewing = False
        self._last_frame_time = time.time()
        self._fps = 0.0

        self._setup_style()
        self._init_ui()
        self._setup_hotkeys()
        self._setup_log_listener()

        # 定时检测设备与游戏窗口
        self.device_timer = QTimer(self)
        self.device_timer.timeout.connect(self._check_device_status)
        self.device_timer.start(3000)
        self._check_device_status()

    def _setup_style(self):
        self.setStyleSheet("""
            QMainWindow { background-color: #1e1e2e; }
            QWidget { 
                color: #cdd6f4; 
                font-family: 'Microsoft YaHei', 'Segoe UI', sans-serif; 
                font-size: 13px; 
            }
            QTabWidget::pane {
                border: 1px solid #313244;
                border-radius: 8px;
                background-color: #181825;
                top: -1px;
                padding: 6px;
            }
            QTabBar::tab {
                background-color: #313244;
                color: #a6adc8;
                padding: 8px 18px;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
                margin-right: 4px;
                font-weight: bold;
                font-size: 13px;
            }
            QTabBar::tab:selected {
                background-color: #181825;
                color: #89b4fa;
                border: 1px solid #313244;
                border-bottom: none;
            }
            QGroupBox {
                border: 1px solid #313244;
                border-radius: 8px;
                margin-top: 14px;
                padding: 16px 14px 12px 14px;
                font-weight: bold;
                color: #89b4fa;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 12px;
                padding: 0 6px;
                background-color: #181825;
            }
            QLabel { color: #cdd6f4; }
            QLineEdit {
                background-color: #313244;
                color: #cdd6f4;
                border: 1px solid #45475a;
                border-radius: 6px;
                padding: 5px 10px;
                min-height: 26px;
                selection-background-color: #585b70;
            }
            QLineEdit:focus { border: 1px solid #89b4fa; }
            QComboBox {
                background-color: #313244;
                color: #cdd6f4;
                border: 1px solid #45475a;
                border-radius: 6px;
                padding: 5px 10px;
                min-height: 26px;
            }
            QComboBox:focus { border: 1px solid #89b4fa; }
            QComboBox::drop-down {
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 24px;
                border-left: 1px solid #45475a;
                border-top-right-radius: 6px;
                border-bottom-right-radius: 6px;
            }
            QComboBox QAbstractItemView {
                background-color: #1e1e2e;
                border: 1px solid #45475a;
                color: #cdd6f4;
                selection-background-color: #45475a;
                selection-color: #89b4fa;
                padding: 4px;
            }
            QSpinBox, QDoubleSpinBox {
                background-color: #313244;
                color: #cdd6f4;
                border: 1px solid #45475a;
                border-radius: 6px;
                padding: 4px 8px;
                min-height: 26px;
            }
            QSpinBox:focus, QDoubleSpinBox:focus { border: 1px solid #89b4fa; }
            QSpinBox::up-button, QDoubleSpinBox::up-button {
                subcontrol-origin: border;
                subcontrol-position: top right;
                width: 18px;
                border-left: 1px solid #45475a;
                border-bottom: 1px solid #45475a;
                border-top-right-radius: 6px;
                background-color: #313244;
            }
            QSpinBox::up-button:hover, QDoubleSpinBox::up-button:hover { background-color: #45475a; }
            QSpinBox::down-button, QDoubleSpinBox::down-button {
                subcontrol-origin: border;
                subcontrol-position: bottom right;
                width: 18px;
                border-left: 1px solid #45475a;
                border-bottom-right-radius: 6px;
                background-color: #313244;
            }
            QSpinBox::down-button:hover, QDoubleSpinBox::down-button:hover { background-color: #45475a; }
            QCheckBox { spacing: 8px; }
            QCheckBox::indicator {
                width: 16px;
                height: 16px;
                border-radius: 4px;
                border: 1px solid #45475a;
                background-color: #313244;
            }
            QCheckBox::indicator:checked { background-color: #89b4fa; border-color: #89b4fa; }
            QPushButton {
                background-color: #313244;
                color: #cdd6f4;
                border: 1px solid #45475a;
                border-radius: 6px;
                padding: 6px 16px;
                min-height: 24px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #45475a; }
            QPushButton#btn_start { background-color: #a6e3a1; color: #11111b; font-size: 14px; padding: 10px 24px; min-height: 28px; }
            QPushButton#btn_start:hover { background-color: #94e2d5; }
            QPushButton#btn_stop { background-color: #f38ba8; color: #11111b; font-size: 14px; padding: 10px 24px; min-height: 28px; }
            QPushButton#btn_stop:hover { background-color: #eba0ac; }
            QPushButton#btn_sync { background-color: #89b4fa; color: #11111b; font-size: 12px; padding: 6px 12px; }
            QPushButton#btn_sync:hover { background-color: #b4befe; }
            QPushButton#btn_test { background-color: #89b4fa; color: #11111b; font-size: 12px; font-weight: bold; padding: 6px 14px; border-radius: 6px; }
            QPushButton#btn_test:hover { background-color: #b4befe; }
            QPushButton#btn_preview { background-color: #fab387; color: #11111b; font-size: 12px; font-weight: bold; padding: 6px 14px; border-radius: 6px; }
            QPushButton#btn_preview:hover { background-color: #f9e2af; }
            QTextEdit {
                background-color: #11111b;
                border: 1px solid #313244;
                border-radius: 8px;
                color: #cdd6f4;
                font-family: 'Consolas', 'Courier New', monospace;
                font-size: 12px;
                padding: 6px;
            }
            QProgressBar {
                background-color: #313244;
                border-radius: 6px;
                text-align: center;
                color: #ffffff;
                font-weight: bold;
                height: 18px;
            }
            QProgressBar::chunk { background-color: #89b4fa; border-radius: 6px; }
        """)

    def _init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(12, 12, 12, 12)

        # ========= 顶部设备连接指示状态条 =========
        top_bar = QHBoxLayout()
        self.lbl_device_status = QLabel("🔍 正在检测游戏环境...")
        self.lbl_device_status.setStyleSheet("color: #f9e2af; font-weight: bold; font-size: 14px;")
        btn_refresh_dev = QPushButton("🔄 刷新连接")
        btn_refresh_dev.clicked.connect(self._check_device_status)
        top_bar.addWidget(self.lbl_device_status)
        top_bar.addStretch()
        top_bar.addWidget(btn_refresh_dev)
        main_layout.addLayout(top_bar)

        # ========= 中间多标签页 =========
        self.tabs = QTabWidget()
        self._init_live_screen_tab()
        self._init_strategy_tab()
        self._init_device_tab()
        self._init_advanced_tab()
        main_layout.addWidget(self.tabs, 5)

        # ========= 底部状态与控制台 =========
        bottom_box = QGroupBox("📊 实时运行状态与控制")
        bottom_layout = QVBoxLayout(bottom_box)
        bottom_layout.setSpacing(8)

        # 状态概览与进度
        stat_bar = QHBoxLayout()
        self.lbl_current_state = QLabel("当前状态: 准备就绪")
        self.lbl_current_state.setStyleSheet("font-size: 13px; font-weight: bold; color: #89b4fa;")
        self.lbl_current_target = QLabel("🎯 锁定目标: 无")
        self.lbl_current_target.setStyleSheet("color: #fab387; font-weight: bold;")
        stat_bar.addWidget(self.lbl_current_state)
        stat_bar.addStretch()
        stat_bar.addWidget(self.lbl_current_target)
        bottom_layout.addLayout(stat_bar)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, self.config.total_rounds)
        self.progress_bar.setValue(0)
        bottom_layout.addWidget(self.progress_bar)

        # 按钮栏
        action_bar = QHBoxLayout()
        self.btn_start = QPushButton("▶ 启动百鬼夜行 (F9)", objectName="btn_start")
        self.btn_start.clicked.connect(self._on_start)
        self.btn_stop = QPushButton("⏹ 停止运行 (F10)", objectName="btn_stop")
        self.btn_stop.setEnabled(False)
        self.btn_stop.clicked.connect(self._on_stop)
        self.btn_sync_now = QPushButton("🔄 在线同步最新式神", objectName="btn_sync")
        self.btn_sync_now.clicked.connect(self._on_sync_online)

        action_bar.addWidget(self.btn_start, 2)
        action_bar.addWidget(self.btn_stop, 2)
        action_bar.addWidget(self.btn_sync_now, 1)
        bottom_layout.addLayout(action_bar)

        # 运行日志窗口
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumHeight(110)
        bottom_layout.addWidget(self.log_text)

        main_layout.addWidget(bottom_box, 2)

    def _init_live_screen_tab(self):
        """Tab 1: 📺 实时画面与AI透视 (HUD)"""
        tab = QWidget()
        layout = QHBoxLayout(tab)
        layout.setSpacing(12)
        layout.setContentsMargins(10, 10, 10, 10)

        # 左侧：16:9 画布容器
        left_box = QGroupBox("📺 游戏实时投屏与 AI 视觉 HUD")
        left_layout = QVBoxLayout(left_box)
        left_layout.setContentsMargins(8, 14, 8, 8)

        self.lbl_screen_canvas = QLabel("📺 正在初始化画面...\n(点击右侧“开启待机投屏”或点击下方“启动”查看)")
        self.lbl_screen_canvas.setAlignment(Qt.AlignCenter)
        self.lbl_screen_canvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.lbl_screen_canvas.setStyleSheet("""
            background-color: #11111b;
            border: 1px solid #313244;
            border-radius: 8px;
            color: #6c7086;
            font-size: 14px;
            font-weight: bold;
        """)
        left_layout.addWidget(self.lbl_screen_canvas)
        layout.addWidget(left_box, 4)

        # 右侧：控制面板与 HUD 开关
        right_panel = QVBoxLayout()
        right_panel.setSpacing(10)

        # 1. 实时态势卡片
        hud_box = QGroupBox("🎯 实时态势监控")
        hud_layout = QFormLayout(hud_box)
        hud_layout.setVerticalSpacing(8)
        hud_layout.setHorizontalSpacing(12)
        hud_layout.setContentsMargins(12, 16, 12, 12)

        self.lbl_hud_fps = QLabel("实时帧率: 0.0 FPS")
        self.lbl_hud_fps.setStyleSheet("color: #a6e3a1; font-weight: bold;")
        self.lbl_hud_target_count = QLabel("视野式神: 0 位")
        self.lbl_hud_target_count.setStyleSheet("color: #89b4fa; font-weight: bold;")
        self.lbl_hud_lock = QLabel("锁定目标: 无")
        self.lbl_hud_lock.setStyleSheet("color: #fab387; font-weight: bold;")

        hud_layout.addRow(self.lbl_hud_fps)
        hud_layout.addRow(self.lbl_hud_target_count)
        hud_layout.addRow(self.lbl_hud_lock)
        right_panel.addWidget(hud_box)

        # 2. HUD 透视显示开关
        switch_box = QGroupBox("🎛️ AI 透视 HUD 开关")
        switch_layout = QVBoxLayout(switch_box)
        switch_layout.setSpacing(8)
        switch_layout.setContentsMargins(12, 16, 12, 12)

        self.chk_enable_stream = QCheckBox("开启实时投屏渲染")
        self.chk_enable_stream.setChecked(True)
        self.chk_show_boxes = QCheckBox("显示式神识别包围框")
        self.chk_show_boxes.setChecked(True)
        self.chk_show_labels = QCheckBox("显示式神名称与置信度")
        self.chk_show_labels.setChecked(True)
        self.chk_show_trajectory = QCheckBox("显示运动轨迹与速度向量")
        self.chk_show_trajectory.setChecked(True)
        self.chk_show_aim = QCheckBox("显示提前量打击十字准星")
        self.chk_show_aim.setChecked(True)

        switch_layout.addWidget(self.chk_enable_stream)
        switch_layout.addWidget(self.chk_show_boxes)
        switch_layout.addWidget(self.chk_show_labels)
        switch_layout.addWidget(self.chk_show_trajectory)
        switch_layout.addWidget(self.chk_show_aim)
        right_panel.addWidget(switch_box)

        # 3. 待机抓屏预览按钮
        preview_box = QGroupBox("📸 待机画面测试")
        preview_layout = QVBoxLayout(preview_box)
        preview_layout.setContentsMargins(12, 16, 12, 12)

        self.btn_toggle_preview = QPushButton("📷 开启待机画面投屏", objectName="btn_preview")
        self.btn_toggle_preview.clicked.connect(self._toggle_standby_preview)
        preview_layout.addWidget(self.btn_toggle_preview)
        right_panel.addWidget(preview_box)

        right_panel.addStretch()
        layout.addLayout(right_panel, 1)

        self.tabs.addTab(tab, "📺 实时画面与AI透视")

    def _init_strategy_tab(self):
        tab = QWidget()
        layout = QHBoxLayout(tab)
        layout.setSpacing(14)
        layout.setContentsMargins(14, 14, 14, 14)

        # 左侧基础参数
        left_box = QGroupBox("🎯 核心参数")
        left_layout = QFormLayout(left_box)
        left_layout.setVerticalSpacing(12)
        left_layout.setHorizontalSpacing(16)
        left_layout.setContentsMargins(14, 18, 14, 14)

        self.spin_rounds = QSpinBox()
        self.spin_rounds.setRange(1, 9999)
        self.spin_rounds.setValue(self.config.total_rounds)
        left_layout.addRow("百鬼夜行轮数:", self.spin_rounds)

        self.combo_beans = QComboBox()
        self.combo_beans.addItems(["10 豆 (全力推荐)", "5 豆 (摸鱼模式)"])
        self.combo_beans.setCurrentIndex(0 if self.config.bean_count == 10 else 1)
        left_layout.addRow("每次投豆数量:", self.combo_beans)

        self.chk_auto_bean = QCheckBox("自适应智能调豆 (遇到稀有时切10豆)")
        self.chk_auto_bean.setChecked(self.config.auto_bean)
        left_layout.addRow(self.chk_auto_bean)

        self.combo_onmyoji = QComboBox()
        for om in OnmyojiType:
            self.combo_onmyoji.addItem(om.value)
        self.combo_onmyoji.setCurrentText(self.config.onmyoji)
        left_layout.addRow("出战阴阳师:", self.combo_onmyoji)

        self.chk_invite = QCheckBox("自动邀请好友协助")
        self.chk_invite.setChecked(self.config.invite_friend)
        self.combo_invite_mode = QComboBox()
        self.combo_invite_mode.addItems(["同服好友", "跨服好友", "阴阳寮好友"])
        self.combo_invite_mode.setCurrentText(self.config.invite_mode)
        left_layout.addRow(self.chk_invite, self.combo_invite_mode)

        layout.addWidget(left_box, 1)

        # 右侧优先式神与权重
        right_box = QGroupBox("🌟 优先式神与稀有度权重")
        right_layout = QVBoxLayout(right_box)
        right_layout.setSpacing(12)
        right_layout.setContentsMargins(14, 18, 14, 14)

        top_priority_bar = QHBoxLayout()
        self.lbl_priority_summary = QLabel(f"已选 {len(self.config.priorities)} 位优先目标式神")
        self.lbl_priority_summary.setStyleSheet("color: #a6adc8; font-weight: bold;")
        btn_open_priority = QPushButton("⚙️ 打开优先式神选择器")
        btn_open_priority.clicked.connect(self._open_priority_dialog)
        top_priority_bar.addWidget(self.lbl_priority_summary)
        top_priority_bar.addStretch()
        top_priority_bar.addWidget(btn_open_priority)
        right_layout.addLayout(top_priority_bar)

        # 稀有度权重表单
        w_form = QFormLayout()
        w_form.setVerticalSpacing(8)
        w_form.setHorizontalSpacing(16)
        self.spin_sp_w = QDoubleSpinBox(); self.spin_sp_w.setRange(0, 2); self.spin_sp_w.setValue(self.config.sp_weight); self.spin_sp_w.setSingleStep(0.1)
        self.spin_ssr_w = QDoubleSpinBox(); self.spin_ssr_w.setRange(0, 2); self.spin_ssr_w.setValue(self.config.ssr_weight); self.spin_ssr_w.setSingleStep(0.1)
        self.spin_sr_w = QDoubleSpinBox(); self.spin_sr_w.setRange(0, 2); self.spin_sr_w.setValue(self.config.sr_weight); self.spin_sr_w.setSingleStep(0.1)
        self.spin_r_w = QDoubleSpinBox(); self.spin_r_w.setRange(0, 2); self.spin_r_w.setValue(self.config.r_weight); self.spin_r_w.setSingleStep(0.1)
        self.spin_n_w = QDoubleSpinBox(); self.spin_n_w.setRange(0, 2); self.spin_n_w.setValue(self.config.n_weight); self.spin_n_w.setSingleStep(0.1)

        w_form.addRow("SP 权重:", self.spin_sp_w)
        w_form.addRow("SSR 权重:", self.spin_ssr_w)
        w_form.addRow("SR 权重:", self.spin_sr_w)
        w_form.addRow("R 权重:", self.spin_r_w)
        w_form.addRow("N 权重:", self.spin_n_w)
        right_layout.addLayout(w_form)

        layout.addWidget(right_box, 1)
        self.tabs.addTab(tab, "🎯 百鬼夜行策略")

    def _init_device_tab(self):
        tab = QWidget()
        main_tab_layout = QVBoxLayout(tab)
        main_tab_layout.setSpacing(12)
        main_tab_layout.setContentsMargins(14, 14, 14, 14)

        # 1. 模式与基本设备
        base_box = QGroupBox("📱 连接模式与窗口")
        base_layout = QFormLayout(base_box)
        base_layout.setVerticalSpacing(10)
        base_layout.setHorizontalSpacing(16)
        base_layout.setContentsMargins(14, 18, 14, 14)

        self.combo_conn_mode = QComboBox()
        for m in ConnectionMode:
            self.combo_conn_mode.addItem(m.value)
        self.combo_conn_mode.setCurrentText(self.config.connection_mode)
        base_layout.addRow("连接模式:", self.combo_conn_mode)

        self.edit_window_title = QLineEdit()
        self.edit_window_title.setText(self.config.window_title)
        base_layout.addRow("PC 游戏窗口标题:", self.edit_window_title)

        self.combo_courtyard = QComboBox()
        for ct in CourtyardType:
            self.combo_courtyard.addItem(ct.value)
        self.combo_courtyard.setCurrentText(self.config.courtyard)
        base_layout.addRow("庭院皮肤选择:", self.combo_courtyard)

        main_tab_layout.addWidget(base_box)

        # 2. 模拟器 ADB 端口专属配置区
        adb_box = QGroupBox("🔌 安卓模拟器 ADB 端口设置")
        adb_layout = QFormLayout(adb_box)
        adb_layout.setVerticalSpacing(10)
        adb_layout.setHorizontalSpacing(16)
        adb_layout.setContentsMargins(14, 18, 14, 14)

        self.combo_preset = QComboBox()
        self.combo_preset.addItems([
            "MuMu 12 (端口: 7555)",
            "雷电模拟器 (端口: 5555)",
            "夜神模拟器 (端口: 62001)",
            "逍遥模拟器 (端口: 21503)",
            "MuMu 6 / X (端口: 16384)",
            "自定义主机与端口"
        ])
        self.combo_preset.currentIndexChanged.connect(self._on_preset_changed)
        adb_layout.addRow("常用模拟器预设:", self.combo_preset)

        self.edit_adb_host = QLineEdit()
        self.edit_adb_host.setText(self.config.adb_host)
        self.edit_adb_host.setPlaceholderText("127.0.0.1")
        self.edit_adb_host.textChanged.connect(self._update_serial_from_inputs)
        adb_layout.addRow("ADB 主机 IP:", self.edit_adb_host)

        self.spin_adb_port = QSpinBox()
        self.spin_adb_port.setRange(1, 65535)
        self.spin_adb_port.setValue(self.config.adb_port)
        self.spin_adb_port.valueChanged.connect(self._update_serial_from_inputs)
        adb_layout.addRow("ADB 端口 (Port):", self.spin_adb_port)

        # 最终 Serial 字符串与测试按钮
        serial_test_layout = QHBoxLayout()
        serial_test_layout.setSpacing(10)
        self.edit_serial = QLineEdit()
        self.edit_serial.setText(self.config.serial)
        btn_test_adb = QPushButton("🔌 立即测试连接", objectName="btn_test")
        btn_test_adb.clicked.connect(self._test_adb_connection)

        serial_test_layout.addWidget(self.edit_serial, 3)
        serial_test_layout.addWidget(btn_test_adb, 2)
        adb_layout.addRow("连接目标 (Serial):", serial_test_layout)

        main_tab_layout.addWidget(adb_box)

        # 3. 截图与控制方式
        driver_box = QGroupBox("⚙️ 截图与点击控制协议")
        driver_layout = QFormLayout(driver_box)
        driver_layout.setVerticalSpacing(10)
        driver_layout.setHorizontalSpacing(16)
        driver_layout.setContentsMargins(14, 18, 14, 14)

        self.combo_screenshot = QComboBox()
        for sm in ScreenshotMethod:
            self.combo_screenshot.addItem(sm.value)
        self.combo_screenshot.setCurrentText(self.config.screenshot_method)
        driver_layout.addRow("截图方式:", self.combo_screenshot)

        self.combo_control = QComboBox()
        for cm in ControlMethod:
            self.combo_control.addItem(cm.value)
        self.combo_control.setCurrentText(self.config.control_method)
        driver_layout.addRow("控制方式:", self.combo_control)

        main_tab_layout.addWidget(driver_box)
        main_tab_layout.addStretch()

        self.tabs.addTab(tab, "📱 设备与连接设置")

    def _init_advanced_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(14)
        layout.setContentsMargins(14, 14, 14, 14)

        box = QGroupBox("🤖 AI 模型与识别参数微调")
        form = QFormLayout(box)
        form.setVerticalSpacing(12)
        form.setHorizontalSpacing(16)
        form.setContentsMargins(14, 18, 14, 14)

        self.chk_sync_patches = QCheckBox("启动应用时自动增量同步网易官方最新式神")
        self.chk_sync_patches.setChecked(self.config.auto_sync_patches)
        form.addRow(self.chk_sync_patches)

        self.spin_conf = QDoubleSpinBox()
        self.spin_conf.setRange(0.2, 1.0)
        self.spin_conf.setSingleStep(0.05)
        self.spin_conf.setValue(self.config.conf_threshold)
        form.addRow("YOLO 置信度阈值 (Conf):", self.spin_conf)

        self.spin_iou = QDoubleSpinBox()
        self.spin_iou.setRange(0.2, 1.0)
        self.spin_iou.setSingleStep(0.05)
        self.spin_iou.setValue(self.config.iou_threshold)
        form.addRow("NMS 重叠度阈值 (IOU):", self.spin_iou)

        self.spin_interval = QSpinBox()
        self.spin_interval.setRange(100, 1000)
        self.spin_interval.setSingleStep(50)
        self.spin_interval.setValue(self.config.shot_interval_ms)
        form.addRow("投豆间隔微调 (ms):", self.spin_interval)

        layout.addWidget(box)
        layout.addStretch()

        self.tabs.addTab(tab, "🤖 AI与高级调试")

    def _setup_hotkeys(self):
        self.shortcut_start = QShortcut(QKeySequence("F9"), self)
        self.shortcut_start.activated.connect(self._on_start)
        self.shortcut_stop = QShortcut(QKeySequence("F10"), self)
        self.shortcut_stop.activated.connect(self._on_stop)

    def _setup_log_listener(self):
        emitter.log_signal.connect(self._append_log)

    def _append_log(self, time_str: str, level: str, message: str):
        color_map = {"INFO": "#cdd6f4", "WARNING": "#f9e2af", "ERROR": "#f38ba8", "CRITICAL": "#f38ba8"}
        color = color_map.get(level, "#cdd6f4")
        html_msg = f'<span style="color: #6c7086;">[{time_str}]</span> <span style="color: {color};">[{level}] {message}</span>'
        self.log_text.append(html_msg)
        self.log_text.moveCursor(QTextCursor.End)

    def _check_device_status(self):
        mode = self.combo_conn_mode.currentText()
        if "PC" in mode:
            win = Win32Window(self.edit_window_title.text())
            if win.is_valid():
                rect = win.get_client_rect()
                self.lbl_device_status.setText(f"🟢 已连接 PC 客户端 [HWND: {win.hwnd}] ({rect[2]}x{rect[3]})")
                self.lbl_device_status.setStyleSheet("color: #a6e3a1; font-weight: bold;")
            else:
                self.lbl_device_status.setText("🔴 未找到 PC 客户端窗口 (请确认游戏已启动)")
                self.lbl_device_status.setStyleSheet("color: #f38ba8; font-weight: bold;")
        else:
            self.lbl_device_status.setText(f"📱 模拟器模式 [Serial: {self.edit_serial.text()}]")
            self.lbl_device_status.setStyleSheet("color: #89b4fa; font-weight: bold;")

    def _on_preset_changed(self, index: int):
        presets = [
            ("127.0.0.1", 7555),   # MuMu 12
            ("127.0.0.1", 5555),   # 雷电
            ("127.0.0.1", 62001),  # 夜神
            ("127.0.0.1", 21503),  # 逍遥
            ("127.0.0.1", 16384),  # MuMu 6
        ]
        if index < len(presets):
            host, port = presets[index]
            self.edit_adb_host.setText(host)
            self.spin_adb_port.setValue(port)
            self._update_serial_from_inputs()

    def _update_serial_from_inputs(self):
        host = self.edit_adb_host.text().strip() or "127.0.0.1"
        port = self.spin_adb_port.value()
        self.edit_serial.setText(f"{host}:{port}")

    def _test_adb_connection(self):
        serial = self.edit_serial.text().strip()
        logger.info(f"[Main] 正在测试连接 ADB 设备: {serial}...")
        success, msg = DeviceDriver.test_adb_connection(serial)
        if success:
            QMessageBox.information(self, "ADB 连接测试", msg)
        else:
            QMessageBox.warning(self, "ADB 连接测试", msg)

    def _toggle_standby_preview(self):
        """开启/关闭待机抓屏预览"""
        if self._is_previewing:
            self.preview_timer.stop()
            self._is_previewing = False
            self.btn_toggle_preview.setText("📷 开启待机画面投屏")
            self.lbl_screen_canvas.setText("📺 待机投屏已停止")
            logger.info("[Preview] 待机画面投屏已关闭")
        else:
            self._save_ui_to_config()
            self.preview_driver = DeviceDriver(
                mode=self.config.connection_mode,
                serial=self.config.serial,
                screenshot_method=self.config.screenshot_method,
                control_method=self.config.control_method,
                window_title=self.config.window_title
            )
            if not self.preview_driver.is_connected():
                QMessageBox.warning(self, "投屏提示", "未找到游戏窗口或模拟器连接失败，请先检查连接设置。")
                return

            self._is_previewing = True
            self.btn_toggle_preview.setText("⏹ 停止待机投屏")
            self.preview_timer.start(60)  # ~15 FPS
            logger.info("[Preview] 待机画面投屏已启动")

    def _on_preview_tick(self):
        if not self._is_previewing or not self.preview_driver:
            return
        img = self.preview_driver.screenshot()
        if img is not None:
            self._render_frame_to_canvas(img, targets_info=[], aim_point=None, focus_name=None)

    def _render_frame_to_canvas(self, img: np.ndarray, targets_info: list, aim_point, focus_name):
        if not self.chk_enable_stream.isChecked() or img is None:
            return

        # 1. 计算 FPS
        now = time.time()
        dt = now - self._last_frame_time
        self._last_frame_time = now
        if dt > 0:
            current_fps = 1.0 / dt
            self._fps = 0.85 * self._fps + 0.15 * current_fps if self._fps > 0 else current_fps

        self.lbl_hud_fps.setText(f"实时帧率: {self._fps:.1f} FPS")
        self.lbl_hud_target_count.setText(f"视野式神: {len(targets_info)} 位")
        if focus_name:
            self.lbl_hud_lock.setText(f"🎯 锁定: {focus_name}")
        elif len(targets_info) > 0:
            self.lbl_hud_lock.setText(f"锁定目标: 分析中")
        else:
            self.lbl_hud_lock.setText("锁定目标: 无")

        # 2. 准备 HUD 开关选项
        options = {
            "show_box": self.chk_show_boxes.isChecked(),
            "show_label": self.chk_show_labels.isChecked(),
            "show_trajectory": self.chk_show_trajectory.isChecked(),
            "show_aim": self.chk_show_aim.isChecked()
        }

        # 3. 标注渲染
        annotated_img = self.annotator.annotate(img, targets_info, aim_point, focus_name, options)

        # 4. 转为 QPixmap 绘制
        h, w, ch = annotated_img.shape
        bytes_per_line = ch * w
        rgb_img = cv2.cvtColor(annotated_img, cv2.COLOR_BGR2RGB)
        qimg = QImage(rgb_img.data, w, h, bytes_per_line, QImage.Format_RGB888)
        pixmap = QPixmap.fromImage(qimg)

        canvas_size = self.lbl_screen_canvas.size()
        scaled_pixmap = pixmap.scaled(canvas_size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.lbl_screen_canvas.setPixmap(scaled_pixmap)

    def _open_priority_dialog(self):
        dialog = PriorityDialog(self.config.priorities, self)
        if dialog.exec():
            self.config.priorities = dialog.get_selected()
            self.config_manager.save()
            self.lbl_priority_summary.setText(f"已选 {len(self.config.priorities)} 位优先目标式神")
            logger.info(f"优先式神清单已更新: {self.config.priorities[:5]} 等共 {len(self.config.priorities)} 位")

    def _on_sync_online(self):
        self.btn_sync_now.setEnabled(False)
        self.btn_sync_now.setText("正在拉取官方数据...")
        try:
            sync_online_patches()
            QMessageBox.information(self, "同步成功", "已成功从网易阴阳师官方拉取最新式神数据并生成补丁！")
        except Exception as e:
            QMessageBox.warning(self, "同步提示", f"同步完成或提示: {e}")
        finally:
            self.btn_sync_now.setEnabled(True)
            self.btn_sync_now.setText("🔄 在线同步最新式神")

    def _save_ui_to_config(self):
        self.config.total_rounds = self.spin_rounds.value()
        self.config.bean_count = 10 if self.combo_beans.currentIndex() == 0 else 5
        self.config.auto_bean = self.chk_auto_bean.isChecked()
        self.config.onmyoji = self.combo_onmyoji.currentText()
        self.config.invite_friend = self.chk_invite.isChecked()
        self.config.invite_mode = self.combo_invite_mode.currentText()
        
        self.config.sp_weight = self.spin_sp_w.value()
        self.config.ssr_weight = self.spin_ssr_w.value()
        self.config.sr_weight = self.spin_sr_w.value()
        self.config.r_weight = self.spin_r_w.value()
        self.config.n_weight = self.spin_n_w.value()

        self.config.connection_mode = self.combo_conn_mode.currentText()
        self.config.adb_host = self.edit_adb_host.text().strip() or "127.0.0.1"
        self.config.adb_port = self.spin_adb_port.value()
        self.config.serial = self.edit_serial.text().strip()
        self.config.screenshot_method = self.combo_screenshot.currentText()
        self.config.control_method = self.combo_control.currentText()
        self.config.courtyard = self.combo_courtyard.currentText()
        self.config.window_title = self.edit_window_title.text()

        self.config.auto_sync_patches = self.chk_sync_patches.isChecked()
        self.config.conf_threshold = self.spin_conf.value()
        self.config.iou_threshold = self.spin_iou.value()
        self.config.shot_interval_ms = self.spin_interval.value()

        self.config_manager.save()

    def _on_start(self):
        if self.worker and self.worker.isRunning():
            return

        if self._is_previewing:
            self._toggle_standby_preview()

        self._save_ui_to_config()

        self.progress_bar.setRange(0, self.config.total_rounds)
        self.progress_bar.setValue(0)

        self.worker = HyakkiWorker(self.config)
        self.worker.status_signal.connect(lambda s: self.lbl_current_state.setText(f"当前状态: {s}"))
        self.worker.round_signal.connect(lambda cur, tot: self.progress_bar.setValue(cur - 1))
        self.worker.target_signal.connect(lambda name, x, y: self.lbl_current_target.setText(f"🎯 锁定目标: [{name}] @ ({x}, {y})"))
        self.worker.frame_signal.connect(self._render_frame_to_canvas)
        self.worker.finished_signal.connect(self._on_worker_finished)

        self.btn_start.setEnabled(False)
        self.btn_stop.setEnabled(True)
        self.worker.start()

    def _on_stop(self):
        if self.worker and self.worker.isRunning():
            self.worker.stop()
            self.btn_stop.setEnabled(False)

    def _on_worker_finished(self, success: bool, msg: str):
        self.btn_start.setEnabled(True)
        self.btn_stop.setEnabled(False)
        self.lbl_current_state.setText("当前状态: 运行结束")
        self.lbl_current_target.setText("🎯 锁定目标: 无")
        if success:
            QMessageBox.information(self, "百鬼夜行结束", msg)
        else:
            QMessageBox.warning(self, "提示", msg)
