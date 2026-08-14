# gui/priority_dialog.py - 优先式神选择与排序对话框
from typing import List
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QListWidget, QListWidgetItem, QPushButton, QCheckBox, QGroupBox
)
from PySide6.QtCore import Qt
from oashya.labels import sp, ssr, sr
from oashya.patch_matcher import patch_matcher

class PriorityDialog(QDialog):
    def __init__(self, current_priorities: List[str], parent=None):
        super().__init__(parent)
        self.setWindowTitle("🎯 优先式神设置 (支持搜索与勾选)")
        self.resize(550, 600)
        self.setStyleSheet("""
            QDialog { background-color: #1e1e2e; color: #cdd6f4; font-family: 'Segoe UI', 'Microsoft YaHei'; }
            QLabel { color: #cdd6f4; font-size: 13px; }
            QLineEdit { background-color: #313244; color: #cdd6f4; border: 1px solid #45475a; border-radius: 6px; padding: 6px; }
            QListWidget { background-color: #181825; border: 1px solid #313244; border-radius: 8px; color: #cdd6f4; }
            QListWidget::item { padding: 6px; border-radius: 4px; }
            QListWidget::item:hover { background-color: #313244; }
            QListWidget::item:selected { background-color: #45475a; color: #89b4fa; }
            QPushButton { background-color: #89b4fa; color: #11111b; font-weight: bold; border-radius: 6px; padding: 8px 16px; }
            QPushButton:hover { background-color: #b4befe; }
            QPushButton#secondary { background-color: #313244; color: #cdd6f4; }
            QPushButton#secondary:hover { background-color: #45475a; }
        """)

        self.selected_priorities: List[str] = list(current_priorities)
        self.all_shikigami = self._collect_all_shikigami()
        self._init_ui()

    def _collect_all_shikigami(self) -> List[dict]:
        """收集所有 SP、SSR 以及官方补丁式神"""
        items = []
        # 1. 补丁库式神
        manifest = patch_matcher.manifest
        for p in manifest:
            name = p.get('name')
            rarity = p.get('rarity', 'SP')
            if name and not any(x['name'] == name for x in items):
                items.append({'name': name, 'rarity': rarity, 'is_patch': True})

        # 2. 原生 SP / SSR
        for name in sp.values():
            if name and not any(x['name'] == name for x in items):
                items.append({'name': name, 'rarity': 'SP', 'is_patch': False})
        for name in ssr.values():
            if name and not any(x['name'] == name for x in items):
                items.append({'name': name, 'rarity': 'SSR', 'is_patch': False})

        return items

    def _init_ui(self):
        layout = QVBoxLayout(self)

        # 搜索栏
        search_layout = QHBoxLayout()
        search_label = QLabel("🔍 快速搜索:")
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("输入式神名字筛选 (如 铃鹿御前 / 天照 / 紧那罗)")
        self.search_input.textChanged.connect(self._filter_list)
        search_layout.addWidget(search_label)
        search_layout.addWidget(self.search_input)
        layout.addLayout(search_layout)

        # 快捷全选按钮栏
        quick_btn_layout = QHBoxLayout()
        btn_all_sp = QPushButton("全选所有 SP", objectName="secondary")
        btn_all_sp.clicked.connect(lambda: self._select_by_rarity("SP"))
        btn_all_ssr = QPushButton("全选所有 SSR", objectName="secondary")
        btn_all_ssr.clicked.connect(lambda: self._select_by_rarity("SSR"))
        btn_clear = QPushButton("清空选择", objectName="secondary")
        btn_clear.clicked.connect(self._clear_selection)
        quick_btn_layout.addWidget(btn_all_sp)
        quick_btn_layout.addWidget(btn_all_ssr)
        quick_btn_layout.addWidget(btn_clear)
        layout.addLayout(quick_btn_layout)

        # 式神列表
        self.list_widget = QListWidget()
        layout.addWidget(self.list_widget)
        self._populate_list(self.all_shikigami)

        # 底部确定取消按钮
        btn_layout = QHBoxLayout()
        btn_cancel = QPushButton("取消", objectName="secondary")
        btn_cancel.clicked.connect(self.reject)
        btn_ok = QPushButton("保存选择并应用")
        btn_ok.clicked.connect(self._on_save)
        btn_layout.addStretch()
        btn_layout.addWidget(btn_cancel)
        btn_layout.addWidget(btn_ok)
        layout.addLayout(btn_layout)

    def _populate_list(self, shikigamis):
        self.list_widget.clear()
        for shiki in shikigamis:
            name = shiki['name']
            rarity = shiki['rarity']
            tag = "🌟 [最新补丁]" if shiki.get('is_patch') else ""
            item_text = f"[{rarity}]  {name}  {tag}"
            
            item = QListWidgetItem(item_text, self.list_widget)
            item.setData(Qt.UserRole, name)
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            
            if name in self.selected_priorities:
                item.setCheckState(Qt.Checked)
            else:
                item.setCheckState(Qt.Unchecked)

    def _filter_list(self, keyword: str):
        keyword = keyword.strip().lower()
        if not keyword:
            filtered = self.all_shikigami
        else:
            filtered = [s for s in self.all_shikigami if keyword in s['name'].lower() or keyword in s['rarity'].lower()]
        self._populate_list(filtered)

    def _select_by_rarity(self, rarity: str):
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            name = item.data(Qt.UserRole)
            for s in self.all_shikigami:
                if s['name'] == name and s['rarity'] == rarity:
                    item.setCheckState(Qt.Checked)
                    if name not in self.selected_priorities:
                        self.selected_priorities.append(name)

    def _clear_selection(self):
        self.selected_priorities.clear()
        for i in range(self.list_widget.count()):
            self.list_widget.item(i).setCheckState(Qt.Unchecked)

    def _on_save(self):
        # 收集选中的式神
        selected = []
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            if item.checkState() == Qt.Checked:
                selected.append(item.data(Qt.UserRole))
        self.selected_priorities = selected
        self.accept()

    def get_selected(self) -> List[str]:
        return self.selected_priorities
