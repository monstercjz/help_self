# desktop_center/src/features/program_launcher/widgets/pill_widget.py
from PySide6.QtWidgets import QWidget, QHBoxLayout, QLabel, QFrame
from PySide6.QtGui import QIcon, QMouseEvent, QContextMenuEvent, QDrag, QPixmap, QPainter
from PySide6.QtCore import Qt, Signal, QSize, QMimeData

class PillWidget(QFrame):
    """
    一个“药丸”或“标签”样式的控件，用于在网格布局中显示单个程序。
    【变更】尺寸由外部动态计算并传入，不再使用内部固定的宽度。
    """
    doubleClicked = Signal(str)
    customContextMenuRequested = Signal(str, QContextMenuEvent)

    def __init__(self, program_data: dict, icon: QIcon, fixed_size: QSize, parent=None):
        super().__init__(parent)
        self.setObjectName("PillWidget")
        self.program_id = program_data.get('id')
        self.program_data = program_data
        self.drag_start_position = None
        
        # 【核心变更】应用由外部计算得出的固定尺寸
        self.setFixedSize(fixed_size)
        self.setToolTip(program_data.get('path', ''))

        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 5, 10, 5)
        layout.setSpacing(8)

        self.icon_label = QLabel()
        self.icon_label.setPixmap(icon.pixmap(QSize(16, 16)))
        self.icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.name_label = QLabel(program_data.get('name', ''))
        self.name_label.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)

        layout.addWidget(self.icon_label)
        layout.addWidget(self.name_label)
        layout.addStretch(1)

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_start_position = event.position().toPoint()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent):
        if not (event.buttons() & Qt.MouseButton.LeftButton): return
        if not self.drag_start_position or (event.position().toPoint() - self.drag_start_position).manhattanLength() < 10: return

        drag = QDrag(self)
        mime_data = QMimeData()
        mime_data.setText(f"card:{self.program_id}")
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

    def mouseDoubleClickEvent(self, event: QMouseEvent):
        self.doubleClicked.emit(self.program_id)
        super().mouseDoubleClickEvent(event)
        
    def contextMenuEvent(self, event: QContextMenuEvent):
        self.customContextMenuRequested.emit(self.program_id, event)
        super().contextMenuEvent(event)