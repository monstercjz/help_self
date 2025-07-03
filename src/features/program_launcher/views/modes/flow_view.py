# desktop_center/src/features/program_launcher/views/modes/flow_view.py
import logging
from PySide6.QtWidgets import QVBoxLayout, QLabel, QWidget, QScrollArea, QFrame
from PySide6.QtGui import QDragEnterEvent, QDropEvent, QDragMoveEvent
from PySide6.QtCore import Qt, QPoint, QRect, QSize

from .base_view import BaseViewMode
from .flow_layout import FlowLayout
from ...widgets.pill_widget import PillWidget
from ...widgets.flow_group_header_widget import FlowGroupHeaderWidget
from ...services.icon_service import icon_service
from ...widgets.menu_factory import MenuFactory

class FlowViewMode(BaseViewMode):
    """
    流式视图模式，以“标签云”的形式展示程序，并支持完整的拖放和右键菜单交互。
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("FlowViewMode")
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QScrollArea.Shape.NoFrame)
        
        self.content_widget = QWidget()
        self.setAcceptDrops(True)
        
        self.view_layout = QVBoxLayout(self.content_widget)
        self.view_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        scroll_area.setWidget(self.content_widget)
        main_layout.addWidget(scroll_area)
        
        self.drop_indicator = QFrame(self.content_widget)
        self.drop_indicator.setObjectName("dropIndicator")
        self.drop_indicator.hide()

    def update_view(self, data: dict):
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
            
            # 【核心变更】创建分组的总容器
            group_block = QFrame()
            group_block.setObjectName("FlowGroupBlock")
            group_block_layout = QVBoxLayout(group_block)
            group_block_layout.setContentsMargins(0,0,0,0)
            group_block_layout.setSpacing(15) # 标题和内容区的间距

            group_title = FlowGroupHeaderWidget(group_data)
            group_block_layout.addWidget(group_title)

            pills_container = QWidget()
            pills_container.setObjectName(f"pills_container_{group_id}")
            flow_layout = FlowLayout(pills_container, margin=0, h_spacing=10, v_spacing=10)
            
            self.group_widgets_map[group_id] = (group_title, pills_container)
            
            programs_in_group = programs_by_group.get(group_id, [])
            if not programs_in_group:
                empty_label = QLabel("(此分组为空)")
                # 【变更】为美化做准备，设置对齐和对象名
                empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                empty_label.setObjectName("emptyGroupLabel")
                flow_layout.addWidget(empty_label)
            else:
                for prog_data in programs_in_group:
                    icon = icon_service.get_program_icon(prog_data['path'])
                    pill = PillWidget(prog_data, icon)
                    pill.doubleClicked.connect(self.item_double_clicked)
                    pill.customContextMenuRequested.connect(self._on_pill_context_menu)
                    flow_layout.addWidget(pill)

            group_block_layout.addWidget(pills_container)
            self.view_layout.addWidget(group_block)
        
        self.view_layout.addStretch(1)

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
                         if isinstance(self.view_layout.itemAt(i).widget(), QFrame)]

            if source_id in group_ids:
                group_ids.remove(source_id)
                if target_index > len(group_ids):
                    target_index = len(group_ids)
                group_ids.insert(target_index, source_id)
                
                logging.info(f"[FlowView] Emitting group_order_changed with new order: {group_ids}")
                self.group_order_changed.emit(group_ids)
                event.acceptProposedAction()
                return
        
        event.ignore()

    def _find_group_drop_pos(self, pos: QPoint) -> tuple[int, QRect | None]:
        target_index = 0
        min_dist = float('inf')
        
        # 【变更】查找 FlowGroupBlock
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
        local_pos = pills_container.mapFrom(self.content_widget, pos)
        pills = [child for child in pills_container.children() if isinstance(child, PillWidget)]
        
        if not pills:
             return group_id, 0, QRect(pills_container.mapTo(self.content_widget, QPoint(10, 5)), QSize(2, 20))

        target_index = 0
        min_dist = float('inf')

        for i, pill in enumerate(pills):
            center = pill.geometry().center()
            dist = (local_pos - center).manhattanLength()
            if dist < min_dist:
                min_dist = dist
                target_index = i
        
        pill = pills[target_index]
        g = pill.geometry()
        
        self.drop_indicator.setFrameShape(QFrame.Shape.VLine)
        self.drop_indicator.setLineWidth(2)

        if local_pos.x() < g.center().x():
            final_pos = pills_container.mapTo(self.content_widget, QPoint(g.x() - 5, g.y()))
            return group_id, target_index, QRect(final_pos, QSize(2, g.height()))
        else:
            final_pos = pills_container.mapTo(self.content_widget, QPoint(g.right() + 5, g.y()))
            return group_id, target_index + 1, QRect(final_pos, QSize(2, g.height()))