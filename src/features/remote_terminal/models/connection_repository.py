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

    def get_current_db_path(self) -> str:
        """Returns the path of the currently loaded database from the service."""
        return self.db_service.db_path

    def load_from_file(self, file_path: str):
        """
        Handles a user-initiated request to switch to a different database file.
        """
        old_db_service = self.db_service
        try:
            # 1. Instantiate the new DB service directly
            new_db_service = ConnectionDBService(file_path)

            # 2. Validate the schema of the new database
            if not new_db_service.validate_database_schema():
                raise ValueError("The selected database file does not match the required schema or is not writable.")

            # 3. If validation passes, switch to the new service
            self.db_service = new_db_service
            
            # 4. Notify listeners and update configuration
            self.connections_changed.emit()
            self.context.config_service.set_option(self.plugin_name, "db_path", file_path)
            self.context.config_service.save_config()

        except Exception as e:
            # If anything goes wrong, revert to the old service
            self.db_service = old_db_service
            error_message = f"Failed to load database: {e}"
            self.error_occurred.emit(error_message)
            # Ensure the view is consistent with the actual state
            self.connections_changed.emit()

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