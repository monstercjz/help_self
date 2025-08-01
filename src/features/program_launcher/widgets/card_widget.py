# desktop_center/src/features/program_launcher/widgets/card_widget.py
from PySide6.QtWidgets import QFrame, QVBoxLayout, QLabel
from PySide6.QtGui import QIcon, QMouseEvent, QContextMenuEvent, QDrag, QPixmap, QPainter
from PySide6.QtCore import Qt, Signal, QSize, QMimeData, QPoint

# class CardWidget(QWidget):新加 修改可以实现悬停背景有颜色
class CardWidget(QFrame):
    """
    一个独立的卡片控件，用于在图标视图中显示单个程序。
    其尺寸由外部视图动态计算并设置。
    """
    doubleClicked = Signal(str)
    customContextMenuRequested = Signal(str, QContextMenuEvent)

    def __init__(self, program_data: dict, icon: QIcon, fixed_size: QSize, parent=None):
        super().__init__(parent)
        #新加
        self.setObjectName("CardWidget")
        self.program_id = program_data.get('id')
        self.program_data = program_data
        # 新加
        self.setAutoFillBackground(True)
        # 【变更】应用由外部计算得出的固定尺寸，取代硬编码
        self.setFixedSize(fixed_size)
        self.setToolTip(program_data.get('path', ''))
        self.drag_start_position = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)

        self.icon_label = QLabel()
        # 图标大小应与卡片尺寸关联，保持一定比例
        icon_size = int(fixed_size.width() * 0.45)
        self.icon_label.setPixmap(icon.pixmap(QSize(icon_size, icon_size)))
        self.icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.icon_label.setTextInteractionFlags(Qt.TextInteractionFlag.NoTextInteraction)
        
        self.name_label = QLabel(program_data.get('name', ''))
        self.name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.name_label.setWordWrap(True)
        self.name_label.setTextInteractionFlags(Qt.TextInteractionFlag.NoTextInteraction)

        layout.addWidget(self.icon_label)
        layout.addStretch()
        layout.addWidget(self.name_label)
        layout.addStretch()

    def enterEvent(self, event):
        """鼠标进入时，将光标设置为手形"""
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        super().enterEvent(event)

    def leaveEvent(self, event):
        """鼠标离开时，恢复默认光标"""
        self.unsetCursor()  # 恢复默认光标
        super().leaveEvent(event)

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

        drag.exec(Qt.DropAction.MoveAction)

    def mouseDoubleClickEvent(self, event: QMouseEvent):
        self.doubleClicked.emit(self.program_id)
        super().mouseDoubleClickEvent(event)
        
    def contextMenuEvent(self, event: QContextMenuEvent):
        self.customContextMenuRequested.emit(self.program_id, event)
        super().contextMenuEvent(event)