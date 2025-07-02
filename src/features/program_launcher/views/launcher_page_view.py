# desktop_center/src/features/program_launcher/views/launcher_page_view.py
import logging
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QPushButton, QHBoxLayout, 
                               QLineEdit, QSpacerItem, QSizePolicy, QStackedWidget, QButtonGroup)
from PySide6.QtCore import Signal
from PySide6.QtGui import QIcon

# 导入新的视图模式
from .modes.base_view import BaseViewMode
from .modes.tree_view import TreeViewMode
from .modes.icon_view import IconViewMode

class LauncherPageView(QWidget):
    """
    程序启动器插件的顶层视图容器。
    负责管理和切换不同的视图模式（如树状、图标等）。
    """
    # 信号代理：将激活的视图模式的信号转发出去，对控制器保持统一接口
    add_group_requested = Signal()
    add_program_requested = Signal()
    item_double_clicked = Signal(str)
    edit_item_requested = Signal(str, str)
    delete_item_requested = Signal(str, str)
    search_text_changed = Signal(str)
    change_data_path_requested = Signal()
    items_moved = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.data_cache = {}
        self._init_ui()
        self.tree_view.update_view({}) # 初始为空

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        # 顶部工具栏
        toolbar_layout = QHBoxLayout()
        self.add_group_btn = QPushButton(QIcon.fromTheme("list-add"), " 新建分组")
        self.add_program_btn = QPushButton(QIcon.fromTheme("document-new"), " 添加程序")
        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("搜索程序...")
        self.settings_btn = QPushButton()
        self.settings_btn.setIcon(QIcon.fromTheme("emblem-system"))
        self.settings_btn.setToolTip("设置数据文件路径")
        
        # 视图切换按钮
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

        # 视图容器
        self.stacked_widget = QStackedWidget()
        self.tree_view = TreeViewMode()
        self.icon_view = IconViewMode()
        self.stacked_widget.addWidget(self.tree_view)
        self.stacked_widget.addWidget(self.icon_view)
        layout.addWidget(self.stacked_widget)
        
        # 连接顶层UI信号
        self.add_group_btn.clicked.connect(self.add_group_requested)
        self.add_program_btn.clicked.connect(self._on_add_program_proxy)
        self.settings_btn.clicked.connect(self.change_data_path_requested)
        self.search_bar.textChanged.connect(self.search_text_changed)
        self.view_mode_group.idClicked.connect(self.stacked_widget.setCurrentIndex)
        self.stacked_widget.currentChanged.connect(self.on_view_mode_changed)

        # 信号代理: 将子视图的信号连接到本容器的信号
        self._connect_view_signals(self.tree_view)
        self._connect_view_signals(self.icon_view)

    def _connect_view_signals(self, view: BaseViewMode):
        """将一个视图模式的信号连接到容器的代理信号上。"""
        view.item_double_clicked.connect(self.item_double_clicked)
        view.edit_item_requested.connect(self.edit_item_requested)
        view.delete_item_requested.connect(self.delete_item_requested)
        view.items_moved.connect(self.items_moved)
        # 特定信号
        if isinstance(view, TreeViewMode):
            view.add_program_to_group_requested.connect(self._on_add_program_proxy)

    def rebuild_ui(self, data: dict):
        """
        接收新数据，并只更新当前可见的视图。
        """
        self.data_cache = data
        active_view = self.stacked_widget.currentWidget()
        if active_view:
            active_view.update_view(self.data_cache)

    def on_view_mode_changed(self, index: int):
        """当视图切换时，确保新视图显示的是最新数据。"""
        self.rebuild_ui(self.data_cache)

    def get_current_structure(self) -> dict:
        """从当前激活的视图获取其结构，主要用于树状视图的拖拽。"""
        active_view = self.stacked_widget.currentWidget()
        if hasattr(active_view, 'get_current_structure'):
            return active_view.get_current_structure()
        return self.data_cache # 如果视图不支持，返回缓存数据

    def filter_items(self, text: str):
        """将过滤请求传递给所有视图。"""
        # 简单起见，可以只过滤当前视图，或都过滤
        if hasattr(self.tree_view, 'filter_items'): self.tree_view.filter_items(text)
        if hasattr(self.icon_view, 'filter_items'): pass # IconView暂未实现过滤

    def _on_add_program_proxy(self, group_id: str = None):
        """
        代理添加程序的请求，区分是全局添加还是指定分组添加。
        控制器不需要知道这个细节。
        """
        # 在这里可以做一些预处理，但目前直接转发信号
        if group_id:
             # 这是个不好的设计，控制器应该接收这个信号
             # 暂时保持简单，让控制器处理
             pass
        self.add_program_requested.emit()