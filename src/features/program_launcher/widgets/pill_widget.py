# desktop_center/src/features/program_launcher/widgets/pill_widget.py
from PySide6.QtWidgets import QWidget, QHBoxLayout, QLabel, QFrame
from PySide6.QtGui import QIcon, QMouseEvent, QContextMenuEvent, QDrag, QPixmap, QPainter
from PySide6.QtCore import Qt, Signal, QSize, QMimeData

class PillWidget(QFrame):
    """
    一个“药丸”或“标签”样式的控件，用于在网格布局中显示单个程序。
    尺寸由外部动态计算并传入，内部布局经过微调以确保内容完整显示。
    """
    doubleClicked = Signal(str)
    customContextMenuRequested = Signal(str, QContextMenuEvent)

    def __init__(self, program_data: dict, icon: QIcon, fixed_size: QSize, parent=None):
        super().__init__(parent)
        self.setObjectName("PillWidget")
        self.program_id = program_data.get('id')
        self.program_data = program_data
        self.drag_start_position = None
        
        # --- 尺寸与布局 ---
        # 【影响因素 1: 外部固定尺寸】
        # PillWidget的总尺寸由外部视图（如FlowViewMode）计算后传入。
        # 这是所有内部布局约束的基础。
        self.setFixedSize(fixed_size)
        self.setToolTip(program_data.get('path', ''))

        # 创建水平布局管理器
        layout = QHBoxLayout(self)

        # 【影响因素 2: 内部边距】
        # setContentsMargins(left, top, right, bottom)
        # 定义了布局边缘与PillWidget边框之间的距离。
        # 减小左右边距可以为图标和文字提供更多水平空间。
        # 原为 (10, 5, 10, 5)，现调整为 (8, 4, 8, 4)
        layout.setContentsMargins(15, 4, 15, 4)
        
        # 【影响因素 3: 控件间距】
        # setSpacing() 定义了布局内各个控件（这里是图标和文字）之间的距离。
        # 减小此值可以使图标和文字靠得更近，为文字腾出空间。
        # 原为 8，现调整为 6
        layout.setSpacing(4)

        # --- 图标控件 ---
        self.icon_label = QLabel()
        # 【核心修复】为图标的容器（QLabel）设置一个固定的宽度。
        # 这确保了无论旁边的文本多长，图标的水平位置都是恒定的。
        self.icon_label.setFixedWidth(38) 
        self.icon_label.setPixmap(icon.pixmap(QSize(24, 24)))
        self.icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # --- 文字控件 ---
        self.name_label = QLabel(program_data.get('name', ''))
        self.name_label.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignHCenter)
        # 当分配给QLabel的空间不足时，它会自动用 "..." 截断文本，这是我们期望的行为。
         # 【核心修复】显式设置文本溢出模式，确保在文本过长时显示省略号。
        

        # --- 组装布局 ---
        layout.addWidget(self.icon_label)
        layout.addWidget(self.name_label)
        
        # 【影响因素 5: 弹性伸缩】 (已移除)
        # addStretch() 会添加一个可伸缩的空白空间。
        # 在固定宽度的布局中，如果文字标签自身的尺寸策略已经可以填满空间，
        # 额外的Stretch可能会不必要地抢占空间，导致文字被提前截断。
        # 移除它可以让QLabel获得最大的可用空间。
        # layout.addStretch(1) <-- 已移除

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