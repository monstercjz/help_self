from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                               QLineEdit, QPushButton, QTextEdit, QTreeView,
                               QSplitter, QAbstractItemView, QMenu, QGroupBox)
from PySide6.QtCore import Signal, Qt, QEvent, QModelIndex
from PySide6.QtGui import QFont, QStandardItemModel, QStandardItem, QTextCursor, QAction
from ansi2html import Ansi2HTMLConverter

class TerminalView(QWidget):
    """
    The user interface for the remote terminal, featuring a tree-based connection manager.
    """
    connect_requested = Signal(dict)
    disconnect_requested = Signal()
    command_sent = Signal(str)
    load_connections_requested = Signal()
    add_connection_requested = Signal()
    edit_connection_requested = Signal(dict)
    delete_connection_requested = Signal(dict)
    connection_selected = Signal(dict)

    def __init__(self):
        super().__init__()
        self.setWindowTitle("远程终端")
        self.ansi_converter = Ansi2HTMLConverter(dark_bg=True, scheme='xterm')
        self.command_history = []
        self.history_index = -1
        self._init_ui()

    def _init_ui(self):
        """Initializes the UI components."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(15, 0, 15, 15)
        main_layout.setSpacing(0)

        # Global Top Toolbar (always visible)
        top_toolbar = QWidget()
        top_bar_layout = QHBoxLayout(top_toolbar)
        top_bar_layout.setContentsMargins(5, 2, 5, 2)
        self.load_button = QPushButton("加载库")
        self.add_button = QPushButton("添加连接")
        self.db_path_label = QLabel("数据库: 未加载")
        self.db_path_label.setWordWrap(True)
        
        
        top_bar_layout.addWidget(self.add_button)
        top_bar_layout.addWidget(self.load_button)
        top_bar_layout.addStretch()
        top_bar_layout.addWidget(self.db_path_label)
        
        # Main content area with splitter
        self.splitter = QSplitter(Qt.Horizontal)

        # Left Panel: Connection Management
        left_group_box = QGroupBox("连接列表")
        left_group_box.setStyleSheet("""
            QGroupBox {
                font-size: 16px;
                font-weight: bold;
                color: #CE13F3; /* 这是组内文本颜色 */
                margin-top: 10px;

                /* --- 以下是新增的边框设置 --- */
                border: 2px solid #E0E0E0; /* 设置2px实线边框，颜色为#eea00f */
                border-radius: 5px; /* 可选：设置圆角 */
            }

            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 0 10px;
                left: 10px;
                /* 如果您想让标题背景也与边框颜色一致，可以给title设置background-color */
                /* background-color: #eea00f; */
            }
        """)
        
        left_layout = QVBoxLayout(left_group_box)
        left_layout.setContentsMargins(10, 35, 10, 10)
        
        self.tree_view = QTreeView()
        self.tree_view.setHeaderHidden(True)
        self.tree_view.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.tree_view.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tree_model = QStandardItemModel()
        self.tree_view.setModel(self.tree_model)
        left_layout.addWidget(self.tree_view)

        # Right Panel: Terminal
        right_group_box = QGroupBox("终端")
        right_group_box.setStyleSheet("""
            QGroupBox {
                font-size: 16px;
                font-weight: bold;
                color: #CE13F3; /* 这是组内文本颜色 */
                margin-top: 10px;

                /* --- 以下是新增的边框设置 --- */
                border: 2px solid #E0E0E0; /* 设置2px实线边框，颜色为#eea00f */
                border-radius: 5px; /* 可选：设置圆角 */
            }

            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 0 10px;
                left: 10px;
                /* 如果您想让标题背景也与边框颜色一致，可以给title设置background-color */
                /* background-color: #eea00f; */
            }
        """)
        right_layout = QVBoxLayout(right_group_box)

        self.disconnect_button = QPushButton("断开连接")
        self.disconnect_button.setEnabled(False)
        
        self.toggle_button = QPushButton("<<")
        self.toggle_button.setFixedWidth(30)
        
        terminal_buttons_layout = QHBoxLayout()
        terminal_buttons_layout.addWidget(self.toggle_button)
        terminal_buttons_layout.addStretch()
        terminal_buttons_layout.addWidget(self.disconnect_button)

        self.terminal_output = QTextEdit()
        self.terminal_output.setReadOnly(True)
        font = QFont("Consolas", 10)
        self.terminal_output.setFont(font)
        self.terminal_output.setStyleSheet("background-color: #1e1e1e; color: #d4d4d4;")

        self.command_input = QLineEdit()
        self.command_input.setFont(font)
        self.command_input.setStyleSheet("background-color: #1e1e1e; color: #d4d4d4;")
        self.command_input.setEnabled(False)

        right_layout.addLayout(terminal_buttons_layout)
        
        right_layout.addWidget(self.command_input)
        right_layout.addWidget(self.terminal_output, 1)

        self.splitter.addWidget(left_group_box)
        self.splitter.addWidget(right_group_box)
        self.splitter.setSizes([410, 590]) # Initial size ratio
        
        content_group_box = QGroupBox()
        content_group_box.setStyleSheet("""
            QGroupBox {   
                margin-top: 10px;

                /* --- 以下是新增的边框设置 --- */
                border: 1px solid #E0E0E0; /* 设置2px实线边框，颜色为#eea00f */
                border-radius: 5px; /* 可选：设置圆角 */
            }
        """)
        content_layout = QVBoxLayout(content_group_box)
        content_layout.setContentsMargins(8, 3, 8, 8)
        content_layout.addWidget(self.splitter)

        main_layout.addWidget(top_toolbar)
        main_layout.addWidget(content_group_box, 1)

        self._connect_signals()

    def _connect_signals(self):
        """Connects UI signals to handlers or emits them."""
        self.load_button.clicked.connect(self.load_connections_requested)
        self.add_button.clicked.connect(self.add_connection_requested)
        self.tree_view.customContextMenuRequested.connect(self._show_tree_context_menu)
        self.tree_view.selectionModel().selectionChanged.connect(self._on_tree_selection_changed)
        self.tree_view.doubleClicked.connect(self._on_tree_double_clicked)
        self.toggle_button.clicked.connect(self._toggle_left_panel)
        self.disconnect_button.clicked.connect(self.disconnect_requested)
        self.command_input.returnPressed.connect(self._on_command_entered)
        self.command_input.installEventFilter(self)

    def eventFilter(self, source, event):
        if source is self.command_input and event.type() == QEvent.KeyPress:
            if event.key() == Qt.Key_Up:
                self._show_previous_command()
                return True
            elif event.key() == Qt.Key_Down:
                self._show_next_command()
                return True
        return super().eventFilter(source, event)

    def _get_selected_connection_data(self):
        """Retrieves the data dictionary from the selected tree item."""
        indexes = self.tree_view.selectedIndexes()
        if not indexes:
            return None
        item = self.tree_model.itemFromIndex(indexes[0])
        if item and item.data():
            return item.data()
        return None

    def _on_edit_clicked(self):
        conn_data = self._get_selected_connection_data()
        if conn_data:
            self.edit_connection_requested.emit(conn_data)

    def _on_delete_clicked(self):
        conn_data = self._get_selected_connection_data()
        if conn_data:
            self.delete_connection_requested.emit(conn_data)

    def _on_tree_selection_changed(self, selected, deselected):
        # This can be simplified as the connect button is removed.
        # The logic is now handled by the context menu and double-click.
        pass

    def _on_tree_double_clicked(self, index):
        item = self.tree_model.itemFromIndex(index)
        if item and item.data():
            self.connect_requested.emit(item.data())

    def _on_connect_clicked(self):
        # This is now triggered by the context menu
        conn_data = self._get_selected_connection_data()
        if conn_data:
            self.connect_requested.emit(conn_data)

    def _on_command_entered(self):
        command = self.command_input.text()
        if command:
            self.command_history.append(command)
            self.history_index = len(self.command_history)
            self.command_sent.emit(command + '\n')
            self.command_input.clear()

    def _show_previous_command(self):
        if self.command_history:
            self.history_index = max(0, self.history_index - 1)
            self.command_input.setText(self.command_history[self.history_index])

    def _show_next_command(self):
        if self.history_index < len(self.command_history) - 1:
            self.history_index += 1
            self.command_input.setText(self.command_history[self.history_index])
        else:
            self.history_index = len(self.command_history)
            self.command_input.clear()

    def _toggle_left_panel(self):
        """Shows or hides the left connection panel."""
        sizes = self.splitter.sizes()
        if sizes[0] > 0:
            self.splitter.setSizes([0, sizes[1]])
            self.toggle_button.setText(">>")
        else:
            # Restore to a reasonable default size
            total_width = sum(sizes)
            left_width = min(250, int(total_width * 0.25))
            self.splitter.setSizes([left_width, total_width - left_width])
            self.toggle_button.setText("<<")

    def _show_tree_context_menu(self, point):
        index = self.tree_view.indexAt(point)
        if not index.isValid():
            return

        item = self.tree_model.itemFromIndex(index)
        if not item or not item.data():  # Ensure it's a connection item, not a group
            return

        context_menu = QMenu(self)
        connect_action = QAction("连接", self)
        edit_action = QAction("编辑", self)
        delete_action = QAction("删除", self)

        connect_action.triggered.connect(self._on_connect_clicked)
        edit_action.triggered.connect(self._on_edit_clicked)
        delete_action.triggered.connect(self._on_delete_clicked)

        context_menu.addAction(connect_action)
        context_menu.addSeparator()
        context_menu.addAction(edit_action)
        context_menu.addAction(delete_action)
        context_menu.exec(self.tree_view.viewport().mapToGlobal(point))

    def populate_connections(self, groups):
        """Populates the tree view with connections sorted by group."""
        self.tree_model.clear()
        for group_name, connections in sorted(groups.items()):
            group_item = QStandardItem(group_name)
            group_item.setSelectable(False)
            self.tree_model.appendRow(group_item)
            for conn in connections:
                display_text = f"{conn['name']} ({conn['username']}@{conn['hostname']}:{conn['port']})"
                conn_item = QStandardItem(display_text)
                conn_item.setData(conn) # Store the full dict
                group_item.appendRow(conn_item)
        self.tree_view.expandAll()

    def append_data(self, raw_data):
        html = self.ansi_converter.convert(raw_data, full=False).replace('\n', '<br>')
        self.terminal_output.moveCursor(QTextCursor.End)
        self.terminal_output.insertHtml(html)
        self.terminal_output.moveCursor(QTextCursor.End)

    def set_connection_status(self, is_connected):
        self.disconnect_button.setEnabled(is_connected)
        self.command_input.setEnabled(is_connected)
        self.tree_view.setEnabled(not is_connected)
        
        if is_connected:
            self.command_input.setFocus()
        else:
            self.tree_view.setFocus()

    def clear_terminal(self):
        self.terminal_output.clear()

    def set_database_path(self, path):
        """Sets the text of the database path label."""
        self.db_path_label.setText(f"数据库: {path}")
        self.db_path_label.setToolTip(path)