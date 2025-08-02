# src/features/memo_pad/widgets/clickable_list_widget.py

from PySide6.QtWidgets import QListWidget
from PySide6.QtGui import QMouseEvent
from PySide6.QtCore import Signal

class ClickableListWidget(QListWidget):
    """
    一个自定义的QListWidget，增加了点击空白区域时发出信号的功能。
    """
    blank_area_clicked = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)

    def mousePressEvent(self, event: QMouseEvent):
        """
        重写鼠标点击事件。
        如果点击位置没有项目，则发出 blank_area_clicked 信号。
        然后调用父类方法以保证默认行为（如选择项目）正常工作。
        """
        # 先调用父类方法，让它有机会处理选择等默认行为
        super().mousePressEvent(event)
        
        # 然后我们再检查点击位置
        item = self.itemAt(event.pos())
        if item is None:
            self.blank_area_clicked.emit()