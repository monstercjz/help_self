# desktop_center/src/ui/history_page.py
from PySide6.QtWidgets import QWidget, QLabel, QVBoxLayout
from PySide6.QtCore import Qt
from src.services.database_service import DatabaseService

class HistoryPageWidget(QWidget):
    """
    【占位】历史记录查询页面。
    将在未来的版本中实现完整的查询功能。
    """
    def __init__(self, db_service: DatabaseService, parent=None):
        super().__init__(parent)
        self.db_service = db_service

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        label = QLabel("这里是未来的“历史记录浏览器”功能区。\n\n将提供按日期、等级和关键词查询数据库中所有告警的功能。")
        label.setStyleSheet("font-size: 20px; color: #666;")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(label)