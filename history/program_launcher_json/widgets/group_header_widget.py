# desktop_center/src/features/program_launcher/widgets/group_header_widget.py
from PySide6.QtWidgets import QWidget, QHBoxLayout, QLabel
from PySide6.QtGui import QContextMenuEvent
from PySide6.QtCore import Qt, Signal

class GroupHeaderWidget(QWidget):
    """
    一个分组标题显示控件，现在只负责显示标题和发出右键菜单信号。
    拖拽逻辑已移至GroupContainerWidget。
    """
    customContextMenuRequested = Signal(str, QContextMenuEvent)

    def __init__(self, group_data: dict, parent=None):
        super().__init__(parent)
        self.setObjectName("GroupHeaderWidget")
        self.group_id = group_data.get('id')
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        self.title_label = QLabel(group_data.get('name', ''))
        self.title_label.setTextInteractionFlags(Qt.TextInteractionFlag.NoTextInteraction)
        layout.addWidget(self.title_label)
        
    def contextMenuEvent(self, event: QContextMenuEvent):
        self.customContextMenuRequested.emit(self.group_id, event)
        super().contextMenuEvent(event)