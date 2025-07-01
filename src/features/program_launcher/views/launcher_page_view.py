# desktop_center/src/features/program_launcher/views/launcher_page_view.py
import logging
import sys
import os
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QPushButton, QTreeWidget,
                               QTreeWidgetItem, QHBoxLayout, QLineEdit, QMenu,
                               QAbstractItemView, QSpacerItem, QSizePolicy) # 【修改】导入QSizePolicy
from PySide6.QtCore import Signal, Qt, QMimeData
from PySide6.QtGui import QIcon, QAction, QPixmap, QDrag

from ..services.win_icon_extractor import WinIconExtractor

class LauncherPageView(QWidget):
    """
    视图层，负责展示程序启动器的UI界面。
    """
    add_group_requested = Signal()
    add_program_requested = Signal(str)  # group_id
    item_double_clicked = Signal(str)  # program_id
    edit_item_requested = Signal(str, str) # item_id, item_type ('group' or 'program')
    delete_item_requested = Signal(str, str) # item_id, item_type
    search_text_changed = Signal(str)
    group_order_changed = Signal(list) # list of group_ids
    program_order_changed = Signal(str, list) # group_id, list of program_ids
    change_data_path_requested = Signal() # 【新增】定义新信号

    def __init__(self, parent=None):
        super().__init__(parent)
        self.icon_cache = {}
        self.icon_extractor = WinIconExtractor() if sys.platform == "win32" else None
        
        self._init_ui()

    def _init_ui(self):
        """初始化UI组件。"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        # 顶部工具栏
        toolbar_layout = QHBoxLayout()
        self.add_group_btn = QPushButton(QIcon.fromTheme("list-add"), " 新建分组")
        self.add_program_btn = QPushButton(QIcon.fromTheme("document-new"), " 添加程序")
        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("搜索程序...")
        
        # 【新增】设置按钮
        self.settings_btn = QPushButton()
        self.settings_btn.setIcon(QIcon.fromTheme("emblem-system")) # 使用一个常见的设置图标
        self.settings_btn.setToolTip("设置数据文件路径")
        
        toolbar_layout.addWidget(self.add_group_btn)
        toolbar_layout.addWidget(self.add_program_btn)
        toolbar_layout.addSpacerItem(QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)) # 【修改】增加弹簧
        toolbar_layout.addWidget(self.search_bar)
        toolbar_layout.addWidget(self.settings_btn) # 【新增】将设置按钮添加到布局
        layout.addLayout(toolbar_layout)

        # 树状视图
        self.tree = QTreeWidget()
        self.tree.setHeaderHidden(True)
        self.tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.tree.setDragDropMode(QAbstractItemView.DragDropMode.InternalMove)
        self.tree.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.tree.setDragEnabled(True)
        self.tree.setAcceptDrops(True)
        self.tree.setDropIndicatorShown(True)
        
        layout.addWidget(self.tree)

        # 连接信号
        self.add_group_btn.clicked.connect(self.add_group_requested)
        self.add_program_btn.clicked.connect(self._on_add_program_clicked)
        self.settings_btn.clicked.connect(self.change_data_path_requested) # 【新增】连接信号
        self.tree.itemDoubleClicked.connect(self._on_item_double_clicked)
        self.tree.customContextMenuRequested.connect(self._on_context_menu)
        self.search_bar.textChanged.connect(self.search_text_changed)
        self.tree.model().rowsMoved.connect(self._on_rows_moved)
        
    def rebuild_ui(self, data: dict):
        """根据模型数据完全重建UI。"""
        self.tree.clear()
        groups = data.get("groups", [])
        programs = data.get("programs", {})
        
        # 将程序按 group_id 分组
        programs_by_group = {}
        for prog_id, prog_data in programs.items():
            group_id = prog_data['group_id']
            if group_id not in programs_by_group:
                programs_by_group[group_id] = []
            programs_by_group[group_id].append(prog_data)
        
        # 按order字段排序
        for group_id in programs_by_group:
            programs_by_group[group_id].sort(key=lambda p: p.get("order", 0))

        for group_data in groups:
            group_id = group_data['id']
            group_item = QTreeWidgetItem(self.tree, [group_data['name']])
            group_item.setData(0, Qt.ItemDataRole.UserRole, {"id": group_id, "type": "group"})
            group_item.setIcon(0, QIcon.fromTheme("folder"))
            group_item.setFlags(group_item.flags() | Qt.ItemFlag.ItemIsDropEnabled) # 允许接收拖拽

            for prog_data in programs_by_group.get(group_id, []):
                program_item = QTreeWidgetItem(group_item, [prog_data['name']])
                program_item.setData(0, Qt.ItemDataRole.UserRole, {"id": prog_data['id'], "type": "program"})
                
                # 设置图标
                icon = self._get_program_icon(prog_data['path'])
                program_item.setIcon(0, icon)
                program_item.setFlags(program_item.flags() & ~Qt.ItemFlag.ItemIsDropEnabled) # 程序项不允许接收拖拽

            group_item.setExpanded(True)

    def _get_program_icon(self, path: str) -> QIcon:
        """获取并缓存程序图标。"""
        if path in self.icon_cache:
            return self.icon_cache[path]

        if self.icon_extractor and path and os.path.exists(path):
            pixmap = self.icon_extractor.get_icon_pixmap(path)
            if pixmap:
                icon = QIcon(pixmap)
                self.icon_cache[path] = icon
                return icon
        
        # 默认图标
        default_icon = QIcon.fromTheme("application-x-executable")
        self.icon_cache[path] = default_icon
        return default_icon

    def _on_add_program_clicked(self):
        """当点击'添加程序'按钮时，确定当前选中的分组。"""
        current_item = self.tree.currentItem()
        group_id = None
        if current_item:
            data = current_item.data(0, Qt.ItemDataRole.UserRole)
            if data['type'] == 'group':
                group_id = data['id']
            elif data['type'] == 'program':
                group_id = current_item.parent().data(0, Qt.ItemDataRole.UserRole)['id']
        
        self.add_program_requested.emit(group_id)

    def _on_item_double_clicked(self, item: QTreeWidgetItem):
        """当双击项目时，只处理程序项。"""
        data = item.data(0, Qt.ItemDataRole.UserRole)
        if data and data['type'] == 'program':
            self.item_double_clicked.emit(data['id'])
            
    def _on_context_menu(self, pos):
        """处理右键菜单请求。"""
        item = self.tree.itemAt(pos)
        if not item:
            return

        data = item.data(0, Qt.ItemDataRole.UserRole)
        menu = QMenu(self)
        
        if data['type'] == 'group':
            edit_action = menu.addAction("重命名分组")
            delete_action = menu.addAction("删除分组")
            edit_action.triggered.connect(lambda: self.edit_item_requested.emit(data['id'], 'group'))
            delete_action.triggered.connect(lambda: self.delete_item_requested.emit(data['id'], 'group'))
        elif data['type'] == 'program':
            launch_action = menu.addAction("启动")
            delete_action = menu.addAction("删除程序")
            launch_action.triggered.connect(lambda: self.item_double_clicked.emit(data['id']))
            delete_action.triggered.connect(lambda: self.delete_item_requested.emit(data['id'], 'program'))
            
        menu.exec_(self.tree.mapToGlobal(pos))

    def filter_items(self, text: str):
        """根据文本隐藏或显示树中的项目。"""
        text = text.lower()
        root = self.tree.invisibleRootItem()
        for i in range(root.childCount()):
            group_item = root.child(i)
            group_visible = False
            for j in range(group_item.childCount()):
                program_item = group_item.child(j)
                is_match = text in program_item.text(0).lower()
                program_item.setHidden(not is_match)
                if is_match:
                    group_visible = True
            
            # 如果分组名称匹配或其下有匹配的程序，则显示分组
            group_match = text in group_item.text(0).lower()
            group_item.setHidden(not (group_visible or group_match))
            group_item.setExpanded(True if text and (group_visible or group_match) else False)

    def _on_rows_moved(self, parent, start, end, destination, dest_start):
        """处理拖拽排序事件。"""
        # 情况1: 重新排序分组
        if not parent.isValid(): # 拖拽的是顶层项目（分组）
            group_ids = []
            for i in range(self.tree.topLevelItemCount()):
                group_item = self.tree.topLevelItem(i)
                group_ids.append(group_item.data(0, Qt.ItemDataRole.UserRole)['id'])
            self.group_order_changed.emit(group_ids)
            logging.debug(f"Group order changed: {group_ids}")
        
        # 情况2: 在分组内重新排序程序，或将程序移动到另一个分组
        else:
            # 目标就是父项
            target_group_item = destination
            # 获取拖拽的源项目
            source_item = target_group_item.child(dest_start)
            if source_item:
                source_data = source_item.data(0, Qt.ItemDataRole.UserRole)
                # 确保拖拽的是程序
                if source_data and source_data['type'] == 'program':
                    # 更新程序的 group_id
                    target_group_id = target_group_item.data(0, Qt.ItemDataRole.UserRole)['id']
                    # 这是PySide6的一个bug或特性，拖拽后需要手动更新数据模型
                    # 我们这里只发出信号，让控制器去处理
                    
                    program_ids_in_group = []
                    for i in range(target_group_item.childCount()):
                        prog_item = target_group_item.child(i)
                        prog_id = prog_item.data(0, Qt.ItemDataRole.UserRole)['id']
                        program_ids_in_group.append(prog_id)
                    
                    self.program_order_changed.emit(target_group_id, program_ids_in_group)
                    logging.debug(f"Program order in group {target_group_id} changed: {program_ids_in_group}")