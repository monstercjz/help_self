# desktop_center/src/features/program_launcher/widgets/no_results_widget.py
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PySide6.QtGui import QIcon
from PySide6.QtCore import Qt

class NoResultsWidget(QWidget):
    """
    一个用于显示“无搜索结果”的占位符控件。
    """
    def __init__(self, parent=None):
        super().__init__(parent)

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(20)

        # 图标
        icon_label = QLabel()
        pixmap = QIcon.fromTheme("edit-find").pixmap(64, 64)
        icon_label.setPixmap(pixmap)
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # 标题
        title_label = QLabel("未找到匹配项")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet("font-size: 20px; font-weight: bold;")

        # 描述
        description_label = QLabel("请尝试使用其他关键词进行搜索。")
        description_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        description_label.setStyleSheet("font-size: 14px; color: #888;")

        layout.addWidget(icon_label)
        layout.addWidget(title_label)
        layout.addWidget(description_label)