# desktop_center/src/features/program_launcher/views/modes/base_view.py
from PySide6.QtWidgets import QWidget
from PySide6.QtCore import Signal

# 【核心修复】移除 ABC 和自定义元类，以避免所有元类冲突问题。
# from abc import ABC, abstractmethod
# class QABCMeta(type(QWidget), type(ABC)): pass

class BaseViewMode(QWidget):
    """
    所有视图模式的基类。
    我们使用 NotImplementedError 来模拟抽象方法，这更简单且避免了元类问题。
    """
    # 通用信号，确保所有视图都提供相同的交互出口
    item_double_clicked = Signal(str)  # program_id
    edit_item_requested = Signal(str, str) # item_id, item_type
    delete_item_requested = Signal(str, str) # item_id, item_type
    add_program_to_group_requested = Signal(str) # group_id, 用于右键菜单
    items_moved = Signal() # 用于拖拽排序

    def __init__(self, parent=None):
        super().__init__(parent)

    def update_view(self, data: dict):
        """
        接收完整的模型数据并刷新视图。
        子类必须重写此方法。
        """
        raise NotImplementedError("Subclasses of BaseViewMode must implement the 'update_view' method.")