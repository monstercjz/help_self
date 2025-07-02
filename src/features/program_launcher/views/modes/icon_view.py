# desktop_center/src/features/program_launcher/views/modes/icon_view.py
import logging
from PySide6.QtWidgets import (QMenu, QFileIconProvider, QVBoxLayout, 
                               QLabel, QWidget, QScrollArea)
from PySide6.QtGui import QIcon
from PySide6.QtCore import Qt, QFileInfo

from .base_view import BaseViewMode
from ...widgets.card_widget import CardWidget
from .flow_layout import FlowLayout # 【修改】导入FlowLayout

class IconViewMode(BaseViewMode):
    """
    图标网格视图模式的实现。
    【重构】使用QScrollArea和手动布局来精确控制UI。
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.icon_cache = {}
        self.icon_provider = QFileIconProvider()
        
        # 主布局是一个简单的垂直布局
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # 创建一个滚动区域
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QScrollArea.Shape.NoFrame)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        # 滚动区域的内容是一个QWidget，它是我们所有卡片的容器
        self.content_widget = QWidget()
        scroll_area.setWidget(self.content_widget)

        # 内容容器使用垂直布局，依次放置 "标题" 和 "卡片流"
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        main_layout.addWidget(scroll_area)

    def update_view(self, data: dict):
        # 清空旧内容
        while self.content_layout.count():
            child = self.content_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        groups = data.get("groups", [])
        programs = data.get("programs", {})
        
        programs_by_group = {}
        for prog_id, prog_data in programs.items():
            group_id = prog_data.get('group_id')
            if group_id not in programs_by_group: programs_by_group[group_id] = []
            programs_by_group[group_id].append(prog_data)
        for group_id in programs_by_group:
            programs_by_group[group_id].sort(key=lambda p: p.get("order", 0))

        if not groups:
            self.content_layout.addWidget(QLabel("没有内容，请先添加分组和程序。"))
            return

        for group_data in groups:
            # 1. 创建并添加分组标题
            group_title = QLabel(f"<b>{group_data['name']}</b>")
            group_title.setStyleSheet("padding: 15px 0 8px 5px; font-size: 14px; border-bottom: 1px solid #e0e0e0; margin-bottom: 5px;")
            self.content_layout.addWidget(group_title)

            # 2. 创建一个使用FlowLayout的容器来放卡片
            card_container = QWidget()
            flow_layout = FlowLayout(card_container, h_spacing=10, v_spacing=10)

            programs_in_group = programs_by_group.get(group_data['id'], [])
            if not programs_in_group:
                flow_layout.addWidget(QLabel("(此分组为空)"))
            else:
                for prog_data in programs_in_group:
                    icon = self._get_program_icon(prog_data['path'])
                    card = CardWidget(prog_data, icon)
                    card.doubleClicked.connect(self.item_double_clicked)
                    card.customContextMenuRequested.connect(self._on_context_menu)
                    flow_layout.addWidget(card)
            
            # 3. 将卡片容器添加到主垂直布局中
            self.content_layout.addWidget(card_container)
    
    def _get_program_icon(self, path: str) -> QIcon:
        if not path or path in self.icon_cache: return self.icon_cache.get(path, QIcon.fromTheme("application-x-executable"))
        icon = self.icon_provider.icon(QFileInfo(path))
        if icon.isNull(): icon = QIcon.fromTheme("application-x-executable")
        self.icon_cache[path] = icon
        return icon

    def _on_context_menu(self, program_id, event):
        menu = QMenu(self)
        menu.addAction("启动").triggered.connect(lambda: self.item_double_clicked.emit(program_id))
        menu.addAction("编辑...").triggered.connect(lambda: self.edit_item_requested.emit(program_id, 'program'))
        menu.addAction("删除").triggered.connect(lambda: self.delete_item_requested.emit(program_id, 'program'))
        menu.exec_(event.globalPos())