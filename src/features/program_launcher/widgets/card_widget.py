# desktop_center/src/features/program_launcher/widgets/card_widget.py
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PySide6.QtGui import QIcon, QMouseEvent, QContextMenuEvent, QDrag, QPixmap, QPainter
from PySide6.QtCore import Qt, Signal, QSize, QMimeData, QPoint

class CardWidget(QWidget):
    """
    一个独立的卡片控件，用于在图标视图中显示单个程序。
    """
    doubleClicked = Signal(str)
    customContextMenuRequested = Signal(str, QContextMenuEvent)

    def __init__(self, program_data: dict, icon: QIcon, parent=None):
        super().__init__(parent)
        self.program_id = program_data.get('id')
        self.program_data = program_data
        self.setFixedSize(100, 100)
        self.setToolTip(program_data.get('path', ''))
        self.drag_start_position = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 10, 5, 10)
        layout.setSpacing(5)

        self.icon_label = QLabel()
        self.icon_label.setPixmap(icon.pixmap(QSize(48, 48)))
        self.icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.icon_label.setTextInteractionFlags(Qt.TextInteractionFlag.NoTextInteraction)
        self.name_label = QLabel(program_data.get('name', ''))
        self.name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.name_label.setWordWrap(True)
        self.name_label.setTextInteractionFlags(Qt.TextInteractionFlag.NoTextInteraction)

        layout.addWidget(self.icon_label)
        layout.addWidget(self.name_label)
        layout.addStretch()
        self._set_style()

    def _set_style(self):
        self.setAutoFillBackground(True)
        self.setStyleSheet("""
            CardWidget { background-color: #f8f9fa; border-radius: 8px; border: 1px solid #e9ecef; }
            CardWidget:hover { background-color: #e9ecef; border: 1px solid #dee2e6; }
        """)

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_start_position = event.position().toPoint()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent):
        if not (event.buttons() & Qt.MouseButton.LeftButton): return
        if not self.drag_start_position or (event.position().toPoint() - self.drag_start_position).manhattanLength() < 10: return

        drag = QDrag(self.parentWidget())
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

        # 【核心修复】不再隐藏源控件，让数据驱动刷新来处理UI变化
        # self.hide()
        drag.exec(Qt.DropAction.MoveAction)
        # if drag.exec(...) == Qt.DropAction.IgnoreAction:
        #    self.show()

    def mouseDoubleClickEvent(self, event: QMouseEvent):
        self.doubleClicked.emit(self.program_id)
        super().mouseDoubleClickEvent(event)
        
    def contextMenuEvent(self, event: QContextMenuEvent):
        self.customContextMenuRequested.emit(self.program_id, event)
        super().contextMenuEvent(event)