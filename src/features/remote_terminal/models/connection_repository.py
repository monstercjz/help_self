import sqlite3
import os
from PySide6.QtCore import QObject, Signal
from src.core.context import ApplicationContext

class ConnectionRepository(QObject):
    """
    Manages SSH connection configurations using a SQLite database.
    This class handles database initialization, CRUD operations, and loading from different DB files.
    """
    connections_changed = Signal()
    error_occurred = Signal(str)

    def __init__(self, context: ApplicationContext, parent=None):
        super().__init__(parent)
        self.context = context
        
        # 从配置文件获取相对路径，如果不存在则使用默认值
        relative_path = self.context.config_service.get_value(
            "RemoteTerminal",
            "config_path"
        )
        # 如果路径为空或未在config中定义，则使用默认值
        if not relative_path:
            relative_path = "plugins/remote_terminal/connections.db"
            
        # 使用上下文提供的工具函数获取最终的、可写的绝对路径
        self._db_path = self.context.get_data_path(relative_path)
        
        self._db_conn = None
        self._ensure_database_exists()

    def get_current_db_path(self):
        """Returns the path of the currently loaded database."""
        return self._db_path

    def _ensure_database_exists(self):
        """Connects to the database and creates the necessary tables if they don't exist."""
        try:
            self._db_conn = sqlite3.connect(self._db_path)
            self._db_conn.row_factory = sqlite3.Row
            cursor = self._db_conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS connections (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    group_name TEXT NOT NULL,
                    hostname TEXT NOT NULL,
                    port INTEGER NOT NULL,
                    username TEXT,
                    password TEXT,
                    UNIQUE(group_name, name)
                )
            """)
            self._db_conn.commit()
        except sqlite3.Error as e:
            self.error_occurred.emit(f"Database error: {e}")
            if self._db_conn:
                self._db_conn.close()
            self._db_conn = None

    def load_from_file(self, file_path):
        """Loads connections from a specified SQLite database file."""
        if self._db_conn:
            self._db_conn.close()
        
        self._db_path = file_path
        self._ensure_database_exists()
        
        # 【核心修复】将新加载的DB路径持久化到配置文件
        self.context.config_service.set_option("RemoteTerminal", "config_path", file_path)
        self.context.config_service.save_config()
        
        self.connections_changed.emit()

    def get_all_connections_by_group(self):
        """Returns all connections, structured as a dictionary of groups."""
        if not self._db_conn:
            return {}
            
        groups = {}
        try:
            cursor = self._db_conn.cursor()
            cursor.execute("SELECT * FROM connections ORDER BY group_name, name")
            for row in cursor.fetchall():
                group = row['group_name']
                if group not in groups:
                    groups[group] = []
                groups[group].append(dict(row))
            return groups
        except sqlite3.Error as e:
            self.error_occurred.emit(f"Failed to fetch connections: {e}")
            return {}

    def add_connection(self, conn_data):
        """Adds a new connection to the database."""
        sql = """
            INSERT INTO connections (name, group_name, hostname, port, username, password)
            VALUES (:name, :group_name, :hostname, :port, :username, :password)
        """
        try:
            cursor = self._db_conn.cursor()
            cursor.execute(sql, conn_data)
            self._db_conn.commit()
            self.connections_changed.emit()
            return True
        except sqlite3.IntegrityError:
            self.error_occurred.emit(f"Error: A connection named '{conn_data['name']}' already exists in group '{conn_data['group_name']}'.")
            return False
        except sqlite3.Error as e:
            self.error_occurred.emit(f"Failed to add connection: {e}")
            return False

    def update_connection(self, connection_id, conn_data):
        """Updates an existing connection."""
        conn_data['id'] = connection_id
        sql = """
            UPDATE connections SET
                name = :name,
                group_name = :group_name,
                hostname = :hostname,
                port = :port,
                username = :username,
                password = :password
            WHERE id = :id
        """
        try:
            cursor = self._db_conn.cursor()
            cursor.execute(sql, conn_data)
            self._db_conn.commit()
            self.connections_changed.emit()
            return True
        except sqlite3.Error as e:
            self.error_occurred.emit(f"Failed to update connection: {e}")
            return False

    def delete_connection(self, connection_id):
        """Deletes a connection from the database."""
        sql = "DELETE FROM connections WHERE id = ?"
        try:
            cursor = self._db_conn.cursor()
            cursor.execute(sql, (connection_id,))
            self._db_conn.commit()
            self.connections_changed.emit()
            return True
        except sqlite3.Error as e:
            self.error_occurred.emit(f"Failed to delete connection: {e}")
            return False

    def close(self):
        """Closes the database connection."""
        if self._db_conn:
            self._db_conn.close()