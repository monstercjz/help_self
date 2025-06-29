# src/ui/action_manager.py
from PySide6.QtCore import QObject
from PySide6.QtGui import QAction, QIcon

class ActionManager(QObject):
    """
    中央动作管理器。
    创建并持有代表全局操作的QAction实例，实现功能触发和UI组件的解耦。
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # 告警中心相关动作
        self.show_history = QAction(QIcon.fromTheme("document-open-recent"), "查看历史记录...", self)
        self.show_statistics = QAction(QIcon.fromTheme("utilities-system-monitor"), "打开统计分析...", self)