# src/features/remote_terminal/services/connection_db_service.py
import sqlite3
import logging
from typing import Dict, Any, List, Set
from src.services.sqlite_base_service import SqlDataService

class ConnectionDBService(SqlDataService):
    """
    Manages the database operations for SSH connection configurations.
    Inherits from SqlDataService to handle common DB tasks.
    """
    TABLE_NAME: str = "connections"
    EXPECTED_COLUMNS: Set[str] = {
        'id', 'name', 'group_name', 'hostname', 'port', 'username', 'password'
    }

    def _create_table(self):
        """Creates the 'connections' table if it doesn't exist."""
        try:
            cursor = self.conn.cursor()
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
            self.conn.commit()
            logging.info(f"Database table '{self.TABLE_NAME}' initialized.")
        except sqlite3.Error as e:
            logging.error(f"Failed to create table '{self.TABLE_NAME}': {e}", exc_info=True)
            raise

    def get_all_connections_by_group(self) -> Dict[str, List[Dict[str, Any]]]:
        """Returns all connections, structured as a dictionary of groups."""
        if not self.conn:
            return {}
            
        groups = {}
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT * FROM connections ORDER BY group_name, name")
            for row in cursor.fetchall():
                group = row['group_name']
                if group not in groups:
                    groups[group] = []
                groups[group].append(dict(row))
            return groups
        except sqlite3.Error as e:
            logging.error(f"Failed to fetch connections: {e}", exc_info=True)
            return {}

    def add_connection(self, conn_data: Dict[str, Any]) -> bool:
        """Adds a new connection to the database."""
        sql = """
            INSERT INTO connections (name, group_name, hostname, port, username, password)
            VALUES (:name, :group_name, :hostname, :port, :username, :password)
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute(sql, conn_data)
            self.conn.commit()
            return True
        except sqlite3.IntegrityError:
            logging.warning(f"A connection named '{conn_data['name']}' already exists in group '{conn_data['group_name']}'.")
            return False
        except sqlite3.Error as e:
            logging.error(f"Failed to add connection: {e}", exc_info=True)
            return False

    def update_connection(self, connection_id: int, conn_data: Dict[str, Any]) -> bool:
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
            cursor = self.conn.cursor()
            cursor.execute(sql, conn_data)
            self.conn.commit()
            return True
        except sqlite3.Error as e:
            logging.error(f"Failed to update connection: {e}", exc_info=True)
            return False

    def delete_connection(self, connection_id: int) -> bool:
        """Deletes a connection from the database."""
        sql = "DELETE FROM connections WHERE id = ?"
        try:
            cursor = self.conn.cursor()
            cursor.execute(sql, (connection_id,))
            self.conn.commit()
            return True
        except sqlite3.Error as e:
            logging.error(f"Failed to delete connection: {e}", exc_info=True)
            return False