# desktop_center/src/features/program_launcher/views/launcher_page_view.py
import logging
import os
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QPushButton, QHBoxLayout,
                               QLineEdit, QSpacerItem, QSizePolicy, QStackedWidget, QButtonGroup)
from PySide6.QtCore import Signal, QDir
from PySide6.QtGui import QIcon

from .modes.base_view import BaseViewMode
from .modes.tree_view import TreeViewMode
from .modes.icon_view import IconViewMode
from .modes.flow_view import FlowViewMode
from ..widgets.empty_state_widget import EmptyStateWidget
from ..widgets.no_results_widget import NoResultsWidget

class LauncherPageView(QWidget):
    # 【核心修复】恢复被意外删除的信号定义
    add_group_requested = Signal()
    add_program_requested = Signal(str)
    item_double_clicked = Signal(str)
    edit_item_requested = Signal(str, str)
    delete_item_requested = Signal(str, str)
    search_text_changed = Signal(str)
    change_data_path_requested = Signal()
    program_dropped = Signal(str, str, int)
    # 这个信号现在是所有子视图分组排序信号的统一出口
    group_order_changed = Signal(list)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("LauncherPageView")
        self.data_cache = {}
        self._init_ui()
        self._load_stylesheet()
        self.tree_view.update_view({})

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 0, 15, 15)
        layout.setSpacing(10)

        # --- 顶部工具栏 ---
        toolbar_container = QWidget()
        toolbar_container.setObjectName("toolbarContainer")
        toolbar_container.setStyleSheet("#toolbarContainer { background-color: #F8F8F8; border-top: 1px solid #E0E0E0; border-bottom: 1px solid #E0E0E0; }")
        toolbar_container.setContentsMargins(15, 10, 15, 10)
        toolbar_container.setFixedHeight(60)

        toolbar_layout = QHBoxLayout(toolbar_container)
        toolbar_layout.setContentsMargins(0, 0, 0, 0)

        # 1. 搜索框 (最左)
        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("搜索程序...")
        self.clear_action = self.search_bar.addAction(QIcon.fromTheme("edit-clear"), QLineEdit.ActionPosition.TrailingPosition)
        self.clear_action.setVisible(False)
        toolbar_layout.addWidget(self.search_bar)

        # 2. 添加按钮
        self.add_program_btn = QPushButton(QIcon.fromTheme("list-add"), "")
        self.add_program_btn.setObjectName("addProgramBtn")
        self.add_program_btn.setToolTip("添加程序")
        self.add_group_btn = QPushButton("🗂️")
        self.add_group_btn.setObjectName("addGroupBtn")
        self.add_group_btn.setToolTip("新建分组")
        toolbar_layout.addWidget(self.add_program_btn)
        toolbar_layout.addWidget(self.add_group_btn)
        # 4. 设置按钮 (最右)
        self.settings_btn = QPushButton("📂")
        self.settings_btn.setObjectName("settingsBtn")
        self.settings_btn.setToolTip("设置数据文件路径")
        toolbar_layout.addWidget(self.settings_btn)

        # 添加一个弹性空间
        toolbar_layout.addSpacerItem(QSpacerItem(20, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum))

        # 3. 视图模式切换按钮组
        view_mode_widget = QWidget()
        view_mode_widget.setObjectName("viewModeWidget")
        view_mode_layout = QHBoxLayout(view_mode_widget)
        view_mode_layout.setContentsMargins(0,0,0,0)
        view_mode_layout.setSpacing(10)
        
        self.view_mode_group = QButtonGroup(self)
        self.tree_view_btn = QPushButton("●")
        self.tree_view_btn.setToolTip("树状视图")
        self.tree_view_btn.setCheckable(True)
        self.icon_view_btn = QPushButton("●")
        self.icon_view_btn.setToolTip("图标视图")
        self.icon_view_btn.setCheckable(True)
        self.flow_view_btn = QPushButton("●")
        self.flow_view_btn.setToolTip("流式视图")
        self.flow_view_btn.setCheckable(True)

        self.view_mode_group.addButton(self.tree_view_btn, 0)
        self.view_mode_group.addButton(self.icon_view_btn, 1)
        self.view_mode_group.addButton(self.flow_view_btn, 2)
        
        view_mode_layout.addWidget(self.tree_view_btn)
        view_mode_layout.addWidget(self.icon_view_btn)
        view_mode_layout.addWidget(self.flow_view_btn)
        
        # self.tree_view_btn.setChecked(True)  # 注释掉原来的默认设置
        self.icon_view_btn.setChecked(True) # 将图标视图设为默认
        
        toolbar_layout.addWidget(view_mode_widget)

        

        layout.addWidget(toolbar_container)

        # --- 视图堆叠窗口 ---
        self.stacked_widget = QStackedWidget()
        self.tree_view = TreeViewMode()
        self.icon_view = IconViewMode()
        # 【新增】实例化流式视图
        self.flow_view = FlowViewMode()
        self.empty_state_view = EmptyStateWidget()
        self.no_results_view = NoResultsWidget()

        self.stacked_widget.addWidget(self.tree_view)
        self.stacked_widget.addWidget(self.icon_view)
        # 【新增】将流式视图添加到堆叠窗口
        self.stacked_widget.addWidget(self.flow_view)
        self.stacked_widget.addWidget(self.empty_state_view)
        self.stacked_widget.addWidget(self.no_results_view)
        layout.addWidget(self.stacked_widget)
        
        # --- 连接信号 ---
        self.add_group_btn.clicked.connect(self.add_group_requested)
        self.add_program_btn.clicked.connect(lambda: self.add_program_requested.emit(None))
        self.settings_btn.clicked.connect(self.change_data_path_requested)
        self.search_bar.textChanged.connect(self.search_text_changed)
        self.clear_action.triggered.connect(self.search_bar.clear)
        self.search_bar.textChanged.connect(self._update_clear_button_visibility)
        self.view_mode_group.idClicked.connect(self.stacked_widget.setCurrentIndex)
        self.stacked_widget.currentChanged.connect(self.on_view_mode_changed)
        self.empty_state_view.add_group_requested.connect(self.add_group_requested)
        
        # 连接所有视图的信号
        self._connect_view_signals(self.tree_view)
        self._connect_view_signals(self.icon_view)
        # 【新增】连接流式视图的信号
        self._connect_view_signals(self.flow_view)

    def _connect_view_signals(self, view: BaseViewMode):
        view.item_double_clicked.connect(self.item_double_clicked)
        view.edit_item_requested.connect(self.edit_item_requested)
        view.delete_item_requested.connect(self.delete_item_requested)
        view.program_dropped.connect(self.program_dropped)
        view.add_program_to_group_requested.connect(self.add_program_requested)
        view.group_order_changed.connect(self.group_order_changed)

    def rebuild_ui(self, data: dict):
        self.data_cache = data
        
        is_data_empty = not data.get("groups") and not data.get("programs")
        is_searching = bool(self.search_bar.text())

        if is_data_empty and not is_searching:
            self.stacked_widget.setCurrentWidget(self.empty_state_view)
            self.search_bar.setVisible(False)
            self.tree_view_btn.setVisible(False)
            self.icon_view_btn.setVisible(False)
            # 【新增】控制流式视图按钮的可见性
            self.flow_view_btn.setVisible(False)
        elif is_data_empty and is_searching:
            self.stacked_widget.setCurrentWidget(self.no_results_view)
            self.search_bar.setVisible(True)
            self.tree_view_btn.setVisible(False)
            self.icon_view_btn.setVisible(False)
            # 【新增】控制流式视图按钮的可见性
            self.flow_view_btn.setVisible(False)
        else:
            current_id = self.view_mode_group.checkedId()
            # 确保ID在有效范围内
            if current_id < self.stacked_widget.count() - 2: # 减去占位视图
                 self.stacked_widget.setCurrentIndex(current_id)
            self.search_bar.setVisible(True)
            self.tree_view_btn.setVisible(True)
            self.icon_view_btn.setVisible(True)
            # 【新增】控制流式视图按钮的可见性
            self.flow_view_btn.setVisible(True)

        # 即使在显示占位符时，也更新所有后台视图的数据
        self.tree_view.update_view(data)
        self.icon_view.update_view(data)
        # 【新增】更新流式视图的数据
        self.flow_view.update_view(data)

    def on_view_mode_changed(self, index: int):
        pass

    def _update_clear_button_visibility(self, text: str):
        self.clear_action.setVisible(bool(text))

    def _load_stylesheet(self):
        """加载外部QSS样式表。"""
        current_dir = os.path.dirname(os.path.abspath(__file__))
        style_path = os.path.join(current_dir, '..', 'assets', 'style.qss')
        
        if os.path.exists(style_path):
            with open(style_path, 'r', encoding='utf-8') as f:
                style = f.read()
                self.setStyleSheet(style)
                logging.info(f"Stylesheet loaded from {style_path}")
        else:
            logging.warning(f"Stylesheet not found at {style_path}")