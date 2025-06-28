# desktop_center/src/ui/statistics_dialog.py
from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel
from PySide6.QtCore import Qt
from src.services.database_service import DatabaseService

class StatisticsDialog(QDialog):
    """
    一个独立的对话框，用于统计和分析告警数据。
    【将在后续实现完整功能】
    """
    def __init__(self, db_service: DatabaseService, parent=None):
        super().__init__(parent)
        self.db_service = db_service
        self.setWindowTitle("统计分析")
        self.setMinimumSize(700, 500)
        
        layout = QVBoxLayout(self)
        label = QLabel("统计分析 - 完整功能开发中...\n\n这里将包含按IP、按小时、按类型的统计图表。")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setStyleSheet("font-size: 18px; color: #888;")
        layout.addWidget(label)