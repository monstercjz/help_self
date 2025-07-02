# desktop_center/src/features/program_launcher/widgets/card_widget.py
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PySide6.QtGui import QIcon, QMouseEvent, QContextMenuEvent, QDrag, QPixmap, QPainter # 【修改】导入 QPainter
from PySide6.QtCore import Qt, Signal, QSize, QMimeData, QPoint

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
        self.drag_start_position = None

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

    def mousePressEvent(self, event: QMouseEvent):
        """记录拖拽起始点。"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_start_position = event.position().toPoint()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent):
        """启动拖拽操作。"""
        if not (event.buttons() & Qt.MouseButton.LeftButton):
            return
        if not self.drag_start_position or (event.position().toPoint() - self.drag_start_position).manhattanLength() < 10:
            return

        drag = QDrag(self)
        mime_data = QMimeData()
        mime_data.setData("application/x-program-launcher-card", self.program_id.encode('utf-8'))
        drag.setMimeData(mime_data)

        # 【核心修复】使用正确的QPainter流程创建半透明图像
        # 1. 获取原始卡片的图像
        source_pixmap = self.grab()
        
        # 2. 创建一个同样大小的、透明的画布 (drag_pixmap)
        drag_pixmap = QPixmap(source_pixmap.size())
        drag_pixmap.fill(Qt.GlobalColor.transparent)
        
        # 3. 创建一个画家，让它在我们的画布上作画
        painter = QPainter(drag_pixmap)
        
        # 4. 设置画家的透明度
        painter.setOpacity(0.7)
        
        # 5. 用画家把原始图像画到画布上
        painter.drawPixmap(0, 0, source_pixmap)
        
        # 6. 结束绘制
        painter.end()

        drag.setPixmap(drag_pixmap)
        drag.setHotSpot(event.position().toPoint())

        self.hide()
        if drag.exec(Qt.DropAction.MoveAction) == Qt.DropAction.IgnoreAction:
            self.show()

    def mouseDoubleClickEvent(self, event: QMouseEvent):
        """处理双击事件。"""
        self.doubleClicked.emit(self.program_id)
        super().mouseDoubleClickEvent(event)
        
    def contextMenuEvent(self, event: QContextMenuEvent):
        """处理右键菜单事件。"""
        self.customContextMenuRequested.emit(self.program_id, event)
        super().contextMenuEvent(event)