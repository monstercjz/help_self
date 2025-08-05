# src/features/program_launcher/services/program_launcher_database_service.py
import sqlite3
import logging
from typing import List, Dict, Any, Set

from src.services.sqlite_base_service import SqlDataService

class ProgramLauncherDatabaseService(SqlDataService):
    TABLE_SCHEMAS: Dict[str, Set[str]] = {
        "groups": {"id", "name", "order_index"},
        "programs": {"id", "group_id", "name", "path", "run_as_admin", "order_index"}
    }

    def _create_tables(self):
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS groups (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    order_index INTEGER NOT NULL
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS programs (
                    id TEXT PRIMARY KEY,
                    group_id TEXT NOT NULL,
                    name TEXT NOT NULL,
                    path TEXT NOT NULL,
                    run_as_admin INTEGER NOT NULL,
                    order_index INTEGER NOT NULL,
                    FOREIGN KEY (group_id) REFERENCES groups (id) ON DELETE CASCADE
                )
            """)
            self.conn.commit()
            logging.info(f"[{self.service_name}] Tables 'groups' and 'programs' created or already exist.")
        except sqlite3.Error as e:
            logging.error(f"[{self.service_name}] Error creating tables: {e}")
            raise

    # Group operations
    def get_groups(self) -> List[Dict[str, Any]]:
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM groups ORDER BY order_index")
        return [dict(row) for row in cursor.fetchall()]

    def add_group(self, group_id: str, name: str, order_index: int):
        cursor = self.conn.cursor()
        cursor.execute("INSERT INTO groups (id, name, order_index) VALUES (?, ?, ?)", (group_id, name, order_index))
        self.conn.commit()

    def update_group(self, group_id: str, name: str):
        cursor = self.conn.cursor()
        cursor.execute("UPDATE groups SET name = ? WHERE id = ?", (name, group_id))
        self.conn.commit()

    def delete_group(self, group_id: str):
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM groups WHERE id = ?", (group_id,))
        self.conn.commit()

    def reorder_groups(self, group_ids: List[str]):
        cursor = self.conn.cursor()
        for i, group_id in enumerate(group_ids):
            cursor.execute("UPDATE groups SET order_index = ? WHERE id = ?", (i, group_id))
        self.conn.commit()

    # Program operations
    def get_programs(self) -> Dict[str, Dict[str, Any]]:
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM programs ORDER BY order_index")
        return {row["id"]: dict(row) for row in cursor.fetchall()}

    def add_program(self, program_id: str, group_id: str, name: str, path: str, run_as_admin: bool, order_index: int):
        cursor = self.conn.cursor()
        cursor.execute(
            "INSERT INTO programs (id, group_id, name, path, run_as_admin, order_index) VALUES (?, ?, ?, ?, ?, ?)",
            (program_id, group_id, name, path, 1 if run_as_admin else 0, order_index)
        )
        self.conn.commit()

    def update_program(self, program_id: str, group_id: str, name: str, path: str, run_as_admin: bool):
        cursor = self.conn.cursor()
        cursor.execute(
            "UPDATE programs SET group_id = ?, name = ?, path = ?, run_as_admin = ? WHERE id = ?",
            (group_id, name, path, 1 if run_as_admin else 0, program_id)
        )
        self.conn.commit()

    def delete_program(self, program_id: str):
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM programs WHERE id = ?", (program_id,))
        self.conn.commit()

    def reorder_programs_in_group(self, group_id: str, program_ids: List[str]):
        cursor = self.conn.cursor()
        for i, program_id in enumerate(program_ids):
            cursor.execute("UPDATE programs SET order_index = ? WHERE id = ? AND group_id = ?", (i, program_id, group_id))
        self.conn.commit()