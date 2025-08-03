import os
from PySide6.QtCore import QObject, Slot
from PySide6.QtWidgets import QFileDialog, QMessageBox
from src.features.remote_terminal.views.terminal_view import TerminalView
from src.features.remote_terminal.services.ssh_service import SSHService, ConnectionStatus
from src.features.remote_terminal.models.connection_repository import ConnectionRepository
from src.features.remote_terminal.views.connection_dialog import ConnectionDialog
from src.features.remote_terminal.services.connection_db_service import ConnectionDBService
from src.core.context import ApplicationContext

class TerminalController(QObject):
    """
    The controller for the remote terminal feature.
    It connects the view, the repository, and the SSH service, handling the application logic.
    """
    def __init__(self, context: ApplicationContext, db_service: ConnectionDBService, plugin_name: str):
        super().__init__()
        self.context = context
        self.view = TerminalView()
        self.service = SSHService()
        self.repository = ConnectionRepository(context, db_service, plugin_name)

        self._connect_signals()
        self._load_initial_connections()

    def _connect_signals(self):
        """Connects signals and slots between all components."""
        # View to Controller
        self.view.connect_requested.connect(self.on_connect_requested)
        self.view.disconnect_requested.connect(self.service.disconnect)
        self.view.command_sent.connect(self.service.send_command)
        self.view.load_connections_requested.connect(self.on_load_connections_requested)
        self.view.add_connection_requested.connect(self.on_add_connection)
        self.view.edit_connection_requested.connect(self.on_edit_connection)
        self.view.delete_connection_requested.connect(self.on_delete_connection)

        # Service to Controller
        self.service.status_changed.connect(self.on_status_changed)
        self.service.data_received.connect(self.on_data_received)

        # Repository to Controller
        self.repository.connections_changed.connect(self.on_connections_changed)
        self.repository.error_occurred.connect(self.on_repository_error)

    def get_view(self):
        """Returns the main view widget."""
        return self.view

    def _load_initial_connections(self):
        """Loads connections from the default database on startup."""
        self.on_connections_changed()
        self.view.set_database_path(self.repository.get_current_db_path())

    @Slot()
    def on_connections_changed(self):
        """Reloads and repopulates the view when connections in the repository change."""
        connections = self.repository.get_all_connections_by_group()
        self.view.populate_connections(connections)
        self.view.set_database_path(self.repository.get_current_db_path())

    @Slot(dict)
    def on_connect_requested(self, details):
        """Handles the connection request from the view."""
        self.view.clear_terminal()
        self.service.connect(details)

    def on_status_changed(self, status, message):
        """Handles all status updates from the SSH service."""
        if status == ConnectionStatus.CONNECTING:
            self.view.append_data(f"{message}\n")
            self.view.set_connection_status(is_connected=False)
        elif status == ConnectionStatus.CONNECTED:
            self.view.set_connection_status(is_connected=True)
            # The initial "Shell is ready" or other messages are now handled by on_data_received
            if "Shell is ready" in message:
                 self.view.append_data("连接成功!\n")
        elif status == ConnectionStatus.DISCONNECTING:
            self.view.append_data("正在断开连接...\n")
        elif status == ConnectionStatus.DISCONNECTED:
            self.view.append_data("已断开连接.\n")
            self.view.set_connection_status(is_connected=False)
        elif status == ConnectionStatus.FAILED:
            self.view.append_data(f"连接失败: {message}\n")
            self.view.set_connection_status(is_connected=False)

    @Slot(str)
    def on_data_received(self, data):
        """Handles raw data from the SSH shell, checking for clear screen codes."""
        # Based on debugging, the clear sequence from Alpine is `\x1b[H\x1b[J`.
        clear_code = '\x1b[H\x1b[J'
        
        # The received data might contain the command echo, the clear code,
        # and the new prompt all in one buffer.
        # Example: 'clear\r\n\x1b[H\x1b[Jalpine-docker-downtools:~# '
        
        if clear_code in data:
            self.view.clear_terminal()
            
            # Display any data that comes *after* the clear code sequence.
            parts = data.split(clear_code, 1)
            remaining_data = parts[1]
            if remaining_data:
                self.view.append_data(remaining_data)
        else:
            self.view.append_data(data)

    @Slot()
    def on_load_connections_requested(self):
        """Opens a file dialog to select a SQLite DB file."""
        current_db_path = self.repository.get_current_db_path()
        start_dir = os.path.dirname(current_db_path) if current_db_path and os.path.exists(os.path.dirname(current_db_path)) else os.path.expanduser("~")
        
        file_path, _ = QFileDialog.getOpenFileName(
            self.view, "打开连接数据库", start_dir, "SQLite DB (*.db)"
        )
        if file_path:
            self.repository.load_from_file(file_path)

    @Slot(str)
    def on_repository_error(self, error_message):
        """Displays an error message from the repository in the terminal."""
        self.view.append_data(f"错误: {error_message}\n")
        QMessageBox.warning(self.view, "数据库错误", error_message)

    @Slot()
    def on_add_connection(self):
        """Handles the request to add a new connection."""
        existing_groups = list(self.repository.get_all_connections_by_group().keys())
        dialog = ConnectionDialog(existing_groups=existing_groups, parent=self.view)
        if dialog.exec():
            new_data = dialog.get_data()
            if new_data['name'] and new_data['group_name']:
                self.repository.add_connection(new_data)
            else:
                QMessageBox.warning(self.view, "输入错误", "连接名称和分组不能为空。")

    @Slot(dict)
    def on_edit_connection(self, conn_data):
        """Handles the request to edit an existing connection."""
        existing_groups = list(self.repository.get_all_connections_by_group().keys())
        dialog = ConnectionDialog(config=conn_data, existing_groups=existing_groups, parent=self.view)
        if dialog.exec():
            updated_data = dialog.get_data()
            if updated_data['name'] and updated_data['group_name']:
                self.repository.update_connection(conn_data['id'], updated_data)
            else:
                QMessageBox.warning(self.view, "输入错误", "连接名称和分组不能为空。")

    @Slot(dict)
    def on_delete_connection(self, conn_data):
        """Handles the request to delete a configuration."""
        reply = QMessageBox.question(self.view, '删除连接',
                                     f"您确定要从分组 '{conn_data['group_name']}' 中删除连接 '{conn_data['name']}' 吗?",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.repository.delete_connection(conn_data['id'])

    def cleanup(self):
        """Properly close resources."""
        self.service.disconnect()
        # The repository no longer manages the DB connection, so closing is not needed here.
