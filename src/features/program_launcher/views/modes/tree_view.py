# desktop_center/src/features/program_launcher/views/modes/tree_view.py
import logging
import os
from PySide6.QtWidgets import (QTreeWidget, QTreeWidgetItem, QMenu, QAbstractItemView,
                               QFileIconProvider, QVBoxLayout)
from PySide6.QtGui import QIcon, QDropEvent
from PySide6.QtCore import Qt, QFileInfo

from .base_view import BaseViewMode

class LauncherTreeWidget(QTreeWidget):
    """
    专用于树状视图的自定义QTreeWidget，以可靠地处理拖放事件。
    """
    def __init__(self, parent_view: BaseViewMode):
        super().__init__(parent_view)
        self.parent_view = parent_view

    def dropEvent(self, event: QDropEvent):
        source_item = self.currentItem()
        if not source_item:
            event.ignore(); return

        target_item = self.itemAt(event.position().toPoint())
        drop_indicator = self.dropIndicatorPosition()

        source_data = source_item.data(0, Qt.ItemDataRole.UserRole)
        source_type = source_data.get('type')

        # 【核心修复-BUG-1】
        if source_type == 'program':
            # 规则：程序不能成为顶层项目
            # 情况1: 拖到了空白处，目标项为空
            if not target_item:
                logging.warning("[LauncherTreeWidget] Illegal drop: Program cannot be dropped into top-level empty space.")
                event.ignore(); return
            
            # 情况2: 拖到了一个分组的上方或下方，这将使其成为顶层项
            if target_item.parent() is None and drop_indicator != QAbstractItemView.DropIndicatorPosition.OnItem:
                 logging.warning("[LauncherTreeWidget] Illegal drop: Program cannot be dropped between groups.")
                 event.ignore(); return

        if source_type == 'group':
            if drop_indicator == QAbstractItemView.DropIndicatorPosition.OnItem:
                event.ignore(); return
            if target_item and target_item.parent():
                event.ignore(); return
        
        super().dropEvent(event)
        self.parent_view.items_moved.emit()


class TreeViewMode(BaseViewMode):
    """
    树状视图模式的实现。
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.icon_cache = {}
        self.icon_provider = QFileIconProvider()
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        self.tree = LauncherTreeWidget(self)
        self.tree.setHeaderHidden(True)
        self.tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.tree.setDragDropMode(QAbstractItemView.DragDropMode.InternalMove)
        self.tree.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.tree.setDragEnabled(True)
        self.tree.setAcceptDrops(True)
        self.tree.setDropIndicatorShown(True)
        
        layout.addWidget(self.tree)

        self.tree.itemDoubleClicked.connect(self._on_item_double_clicked)
        self.tree.customContextMenuRequested.connect(self._on_context_menu)

    def update_view(self, data: dict):
        current_search = self.parent().search_bar.text() if self.parent() and hasattr(self.parent(), 'search_bar') else ""
        
        self.tree.blockSignals(True)
        try:
            self.tree.clear()
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
                group_item = QTreeWidgetItem(self.tree, [group_data['name']])
                group_item.setData(0, Qt.ItemDataRole.UserRole, {"id": group_data['id'], "type": "group", "name": group_data['name']})
                group_item.setIcon(0, QIcon.fromTheme("folder"))
                group_item.setFlags(group_item.flags() | Qt.ItemFlag.ItemIsDropEnabled)
                for prog_data in programs_by_group.get(group_data['id'], []):
                    program_item = QTreeWidgetItem(group_item, [prog_data['name']])
                    program_item.setData(0, Qt.ItemDataRole.UserRole, {"id": prog_data['id'], "type": "program", "name": prog_data['name'], "path": prog_data['path']})
                    program_item.setIcon(0, self._get_program_icon(prog_data['path']))
                    program_item.setFlags(program_item.flags() & ~Qt.ItemFlag.ItemIsDropEnabled)
                group_item.setExpanded(True)
        finally:
            self.tree.blockSignals(False)
        
        if current_search:
            self.filter_items(current_search)

    def get_current_structure(self) -> dict:
        new_groups, new_programs = [], {}
        root = self.tree.invisibleRootItem()
        for i in range(root.childCount()):
            group_item = root.child(i)
            group_data = group_item.data(0, Qt.ItemDataRole.UserRole)
            if not isinstance(group_data, dict) or 'id' not in group_data: continue
            group_id = group_data['id']
            new_groups.append({"id": group_id, "name": group_data['name']})
            for j in range(group_item.childCount()):
                program_item = group_item.child(j)
                program_data = program_item.data(0, Qt.ItemDataRole.UserRole)
                if not isinstance(program_data, dict) or 'id' not in program_data: continue
                program_id = program_data['id']
                new_programs[program_id] = {"id": program_id, "group_id": group_id, "name": program_data['name'], "path": program_data['path'], "order": j}
        return {"groups": new_groups, "programs": new_programs}

    def _get_program_icon(self, path: str) -> QIcon:
        if not path or path in self.icon_cache: return self.icon_cache.get(path, QIcon.fromTheme("application-x-executable"))
        icon = self.icon_provider.icon(QFileInfo(path))
        if icon.isNull(): icon = QIcon.fromTheme("application-x-executable")
        self.icon_cache[path] = icon
        return icon

    def _on_item_double_clicked(self, item: QTreeWidgetItem):
        data = item.data(0, Qt.ItemDataRole.UserRole)
        if data and data.get('type') == 'program':
            self.item_double_clicked.emit(data['id'])
            
    def _on_context_menu(self, pos):
        item = self.tree.itemAt(pos)
        if not item: return
        data = item.data(0, Qt.ItemDataRole.UserRole)
        menu = QMenu(self)
        if data.get('type') == 'group':
            menu.addAction("添加程序到此分组...").triggered.connect(lambda: self.add_program_to_group_requested.emit(data['id']))
            menu.addSeparator()
            menu.addAction("重命名分组").triggered.connect(lambda: self.edit_item_requested.emit(data['id'], 'group'))
            menu.addAction("删除分组").triggered.connect(lambda: self.delete_item_requested.emit(data['id'], 'group'))
        elif data.get('type') == 'program':
            menu.addAction("启动").triggered.connect(lambda: self.item_double_clicked.emit(data['id']))
            menu.addAction("编辑...").triggered.connect(lambda: self.edit_item_requested.emit(data['id'], 'program'))
            menu.addAction("删除").triggered.connect(lambda: self.delete_item_requested.emit(data['id'], 'program'))
        menu.exec_(self.tree.mapToGlobal(pos))
        
    def filter_items(self, text: str):
        """【核心修复-BUG-2】为树状视图实现/验证搜索功能。"""
        text = text.lower()
        root = self.tree.invisibleRootItem()
        for i in range(root.childCount()):
            group_item = root.child(i)
            group_data = group_item.data(0, Qt.ItemDataRole.UserRole)
            group_name = group_data.get('name', '').lower()
            
            group_has_visible_child = False
            for j in range(group_item.childCount()):
                program_item = group_item.child(j)
                program_data = program_item.data(0, Qt.ItemDataRole.UserRole)
                program_name = program_data.get('name', '').lower()
                
                is_match = text in program_name
                program_item.setHidden(not is_match)
                if is_match:
                    group_has_visible_child = True
            
            # 如果分组名匹配，或其下有匹配的程序，则显示该分组
            group_is_match = text in group_name
            group_item.setHidden(not (group_has_visible_child or group_is_match))
            
            # 如果在搜索，则展开匹配的分组
            if text:
                group_item.setExpanded(group_has_visible_child or group_is_match)