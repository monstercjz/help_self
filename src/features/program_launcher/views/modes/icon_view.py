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

    def filter_items(self, text: str):
        text = text.lower()
        for group_id, header in self.group_headers.items():
            container = self.card_containers.get(group_id)
            if not container: continue

            group_name = header.title_label.text().lower()
            group_has_visible_child = False
            
            layout = container.layout()
            for i in range(layout.count()):
                widget = layout.itemAt(i).widget()
                if isinstance(widget, CardWidget):
                    card_name = widget.name_label.text().lower()
                    is_match = text in card_name
                    widget.setVisible(is_match)
                    if is_match:
                        group_has_visible_child = True
            
            group_is_match = text in group_name
            header.setVisible(group_has_visible_child or group_is_match)
            container.setVisible(group_has_visible_child or group_is_match)

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
        menu = QMenu(self)
        menu.addAction("添加程序到此分组...").triggered.connect(lambda: self.add_program_to_group_requested.emit(group_id))
        menu.addSeparator()
        menu.addAction("重命名分组").triggered.connect(lambda: self.edit_item_requested.emit(group_id, 'group'))
        menu.addAction("删除分组").triggered.connect(lambda: self.delete_item_requested.emit(group_id, 'group'))
        menu.exec_(event.globalPos())

    def dragEnterEvent(self, event: QDragEnterEvent):
        # Check for the unified text format
        if event.mimeData().hasText() and ":" in event.mimeData().text():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dragLeaveEvent(self, event):
        self.drop_indicator.hide()

    def dragMoveEvent(self, event: QDragMoveEvent):
        pos = self.content_widget.mapFrom(self, event.position().toPoint())
        
        # Parse the unified text format to determine drag type
        mime_text = event.mimeData().text()
        drag_type, _ = mime_text.split(":", 1)

        indicator_pos = None
        if drag_type == "card":
            self.drop_indicator.setFrameShape(QFrame.Shape.VLine)
            _, _, indicator_pos = self._find_card_drop_pos(pos)
        elif drag_type == "group":
            self.drop_indicator.setFrameShape(QFrame.Shape.HLine)
            _, indicator_pos = self._find_group_drop_pos(pos)
        
        if indicator_pos:
            self.drop_indicator.setGeometry(indicator_pos)
            self.drop_indicator.show()
            event.accept()
        else:
            self.drop_indicator.hide()
            event.ignore()

    def dropEvent(self, event: QDropEvent):
        self.drop_indicator.hide()
        if not event.mimeData().hasText():
            event.ignore()
            return

        # Parse the unified text format
        pos = self.content_widget.mapFrom(self, event.position().toPoint())
        mime_text = event.mimeData().text()
        drag_type, source_id = mime_text.split(":", 1)

        if drag_type == "card":
            target_group_id, target_index, _ = self._find_card_drop_pos(pos)
            if target_group_id is not None:
                self.program_dropped.emit(source_id, target_group_id, target_index)
                event.acceptProposedAction()
            else:
                event.ignore()
        elif drag_type == "group":
            target_index, _ = self._find_group_drop_pos(pos)
            group_ids = list(self.group_headers.keys())
            if source_id in group_ids:
                group_ids.remove(source_id)
                if target_index > len(group_ids):
                    target_index = len(group_ids)
                group_ids.insert(target_index, source_id)
                self.group_order_changed.emit(group_ids)
                event.acceptProposedAction()
            else:
                event.ignore()
        else:
            event.ignore()

    def _find_card_drop_pos(self, pos_in_content: QPoint):
        # First, determine which group the cursor is over.
        target_group_id = None
        for gid, header in self.group_headers.items():
            container = self.card_containers[gid]
            # Consider the entire area of the group (header + container)
            group_rect = header.geometry().united(container.geometry())
            if group_rect.contains(pos_in_content):
                target_group_id = gid
                break
        
        if target_group_id is None:
            return None, -1, None

        # Now, find the exact position within that target group.
        container = self.card_containers[target_group_id]
        layout = container.layout()
        local_pos = container.mapFrom(self.content_widget, pos_in_content)
        
        target_index = 0
        # Find the correct insertion index based on horizontal position
        for i in range(layout.count()):
            widget = layout.itemAt(i).widget()
            if not isinstance(widget, CardWidget): continue
            if local_pos.x() < widget.geometry().center().x():
                break
            target_index = i + 1

        # Calculate the visual indicator's position
        rect = QRect()
        card_widgets_exist = any(isinstance(layout.itemAt(i).widget(), CardWidget) for i in range(layout.count()))

        if not card_widgets_exist:
            # If the group is empty, place indicator at the start.
            rect.setRect(5, 5, 2, 80)
        elif target_index < layout.count():
            # Place indicator before the target widget.
            widget = layout.itemAt(target_index).widget()
            if isinstance(widget, CardWidget):
                rect.setRect(widget.x() - 5, widget.y(), 2, widget.height())
        else:
            # Place indicator at the end of the last widget.
            last_card = None
            for i in range(layout.count() - 1, -1, -1):
                widget = layout.itemAt(i).widget()
                if isinstance(widget, CardWidget):
                    last_card = widget
                    break
            if last_card:
                rect.setRect(last_card.x() + last_card.width() + 3, last_card.y(), 2, last_card.height())

        if not rect.isNull():
            final_rect = QRect(container.mapTo(self.content_widget, rect.topLeft()), rect.size())
            return target_group_id, target_index, final_rect
            
        return target_group_id, 0, QRect(container.mapTo(self.content_widget, QPoint(5,5)), QSize(2,80))

    def _find_group_drop_pos(self, pos_in_content: QPoint):
        target_index = 0
        for i, (gid, header) in enumerate(self.group_headers.items()):
            container = self.card_containers[gid]
            group_rect = header.geometry().united(container.geometry())
            if pos_in_content.y() < group_rect.center().y(): break
            target_index = i + 1
        rect = QRect()
        if not self.group_headers: return target_index, None
        if target_index < len(self.group_headers):
            header = list(self.group_headers.values())[target_index]
            rect.setRect(header.x(), header.y() - 5, self.content_widget.width() - 20, 2)
        else:
            last_header = list(self.group_headers.values())[-1]
            last_container = self.card_containers[list(self.group_headers.keys())[-1]]
            rect.setRect(last_header.x(), last_container.y() + last_container.height() + 5, self.content_widget.width() - 20, 2)
        return target_index, rect