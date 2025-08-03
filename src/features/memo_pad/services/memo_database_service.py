# src/features/memo_pad/services/memo_database_service.py

import sqlite3
import os
import logging # 导入 logging 模块
from datetime import datetime
from typing import List, Optional

from src.features.memo_pad.models.memo_model import Memo

class MemoDatabaseService:
    """
    负责处理备忘录数据与SQLite数据库之间所有交互的服务。
    """
    def __init__(self, db_path: str):
        """
        初始化数据库服务。
        
        Args:
            db_path (str): 数据库文件的路径。
        """
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self.db_path = db_path
        self._create_table()

    def _get_connection(self):
        """获取数据库连接。"""
        return sqlite3.connect(self.db_path)

    def _check_write_access(self, conn: sqlite3.Connection) -> bool:
        """
        尝试在数据库中执行一个简单的写入操作，以验证写入权限。
        """
        try:
            cursor = conn.cursor()
            # 尝试创建一个临时表并立即删除
            cursor.execute("CREATE TABLE IF NOT EXISTS _temp_write_test (id INTEGER)")
            cursor.execute("DROP TABLE IF EXISTS _temp_write_test")
            conn.commit()
            return True
        except sqlite3.OperationalError as e:
            # 例如，数据库文件被锁定或只读
            logging.error(f"Database write access check failed: {e}")
            return False
        except Exception as e:
            logging.error(f"An unexpected error occurred during write access check: {e}")
            return False

    def _create_table(self):
        """如果表不存在，则创建 'memos' 表。"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS memos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    content TEXT NOT NULL,
                    created_at TIMESTAMP NOT NULL,
                    updated_at TIMESTAMP NOT NULL
                )
            """)
            conn.commit()

    def validate_database_schema(self) -> bool:
        """
        验证当前数据库是否包含预期的 'memos' 表及其正确的结构。
        如果 'memos' 表不存在，则返回 True，表示可以创建。
        如果存在，则检查其列结构是否符合预期。
        同时检查数据库的写入权限。
        """
        try:
            with self._get_connection() as conn:
                # 1. 检查写入权限
                if not self._check_write_access(conn):
                    return False

                # 2. 检查 'memos' 表是否存在
                cursor = conn.cursor()
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='memos'")
                if cursor.fetchone() is None:
                    # 'memos' 表不存在，表示这是一个新的或共享的数据库，可以创建
                    return True

                # 3. 如果 'memos' 表存在，则检查其列结构
                cursor.execute("PRAGMA table_info(memos)")
                columns = cursor.fetchall()
                column_names = {col[1] for col in columns} # col[1] 是列名

                expected_columns = {'id', 'title', 'content', 'created_at', 'updated_at'}
                if not expected_columns.issubset(column_names):
                    logging.warning(f"Memo table schema mismatch. Expected columns: {expected_columns}, Found: {column_names}")
                    return False # 缺少预期的列

                # 可以进一步检查列的数据类型、非空约束等，但对于SQLite通常不是严格必需的
                # 例如：
                # for col in columns:
                #     name, type, notnull, pk = col[1], col[2], col[3], col[5]
                #     if name == 'title' and (type.upper() != 'TEXT' or notnull != 1): return False
                #     if name == 'created_at' and (type.upper() != 'TIMESTAMP' or notnull != 1): return False

                # 4. 尝试执行一个简单的查询，确保数据库可读
                cursor.execute("SELECT COUNT(*) FROM memos")
                cursor.fetchone() # 确保查询成功

            return True
        except sqlite3.Error as e:
            logging.error(f"Database schema validation or read access failed: {e}")
            return False
        except Exception as e:
            logging.error(f"An unexpected error occurred during database schema validation: {e}")
            return False

    def create_memo(self, title: str, content: str) -> Memo:
        """创建一条新的备忘录。"""
        now = datetime.now()
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO memos (title, content, created_at, updated_at) VALUES (?, ?, ?, ?)",
                (title, content, now, now)
            )
            conn.commit()
            new_id = cursor.lastrowid
            return Memo(id=new_id, title=title, content=content, created_at=now, updated_at=now)

    def get_all_memos(self) -> List[Memo]:
        """获取所有的备忘录。"""
        with self._get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM memos ORDER BY updated_at DESC")
            rows = cursor.fetchall()
            memos = []
            for row in rows:
                row_dict = dict(row)
                row_dict['created_at'] = datetime.fromisoformat(row_dict['created_at'])
                row_dict['updated_at'] = datetime.fromisoformat(row_dict['updated_at'])
                memos.append(Memo(**row_dict))
            return memos

    def update_memo(self, memo_id: int, title: str, content: str) -> Optional[Memo]:
        """更新一条备忘录。"""
        now = datetime.now()
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE memos SET title = ?, content = ?, updated_at = ? WHERE id = ?",
                (title, content, now, memo_id)
            )
            conn.commit()
            if cursor.rowcount > 0:
                # To get the full object back, we need to fetch it.
                return self.get_memo(memo_id)
        return None

    def delete_memo(self, memo_id: int) -> bool:
        """删除一条备忘录。"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM memos WHERE id = ?", (memo_id,))
            conn.commit()
            return cursor.rowcount > 0

    def get_memo(self, memo_id: int) -> Optional[Memo]:
        """根据ID获取单条备忘录。"""
        with self._get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM memos WHERE id = ?", (memo_id,))
            row = cursor.fetchone()
            if not row:
                return None
            row_dict = dict(row)
            row_dict['created_at'] = datetime.fromisoformat(row_dict['created_at'])
            row_dict['updated_at'] = datetime.fromisoformat(row_dict['updated_at'])
            return Memo(**row_dict)
