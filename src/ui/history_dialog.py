# desktop_center/src/ui/history_dialog.py
from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel
from PySide6.QtCore import Qt
from src.services.database_service import DatabaseService

class HistoryDialog(QDialog):
    """
    一个独立的对话框，用于浏览和查询历史告警记录。
    【将在后续实现完整功能】
    """
    def __init__(self, db_service: DatabaseService, parent=None):
        super().__init__(parent)
        self.db_service = db_service
        self.setWindowTitle("历史记录浏览器")
        self.setMinimumSize(800, 600)
        
        layout = QVBoxLayout(self)
        label = QLabel("历史记录浏览器 - 完整功能开发中...\n\n这里将包含日期筛选、关键词搜索和分页功能。")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setStyleSheet("font-size: 18px; color: #888;")
        layout.addWidget(label)