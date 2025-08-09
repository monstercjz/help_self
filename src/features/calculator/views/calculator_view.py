# src/features/calculator/views/calculator_view.py
import os
from PySide6.QtWidgets import QWidget, QVBoxLayout, QGridLayout, QLineEdit, QPushButton, QListWidget, QHBoxLayout
from PySide6.QtCore import Qt

class CalculatorView(QWidget):
    """
    计算器的用户界面。
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("CalculatorView")
        self._init_ui()
        self._load_stylesheet()

    def _init_ui(self):
        """初始化UI组件。"""
        root_layout = QHBoxLayout(self)
        
        # --- 计算器主面板 ---
        calculator_widget = QWidget()
        main_layout = QVBoxLayout(calculator_widget)
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(10, 10, 10, 10)

        # 显示屏
        self.display = QLineEdit("0")
        self.display.setObjectName("display")
        self.display.setReadOnly(True)
        self.display.setAlignment(Qt.AlignRight)
        self.display.setFixedHeight(70)
        main_layout.addWidget(self.display)

        # 按钮网格
        grid_layout = QGridLayout()
        grid_layout.setSpacing(10)
        
        buttons = [
            ('历史', 0, 0, 1, 1), ('清除历史', 0, 1, 1, 1), ('(', 0, 2, 1, 1), (')', 0, 3, 1, 1),
            ('7', 1, 0, 1, 1), ('8', 1, 1, 1, 1), ('9', 1, 2, 1, 1), ('/', 1, 3, 1, 1),
            ('4', 2, 0, 1, 1), ('5', 2, 1, 1, 1), ('6', 2, 2, 1, 1), ('*', 2, 3, 1, 1),
            ('1', 3, 0, 1, 1), ('2', 3, 1, 1, 1), ('3', 3, 2, 1, 1), ('-', 3, 3, 1, 1),
            ('0', 4, 0, 1, 2), ('.', 4, 2, 1, 1), ('+', 4, 3, 1, 1),
            ('C', 5, 0, 1, 1), ('<-', 5, 1, 1, 1), ('=', 5, 2, 1, 2)
        ]

        self.buttons = {}
        for btn_text, row, col, rowspan, colspan in buttons:
            button = QPushButton(btn_text)
            button.setProperty("text", btn_text)
            grid_layout.addWidget(button, row, col, rowspan, colspan)
            self.buttons[btn_text] = button
        
        main_layout.addLayout(grid_layout)
        
        # --- 历史记录面板 ---
        self.history_panel = QListWidget()
        self.history_panel.setObjectName("historyPanel")
        self.history_panel.setVisible(True) # 默认显示
        
        root_layout.addWidget(self.history_panel)
        root_layout.addWidget(calculator_widget)

    def set_display_text(self, text: str):
        """更新显示屏的文本。"""
        self.display.setText(text)

    def get_display_text(self) -> str:
        """获取显示屏的文本。"""
        return self.display.text()

    def update_history_list(self, history: list[str]):
        """更新历史记录列表。"""
        self.history_panel.clear()
        self.history_panel.addItems(history)
        # 滚动到底部
        self.history_panel.scrollToBottom()

    def _load_stylesheet(self):
        """加载QSS样式表。"""
        current_dir = os.path.dirname(os.path.abspath(__file__))
        qss_path = os.path.join(current_dir, '..', 'assets', 'style.qss')
        try:
            with open(qss_path, "r", encoding="utf-8") as f:
                self.setStyleSheet(f.read())
        except FileNotFoundError:
            print(f"错误: 样式文件未找到 at '{qss_path}'")