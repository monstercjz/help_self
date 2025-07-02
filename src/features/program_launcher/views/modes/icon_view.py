# desktop_center/src/features/program_launcher/views/modes/icon_view.py
import logging
from PySide6.QtWidgets import (QListWidget, QListWidgetItem, QMenu,
                               QFileIconProvider, QVBoxLayout, QLabel, QWidget)
from PySide6.QtGui import QIcon
from PySide6.QtCore import Qt, QFileInfo, QSize

from .base_view import BaseViewMode

class IconViewMode(BaseViewMode):
    """
    图标网格视图模式的实现。
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.icon_cache = {}
        self.icon_provider = QFileIconProvider()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.list_widget = QListWidget()
        self.list_widget.setViewMode(QListWidget.ViewMode.IconMode)
        self.list_widget.setFlow(QListWidget.Flow.LeftToRight)
        self.list_widget.setWrapping(True)
        self.list_widget.setResizeMode(QListWidget.ResizeMode.Adjust)
        self.list_widget.setMovement(QListWidget.Movement.Static) # 暂不支持拖拽
        self.list_widget.setSpacing(10)
        self.list_widget.setIconSize(QSize(48, 48))
        self.list_widget.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        
        layout.addWidget(self.list_widget)
        
        self.list_widget.itemDoubleClicked.connect(self._on_item_double_clicked)
        self.list_widget.customContextMenuRequested.connect(self._on_context_menu)

    def update_view(self, data: dict):
        self.list_widget.clear()
        groups = data.get("groups", [])
        programs = data.get("programs", {})
        
        programs_by_group = {}
        for prog_id, prog_data in programs.items():
            group_id = prog_data.get('group_id')
            if group_id not in programs_by_group: programs_by_group[group_id] = []
            programs_by_group[group_id].append(prog_data)
        for group_id in programs_by_group:
            programs_by_group[group_id].sort(key=lambda p: p.get("order", 0))

        for group_data in groups:
            # 添加分组标题
            group_label_item = QListWidgetItem()
            group_label_item.setFlags(Qt.ItemFlag.NoItemFlags) # 不可交互
            self.list_widget.addItem(group_label_item)
            
            label_widget = QLabel(f"<b>{group_data['name']}</b>")
            label_widget.setStyleSheet("padding: 10px 5px 5px 5px; font-size: 14px;")
            self.list_widget.setItemWidget(group_label_item, label_widget)
            
            # 添加该分组的程序
            if not programs_by_group.get(group_data['id']):
                empty_item = QListWidgetItem(" (空)")
                empty_item.setFlags(Qt.ItemFlag.NoItemFlags)
                empty_item.setForeground(Qt.GlobalColor.gray)
                self.list_widget.addItem(empty_item)

            for prog_data in programs_by_group.get(group_data['id'], []):
                item = QListWidgetItem(self._get_program_icon(prog_data['path']), prog_data['name'])
                item.setData(Qt.ItemDataRole.UserRole, {"id": prog_data['id'], "type": "program", "group_id": group_data['id']})
                item.setToolTip(prog_data['path'])
                self.list_widget.addItem(item)
    
    def _get_program_icon(self, path: str) -> QIcon:
        if not path or path in self.icon_cache: return self.icon_cache.get(path, QIcon.fromTheme("application-x-executable"))
        icon = self.icon_provider.icon(QFileInfo(path))
        if icon.isNull(): icon = QIcon.fromTheme("application-x-executable")
        self.icon_cache[path] = icon
        return icon

    def _on_item_double_clicked(self, item: QListWidgetItem):
        data = item.data(Qt.ItemDataRole.UserRole)
        if data and data.get('type') == 'program':
            self.item_double_clicked.emit(data['id'])

    def _on_context_menu(self, pos):
        item = self.list_widget.itemAt(pos)
        # 右键在空白处，可以提供“添加程序”等全局操作
        if not item or not item.data(Qt.ItemDataRole.UserRole): return

        data = item.data(Qt.ItemDataRole.UserRole)
        menu = QMenu(self)
        if data.get('type') == 'program':
            menu.addAction("启动").triggered.connect(lambda: self.item_double_clicked.emit(data['id']))
            menu.addAction("编辑...").triggered.connect(lambda: self.edit_item_requested.emit(data['id'], 'program'))
            menu.addAction("删除").triggered.connect(lambda: self.delete_item_requested.emit(data['id'], 'program'))
        menu.exec_(self.list_widget.mapToGlobal(pos))