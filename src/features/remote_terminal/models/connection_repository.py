from PySide6.QtCore import QObject, Signal
from src.core.context import ApplicationContext
from src.features.remote_terminal.services.connection_db_service import ConnectionDBService

class ConnectionRepository(QObject):
    """
    Manages the business logic for SSH connection configurations.
    Delegates database operations to a dedicated DB service.
    """
    connections_changed = Signal()
    error_occurred = Signal(str)

    def __init__(self, context: ApplicationContext, db_service: ConnectionDBService, plugin_name: str, parent=None):
        super().__init__(parent)
        self.context = context
        self.db_service = db_service
        self.plugin_name = plugin_name

    def set_db_service(self, new_db_service: ConnectionDBService):
        self.db_service = new_db_service
        self.connections_changed.emit()

    def get_current_db_path(self) -> str:
        """Returns the path of the currently loaded database from the service."""
        return self.db_service.db_path

    def get_all_connections_by_group(self):
        """Returns all connections, structured as a dictionary of groups."""
        return self.db_service.get_all_connections_by_group()

    def add_connection(self, conn_data):
        """Adds a new connection to the database."""
        if self.db_service.add_connection(conn_data):
            self.connections_changed.emit()
            return True
        else:
            self.error_occurred.emit(f"Error: A connection named '{conn_data['name']}' already exists in group '{conn_data['group_name']}'.")
            return False

    def update_connection(self, connection_id, conn_data):
        """Updates an existing connection."""
        if self.db_service.update_connection(connection_id, conn_data):
            self.connections_changed.emit()
            return True
        else:
            self.error_occurred.emit(f"Failed to update connection with ID {connection_id}.")
            return False

    def delete_connection(self, connection_id):
        """Deletes a connection from the database."""
        if self.db_service.delete_connection(connection_id):
            self.connections_changed.emit()
            return True
        else:
            self.error_occurred.emit(f"Failed to delete connection with ID {connection_id}.")
            return False

    def close(self):
        """The underlying DB service is managed by the plugin, so no action is needed here."""
        pass