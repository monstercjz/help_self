# src/features/ssh_client/views/SessionWidget.py
import pyte # 导入pyte
from PySide6.QtWidgets import QWidget, QVBoxLayout, QTextEdit, QLineEdit, QPushButton, QHBoxLayout
from PySide6.QtCore import Qt, Signal, QSize, QEvent # 导入QEvent
from PySide6.QtGui import QFont, QTextCharFormat, QColor, QTextCursor # 导入QTextCursor, QFont, QTextCharFormat, QColor

# 终端颜色映射 (pyte默认颜色到CSS颜色)
# 这是一个简化的映射，可以根据需要扩展
COLOR_MAP = {
    0: "black", 1: "red", 2: "green", 3: "yellow",
    4: "blue", 5: "magenta", 6: "cyan", 7: "white",
    8: "gray", 9: "red", 10: "green", 11: "yellow", # bright colors
    12: "blue", 13: "magenta", 14: "cyan", 15: "white",
}

class SessionWidget(QWidget):
    """
    单个SSH会话的终端显示和输入控件。
    """
    commandEntered = Signal(str, str) # session_id, command_text
    shellDataEntered = Signal(str, str) # session_id, data_text (发送字符串)
    sessionClosed = Signal(str) # session_id
    terminalResized = Signal(str, int, int) # session_id, cols, rows (通知控制器终端尺寸变化)

    def __init__(self, session_id: str, connection_name: str, parent=None):
        super().__init__(parent)
        self.session_id = session_id
        self.connection_name = connection_name
        self.setWindowTitle(f"SSH会话: {connection_name}")

        # 初始化pyte终端模拟器
        self.screen = pyte.Screen(80, 24) # 初始尺寸，后续会根据QTextEdit调整
        self.stream = pyte.Stream(self.screen)

        self._init_ui()

        # 连接resizeEvent以更新终端尺寸
        self.output_display.installEventFilter(self) # 监听QTextEdit的事件
        self._update_terminal_size() # 初始设置终端尺寸

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        self.output_display = QTextEdit()
        self.output_display.setReadOnly(True)
        # 设置QTextEdit的背景色和前景色，并使用等宽字体
        self.output_display.setStyleSheet("background-color: #282c34; color: #abb2bf;")
        font = QFont("Cascadia Code", 10) # 推荐使用等宽字体
        font.setStyleHint(QFont.Monospace)
        self.output_display.setFont(font)
        self.output_display.setLineWrapMode(QTextEdit.NoWrap) # 禁用自动换行
        
        self.output_display.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.output_display.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        main_layout.addWidget(self.output_display)

        self.input_line = QLineEdit()
        self.input_line.setPlaceholderText("输入命令或Shell数据...")
        self.input_line.setStyleSheet("background-color: #3b4048; color: #abb2bf; font-family: 'Cascadia Code', 'Consolas', 'Monaco', 'monospace'; font-size: 10pt; border: 1px solid #5c6370;")
        self.input_line.returnPressed.connect(self._on_input_entered)
        main_layout.addWidget(self.input_line)

        # 暂时移除发送按钮，因为对于交互式shell，直接回车发送更自然
        # self.send_button = QPushButton("发送")
        # self.send_button.clicked.connect(self._on_input_entered)
        # button_layout = QHBoxLayout()
        # button_layout.addStretch()
        # button_layout.addWidget(self.send_button)
        # main_layout.addLayout(button_layout)

    def append_output(self, output_bytes: bytes):
        """
        向终端显示区域追加原始字节输出。
        """
        # 将原始字节流送入pyte流
        if isinstance(output_bytes, bytes):
            decoded_output = output_bytes.decode('utf-8', errors='ignore')
        else:
            decoded_output = output_bytes
        self.stream.feed(decoded_output)
        self._render_screen_to_text_edit()

    def _render_screen_to_text_edit(self):
        """
        将pyte屏幕的内容渲染到QTextEdit。
        """
        html_content = []
        for row_idx in range(self.screen.lines):
            line_html = []
            for col_idx in range(self.screen.columns):
                char_data = self.screen.buffer[row_idx][col_idx] # 从buffer获取Char对象
                char = char_data.data
                
                style = []
                # 直接从char_data对象访问属性
                fg_color = COLOR_MAP.get(char_data.fg, "white")
                bg_color = COLOR_MAP.get(char_data.bg, "black")

                style.append(f"color: {fg_color};")
                style.append(f"background-color: {bg_color};")

                if char_data.bold:
                    style.append("font-weight: bold;")
                if char_data.underscore:
                    style.append("text-decoration: underline;")
                if char_data.reverse: # 反色
                    style.append(f"color: {bg_color};")
                    style.append(f"background-color: {fg_color};")

                # 确保特殊字符被正确转义
                escaped_char = char.replace('&', '&').replace('<', '<').replace('>', '>')
                
                line_html.append(f"<span style=\"{' '.join(style)}\">{escaped_char}</span>")
            html_content.append("".join(line_html))
        
        # 使用setHtml来清空并设置整个屏幕内容，实现清屏效果
        # 注意：<pre>标签用于保留空白和换行，但QTextEdit的HTML渲染可能仍有差异
        self.output_display.setHtml("<pre style='margin:0;padding:0;border:none;background-color:#282c34;'>" + "<br>".join(html_content) + "</pre>")
        # 滚动到最新内容，确保显示最顶部的内容
        self.output_display.verticalScrollBar().setValue(self.output_display.verticalScrollBar().minimum())

    def _on_input_entered(self):
        """
        处理用户输入。
        """
        text = self.input_line.text()
        self.input_line.clear() # 先清空输入框
        if text:
            # 对于shell，需要加上换行符，并编码为字节流
            self.shellDataEntered.emit(self.session_id, text + "\n")

    def eventFilter(self, obj, event):
        """
        事件过滤器，用于捕获QTextEdit的尺寸变化事件。
        """
        if obj == self.output_display and event.type() == QEvent.Type.Resize:
            self._update_terminal_size()
        return super().eventFilter(obj, event)

    def _update_terminal_size(self):
        """
        根据QTextEdit的当前尺寸计算并更新pyte屏幕的尺寸。
        """
        # 获取字体度量
        font_metrics = self.output_display.fontMetrics()
        char_width = font_metrics.horizontalAdvance('M') # 使用'M'作为平均字符宽度
        char_height = font_metrics.height()

        if char_width == 0 or char_height == 0:
            return # 避免除以零

        # 计算QTextEdit内容区域的可用宽度和高度
        # 减去滚动条和边距（如果存在）
        viewport_width = self.output_display.viewport().width()
        viewport_height = self.output_display.viewport().height()

        cols = max(1, viewport_width // char_width)
        rows = max(1, viewport_height // char_height)

        if self.screen.columns != cols or self.screen.lines != rows:
            self.screen.resize(cols, rows)
            self.terminalResized.emit(self.session_id, cols, rows)
            # self.logger.info(f"终端尺寸更新: {cols}x{rows} (会话ID: {self.session_id})") # 暂时注释，因为SessionWidget没有logger
            self._render_screen_to_text_edit() # 尺寸变化后重新渲染

    def closeEvent(self, event):
        """
        当会话窗口关闭时发出信号。
        """
        self.sessionClosed.emit(self.session_id)
        super().closeEvent(event)