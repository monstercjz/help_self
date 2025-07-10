from PySide6.QtCore import QObject, Slot
from PySide6.QtWidgets import QFileDialog, QMessageBox
from src.features.remote_terminal.views.terminal_view import TerminalView
from src.features.remote_terminal.services.ssh_service import SSHService, ConnectionStatus
from src.features.remote_terminal.models.connection_model import ConnectionModel
from src.features.remote_terminal.views.connection_dialog import ConnectionDialog

class TerminalController(QObject):
    """
    The controller for the remote terminal feature.
    It connects the view and the SSH service, handling the application logic.
    """
    def __init__(self):
        super().__init__()
        self.view = TerminalView()
        self.service = SSHService()
        self.model = ConnectionModel()

        self._connect_signals()

    def _connect_signals(self):
        """Connects signals and slots between all components."""
        # View to Controller
        self.view.connect_requested.connect(self.on_connect_requested)
        self.view.disconnect_requested.connect(self.service.disconnect)
        self.view.command_sent.connect(self.service.send_command)
        self.view.load_config_requested.connect(self.on_load_config_requested)
        self.view.config_selected.connect(self.on_config_selected)
        self.view.add_config_requested.connect(self.on_add_config)
        self.view.edit_config_requested.connect(self.on_edit_config)
        self.view.delete_config_requested.connect(self.on_delete_config)

        # Service to Controller
        self.service.status_changed.connect(self.on_status_changed)

        # Model to Controller
        self.model.configurations_loaded.connect(self.on_configurations_loaded)
        self.model.error_occurred.connect(self.on_load_error)

    def get_view(self):
        """Returns the main view widget."""
        return self.view

    def on_connect_requested(self, details):
        """Handles the connection request from the view."""
        self.view.clear_terminal()
        self.service.connect(details)

    def on_status_changed(self, status, message):
        """Handles all status updates from the SSH service."""
        if status == ConnectionStatus.CONNECTING:
            self.view.append_data(f"{message}\n")
            self.view.set_connection_status(is_connected=False) # Keep controls disabled
        elif status == ConnectionStatus.CONNECTED:
            self.view.set_connection_status(is_connected=True)
            if "Shell is ready" in message:
                 self.view.append_data("Connection successful!\n")
            else:
                self.view.append_data(message) # Append shell output
        elif status == ConnectionStatus.DISCONNECTING:
            self.view.append_data("Disconnecting...\n")
        elif status == ConnectionStatus.DISCONNECTED:
            self.view.append_data("Disconnected.\n")
            self.view.set_connection_status(is_connected=False)
        elif status == ConnectionStatus.FAILED:
            self.view.append_data(f"Connection failed: {message}\n")
            self.view.set_connection_status(is_connected=False)

    @Slot()
    def on_load_config_requested(self):
        """Opens a file dialog to select a JSON config file."""
        file_path, _ = QFileDialog.getOpenFileName(
            self.view, "Open SSH Configuration", "", "JSON Files (*.json)"
        )
        if file_path:
            self.model.load_configurations(file_path)

    @Slot(str)
    def on_config_selected(self, config_name):
        """Handles the selection of a configuration from the dropdown."""
        config = self.model.get_configuration(config_name)
        if config:
            self.view.set_connection_details(config)

    @Slot(list)
    def on_configurations_loaded(self, config_names):
        """Updates the view with the list of loaded configuration names."""
        self.view.update_configurations(config_names)
        self.view.append_data("Configurations loaded successfully.\n")

    @Slot(str)
    def on_load_error(self, error_message):
        """Displays an error message in the terminal."""
        self.view.append_data(f"{error_message}\n")

    @Slot()
    def on_add_config(self):
        """Handles the request to add a new configuration."""
        dialog = ConnectionDialog(parent=self.view)
        if dialog.exec():
            new_data = dialog.get_data()
            if new_data['name']:
                self.model.add_configuration(new_data)
            else:
                self.on_load_error("Configuration name cannot be empty.")

    @Slot(str)
    def on_edit_config(self, config_name):
        """Handles the request to edit an existing configuration."""
        config_to_edit = self.model.get_configuration(config_name)
        if not config_to_edit:
            self.on_load_error(f"Cannot edit. Configuration '{config_name}' not found.")
            return

        dialog = ConnectionDialog(config=config_to_edit, parent=self.view)
        if dialog.exec():
            updated_data = dialog.get_data()
            if updated_data['name']:
                self.model.update_configuration(config_name, updated_data)
            else:
                self.on_load_error("Configuration name cannot be empty.")

    @Slot(str)
    def on_delete_config(self, config_name):
        """Handles the request to delete a configuration."""
        reply = QMessageBox.question(self.view, 'Delete Configuration',
                                     f"Are you sure you want to delete '{config_name}'?",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.model.delete_configuration(config_name)
