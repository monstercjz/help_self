# desktop_center/src/features/program_launcher/widgets/flow_group_header_widget.py
from PySide6.QtWidgets import QWidget, QHBoxLayout, QLabel
from PySide6.QtGui import QMouseEvent, QContextMenuEvent, QDrag, QPixmap, QPainter
from PySide6.QtCore import Qt, Signal, QMimeData

class FlowGroupHeaderWidget(QWidget):
    """
    一个专门用于流式布局的分组标题控件，支持拖拽和右键菜单。
    """
    customContextMenuRequested = Signal(str, QContextMenuEvent)
    
    def __init__(self, group_data: dict, parent=None):
        super().__init__(parent)
        self.setObjectName("groupTitle")
        self.group_id = group_data.get('id')
        self.drag_start_position = None
        
        self.setCursor(Qt.CursorShape.OpenHandCursor)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        self.title_label = QLabel(group_data.get('name', ''))
        self.title_label.setTextInteractionFlags(Qt.TextInteractionFlag.NoTextInteraction)
        
        layout.addWidget(self.title_label)
        layout.addStretch(1)

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_start_position = event.position().toPoint()
            self.setCursor(Qt.CursorShape.ClosedHandCursor)
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent):
        self.setCursor(Qt.CursorShape.OpenHandCursor)
        super().mouseReleaseEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent):
        if not (event.buttons() & Qt.MouseButton.LeftButton) or self.drag_start_position is None:
            return
        if (event.position().toPoint() - self.drag_start_position).manhattanLength() < 10:
            return

        # 【核心修复】将QDrag的父对象设置为父视图(self.parentWidget())，而不是自身(self)。
        # 这确保了拖放事件的上下文是整个视图，而不是单个标题控件，从而允许FlowViewMode正确处理dropEvent。
        drag = QDrag(self.parentWidget())
        mime_data = QMimeData()
        mime_data.setText(f"group:{self.group_id}")
        drag.setMimeData(mime_data)

        drag_pixmap = QPixmap(self.size())
        drag_pixmap.fill(Qt.GlobalColor.transparent)
        painter = QPainter(drag_pixmap)
        painter.setOpacity(0.7)
        painter.drawPixmap(0, 0, self.grab())
        painter.end()
        
        drag.setPixmap(drag_pixmap)
        drag.setHotSpot(event.position().toPoint())
        
        drag.exec(Qt.DropAction.MoveAction)
        self.setCursor(Qt.CursorShape.OpenHandCursor)

    def contextMenuEvent(self, event: QContextMenuEvent):
        self.customContextMenuRequested.emit(self.group_id, event)
        super().contextMenuEvent(event)