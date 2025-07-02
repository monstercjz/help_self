# desktop_center/src/features/program_launcher/views/modes/icon_view.py
import logging
from PySide6.QtWidgets import (QFileIconProvider, QVBoxLayout,
                               QLabel, QWidget, QScrollArea, QFrame)
from PySide6.QtGui import QIcon, QDragEnterEvent, QDropEvent, QDragMoveEvent
from PySide6.QtCore import Qt, QFileInfo, QSize, QPoint, QRect

from .base_view import BaseViewMode
from ...widgets.card_widget import CardWidget
from ...widgets.group_header_widget import GroupHeaderWidget
from ...services.icon_service import icon_service
from ...widgets.menu_factory import MenuFactory
from .flow_layout import FlowLayout

class IconViewMode(BaseViewMode):
    def __init__(self, parent=None):
        super().__init__(parent)
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
                    icon = icon_service.get_program_icon(prog_data['path'])
                    card = CardWidget(prog_data, icon)
                    card.doubleClicked.connect(self.item_double_clicked)
                    card.customContextMenuRequested.connect(self._on_card_context_menu)
                    flow_layout.addWidget(card)
            
            self.content_layout.addWidget(card_container)
        self.content_layout.addStretch()

    def _on_card_context_menu(self, program_id, event):
        menu = MenuFactory.create_context_menu('program', program_id, self)
        menu.exec_(event.globalPos())

    def _on_group_context_menu(self, group_id, event):
        menu = MenuFactory.create_context_menu('group', group_id, self)
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

    def _find_card_drop_pos(self, pos_in_content: QPoint) -> tuple[str | None, int, QRect | None]:
        """
        计算程序卡片(Card)的拖放目标位置。

        这个方法实现了两个核心功能：
        1. 确定鼠标指针当前悬停在哪个分组的区域上。
        2. 在确定了目标分组后，计算出卡片应该插入到该分组的哪个索引位置。

        Args:
            pos_in_content: 鼠标指针在 content_widget 坐标系中的位置。

        Returns:
            一个元组 (target_group_id, target_index, indicator_rect)。
            如果找不到有效的目标位置，则返回 (None, -1, None)。
        """
        # 步骤1: 确定鼠标悬停在哪个分组的整体区域上
        target_group_id = None
        for gid, header in self.group_headers.items():
            container = self.card_containers[gid]
            # 将分组标题和其内容容器的矩形区域合并，作为该分组的完整响应区域
            group_rect = header.geometry().united(container.geometry())
            if group_rect.contains(pos_in_content):
                target_group_id = gid
                break
        
        if target_group_id is None:
            return None, -1, None

        # 步骤2: 在已确定的目标分组内，查找精确的插入索引
        container = self.card_containers[target_group_id]
        layout = container.layout()
        # 将全局坐标转换为目标容器的局部坐标
        local_pos = container.mapFrom(self.content_widget, pos_in_content)
        
        target_index = 0
        # 遍历容器内的所有控件，找到第一个中心点在鼠标指针右侧的卡片
        for i in range(layout.count()):
            widget = layout.itemAt(i).widget()
            if not isinstance(widget, CardWidget): continue
            if local_pos.x() < widget.geometry().center().x():
                break
            target_index = i + 1

        # 步骤3: 计算用于视觉反馈的指示器矩形区域
        rect = QRect()
        card_widgets_exist = any(isinstance(layout.itemAt(i).widget(), CardWidget) for i in range(layout.count()))

        if not card_widgets_exist:
            # 如果分组为空，指示器显示在最左侧
            rect.setRect(5, 5, 2, 80)
        elif target_index < layout.count():
            # 如果插入点在中间，指示器显示在目标卡片的左侧
            widget = layout.itemAt(target_index).widget()
            if isinstance(widget, CardWidget):
                rect.setRect(widget.x() - 5, widget.y(), 2, widget.height())
        else:
            # 如果插入点在末尾，指示器显示在最后一个卡片的右侧
            last_card = None
            for i in range(layout.count() - 1, -1, -1):
                widget = layout.itemAt(i).widget()
                if isinstance(widget, CardWidget):
                    last_card = widget
                    break
            if last_card:
                rect.setRect(last_card.x() + last_card.width() + 3, last_card.y(), 2, last_card.height())

        if not rect.isNull():
            # 将局部坐标系的矩形转换为 content_widget 的全局坐标系
            final_rect = QRect(container.mapTo(self.content_widget, rect.topLeft()), rect.size())
            return target_group_id, target_index, final_rect
            
        # 如果上述逻辑都失败了（例如，一个空的FlowLayout），提供一个默认的返回值
        return target_group_id, 0, QRect(container.mapTo(self.content_widget, QPoint(5,5)), QSize(2,80))

    def _find_group_drop_pos(self, pos_in_content: QPoint) -> tuple[int, QRect | None]:
        """
        计算分组(Group)的拖放目标位置。

        分组只能在垂直方向上进行重新排序。
        此方法通过判断鼠标指针的Y坐标，来确定分组应该插入到哪个现有分组的前面。

        Args:
            pos_in_content: 鼠标指针在 content_widget 坐标系中的位置。

        Returns:
            一个元组 (target_index, indicator_rect)。
        """
        target_index = 0
        # 遍历所有分组，找到第一个中心点在鼠标指针下方的分组
        for i, (gid, header) in enumerate(self.group_headers.items()):
            container = self.card_containers[gid]
            group_rect = header.geometry().united(container.geometry())
            if pos_in_content.y() < group_rect.center().y():
                break
            target_index = i + 1
            
        rect = QRect()
        if not self.group_headers:
            return 0, None
            
        if target_index < len(self.group_headers):
            # 如果插入点在中间，指示器显示在目标分组的上方
            header = list(self.group_headers.values())[target_index]
            rect.setRect(header.x(), header.y() - 5, self.content_widget.width() - 20, 2)
        else:
            # 如果插入点在末尾，指示器显示在最后一个分组的下方
            last_header = list(self.group_headers.values())[-1]
            last_container = self.card_containers[list(self.group_headers.keys())[-1]]
            rect.setRect(last_header.x(), last_container.y() + last_container.height() + 5, self.content_widget.width() - 20, 2)
            
        return target_index, rect