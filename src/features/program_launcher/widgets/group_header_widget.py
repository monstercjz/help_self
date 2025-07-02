# desktop_center/src/features/program_launcher/widgets/group_header_widget.py
from PySide6.QtWidgets import QWidget, QHBoxLayout, QLabel
from PySide6.QtGui import QMouseEvent, QContextMenuEvent, QDrag, QPixmap
from PySide6.QtCore import Qt, Signal, QMimeData

class GroupHeaderWidget(QWidget):
    """
    一个可交互的分组标题控件，支持右键菜单和拖拽。
    """
    customContextMenuRequested = Signal(str, QContextMenuEvent)

    def __init__(self, group_data: dict, parent=None):
        super().__init__(parent)
        self.group_id = group_data.get('id')
        self.drag_start_position = None
        
        self.setCursor(Qt.CursorShape.OpenHandCursor)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 0, 5, 0)
        
        self.title_label = QLabel(f"<b>{group_data.get('name', '')}</b>")
        self.title_label.setStyleSheet("padding: 15px 0 8px 0; font-size: 14px; border-bottom: 1px solid #e0e0e0;")
        
        layout.addWidget(self.title_label)
        
    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_start_position = event.position().toPoint()
            self.setCursor(Qt.CursorShape.ClosedHandCursor)
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent):
        self.setCursor(Qt.CursorShape.OpenHandCursor)
        super().mouseReleaseEvent(event)
        
    def mouseMoveEvent(self, event: QMouseEvent):
        if not (event.buttons() & Qt.MouseButton.LeftButton): return
        if not self.drag_start_position or (event.position().toPoint() - self.drag_start_position).manhattanLength() < 10: return

        drag = QDrag(self)
        mime_data = QMimeData()
        mime_data.setData("application/x-program-launcher-group", self.group_id.encode('utf-8'))
        drag.setMimeData(mime_data)

        pixmap = self.grab()
        drag.setPixmap(pixmap)
        drag.setHotSpot(event.position().toPoint())
        
        # 【核心修复】不再隐藏源控件，让数据驱动刷新来处理UI变化
        # self.hide()
        drag.exec(Qt.DropAction.MoveAction)
        # if drag.exec(...) == Qt.DropAction.IgnoreAction:
        #     self.show()

    def contextMenuEvent(self, event: QContextMenuEvent):
        self.customContextMenuRequested.emit(self.group_id, event)
        super().contextMenuEvent(event)