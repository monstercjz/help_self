# desktop_center/src/features/program_launcher/widgets/card_widget.py
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PySide6.QtGui import QIcon, QMouseEvent, QContextMenuEvent
from PySide6.QtCore import Qt, Signal, QSize

class CardWidget(QWidget):
    """
    一个独立的卡片控件，用于在图标视图中显示单个程序。
    """
    doubleClicked = Signal(str)  # program_id
    customContextMenuRequested = Signal(str, QContextMenuEvent) # program_id, event

    def __init__(self, program_data: dict, icon: QIcon, parent=None):
        super().__init__(parent)
        self.program_id = program_data.get('id')
        self.program_data = program_data

        self.setFixedSize(100, 100)
        self.setToolTip(program_data.get('path', ''))

        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 10, 5, 10)
        layout.setSpacing(5)

        self.icon_label = QLabel()
        self.icon_label.setPixmap(icon.pixmap(QSize(48, 48)))
        self.icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.name_label = QLabel(program_data.get('name', ''))
        self.name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.name_label.setWordWrap(True)

        layout.addWidget(self.icon_label)
        layout.addWidget(self.name_label)
        layout.addStretch()

        self._set_style()

    def _set_style(self):
        """设置卡片的QSS样式。"""
        self.setAutoFillBackground(True)
        self.setStyleSheet("""
            CardWidget {
                background-color: #f8f9fa;
                border-radius: 8px;
                border: 1px solid #e9ecef;
            }
            CardWidget:hover {
                background-color: #e9ecef;
                border: 1px solid #dee2e6;
            }
        """)

    def mouseDoubleClickEvent(self, event: QMouseEvent):
        """处理双击事件。"""
        self.doubleClicked.emit(self.program_id)
        super().mouseDoubleClickEvent(event)
        
    def contextMenuEvent(self, event: QContextMenuEvent):
        """处理右键菜单事件。"""
        self.customContextMenuRequested.emit(self.program_id, event)
        super().contextMenuEvent(event)