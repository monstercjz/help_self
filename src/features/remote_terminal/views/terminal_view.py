from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                               QLineEdit, QPushButton, QTextEdit, QFormLayout,
                               QComboBox, QFileDialog)
from PySide6.QtCore import Signal, Qt, QEvent
from PySide6.QtGui import QFont, QColor, QTextCursor
from ansi2html import Ansi2HTMLConverter

class TerminalView(QWidget):
    """
    The user interface for the remote terminal.
    It displays connection info, terminal output, and a command input line.
    """
    connect_requested = Signal(dict)
    disconnect_requested = Signal()
    command_sent = Signal(str)
    load_config_requested = Signal()
    config_selected = Signal(str)
    add_config_requested = Signal()
    edit_config_requested = Signal(str)
    delete_config_requested = Signal(str)

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Remote Terminal")
        self.ansi_converter = Ansi2HTMLConverter(dark_bg=True, scheme='xterm')
        self.command_history = []
        self.history_index = -1

        self._init_ui()

    def _init_ui(self):
        """Initializes the UI components."""
        main_layout = QVBoxLayout(self)

        # Connection Form
        connection_widget = QWidget()
        form_layout = QFormLayout(connection_widget)
        form_layout.setContentsMargins(0, 0, 0, 0)
        
        self.host_input = QLineEdit("localhost")
        self.port_input = QLineEdit("22")
        self.user_input = QLineEdit("user")
        self.pass_input = QLineEdit()
        self.pass_input.setEchoMode(QLineEdit.Password)

        form_layout.addRow(QLabel("Host:"), self.host_input)
        form_layout.addRow(QLabel("Port:"), self.port_input)
        form_layout.addRow(QLabel("Username:"), self.user_input)
        form_layout.addRow(QLabel("Password:"), self.pass_input)

        # Config Loader
        config_layout = QHBoxLayout()
        self.load_config_button = QPushButton("加载配置")
        self.config_combo = QComboBox()
        self.config_combo.setPlaceholderText("Select a Configuration")
        self.add_button = QPushButton("添加")
        self.edit_button = QPushButton("编辑")
        self.delete_button = QPushButton("删除")
        self.edit_button.setEnabled(False)
        self.delete_button.setEnabled(False)

        config_layout.addWidget(self.load_config_button)
        config_layout.addWidget(self.config_combo, 1)
        config_layout.addWidget(self.add_button)
        config_layout.addWidget(self.edit_button)
        config_layout.addWidget(self.delete_button)

        # Connection Buttons
        button_layout = QHBoxLayout()
        self.connect_button = QPushButton("连接远程SSH")
        self.disconnect_button = QPushButton("断开连接")
        self.disconnect_button.setEnabled(False)
        button_layout.addWidget(self.connect_button)
        button_layout.addWidget(self.disconnect_button)
        
        # Terminal Display
        self.terminal_output = QTextEdit()
        self.terminal_output.setReadOnly(True)
        font = QFont("Consolas", 10)
        self.terminal_output.setFont(font)
        self.terminal_output.setStyleSheet("""
            QTextEdit {
                background-color: #1e1e1e;
                color: #d4d4d4;
                border: 1px solid #3c3c3c;
            }
        """)

        # Command Input
        self.command_input = QLineEdit()
        self.command_input.setFont(font)
        self.command_input.setStyleSheet("""
            QLineEdit {
                background-color: #1e1e1e;
                color: #d4d4d4;
                border: 1px solid #3c3c3c;
                padding: 2px;
            }
        """)
        self.command_input.returnPressed.connect(self._on_command_entered)
        self.command_input.installEventFilter(self) # For key press handling

        main_layout.addLayout(config_layout)
        main_layout.addWidget(connection_widget)
        main_layout.addLayout(button_layout)
        main_layout.addWidget(self.terminal_output, 1) # Give terminal output more space
        main_layout.addWidget(self.command_input)

        # Connect signals
        self.load_config_button.clicked.connect(self.load_config_requested)
        self.add_button.clicked.connect(self.add_config_requested)
        self.edit_button.clicked.connect(self._on_edit_clicked)
        self.delete_button.clicked.connect(self._on_delete_clicked)
        self.config_combo.activated.connect(self._on_config_selected)
        self.connect_button.clicked.connect(self._on_connect_clicked)
        self.disconnect_button.clicked.connect(self.disconnect_requested)

    def eventFilter(self, source, event):
        """Handle key presses on the command input for history."""
        if source is self.command_input and event.type() == QEvent.KeyPress:
            if event.key() == Qt.Key_Up:
                self._show_previous_command()
                return True
            elif event.key() == Qt.Key_Down:
                self._show_next_command()
                return True
        return super().eventFilter(source, event)

    def _on_connect_clicked(self):
        """Emits a signal with the connection details."""
        details = {
            "hostname": self.host_input.text(),
            "port": int(self.port_input.text()),
            "username": self.user_input.text(),
            "password": self.pass_input.text()
        }
        self.connect_requested.emit(details)

    def _on_config_selected(self, index):
        """Emits a signal when a configuration is selected from the dropdown."""
        is_valid_selection = index > 0
        self.edit_button.setEnabled(is_valid_selection)
        self.delete_button.setEnabled(is_valid_selection)
        if is_valid_selection:
            config_name = self.config_combo.itemText(index)
            self.config_selected.emit(config_name)

    def _on_edit_clicked(self):
        """Emits a signal to request editing the current configuration."""
        if self.config_combo.currentIndex() > 0:
            config_name = self.config_combo.currentText()
            self.edit_config_requested.emit(config_name)

    def _on_delete_clicked(self):
        """Emits a signal to request deleting the current configuration."""
        if self.config_combo.currentIndex() > 0:
            config_name = self.config_combo.currentText()
            self.delete_config_requested.emit(config_name)

    def _on_command_entered(self):
        """Handles when a command is entered."""
        command = self.command_input.text()
        if command:
            self.command_history.append(command)
            self.history_index = len(self.command_history)
            self.command_sent.emit(command + '\n')
            self.command_input.clear()

    def _show_previous_command(self):
        """Shows the previous command from history."""
        if not self.command_history:
            return
        self.history_index = max(0, self.history_index - 1)
        self.command_input.setText(self.command_history[self.history_index])

    def _show_next_command(self):
        """Shows the next command from history."""
        if not self.command_history:
            return
        if self.history_index < len(self.command_history) - 1:
            self.history_index += 1
            self.command_input.setText(self.command_history[self.history_index])
        else:
            self.history_index = len(self.command_history)
            self.command_input.clear()

    def append_data(self, raw_data):
        """Converts ANSI data to HTML and appends it to the terminal."""
        html = self.ansi_converter.convert(raw_data, full=False)
        # Replace newlines with <br> for proper HTML rendering
        html = html.replace('\n', '<br>')
        self.terminal_output.moveCursor(QTextCursor.End)
        self.terminal_output.insertHtml(html)
        self.terminal_output.moveCursor(QTextCursor.End)

    def set_connection_status(self, is_connected):
        """Enables/disables UI elements based on connection status."""
        self.connect_button.setEnabled(not is_connected)
        self.disconnect_button.setEnabled(is_connected)
        self.command_input.setEnabled(is_connected)
        self.host_input.setEnabled(not is_connected)
        self.port_input.setEnabled(not is_connected)
        self.user_input.setEnabled(not is_connected)
        self.pass_input.setEnabled(not is_connected)
        if is_connected:
            self.command_input.setFocus()
        else:
            self.host_input.setFocus()

    def clear_terminal(self):
        """Clears the terminal display."""
        self.terminal_output.clear()

    def update_configurations(self, config_names):
        """Populates the dropdown with loaded configuration names."""
        self.config_combo.clear()
        self.config_combo.addItem("Select a Configuration") # Placeholder
        self.config_combo.addItems(config_names)

    def set_connection_details(self, details):
        """Fills the input fields with details from a selected configuration."""
        self.host_input.setText(details.get("hostname", ""))
        self.port_input.setText(str(details.get("port", "")))
        self.user_input.setText(details.get("username", ""))
        self.pass_input.setText(details.get("password", "")) # Optional