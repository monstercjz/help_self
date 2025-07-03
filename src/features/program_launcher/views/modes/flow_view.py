# desktop_center/src/features/program_launcher/views/modes/flow_view.py
import logging
import math
from PySide6.QtWidgets import QVBoxLayout, QLabel, QWidget, QScrollArea, QFrame, QGridLayout
from PySide6.QtGui import QDragEnterEvent, QDropEvent, QDragMoveEvent, QShowEvent
from PySide6.QtCore import Qt, QPoint, QRect, QSize

from .base_view import BaseViewMode
from ...widgets.pill_widget import PillWidget
from ...widgets.flow_group_header_widget import FlowGroupHeaderWidget
from ...services.icon_service import icon_service
from ...widgets.menu_factory import MenuFactory

class FlowViewMode(BaseViewMode):
    """
    【重构】网格视图模式，以固定的4列网格展示程序，采用与IconViewMode一致的健壮布局策略。
    """
    COLUMNS = 4
    MAIN_SPACING = 15
    GROUP_PADDING = 15
    PILL_H_SPACING = 10
    PILL_V_SPACING = 10
    PILL_ASPECT_RATIO = 0.25
    # 【新增】用于水平居中的边距常量
    HORIZONTAL_MARGIN = 16

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("FlowViewMode")
        
        self.data_cache = {}
        self._calculated_pill_size = QSize(160, 40)
        # 【新增】存储分组卡片的固定宽度
        self._calculated_group_block_width = 0
        self._initial_show_done = False 

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QScrollArea.Shape.NoFrame)
        
        self.content_widget = QWidget()
        self.setAcceptDrops(True)
        
        self.view_layout = QVBoxLayout(self.content_widget)
        self.view_layout.setSpacing(self.MAIN_SPACING)
        self.view_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        # 【新增】为父布局增加边距，以便内容可以居中
        self.view_layout.setContentsMargins(self.HORIZONTAL_MARGIN, 10, self.HORIZONTAL_MARGIN, 10)
        
        self.scroll_area.setWidget(self.content_widget)
        main_layout.addWidget(self.scroll_area)
        
        self.drop_indicator = QFrame(self.content_widget)
        self.drop_indicator.setObjectName("dropIndicator")
        self.drop_indicator.hide()

    def showEvent(self, event: QShowEvent):
        super().showEvent(event)
        if not self._initial_show_done:
            logging.info("FlowViewMode is being shown for the first time. Triggering layout calculation.")
            self._initial_show_done = True
            self._recalculate_sizes()
            self.update_view(self.data_cache)

    def _recalculate_sizes(self):
        viewport_width = self.scroll_area.viewport().width()
        content_padding = self.view_layout.contentsMargins().left() + self.view_layout.contentsMargins().right()
        available_width = viewport_width - content_padding

        # 【核心修复】计算逻辑调整
        # 1. 计算 PillWidget 的尺寸
        pill_width = (available_width - (self.COLUMNS - 1) * self.PILL_H_SPACING) / self.COLUMNS
        pill_height = pill_width * self.PILL_ASPECT_RATIO
        self._calculated_pill_size = QSize(int(pill_width), int(pill_height))
        logging.info(f"FlowViewMode calculated pill size: {self._calculated_pill_size}")

        # 2. 基于 PillWidget 的尺寸，反向计算出 GroupBlock 的固定宽度
        group_block_internal_width = (self._calculated_pill_size.width() * self.COLUMNS) + \
                                     (self.PILL_H_SPACING * (self.COLUMNS - 1))
        self._calculated_group_block_width = group_block_internal_width + (self.GROUP_PADDING * 2)
        logging.info(f"FlowViewMode calculated group block fixed width: {self._calculated_group_block_width}")


    def update_view(self, data: dict):
        self.data_cache = data
        if not self._initial_show_done:
            return

        while self.view_layout.count():
            item = self.view_layout.takeAt(0)
            if item and item.widget():
                item.widget().deleteLater()

        groups = data.get("groups", [])
        programs = data.get("programs", {})
        
        programs_by_group = {group['id']: [] for group in groups}
        for prog_id, prog_data in programs.items():
            group_id = prog_data.get('group_id')
            if group_id in programs_by_group:
                programs_by_group[group_id].append(prog_data)
        
        for group_id in programs_by_group:
            programs_by_group[group_id].sort(key=lambda p: p.get("order", 0))

        self.group_widgets_map = {}
        
        for group_data in groups:
            group_id = group_data['id']
            
            group_block = QFrame()
            group_block.setObjectName("FlowGroupBlock")
            # 【核心修复】为分组卡片设置固定的宽度
            group_block.setFixedWidth(self._calculated_group_block_width)
            
            group_block_layout = QVBoxLayout(group_block)
            group_block_layout.setContentsMargins(self.GROUP_PADDING, self.GROUP_PADDING, self.GROUP_PADDING, self.GROUP_PADDING)
            group_block_layout.setSpacing(15)

            group_title = FlowGroupHeaderWidget(group_data)
            group_block_layout.addWidget(group_title)

            pills_container = QWidget()
            pills_container.setObjectName(f"pills_container_{group_id}")
            grid_layout = QGridLayout(pills_container)
            grid_layout.setHorizontalSpacing(self.PILL_H_SPACING)
            grid_layout.setVerticalSpacing(self.PILL_V_SPACING)
            
            self.group_widgets_map[group_id] = (group_title, pills_container)
            
            programs_in_group = programs_by_group.get(group_id, [])
            if not programs_in_group:
                empty_label = QLabel("(此分组为空)")
                empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                empty_label.setObjectName("emptyGroupLabel")
                grid_layout.addWidget(empty_label, 0, 0, 1, self.COLUMNS)
            else:
                row, col = 0, 0
                for prog_data in programs_in_group:
                    icon = icon_service.get_program_icon(prog_data['path'])
                    pill = PillWidget(prog_data, icon, self._calculated_pill_size)
                    pill.doubleClicked.connect(self.item_double_clicked)
                    pill.customContextMenuRequested.connect(self._on_pill_context_menu)
                    grid_layout.addWidget(pill, row, col)
                    col += 1
                    if col >= self.COLUMNS:
                        col = 0
                        row += 1

            group_block_layout.addWidget(pills_container)
            # 添加到主布局，并设置居中对齐
            self.view_layout.addWidget(group_block, 0, Qt.AlignmentFlag.AlignHCenter)
        
        self.view_layout.addStretch(1)

    # ... 其他所有方法 (_on_pill_context_menu, drag/drop events etc.) 保持不变 ...
    def _on_pill_context_menu(self, program_id, event):
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
        pos_in_content = self.content_widget.mapFrom(self, event.position().toPoint())
        mime_text = event.mimeData().text()
        drag_type, _ = mime_text.split(":", 1)

        indicator_rect = None
        if drag_type == "card":
            _, _, indicator_rect = self._find_pill_drop_pos(pos_in_content)
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
        if not event.mimeData().hasText(): event.ignore(); return

        pos_in_content = self.content_widget.mapFrom(self, event.position().toPoint())
        mime_text = event.mimeData().text()
        drag_type, source_id = mime_text.split(":", 1)

        if drag_type == "card": 
            target_group_id, target_index, _ = self._find_pill_drop_pos(pos_in_content)
            if target_group_id is not None:
                self.program_dropped.emit(source_id, target_group_id, target_index)
                event.acceptProposedAction()
                return

        elif drag_type == "group":
            target_index, _ = self._find_group_drop_pos(pos_in_content)
            group_ids = [self.view_layout.itemAt(i).widget().findChild(FlowGroupHeaderWidget).group_id
                         for i in range(self.view_layout.count())
                         if self.view_layout.itemAt(i).widget() and self.view_layout.itemAt(i).widget().objectName() == "FlowGroupBlock"]

            if source_id in group_ids:
                group_ids.remove(source_id)
                if target_index > len(group_ids):
                    target_index = len(group_ids)
                group_ids.insert(target_index, source_id)
                
                self.group_order_changed.emit(group_ids)
                event.acceptProposedAction()
                return
        
        event.ignore()

    def _find_group_drop_pos(self, pos: QPoint) -> tuple[int, QRect | None]:
        target_index = 0
        min_dist = float('inf')
        
        group_blocks = [self.view_layout.itemAt(i).widget() 
                        for i in range(self.view_layout.count()) 
                        if self.view_layout.itemAt(i).widget() and self.view_layout.itemAt(i).widget().objectName() == "FlowGroupBlock"]
        
        if not group_blocks: return 0, None

        for i, widget in enumerate(group_blocks):
            dist = abs(pos.y() - widget.geometry().center().y())
            if dist < min_dist:
                min_dist = dist
                target_index = i
        
        widget = group_blocks[target_index]
        g = widget.geometry()
        
        self.drop_indicator.setFrameShape(QFrame.Shape.HLine)
        self.drop_indicator.setLineWidth(2)
        
        if pos.y() < g.center().y():
            return target_index, QRect(g.x(), g.y() - 6, g.width(), 2)
        else:
            return target_index + 1, QRect(g.x(), g.bottom() + 6, g.width(), 2)

    def _find_pill_drop_pos(self, pos: QPoint) -> tuple[str | None, int, QRect | None]:
        target_widget = self.content_widget.childAt(pos)
        if not target_widget: return None, -1, None

        pills_container = target_widget
        while pills_container:
            if pills_container.objectName().startswith("pills_container_"):
                break
            pills_container = pills_container.parentWidget()
        
        if not pills_container: return None, -1, None
            
        group_id = pills_container.objectName().split("_")[-1]
        grid_layout = pills_container.layout()
        
        cell_width = self._calculated_pill_size.width() + grid_layout.horizontalSpacing()
        cell_height = self._calculated_pill_size.height() + grid_layout.verticalSpacing()
        
        local_pos = pills_container.mapFrom(self.content_widget, pos)
        row = math.floor(local_pos.y() / cell_height) if cell_height > 0 else 0
        col = math.floor(local_pos.x() / cell_width) if cell_width > 0 else 0
        
        col = max(0, min(col, self.COLUMNS - 1))

        target_index = row * self.COLUMNS + col
        
        card_count = sum(1 for i in range(grid_layout.count()) if isinstance(grid_layout.itemAt(i).widget(), PillWidget))
        if target_index > card_count:
            target_index = card_count

        self.drop_indicator.setFrameShape(QFrame.Shape.VLine)
        self.drop_indicator.setLineWidth(2)

        item_at_index = grid_layout.itemAtPosition(row, col)
        if not item_at_index and target_index == card_count and card_count > 0:
            # 拖到行末尾
            item_at_index = grid_layout.itemAt(card_count - 1)

        if item_at_index and item_at_index.widget():
            widget = item_at_index.widget()
            g = widget.geometry()
            if local_pos.x() < g.center().x():
                final_pos = pills_container.mapTo(self.content_widget, QPoint(g.x() - 5, g.y()))
                return group_id, target_index, QRect(final_pos, QSize(2, g.height()))
            else:
                final_pos = pills_container.mapTo(self.content_widget, QPoint(g.right() + 5, g.y()))
                return group_id, target_index + 1, QRect(final_pos, QSize(2, g.height()))
        else:
            return group_id, target_index, QRect(pills_container.mapTo(self.content_widget, QPoint(5, 5)), QSize(2, 20))