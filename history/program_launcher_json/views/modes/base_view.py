# desktop_center/src/features/program_launcher/views/modes/base_view.py
from PySide6.QtWidgets import QWidget
from PySide6.QtCore import Signal

class BaseViewMode(QWidget):
    item_double_clicked = Signal(str)
    edit_item_requested = Signal(str, str)
    delete_item_requested = Signal(str, str)
    add_program_to_group_requested = Signal(str)
    items_moved = Signal() # 用于树状视图
    program_dropped = Signal(str, str, int) # 用于图标视图的程序卡片
    group_order_changed = Signal(list) # 【新增】用于图标视图的分组排序

    def __init__(self, parent=None):
        super().__init__(parent)

    def update_view(self, data: dict):
        raise NotImplementedError("Subclasses of BaseViewMode must implement the 'update_view' method.")