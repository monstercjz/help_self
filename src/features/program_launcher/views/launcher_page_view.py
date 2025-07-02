# desktop_center/src/features/program_launcher/views/launcher_page_view.py
import logging
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QPushButton, QHBoxLayout, 
                               QLineEdit, QSpacerItem, QSizePolicy, QStackedWidget, QButtonGroup)
from PySide6.QtCore import Signal
from PySide6.QtGui import QIcon

from .modes.base_view import BaseViewMode
from .modes.tree_view import TreeViewMode
from .modes.icon_view import IconViewMode

class LauncherPageView(QWidget):
    # ... 信号定义保持不变 ...
    add_group_requested = Signal()
    add_program_requested = Signal(str)
    item_double_clicked = Signal(str)
    edit_item_requested = Signal(str, str)
    delete_item_requested = Signal(str, str)
    search_text_changed = Signal(str)
    change_data_path_requested = Signal()
    items_moved = Signal()
    program_dropped = Signal(str, str, int)
    group_order_changed = Signal(list)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.data_cache = {}
        self._init_ui()
        self.tree_view.update_view({})

    def _init_ui(self):
        # ... UI创建部分保持不变 ...
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        toolbar_layout = QHBoxLayout()
        self.add_group_btn = QPushButton(QIcon.fromTheme("list-add"), " 新建分组")
        self.add_program_btn = QPushButton(QIcon.fromTheme("document-new"), " 添加程序")
        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("搜索程序...")
        self.settings_btn = QPushButton()
        self.settings_btn.setIcon(QIcon.fromTheme("emblem-system"))
        self.settings_btn.setToolTip("设置数据文件路径")
        self.view_mode_group = QButtonGroup(self)
        self.tree_view_btn = QPushButton(QIcon.fromTheme("view-list-tree"), "")
        self.tree_view_btn.setToolTip("树状视图")
        self.tree_view_btn.setCheckable(True)
        self.icon_view_btn = QPushButton(QIcon.fromTheme("view-grid"), "")
        self.icon_view_btn.setToolTip("图标视图")
        self.icon_view_btn.setCheckable(True)
        self.view_mode_group.addButton(self.tree_view_btn, 0)
        self.view_mode_group.addButton(self.icon_view_btn, 1)
        self.tree_view_btn.setChecked(True)
        toolbar_layout.addWidget(self.add_group_btn)
        toolbar_layout.addWidget(self.add_program_btn)
        toolbar_layout.addSpacerItem(QSpacerItem(20, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum))
        toolbar_layout.addWidget(self.search_bar)
        toolbar_layout.addWidget(self.tree_view_btn)
        toolbar_layout.addWidget(self.icon_view_btn)
        toolbar_layout.addWidget(self.settings_btn)
        layout.addLayout(toolbar_layout)
        self.stacked_widget = QStackedWidget()
        self.tree_view = TreeViewMode()
        self.icon_view = IconViewMode()
        self.stacked_widget.addWidget(self.tree_view)
        self.stacked_widget.addWidget(self.icon_view)
        layout.addWidget(self.stacked_widget)
        
        # 连接信号
        self.add_group_btn.clicked.connect(self.add_group_requested)
        self.add_program_btn.clicked.connect(lambda: self.add_program_requested.emit(None))
        self.settings_btn.clicked.connect(self.change_data_path_requested)
        # 【修改】连接到自身的 filter_items 方法
        self.search_bar.textChanged.connect(self.filter_items)
        self.view_mode_group.idClicked.connect(self.stacked_widget.setCurrentIndex)
        self.stacked_widget.currentChanged.connect(self.on_view_mode_changed)
        self._connect_view_signals(self.tree_view)
        self._connect_view_signals(self.icon_view)

    def _connect_view_signals(self, view: BaseViewMode):
        view.item_double_clicked.connect(self.item_double_clicked)
        view.edit_item_requested.connect(self.edit_item_requested)
        view.delete_item_requested.connect(self.delete_item_requested)
        view.items_moved.connect(self.items_moved)
        view.program_dropped.connect(self.program_dropped)
        view.add_program_to_group_requested.connect(self.add_program_requested)
        view.group_order_changed.connect(self.group_order_changed)

    def rebuild_ui(self, data: dict):
        self.data_cache = data
        # 【修改】刷新时，同时更新两个视图的数据，并应用当前搜索
        current_search = self.search_bar.text()
        self.tree_view.update_view(data)
        self.icon_view.update_view(data)
        if current_search:
            self.filter_items(current_search)

    def on_view_mode_changed(self, index: int):
        # 切换视图时，数据已经是新的，只需要应用搜索即可
        self.filter_items(self.search_bar.text())

    def get_current_structure(self) -> dict:
        active_view = self.stacked_widget.currentWidget()
        if hasattr(active_view, 'get_current_structure'):
            return active_view.get_current_structure()
        return self.data_cache

    def filter_items(self, text: str):
        """将过滤请求分发到所有视图模式。"""
        self.tree_view.filter_items(text)
        self.icon_view.filter_items(text)