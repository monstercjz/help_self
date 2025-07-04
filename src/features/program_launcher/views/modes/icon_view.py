# desktop_center/src/features/program_launcher/views/modes/icon_view.py
import logging
import math
from PySide6.QtWidgets import (QVBoxLayout, QLabel, QWidget, QScrollArea, QFrame, QGridLayout)
from PySide6.QtGui import QDragEnterEvent, QDropEvent, QDragMoveEvent, QShowEvent
from PySide6.QtCore import Qt, QPoint, QRect, QSize

from .base_view import BaseViewMode
from ...widgets.card_widget import CardWidget
from ...services.icon_service import icon_service
from ...widgets.menu_factory import MenuFactory
from ...widgets.group_container_widget import GroupContainerWidget

class IconViewMode(BaseViewMode):
    # --- 布局常量 ---
    COLUMNS = 2 
    GROUP_INTERNAL_COLUMNS = 3
    MAIN_SPACING = 16
    # 【变更】定义外边距常量
    HORIZONTAL_MARGIN = 16
    GROUP_PADDING = 12
    CARD_SPACING = 10
    CARD_ASPECT_RATIO = 1.0

    def __init__(self, parent=None):
        super().__init__(parent)
        self.group_containers = {}
        self.data_cache = {}
        self._calculated_group_width = 0
        self._calculated_card_size = QSize(90, 90)
        self._initial_show_done = False 

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QScrollArea.Shape.NoFrame)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        self.content_widget = QWidget()
        self.content_widget.setAcceptDrops(True)
        
        self.content_layout = QGridLayout(self.content_widget)
        self.content_layout.setSpacing(self.MAIN_SPACING)
        # 【核心变更】设置内容布局的内外边距，以增加边缘的留白
        self.content_layout.setContentsMargins(self.HORIZONTAL_MARGIN, 0, self.HORIZONTAL_MARGIN, 0)
        self.content_layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter)
        
        self.scroll_area.setWidget(self.content_widget)
        main_layout.addWidget(self.scroll_area)

        self.drop_indicator = QFrame(self.content_widget)
        self.drop_indicator.setFrameShape(QFrame.Shape.VLine)
        self.drop_indicator.setLineWidth(3)
        self.drop_indicator.setObjectName("dropIndicator")
        self.drop_indicator.hide()

        self.setAcceptDrops(True)

    def showEvent(self, event: QShowEvent):
        """
        在控件首次显示时，根据viewport宽度计算并固定所有尺寸，然后触发渲染。
        这是比 resizeEvent 更可靠的触发点。
        """
        super().showEvent(event)
        if not self._initial_show_done:
            logging.info("IconViewMode is being shown for the first time. Triggering layout calculation and rendering.")
            self._initial_show_done = True
            self._recalculate_sizes()
            self._render_view()

    def _recalculate_sizes(self):
        """
        核心计算方法：根据viewport宽度，自顶向下计算并设定所有组件的固定尺寸。
        """
        # 宽度计算现在作用于减去了左右边距的可用空间
        viewport_width = self.scroll_area.viewport().width()
        logging.info(f"Calculating sizes based on viewport width: {viewport_width}px")

        # 布局会自动处理边距，所以这里的计算基于完整的viewport宽度
        # QGridLayout会从其内容矩形(contentRect)中分配空间，该矩形已排除了边距
        group_width = (viewport_width - 
                       (self.HORIZONTAL_MARGIN * 2) - 
                       (self.COLUMNS - 1) * self.MAIN_SPACING) / self.COLUMNS
                       
        self._calculated_group_width = int(group_width)
        logging.info(f"Calculated GroupContainer fixed width: {self._calculated_group_width}px")

        internal_content_width = self._calculated_group_width - (2 * self.GROUP_PADDING)
        card_width = (internal_content_width - (self.GROUP_INTERNAL_COLUMNS - 1) * self.CARD_SPACING) / self.GROUP_INTERNAL_COLUMNS
        card_height = card_width / self.CARD_ASPECT_RATIO
        self._calculated_card_size = QSize(int(card_width), int(card_height))
        logging.info(f"Calculated CardWidget fixed size: {self._calculated_card_size.width()}x{self._calculated_card_size.height()}px")
        
    def update_view(self, data: dict):
        """
        接收新数据，缓存它，并且只有在初始化完成后才立即渲染。
        """
        self.data_cache = data
        if self._initial_show_done:
            logging.info("View is already initialized, re-rendering with new data.")
            self._render_view()

    def _render_view(self):
        """
        真正的渲染方法，使用缓存的数据和计算好的尺寸来构建UI。
        """
        self.group_containers.clear()
        while self.content_layout.count():
            child = self.content_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        groups = self.data_cache.get("groups", [])
        programs = self.data_cache.get("programs", {})
        
        programs_by_group = {group['id']: [] for group in groups}
        for prog_id, prog_data in programs.items():
            group_id = prog_data.get('group_id')
            if group_id in programs_by_group:
                programs_by_group[group_id].append(prog_data)
        
        for group_id in programs_by_group:
            programs_by_group[group_id].sort(key=lambda p: p.get("order", 0))

        row, col = 0, 0
        for group_data in groups:
            group_id = group_data['id']
            container = GroupContainerWidget(group_data, fixed_width=self._calculated_group_width)
            self.group_containers[group_id] = container
            
            container.header_widget.customContextMenuRequested.connect(self._on_group_context_menu)
            
            programs_in_group = programs_by_group.get(group_id, [])
            if not programs_in_group:
                empty_label = QLabel("(此分组为空)")
                empty_label.setStyleSheet("color: #999; padding: 10px;")
                container.add_card(empty_label, self.CARD_SPACING)
            else:
                for prog_data in programs_in_group:
                    icon = icon_service.get_program_icon(prog_data['path'])
                    card = CardWidget(prog_data, icon, fixed_size=self._calculated_card_size)
                    card.doubleClicked.connect(self.item_double_clicked)
                    card.customContextMenuRequested.connect(self._on_card_context_menu)
                    container.add_card(card, self.CARD_SPACING)
            
            self.content_layout.addWidget(container, row, col)
            col += 1
            if col >= self.COLUMNS:
                col = 0
                row += 1
        
        self.content_layout.setRowStretch(self.content_layout.rowCount(), 1)


    def _on_card_context_menu(self, program_id, event):
        menu = MenuFactory.create_context_menu('program', program_id, self)
        menu.exec_(event.globalPos())

    def _on_group_context_menu(self, group_id, event):
        menu = MenuFactory.create_context_menu('group', group_id, self)
        menu.exec_(event.globalPos())

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasText() and ":" in event.mimeData().text():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dragLeaveEvent(self, event):
        self.drop_indicator.hide()

    def dragMoveEvent(self, event: QDragMoveEvent):
        pos_in_content = event.position().toPoint()
        mime_text = event.mimeData().text()
        drag_type, _ = mime_text.split(":", 1)

        indicator_rect = None
        if drag_type == "card":
            _, _, indicator_rect = self._find_card_drop_pos(pos_in_content)
        elif drag_type == "group":
            _, indicator_rect = self._find_group_drop_pos(pos_in_content)
        
        if indicator_rect:
            self.drop_indicator.setGeometry(indicator_rect)
            self.drop_indicator.show()
            event.accept()
        else:
            self.drop_indicator.hide()
            event.ignore()

    def dropEvent(self, event: QDropEvent):
        self.drop_indicator.hide()
        if not event.mimeData().hasText():
            event.ignore(); return

        pos = event.position().toPoint()
        mime_text = event.mimeData().text()
        drag_type, source_id = mime_text.split(":", 1)

        if drag_type == "card":
            target_group_id, target_index, _ = self._find_card_drop_pos(pos)
            if target_group_id is not None:
                self.program_dropped.emit(source_id, target_group_id, target_index)
                event.acceptProposedAction()
        elif drag_type == "group":
            target_index, _ = self._find_group_drop_pos(pos)
            
            group_ids = [self.content_layout.itemAt(i).widget().group_id for i in range(self.content_layout.count()) if self.content_layout.itemAt(i) and self.content_layout.itemAt(i).widget()]

            if source_id in group_ids:
                group_ids.remove(source_id)
                if target_index > len(group_ids): target_index = len(group_ids)
                group_ids.insert(target_index, source_id)
                self.group_order_changed.emit(group_ids)
                event.acceptProposedAction()
        
        event.ignore()

    def _find_card_drop_pos(self, pos: QPoint) -> tuple[str | None, int, QRect | None]:
        target_container = self.content_widget.childAt(pos)
        while target_container and not isinstance(target_container, GroupContainerWidget):
            target_container = target_container.parentWidget()
        
        if not target_container: return None, -1, None

        layout = target_container.card_layout
        local_pos = target_container.card_container.mapFrom(self.content_widget, pos)

        if not layout or layout.count() == 0 or not isinstance(layout.itemAt(0).widget(), CardWidget):
            rect = QRect(0, 0, 3, self._calculated_card_size.height())
            final_rect_pos = target_container.card_container.mapTo(self.content_widget, rect.topLeft())
            final_rect = QRect(final_rect_pos, rect.size())
            return target_container.group_id, 0, final_rect

        cell_width = self._calculated_card_size.width() + layout.horizontalSpacing()
        cell_height = self._calculated_card_size.height() + layout.verticalSpacing()
        
        row = math.floor(local_pos.y() / cell_height) if cell_height > 0 else 0
        col = math.floor(local_pos.x() / cell_width) if cell_width > 0 else 0
        
        target_index = row * self.GROUP_INTERNAL_COLUMNS + col
        
        card_count = sum(1 for i in range(layout.count()) if isinstance(layout.itemAt(i).widget(), CardWidget))
        if target_index > card_count:
            target_index = card_count

        rect = QRect()
        if target_index < card_count:
            item = layout.itemAt(target_index)
            if item and item.widget():
                widget = item.widget()
                rect.setRect(widget.x() - 5, widget.y(), 3, widget.height())
        else:
            if card_count > 0:
                item = layout.itemAt(card_count - 1)
                if item and item.widget():
                    widget = item.widget()
                    rect.setRect(widget.x() + widget.width() + 5, widget.y(), 3, widget.height())
            else: # Fallback for empty group
                rect.setRect(self.GROUP_PADDING, self.GROUP_PADDING, 3, self._calculated_card_size.height())


        if rect.isNull():
            return target_container.group_id, target_index, None

        final_rect_pos = target_container.card_container.mapTo(self.content_widget, rect.topLeft())
        final_rect = QRect(final_rect_pos, rect.size())

        return target_container.group_id, target_index, final_rect

    def _find_group_drop_pos(self, pos: QPoint) -> tuple[int, QRect | None]:
        target_index = 0
        min_dist = float('inf')
        
        if self.content_layout.count() == 0:
            return 0, None

        for i in range(self.content_layout.count()):
            item = self.content_layout.itemAt(i)
            if item and item.widget():
                dist = (pos - item.geometry().center()).manhattanLength()
                if dist < min_dist:
                    min_dist = dist
                    target_index = i
        
        rect = QRect()
        item = self.content_layout.itemAt(target_index)
        if item and item.widget():
            g = item.geometry()
            if pos.x() < g.center().x():
                rect.setRect(g.x() - 8, g.y(), 3, g.height())
            else:
                rect.setRect(g.right() + 5, g.y(), 3, g.height())
                target_index += 1

        return target_index, rect