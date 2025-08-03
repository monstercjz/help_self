# desktop_center/src/features/program_launcher/views/modes/tree_view.py
import logging
import os
from PySide6.QtWidgets import (QTreeWidget, QTreeWidgetItem, QAbstractItemView,
                               QVBoxLayout, QHeaderView, QGroupBox, QHBoxLayout)
from PySide6.QtGui import QIcon, QDropEvent, QFont, QResizeEvent, QColor
from PySide6.QtCore import Qt, QSize

from .base_view import BaseViewMode
from ...services.icon_service import icon_service
from ...widgets.menu_factory import MenuFactory

class LauncherTreeWidget(QTreeWidget):
    """
    专用于树状视图的自定义QTreeWidget，以可靠地处理拖放事件。
    """
    def __init__(self, parent_view: BaseViewMode):
        super().__init__(parent_view)
        self.parent_view = parent_view

    def dropEvent(self, event: QDropEvent):
        # 记录拖放前的信息
        source_item = self.currentItem()
        if not source_item:
            event.ignore(); return
        
        source_data = source_item.data(0, Qt.ItemDataRole.UserRole)
        source_type = source_data.get('type')
        source_id = source_data.get('id')

        # 执行验证逻辑
        target_item = self.itemAt(event.position().toPoint())
        drop_indicator = self.dropIndicatorPosition()

        if source_type == 'group':
            if (target_item and target_item.parent()) or drop_indicator == QAbstractItemView.DropIndicatorPosition.OnItem:
                logging.warning("Illegal drop: Group cannot be dropped into another group.")
                event.ignore(); return
        elif source_type == 'program':
            if (target_item is None or target_item.parent() is None) and drop_indicator != QAbstractItemView.DropIndicatorPosition.OnItem:
                logging.warning("Illegal drop: Program cannot be a top-level item.")
                event.ignore(); return
        
        # 核心修复：先调用父类方法，让Qt完成UI移动
        super().dropEvent(event)

        # --- UI已经更新，现在分析新状态并发射精确信号 ---
        logging.info("Drop event processed by QTreeWidget, analyzing new structure...")

        if source_type == 'group':
            root = self.invisibleRootItem()
            new_group_order = [root.child(i).data(0, Qt.ItemDataRole.UserRole)['id'] for i in range(root.childCount())]
            self.parent_view.group_order_changed.emit(new_group_order)
            logging.info(f"Emitted group_order_changed: {new_group_order}")

        elif source_type == 'program':
            new_parent_item = source_item.parent()
            if not new_parent_item:
                logging.error("Program ended up in an invalid top-level position after drop.")
                return

            target_group_data = new_parent_item.data(0, Qt.ItemDataRole.UserRole)
            target_group_id = target_group_data.get('id')
            new_index = new_parent_item.indexOfChild(source_item)
            
            self.parent_view.program_dropped.emit(source_id, target_group_id, new_index)
            logging.info(f"Emitted program_dropped: program '{source_id}' to group '{target_group_id}' at index {new_index}")


class TreeViewMode(BaseViewMode):
    """
    树状视图模式的实现。
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # 1. 创建外层容器，它将占据100%宽度
        outer_container = QGroupBox() # 移除标题
        outer_container.setObjectName("outerTreeContainer") # 设置对象名
        outer_layout = QHBoxLayout(outer_container)

        # 2. 创建内层容器（宽度为50%）
        self.tree_container = QGroupBox() # 移除标题
        self.tree_container.setObjectName("innerTreeContainer") # 设置对象名
        inner_layout = QVBoxLayout(self.tree_container)
        
        self.tree = LauncherTreeWidget(self)
        self.tree.setObjectName("launcherTreeView")
        self.tree.setHeaderHidden(True)
        self.tree.setColumnCount(2)
        self.tree.setIndentation(20)

        header = self.tree.header()
        # --- 最终列宽策略 ---
        # 第一列拉伸，占据所有可用空间
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        # 第二列根据内容自适应宽度
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setStretchLastSection(False)

        self.tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.tree.setDragDropMode(QAbstractItemView.DragDropMode.InternalMove)
        self.tree.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.tree.setDragEnabled(True)
        self.tree.setAcceptDrops(True)
        self.tree.setDropIndicatorShown(True)

        # 3. 组装UI层级
        inner_layout.addWidget(self.tree)             # 树 -> 内层容器
        outer_layout.addWidget(self.tree_container)   # 内层容器 -> 外层布局
        outer_layout.addStretch(1)                    # 添加弹簧以填充右侧空白
        layout.addWidget(outer_container)             # 外层容器 -> 主布局

        self.tree.itemDoubleClicked.connect(self._on_item_double_clicked)
        self.tree.customContextMenuRequested.connect(self._on_context_menu)

    def update_view(self, data: dict):
        current_search = self.parent().search_bar.text() if self.parent() and hasattr(self.parent(), 'search_bar') else ""
        
        # 应用从配置中读取的样式
        config = data.get('tree_view_config', {})
        icon_size = config.get('icon_size', 20)
        font_size = config.get('font_size', 13)
        
        self.tree.setIconSize(QSize(icon_size, icon_size))
        
        font = self.tree.font()
        font.setPointSize(font_size)
        self.tree.setFont(font)

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
                group_id = group_data['id']
                group_programs = programs_by_group.get(group_id, [])
                
                # 创建分组项，并直接设置文本
                group_item = QTreeWidgetItem(self.tree)
                group_item.setText(0, group_data['name'])
                group_item.setText(1, str(len(group_programs)))
                
                # 设置数据和标识
                group_item.setData(0, Qt.ItemDataRole.UserRole, {"id": group_id, "type": "group", "name": group_data['name']})
                group_item.setFlags(group_item.flags() | Qt.ItemFlag.ItemIsDropEnabled)
                
                # 设置分组的特殊样式
                font = group_item.font(0)
                font.setWeight(QFont.Bold)
                group_item.setFont(0, font)
                group_item.setTextAlignment(1, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                
                # 明确设置第一列（名称）的颜色
                group_item.setForeground(0, QColor("#303133")) # 深灰色

                # 设置第二列数字的颜色为更淡的灰色
                group_item.setForeground(1, QColor("#B0B0B0"))
                
                # 设置第二列数字的字体大小比程序名字小3个数值
                count_font = group_item.font(1)
                count_font.setPointSize(self.tree.font().pointSize() - 3)
                group_item.setFont(1, count_font)

                # 添加程序子项
                for prog_data in group_programs:
                    program_item = QTreeWidgetItem(group_item)
                    # 在名称前添加空格以增加与图标的距离
                    program_item.setText(0, "   " + prog_data['name'])
                    program_item.setIcon(0, icon_service.get_program_icon(prog_data['path']))
                    program_item.setData(0, Qt.ItemDataRole.UserRole, {"id": prog_data['id'], "type": "program", "name": prog_data['name'], "path": prog_data['path']})
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
        if not item:
            return
        
        data = item.data(0, Qt.ItemDataRole.UserRole)
        item_type = data.get('type')
        item_id = data.get('id')

        if not item_type or not item_id:
            return

        menu = MenuFactory.create_context_menu(item_type, item_id, self)
        menu.exec_(self.tree.mapToGlobal(pos))

    def resizeEvent(self, event: QResizeEvent):
        """
        重写 resizeEvent 以动态设置容器宽度为父窗口的一半。
        """
        super().resizeEvent(event)
        # 减去边距，使计算更精确
        new_width = (self.width() - self.layout().contentsMargins().left() * 2) * 0.35
        self.tree_container.setMaximumWidth(int(new_width))
