# desktop_center/src/features/program_launcher/views/modes/icon_view.py
import logging
from PySide6.QtWidgets import (QMenu, QFileIconProvider, QVBoxLayout, 
                               QLabel, QWidget, QScrollArea, QFrame)
from PySide6.QtGui import QIcon, QDragEnterEvent, QDropEvent, QDragMoveEvent
from PySide6.QtCore import Qt, QFileInfo, QSize, QPoint, QRect

from .base_view import BaseViewMode
from ...widgets.card_widget import CardWidget
from ...widgets.group_header_widget import GroupHeaderWidget
from .flow_layout import FlowLayout

class IconViewMode(BaseViewMode):
    """
    图标网格视图模式的实现。
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.icon_cache = {}; self.icon_provider = QFileIconProvider()
        self.card_containers = {}; self.group_headers = {}
        main_layout = QVBoxLayout(self); main_layout.setContentsMargins(0, 0, 0, 0)
        scroll_area = QScrollArea(); scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QScrollArea.Shape.NoFrame)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.content_widget = QWidget(); self.content_widget.setAcceptDrops(True)
        scroll_area.setWidget(self.content_widget)
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        main_layout.addWidget(scroll_area)
        self.drop_indicator = QFrame(self.content_widget)
        self.drop_indicator.setLineWidth(2); self.drop_indicator.hide()
        self.setAcceptDrops(True)

    def update_view(self, data: dict):
        self.card_containers.clear(); self.group_headers.clear()
        while self.content_layout.count():
            child = self.content_layout.takeAt(0)
            if child.widget(): child.widget().deleteLater()

        groups = data.get("groups", []); programs = data.get("programs", {})
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
            group_header = GroupHeaderWidget(group_data)
            group_header.customContextMenuRequested.connect(self._on_group_context_menu)
            self.content_layout.addWidget(group_header)
            self.group_headers[group_data['id']] = group_header

            card_container = QWidget()
            flow_layout = FlowLayout(card_container, h_spacing=10, v_spacing=10)
            self.card_containers[group_data['id']] = card_container

            programs_in_group = programs_by_group.get(group_data['id'], [])
            if not programs_in_group:
                flow_layout.addWidget(QLabel("(此分组为空)"))
            else:
                for prog_data in programs_in_group:
                    icon = self._get_program_icon(prog_data['path'])
                    card = CardWidget(prog_data, icon)
                    card.doubleClicked.connect(self.item_double_clicked)
                    card.customContextMenuRequested.connect(self._on_card_context_menu)
                    flow_layout.addWidget(card)
            
            self.content_layout.addWidget(card_container)
        self.content_layout.addStretch()
    
    def _get_program_icon(self, path: str) -> QIcon:
        if not path or path in self.icon_cache: return self.icon_cache.get(path, QIcon.fromTheme("application-x-executable"))
        icon = self.icon_provider.icon(QFileInfo(path))
        if icon.isNull(): icon = QIcon.fromTheme("application-x-executable")
        self.icon_cache[path] = icon
        return icon

    def _on_card_context_menu(self, program_id, event):
        menu = QMenu(self)
        menu.addAction("启动").triggered.connect(lambda: self.item_double_clicked.emit(program_id))
        menu.addAction("编辑...").triggered.connect(lambda: self.edit_item_requested.emit(program_id, 'program'))
        menu.addAction("删除").triggered.connect(lambda: self.delete_item_requested.emit(program_id, 'program'))
        menu.exec_(event.globalPos())

    def _on_group_context_menu(self, group_id, event):
        """处理分组标题的右键菜单请求。"""
        menu = QMenu(self)
        # 【核心修复】增加“添加程序到此分组...”菜单项
        menu.addAction("添加程序到此分组...").triggered.connect(lambda: self.add_program_to_group_requested.emit(group_id))
        menu.addSeparator()
        menu.addAction("重命名分组").triggered.connect(lambda: self.edit_item_requested.emit(group_id, 'group'))
        menu.addAction("删除分组").triggered.connect(lambda: self.delete_item_requested.emit(group_id, 'group'))
        menu.exec_(event.globalPos())

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasFormat("application/x-program-launcher-card") or \
           event.mimeData().hasFormat("application/x-program-launcher-group"):
            event.acceptProposedAction()
        else:
            event.ignore()

    def dragLeaveEvent(self, event):
        self.drop_indicator.hide()

    def dragMoveEvent(self, event: QDragMoveEvent):
        pos = self.content_widget.mapFrom(self, event.position().toPoint())
        
        if event.mimeData().hasFormat("application/x-program-launcher-card"):
            self.drop_indicator.setFrameShape(QFrame.Shape.VLine)
            target_group_id, _, indicator_pos = self._find_card_drop_pos(pos)
        elif event.mimeData().hasFormat("application/x-program-launcher-group"):
            self.drop_indicator.setFrameShape(QFrame.Shape.HLine)
            _, indicator_pos = self._find_group_drop_pos(pos)
        else:
            event.ignore(); return
        
        if indicator_pos:
            self.drop_indicator.setGeometry(indicator_pos)
            self.drop_indicator.show()
            event.accept()
        else:
            self.drop_indicator.hide()

    def dropEvent(self, event: QDropEvent):
        self.drop_indicator.hide()
        pos = self.content_widget.mapFrom(self, event.position().toPoint())
        
        if event.mimeData().hasFormat("application/x-program-launcher-card"):
            program_id = event.mimeData().data("application/x-program-launcher-card").data().decode('utf-8')
            target_group_id, target_index, _ = self._find_card_drop_pos(pos)
            if target_group_id is not None:
                self.program_dropped.emit(program_id, target_group_id, target_index)
                event.acceptProposedAction()
        elif event.mimeData().hasFormat("application/x-program-launcher-group"):
            source_group_id = event.mimeData().data("application/x-program-launcher-group").data().decode('utf-8')
            target_index, _ = self._find_group_drop_pos(pos)
            
            group_ids = list(self.group_headers.keys())
            if source_group_id in group_ids:
                group_ids.remove(source_group_id)
                group_ids.insert(target_index, source_group_id)
                self.group_order_changed.emit(group_ids)
                event.acceptProposedAction()
        else:
            event.ignore()

    def _find_card_drop_pos(self, pos_in_content: QPoint):
        for group_id, container in self.card_containers.items():
            if container.geometry().contains(pos_in_content):
                layout = container.layout()
                local_pos = container.mapFrom(self.content_widget, pos_in_content)
                target_index = 0
                for i in range(layout.count()):
                    widget = layout.itemAt(i).widget()
                    if local_pos.x() < widget.geometry().center().x(): break
                    target_index = i + 1
                
                rect = QRect()
                if layout.count() == 0: rect.setRect(5, 5, 2, 80)
                elif target_index < layout.count():
                    widget = layout.itemAt(target_index).widget()
                    rect.setRect(widget.x() - 5, widget.y(), 2, widget.height())
                else:
                    last_widget = layout.itemAt(layout.count() - 1).widget()
                    rect.setRect(last_widget.x() + last_widget.width() + 3, last_widget.y(), 2, last_widget.height())
                
                final_rect = QRect(container.mapTo(self.content_widget, rect.topLeft()), rect.size())
                return group_id, target_index, final_rect
        return None, -1, None
    
    def _find_group_drop_pos(self, pos_in_content: QPoint):
        target_index = 0
        for i, (gid, header) in enumerate(self.group_headers.items()):
            container = self.card_containers[gid]
            group_rect = header.geometry().united(container.geometry())
            if pos_in_content.y() < group_rect.center().y():
                break
            target_index = i + 1
        
        rect = QRect()
        if target_index < len(self.group_headers):
            header = list(self.group_headers.values())[target_index]
            rect.setRect(header.x(), header.y() - 5, self.content_widget.width() - 20, 2)
        else:
            last_header = list(self.group_headers.values())[-1]
            last_container = self.card_containers[list(self.group_headers.keys())[-1]]
            rect.setRect(last_header.x(), last_container.y() + last_container.height() + 5, self.content_widget.width() - 20, 2)
            
        return target_index, rect