# desktop_center/src/features/program_launcher/views/modes/tree_view.py
import logging
import os
from PySide6.QtWidgets import (QTreeWidget, QTreeWidgetItem, QMenu, QAbstractItemView,
                               QVBoxLayout)
from PySide6.QtGui import QIcon, QDropEvent
from PySide6.QtCore import Qt

from .base_view import BaseViewMode
from ...services.icon_service import icon_service

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
            event.ignore()
            return

        target_item = self.itemAt(event.position().toPoint())
        drop_indicator = self.dropIndicatorPosition()
        
        source_data = source_item.data(0, Qt.ItemDataRole.UserRole)
        source_type = source_data.get('type')

        # 规则 1: 分组 (group) 只能在顶层移动，不能被拖入另一个分组
        if source_type == 'group':
            # 如果目标是另一个分组的子项，禁止
            if target_item and target_item.parent():
                event.ignore()
                return
            # 如果想把分组拖“到”另一个分组上（而不是之间），禁止
            if drop_indicator == QAbstractItemView.DropIndicatorPosition.OnItem:
                event.ignore()
                return

        # 规则 2: 程序 (program) 只能在分组内移动，不能成为顶层项目
        if source_type == 'program':
            # 如果目标是顶层（即目标是分组或目标为空白区域）
            if target_item is None or target_item.parent() is None:
                # 并且拖放位置不是在一个分组“之上”（OnItem）
                if drop_indicator != QAbstractItemView.DropIndicatorPosition.OnItem:
                    event.ignore()
                    return
        
        # 所有验证通过，执行默认的拖放操作
        super().dropEvent(event)

        # 操作完成后，发出信号通知模型更新
        # 采用全量更新的方式，简单可靠
        self.parent_view.items_moved.emit()


class TreeViewMode(BaseViewMode):
    """
    树状视图模式的实现。
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        
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
                    program_item.setIcon(0, icon_service.get_program_icon(prog_data['path']))
                    program_item.setFlags(program_item.flags() & ~Qt.ItemFlag.ItemIsDropEnabled)
                group_item.setExpanded(True)
        finally:
            self.tree.blockSignals(False)
        
        if current_search:
            self.filter_items(current_search)

    def get_current_structure(self) -> dict:
        """
        从当前的UI树状态中，反向生成一份完整的数据结构字典。
        """
        new_groups, new_programs = [], {}
        root = self.tree.invisibleRootItem()
        
        # 遍历所有顶层项目（即分组）
        for i in range(root.childCount()):
            group_item = root.child(i)
            group_data = group_item.data(0, Qt.ItemDataRole.UserRole)
            
            # 确保这是一个有效的分组项目
            if not isinstance(group_data, dict) or group_data.get('type') != 'group':
                continue
            
            group_id = group_data['id']
            new_groups.append({"id": group_id, "name": group_data['name']})
            
            # 遍历该分组下的所有子项目（即程序）
            for j in range(group_item.childCount()):
                program_item = group_item.child(j)
                program_data = program_item.data(0, Qt.ItemDataRole.UserRole)

                # 确保这是一个有效的程序项目
                if not isinstance(program_data, dict) or program_data.get('type') != 'program':
                    continue
                
                program_id = program_data['id']
                # 从 program_data 中安全地获取 'path'
                path = program_data.get('path', '') # 使用 .get() 避免 KeyError
                new_programs[program_id] = {
                    "id": program_id,
                    "group_id": group_id,
                    "name": program_data['name'],
                    "path": path,
                    "order": j
                }
        return {"groups": new_groups, "programs": new_programs}

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