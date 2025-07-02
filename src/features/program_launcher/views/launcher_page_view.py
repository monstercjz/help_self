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
    """
    程序启动器插件的顶层视图容器。
    负责管理和切换不同的视图模式（如树状、图标等）。
    """
    add_group_requested = Signal()
    # 【核心修复】定义两个不同签名的信号，以匹配不同的事件源
    add_program_requested = Signal() # 用于无参数的全局添加按钮
    add_program_to_group_requested = Signal(str) # 用于带group_id的右键菜单
    
    item_double_clicked = Signal(str)
    edit_item_requested = Signal(str, str)
    delete_item_requested = Signal(str, str)
    search_text_changed = Signal(str)
    change_data_path_requested = Signal()
    items_moved = Signal()
    program_dropped = Signal(str, str, int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.data_cache = {}
        self._init_ui()
        self.tree_view.update_view({})

    def _init_ui(self):
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
        
        self.add_group_btn.clicked.connect(self.add_group_requested)
        # 【核心修复】将 clicked (无参数) 连接到 add_program_requested (无参数)
        self.add_program_btn.clicked.connect(self.add_program_requested)
        self.settings_btn.clicked.connect(self.change_data_path_requested)
        self.search_bar.textChanged.connect(self.search_text_changed)
        self.view_mode_group.idClicked.connect(self.stacked_widget.setCurrentIndex)
        self.stacked_widget.currentChanged.connect(self.on_view_mode_changed)

        self._connect_view_signals(self.tree_view)
        self._connect_view_signals(self.icon_view)

    def _connect_view_signals(self, view: BaseViewMode):
        """将一个视图模式的信号连接到容器的代理信号上。"""
        view.item_double_clicked.connect(self.item_double_clicked)
        view.edit_item_requested.connect(self.edit_item_requested)
        view.delete_item_requested.connect(self.delete_item_requested)
        view.items_moved.connect(self.items_moved)
        view.program_dropped.connect(self.program_dropped)
        # 【核心修复】连接到新的专用信号
        view.add_program_to_group_requested.connect(self.add_program_to_group_requested)

    def rebuild_ui(self, data: dict):
        self.data_cache = data
        active_view = self.stacked_widget.currentWidget()
        if active_view:
            active_view.update_view(self.data_cache)

    def on_view_mode_changed(self, index: int):
        self.rebuild_ui(self.data_cache)

    def get_current_structure(self) -> dict:
        active_view = self.stacked_widget.currentWidget()
        if hasattr(active_view, 'get_current_structure'):
            return active_view.get_current_structure()
        return self.data_cache

    def filter_items(self, text: str):
        if hasattr(self.tree_view, 'filter_items'): self.tree_view.filter_items(text)