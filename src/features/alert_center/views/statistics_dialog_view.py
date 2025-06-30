# desktop_center/src/features/alert_center/views/statistics_dialog_view.py
from PySide6.QtWidgets import QDialog, QVBoxLayout, QTabWidget, QWidget

class StatisticsDialogView(QDialog):
    """
    【视图】统计分析对话框 (已重构为空壳)。
    只包含一个QTabWidget，用于承载由子组件提供的视图。
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("统计分析")
        self.setMinimumSize(800, 600)
        
        main_layout = QVBoxLayout(self)
        self.tab_widget = QTabWidget()
        main_layout.addWidget(self.tab_widget)

    def add_tab(self, widget: QWidget, title: str):
        """向TabWidget中添加一个由子控制器提供的视图。"""
        self.tab_widget.addTab(widget, title)