# src/ui/quick_launch_page.py
from PySide6.QtWidgets import QWidget, QLabel, QVBoxLayout

class QuickLaunchPageWidget(QWidget):
    """【占位】快捷启动功能页面"""
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        label = QLabel("这里是未来的快捷启动功能区。")
        label.setStyleSheet("font-size: 20px;")
        layout.addWidget(label)