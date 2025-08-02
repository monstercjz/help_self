# src/features/memo_pad/views/memo_page_view.py
import os
import logging
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QListWidget, QTextEdit,
    QPushButton, QLineEdit, QLabel, QSplitter, QListWidgetItem, QGroupBox, QButtonGroup, QMenu
)
from PySide6.QtCore import Qt, QSize, Signal
from PySide6.QtGui import QIcon, QAction
from src.features.memo_pad.widgets.note_card_widget import NoteCardWidget
from src.features.memo_pad.models.memo_model import Memo

class MemoPageView(QWidget):
    """
    备忘录插件的用户界面视图。
    """
    delete_requested = Signal(int)
    edit_requested = Signal(int)

    def __init__(self):
        super().__init__()
        self.setWindowTitle("备忘录")
        self._init_ui()
        self._load_stylesheet()

    def _init_ui(self):
        """初始化UI组件。"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(15, 0, 15, 15)
        main_layout.setSpacing(10)

        # 顶部工具栏
        toolbar_container = QWidget()
        toolbar_container.setObjectName("toolbarContainer")
        toolbar_container.setStyleSheet("#toolbarContainer { background-color: #F8F8F8; border-top: 1px solid #E0E0E0; border-bottom: 1px solid #E0E0E0; }")
        toolbar_container.setContentsMargins(15, 10, 15, 10)
        toolbar_container.setFixedHeight(60)
        toolbar_layout = QHBoxLayout(toolbar_container)
        toolbar_layout.setContentsMargins(0, 0, 0, 0)
        
        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("搜索笔记...")
        self.clear_action = self.search_bar.addAction(QIcon.fromTheme("edit-clear"), QLineEdit.ActionPosition.TrailingPosition)
        self.clear_action.setVisible(False)
        toolbar_layout.addWidget(self.search_bar)

        self.new_button = QPushButton(QIcon.fromTheme("document-new"), "")
        self.new_button.setObjectName("addProgramBtn")
        self.new_button.setToolTip("新建笔记")
        self.delete_button = QPushButton(QIcon.fromTheme("edit-delete"), "")
        self.delete_button.setObjectName("addGroupBtn")
        self.delete_button.setToolTip("删除笔记")
        
        toolbar_layout.addWidget(self.new_button)
        toolbar_layout.addWidget(self.delete_button)
        toolbar_layout.addStretch()

        # 视图模式切换按钮组
        view_mode_widget = QWidget()
        view_mode_widget.setObjectName("viewModeWidget")
        view_mode_layout = QHBoxLayout(view_mode_widget)
        view_mode_layout.setContentsMargins(0,0,0,0)
        view_mode_layout.setSpacing(10)
        
        self.view_mode_group = QButtonGroup(self)
        self.view_btn1 = QPushButton("●")
        self.view_btn1.setToolTip("列表视图")
        self.view_btn1.setCheckable(True)
        self.view_btn2 = QPushButton("●")
        self.view_btn2.setToolTip("卡片视图 (待实现)")
        self.view_btn2.setCheckable(True)
        self.view_btn3 = QPushButton("●")
        self.view_btn3.setToolTip("其他视图 (待实现)")
        self.view_btn3.setCheckable(True)

        self.view_mode_group.addButton(self.view_btn1, 0)
        self.view_mode_group.addButton(self.view_btn2, 1)
        self.view_mode_group.addButton(self.view_btn3, 2)
        
        view_mode_layout.addWidget(self.view_btn1)
        view_mode_layout.addWidget(self.view_btn2)
        view_mode_layout.addWidget(self.view_btn3)
        self.view_btn2.setChecked(True) # Set split view as default
        toolbar_layout.addWidget(view_mode_widget)

        main_layout.addWidget(toolbar_container)

        # 主内容区
        content_group_box = QGroupBox()
        content_group_box.setObjectName("mainContentArea")
        content_layout = QVBoxLayout(content_group_box)
        content_layout.setContentsMargins(8, 3, 8, 8)

        self.splitter = QSplitter(Qt.Horizontal)
        content_layout.addWidget(self.splitter)

        left_group_box = QGroupBox()
        left_group_box.setObjectName("innerContainer")
        left_layout = QVBoxLayout(left_group_box)
        self.memo_list_widget = QListWidget()
        self.memo_list_widget.setSpacing(5)
        self.memo_list_widget.setContextMenuPolicy(Qt.CustomContextMenu)
        self.memo_list_widget.customContextMenuRequested.connect(self._show_context_menu)
        self.memo_list_widget.itemDoubleClicked.connect(self._on_item_double_clicked)
        left_layout.addWidget(self.memo_list_widget)
        self.splitter.addWidget(left_group_box)

        right_group_box = QGroupBox()
        right_group_box.setObjectName("innerContainer")
        right_layout = QVBoxLayout(right_group_box)
        self.title_input = QLineEdit()
        self.title_input.setPlaceholderText("标题")
        self.content_text_edit = QTextEdit()
        self.status_label = QLabel("就绪")
        self.status_label.setObjectName("statusLabel")
        
        right_layout.addWidget(self.title_input)
        right_layout.addWidget(self.content_text_edit)
        right_layout.addWidget(self.status_label)
        self.splitter.addWidget(right_group_box)
        
        self.splitter.setSizes([350, 550])
        main_layout.addWidget(content_group_box, 1)

        self.view_mode_group.idClicked.connect(self.set_view_mode)

    def _show_context_menu(self, point):
        """在指定位置显示右键上下文菜单。"""
        item = self.memo_list_widget.itemAt(point)
        if not item:
            return

        memo_id = item.data(Qt.UserRole)
        
        context_menu = QMenu(self)
        delete_action = QAction(QIcon.fromTheme("edit-delete"), "删除笔记", self)
        delete_action.triggered.connect(lambda: self.delete_requested.emit(memo_id))
        
        context_menu.addAction(delete_action)
        context_menu.exec(self.memo_list_widget.mapToGlobal(point))

    def _on_item_double_clicked(self, item: QListWidgetItem):
        """当一个项目被双击时，发出编辑请求信号。"""
        memo_id = item.data(Qt.UserRole)
        self.edit_requested.emit(memo_id)

    def set_view_mode(self, mode_id: int):
        """根据选择的模式ID调整分割器布局。"""
        if mode_id == 0: # 只显示列表
            self.splitter.setSizes([1, 0])
        elif mode_id == 1: # 默认视图
            self.splitter.setSizes([250, 550])
        elif mode_id == 2: # 只显示编辑器
            self.splitter.setSizes([0, 1])

    def _load_stylesheet(self):
        """加载外部QSS样式表。"""
        # 从本插件的assets目录加载样式表
        style_path = os.path.join(os.path.dirname(__file__), '..', 'assets', 'style.qss')
        if os.path.exists(style_path):
            with open(style_path, 'r', encoding='utf-8') as f:
                style = f.read()
                self.setStyleSheet(style)
                logging.info(f"Stylesheet loaded for MemoPad from {style_path}")
        else:
            logging.warning(f"Stylesheet not found at {style_path}")

    def add_memo_card(self, memo: Memo):
        card = NoteCardWidget(memo)
        item = QListWidgetItem(self.memo_list_widget)
        item.setSizeHint(card.sizeHint())
        item.setData(Qt.UserRole, memo.id)
        self.memo_list_widget.addItem(item)
        self.memo_list_widget.setItemWidget(item, card)

    def update_memo_card(self, memo: Memo):
        for i in range(self.memo_list_widget.count()):
            item = self.memo_list_widget.item(i)
            if item.data(Qt.UserRole) == memo.id:
                card = self.memo_list_widget.itemWidget(item)
                if card:
                    card.update_content(memo)
                break
    
    def remove_memo_card(self, memo_id: int):
        for i in range(self.memo_list_widget.count()):
            item = self.memo_list_widget.item(i)
            if item.data(Qt.UserRole) == memo_id:
                self.memo_list_widget.takeItem(i)
                break

    def clear_selection(self):
        self.memo_list_widget.clearSelection()

    def select_item_by_id(self, memo_id: int):
        for i in range(self.memo_list_widget.count()):
            item = self.memo_list_widget.item(i)
            if item.data(Qt.UserRole) == memo_id:
                item.setSelected(True)
                self.memo_list_widget.scrollToItem(item)
                break
