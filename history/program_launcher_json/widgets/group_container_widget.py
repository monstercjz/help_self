# desktop_center/src/features/program_launcher/widgets/group_container_widget.py
from PySide6.QtWidgets import QWidget, QVBoxLayout, QFrame, QGridLayout
from PySide6.QtGui import QMouseEvent, QDrag, QPixmap, QPainter
from PySide6.QtCore import Qt, QMimeData, QPoint

from .group_header_widget import GroupHeaderWidget

class GroupContainerWidget(QFrame):
    """
    一个容器控件，用于将一个分组（包括标题和程序卡片）显示为一个独立的卡片。
    其宽度由外部视图动态计算和设置，内部使用QGridLayout排列程序卡片。
    """
    def __init__(self, group_data: dict, fixed_width: int, parent=None):
        super().__init__(parent)
        self.setObjectName("GroupContainerWidget")
        self.group_id = group_data.get('id')
        self.drag_start_position = None
        self.card_count = 0
        self.internal_columns = 3 

        self.setFixedWidth(fixed_width)
        self.setCursor(Qt.CursorShape.OpenHandCursor)
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(15, 10, 15, 15)
        main_layout.setSpacing(10)

        self.header_widget = GroupHeaderWidget(group_data)
        
        self.card_container = QWidget()
        self.card_layout = QGridLayout(self.card_container)
        
        # 【核心变更】为内容列右侧的列设置一个大于0的伸缩因子。
        # 这会创建一个“弹簧”，将所有内容（卡片）推到左侧，解决行不满时的居中问题。
        self.card_layout.setColumnStretch(self.internal_columns, 1)

        main_layout.addWidget(self.header_widget)
        main_layout.addWidget(self.card_container)
        
        main_layout.addStretch(1)
        
    def add_card(self, card_widget, spacing: int):
        """向内部的GridLayout添加一个程序卡片，并设置间隙。"""
        self.card_layout.setSpacing(spacing)
        row = self.card_count // self.internal_columns
        col = self.card_count % self.internal_columns
        self.card_layout.addWidget(card_widget, row, col)
        self.card_count += 1

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton and self.header_widget.geometry().contains(event.position().toPoint()):
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