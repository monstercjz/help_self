# src/features/memo_pad/services/memo_database_service.py

import sqlite3
import os
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
