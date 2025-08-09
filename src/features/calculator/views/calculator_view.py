from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QGridLayout, QPushButton, QLineEdit, QTextEdit, QLabel, QHBoxLayout, QSizePolicy
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QColor, QPalette

class CalculatorView(QWidget):
    """
    计算器视图，负责显示UI界面和用户输入。
    """
    button_clicked = Signal(str) # 当按钮被点击时发出信号，传递按钮文本

    def __init__(self):
        super().__init__()
        self.init_ui()
        self.apply_styles()

    def init_ui(self):
        self.main_layout = QHBoxLayout(self)
        self.main_layout.setContentsMargins(10, 10, 10, 10)
        self.main_layout.setSpacing(10)

        # 左侧计算器区域
        self.calculator_widget = QWidget()
        self.calculator_layout = QVBoxLayout(self.calculator_widget)
        self.calculator_layout.setContentsMargins(0, 0, 0, 0)
        self.calculator_layout.setSpacing(5)

        # 表达式显示
        self.expression_display = QLineEdit()
        self.expression_display.setReadOnly(True)
        self.expression_display.setAlignment(Qt.AlignRight)
        self.expression_display.setFixedHeight(40)
        self.expression_display.setFont(QFont("Segoe UI", 14))
        self.expression_display.setObjectName("expressionDisplay")
        self.calculator_layout.addWidget(self.expression_display)

        # 结果显示
        self.result_display = QLineEdit("0")
        self.result_display.setReadOnly(True)
        self.result_display.setAlignment(Qt.AlignRight)
        self.result_display.setFixedHeight(60)
        self.result_display.setFont(QFont("Segoe UI", 28, QFont.Bold))
        self.result_display.setObjectName("resultDisplay")
        self.calculator_layout.addWidget(self.result_display)

        # 按钮网格
        self.buttons_layout = QGridLayout()
        self.buttons_layout.setSpacing(5)

        buttons = [
            ('(', 0, 0, 1, 1, 'operatorButton'), (')', 0, 1, 1, 1, 'operatorButton'), ('C', 0, 2, 1, 1, 'clearButton'), ('DEL', 0, 3, 1, 1, 'deleteButton'),
            ('7', 1, 0, 1, 1, 'numberButton'), ('8', 1, 1, 1, 1, 'numberButton'), ('9', 1, 2, 1, 1, 'numberButton'), ('÷', 1, 3, 1, 1, 'operatorButton'),
            ('4', 2, 0, 1, 1, 'numberButton'), ('5', 2, 1, 1, 1, 'numberButton'), ('6', 2, 2, 1, 1, 'numberButton'), ('×', 2, 3, 1, 1, 'operatorButton'),
            ('1', 3, 0, 1, 1, 'numberButton'), ('2', 3, 1, 1, 1, 'numberButton'), ('3', 3, 2, 1, 1, 'numberButton'), ('-', 3, 3, 1, 1, 'operatorButton'),
            ('0', 4, 0, 1, 2, 'numberButton'), ('.', 4, 2, 1, 1, 'numberButton'), ('+', 4, 3, 1, 1, 'operatorButton'),
            ('=', 5, 0, 1, 4, 'equalsButton') # 将等号按钮放到新的一行，并横跨4列
        ]

        for btn_text, row, col, row_span, col_span, obj_name in buttons:
            button = QPushButton(btn_text)
            button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
            button.setFont(QFont("Segoe UI", 18))
            button.setObjectName(obj_name)
            button.clicked.connect(self._on_button_clicked) # 修改：连接到新的私有方法
            self.buttons_layout.addWidget(button, row, col, row_span, col_span)

        self.calculator_layout.addLayout(self.buttons_layout)
        self.main_layout.addWidget(self.calculator_widget, 2) # 占据2份空间

        # 右侧历史记录区域
        self.history_widget = QWidget()
        self.history_layout = QVBoxLayout(self.history_widget)
        self.history_layout.setContentsMargins(0, 0, 0, 0)
        self.history_layout.setSpacing(5)

        self.history_label = QLabel("历史记录")
        self.history_label.setFont(QFont("Segoe UI", 12, QFont.Bold))
        self.history_label.setAlignment(Qt.AlignCenter)
        self.history_label.setObjectName("historyLabel")
        self.history_layout.addWidget(self.history_label)

        self.history_display = QTextEdit()
        self.history_display.setReadOnly(True)
        self.history_display.setFont(QFont("Segoe UI", 10))
        self.history_display.setObjectName("historyDisplay")
        self.history_display.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded) # 仅在需要时显示滚动条
        self.history_layout.addWidget(self.history_display)

        self.clear_history_button = QPushButton("清空历史")
        self.clear_history_button.setFont(QFont("Segoe UI", 12))
        self.clear_history_button.setObjectName("clearHistoryButton")
        self.clear_history_button.clicked.connect(lambda: self.button_clicked.emit("CLEAR_HISTORY"))
        self.history_layout.addWidget(self.clear_history_button)

        self.main_layout.addWidget(self.history_widget, 1) # 占据1份空间

    def apply_styles(self):
        # 基础调色板
        palette = self.palette()
        palette.setColor(QPalette.Window, QColor("#f0f0f0"))
        palette.setColor(QPalette.WindowText, QColor("#333333"))
        self.setPalette(palette)
        self.setAutoFillBackground(True)

        # QSS 样式
        qss = """
        QWidget {
            background-color: #f0f0f0;
            color: #333333;
        }
        #expressionDisplay, #resultDisplay {
            background-color: #ffffff;
            border: 1px solid #cccccc;
            border-radius: 5px;
            padding: 5px;
            color: #333333;
        }
        #resultDisplay {
            font-weight: bold;
        }
        QPushButton {
            background-color: #e0e0e0;
            border: 1px solid #cccccc;
            border-radius: 5px;
            padding: 15px;
            font-size: 18px;
            color: #333333;
        }
        QPushButton:hover {
            background-color: #d0d0d0;
        }
        QPushButton:pressed {
            background-color: #c0c0c0;
        }
        #numberButton {
            background-color: #ffffff;
        }
        #numberButton:hover {
            background-color: #f0f0f0;
        }
        #operatorButton {
            background-color: #f8f8f8;
            color: #007bff; /* 蓝色 */
        }
        #operatorButton:hover {
            background-color: #e8e8e8;
        }
        #clearButton, #deleteButton {
            background-color: #ffcccc; /* 浅红色 */
            color: #cc0000; /* 深红色 */
        }
        #clearButton:hover, #deleteButton:hover {
            background-color: #ffbbbb;
        }
        #equalsButton {
            background-color: #007bff; /* 蓝色 */
            color: #ffffff;
            font-weight: bold;
        }
        #equalsButton:hover {
            background-color: #0056b3;
        }
        #historyLabel {
            background-color: #e0e0e0;
            padding: 5px;
            border-radius: 5px;
        }
        #historyDisplay {
            background-color: #ffffff;
            border: 1px solid #cccccc;
            border-radius: 5px;
            padding: 5px;
            color: #333333;
        }
        #clearHistoryButton {
            background-color: #f0f0f0;
            border: 1px solid #cccccc;
            border-radius: 5px;
            padding: 8px;
            font-size: 12px;
            color: #666666;
        }
        #clearHistoryButton:hover {
            background-color: #e0e0e0;
        }
        """
        self.setStyleSheet(qss)

    def set_expression(self, expression: str):
        self.expression_display.setText(expression)

    def set_result(self, result: str):
        self.result_display.setText(result)

    def update_history(self, history: list):
        history_text = ""
        for expr, res in history:
            history_text += f"{expr} = {res}\n"
        self.history_display.setText(history_text)

    def _on_button_clicked(self):
        """处理按钮点击，获取发送者文本并发出信号。"""
        sender_button = self.sender()
        if sender_button and isinstance(sender_button, QPushButton):
            self.button_clicked.emit(sender_button.text())
        elif sender_button == self.clear_history_button:
            # 特殊处理清空历史按钮，因为它没有在循环中创建
            self.button_clicked.emit("CLEAR_HISTORY")

    def keyPressEvent(self, event):
        """
        处理键盘按键事件，将键盘输入映射到计算器操作。
        """
        key = event.key()
        text = event.text()

        # 数字键 (0-9) 和小数点
        # 优先使用 event.text() 获取字符，因为它能处理主键盘和小键盘的数字
        if text.isdigit() or text == '.':
            self.button_clicked.emit(text)
        # 运算符
        elif key == Qt.Key_Plus:
            self.button_clicked.emit("+")
        elif key == Qt.Key_Minus:
            self.button_clicked.emit("-")
        elif key == Qt.Key_Asterisk: # 乘号 '*'
            self.button_clicked.emit("×") # 使用 '×' 匹配UI按钮
        elif key == Qt.Key_Slash: # 除号 '/'
            self.button_clicked.emit("÷") # 使用 '÷' 匹配UI按钮
        elif key == Qt.Key_Percent:
            self.button_clicked.emit("%")
        
        # 等号和回车
        elif key == Qt.Key_Equal or key == Qt.Key_Return or key == Qt.Key_Enter:
            self.button_clicked.emit("=")
        
        # 清空和删除
        elif key == Qt.Key_C: # 'C' 键用于清空
            self.button_clicked.emit("C")
        elif key == Qt.Key_Backspace: # 退格键用于删除
            self.button_clicked.emit("DEL")
        
        # 括号
        elif key == Qt.Key_ParenLeft:
            self.button_clicked.emit("(")
        elif key == Qt.Key_ParenRight:
            self.button_clicked.emit(")")
        
        else:
            super().keyPressEvent(event) # 传递未处理的事件