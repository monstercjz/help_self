# desktop_center/src/features/program_launcher/views/launcher_page_view.py
import logging
import sys
import os
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QPushButton, QTreeWidget,
                               QTreeWidgetItem, QHBoxLayout, QLineEdit, QMenu,
                               QAbstractItemView, QSpacerItem, QSizePolicy)
from PySide6.QtCore import Signal, Qt, QMimeData
from PySide6.QtGui import QIcon, QAction, QPixmap, QDrag, QDropEvent

from ..services.win_icon_extractor import WinIconExtractor

class LauncherTreeWidget(QTreeWidget):
    # ... 此类保持不变 ...
    items_moved = Signal()
    def __init__(self, parent=None):
        super().__init__(parent)
    def dropEvent(self, event: QDropEvent):
        source_item = self.currentItem()
        if not source_item:
            event.ignore()
            return
        target_item = self.itemAt(event.position().toPoint())
        drop_indicator = self.dropIndicatorPosition()
        source_data = source_item.data(0, Qt.ItemDataRole.UserRole)
        source_type = source_data.get('type')
        if source_type == 'program':
            if target_item and target_item.data(0, Qt.ItemDataRole.UserRole).get('type') == 'group': pass
            elif target_item and target_item.parent() and target_item.parent().data(0, Qt.ItemDataRole.UserRole).get('type') == 'group': pass
            else:
                logging.warning("[LauncherTreeWidget] Illegal drop: Program cannot be dropped to top level.")
                event.ignore()
                return
        if source_type == 'group':
            if drop_indicator == QAbstractItemView.DropIndicatorPosition.OnItem:
                logging.warning("[LauncherTreeWidget] Illegal drop: Group cannot be a child of another item.")
                event.ignore()
                return
            if target_item and target_item.parent():
                logging.warning("[LauncherTreeWidget] Illegal drop: Group cannot be dropped into another group.")
                event.ignore()
                return
        super().dropEvent(event)
        logging.info("[LauncherTreeWidget] dropEvent finished. Emitting items_moved signal.")
        self.items_moved.emit()


class LauncherPageView(QWidget):
    # ... 此类大部分保持不变 ...
    add_group_requested = Signal()
    add_program_requested = Signal()
    add_program_to_group_requested = Signal(str)
    item_double_clicked = Signal(str)
    edit_item_requested = Signal(str, str)
    delete_item_requested = Signal(str, str)
    search_text_changed = Signal(str)
    change_data_path_requested = Signal()
    items_moved = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.icon_cache = {}
        self.icon_extractor = WinIconExtractor() if sys.platform == "win32" else None
        self._init_ui()

    def _init_ui(self):
        # ... 此方法保持不变 ...
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
        toolbar_layout.addWidget(self.add_group_btn)
        toolbar_layout.addWidget(self.add_program_btn)
        toolbar_layout.addSpacerItem(QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum))
        toolbar_layout.addWidget(self.search_bar)
        toolbar_layout.addWidget(self.settings_btn)
        layout.addLayout(toolbar_layout)
        self.tree = LauncherTreeWidget()
        self.tree.setHeaderHidden(True)
        self.tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.tree.setDragDropMode(QAbstractItemView.DragDropMode.InternalMove)
        self.tree.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.tree.setDragEnabled(True)
        self.tree.setAcceptDrops(True)
        self.tree.setDropIndicatorShown(True)
        layout.addWidget(self.tree)
        self.add_group_btn.clicked.connect(self.add_group_requested)
        self.add_program_btn.clicked.connect(self.add_program_requested)
        self.settings_btn.clicked.connect(self.change_data_path_requested)
        self.tree.itemDoubleClicked.connect(self._on_item_double_clicked)
        self.tree.customContextMenuRequested.connect(self._on_context_menu)
        self.search_bar.textChanged.connect(self.search_text_changed)
        self.tree.items_moved.connect(self.items_moved)
        
    def rebuild_ui(self, data: dict):
        # ... 此方法保持不变 ...
        self.tree.blockSignals(True)
        try:
            self.tree.clear()
            groups = data.get("groups", [])
            programs = data.get("programs", {})
            programs_by_group = {}
            for prog_id, prog_data in programs.items():
                group_id = prog_data['group_id']
                if group_id not in programs_by_group: programs_by_group[group_id] = []
                programs_by_group[group_id].append(prog_data)
            for group_id in programs_by_group:
                programs_by_group[group_id].sort(key=lambda p: p.get("order", 0))
            for group_data in groups:
                group_id = group_data['id']
                group_item = QTreeWidgetItem(self.tree, [group_data['name']])
                group_item.setData(0, Qt.ItemDataRole.UserRole, {
                    "id": group_id, "type": "group", "name": group_data['name']
                })
                group_item.setIcon(0, QIcon.fromTheme("folder"))
                group_item.setFlags(group_item.flags() | Qt.ItemFlag.ItemIsDropEnabled)
                for prog_data in programs_by_group.get(group_id, []):
                    program_item = QTreeWidgetItem(group_item, [prog_data['name']])
                    program_item.setData(0, Qt.ItemDataRole.UserRole, {
                        "id": prog_data['id'], "type": "program",
                        "name": prog_data['name'], "path": prog_data['path']
                    })
                    icon = self._get_program_icon(prog_data['path'])
                    program_item.setIcon(0, icon)
                    program_item.setFlags(program_item.flags() & ~Qt.ItemFlag.ItemIsDropEnabled)
                group_item.setExpanded(True)
        finally:
            self.tree.blockSignals(False)
            logging.debug("[VIEW] Signals for tree widget have been unblocked.")

    def get_current_structure(self) -> dict:
        # ... 此方法保持不变 ...
        new_groups = []; new_programs = {}
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
                new_program_obj = {
                    "id": program_id, "group_id": group_id,
                    "name": program_data['name'], "path": program_data['path'],
                    "order": j 
                }
                new_programs[program_id] = new_program_obj
        logging.info(f"[VIEW] Read current structure from UI. Groups: {len(new_groups)}, Programs: {len(new_programs)}")
        return {"groups": new_groups, "programs": new_programs}

    def _get_program_icon(self, path: str) -> QIcon:
        # ... 此方法保持不变 ...
        if path in self.icon_cache: return self.icon_cache[path]
        if self.icon_extractor and path and os.path.exists(path):
            pixmap = self.icon_extractor.get_icon_pixmap(path)
            if pixmap:
                icon = QIcon(pixmap)
                self.icon_cache[path] = icon
                return icon
        default_icon = QIcon.fromTheme("application-x-executable")
        self.icon_cache[path] = default_icon
        return default_icon

    def _on_item_double_clicked(self, item: QTreeWidgetItem):
        # ... 此方法保持不变 ...
        data = item.data(0, Qt.ItemDataRole.UserRole)
        if data and data.get('type') == 'program': self.item_double_clicked.emit(data['id'])
            
    def _on_context_menu(self, pos):
        item = self.tree.itemAt(pos)
        if not item: return
        data = item.data(0, Qt.ItemDataRole.UserRole)
        menu = QMenu(self)
        if data.get('type') == 'group':
            add_prog_action = menu.addAction("添加程序到此分组...")
            add_prog_action.triggered.connect(lambda: self.add_program_to_group_requested.emit(data['id']))
            menu.addSeparator()
            edit_action = menu.addAction("重命名分组")
            delete_action = menu.addAction("删除分组")
            edit_action.triggered.connect(lambda: self.edit_item_requested.emit(data['id'], 'group'))
            delete_action.triggered.connect(lambda: self.delete_item_requested.emit(data['id'], 'group'))
        elif data.get('type') == 'program':
            launch_action = menu.addAction("启动")
            # 【修改】在此处添加“编辑”菜单项
            edit_action = menu.addAction("编辑...")
            delete_action = menu.addAction("删除")
            menu.addSeparator()
            
            launch_action.triggered.connect(lambda: self.item_double_clicked.emit(data['id']))
            edit_action.triggered.connect(lambda: self.edit_item_requested.emit(data['id'], 'program'))
            delete_action.triggered.connect(lambda: self.delete_item_requested.emit(data['id'], 'program'))
        menu.exec_(self.tree.mapToGlobal(pos))

    def filter_items(self, text: str):
        # ... 此方法保持不变 ...
        text = text.lower()
        root = self.tree.invisibleRootItem()
        for i in range(root.childCount()):
            group_item = root.child(i)
            group_visible = False
            for j in range(group_item.childCount()):
                program_item = group_item.child(j)
                is_match = text in program_item.text(0).lower()
                program_item.setHidden(not is_match)
                if is_match: group_visible = True
            group_match = text in group_item.text(0).lower()
            group_item.setHidden(not (group_visible or group_match))
            group_item.setExpanded(True if text and (group_visible or group_match) else False)