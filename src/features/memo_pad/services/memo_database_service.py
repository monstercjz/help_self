# src/features/memo_pad/services/memo_database_service.py

import sqlite3
import logging
from datetime import datetime
from typing import List, Optional

from src.features.memo_pad.models.memo_model import Memo
from src.services.base_database_service import BaseDatabaseService

class MemoDatabaseService(BaseDatabaseService):
    """
    负责处理备忘录数据与SQLite数据库之间所有交互的服务。
    继承自 BaseDatabaseService，只关注业务逻辑。
    """
    TABLE_NAME = "memos"
    EXPECTED_COLUMNS = {'id', 'title', 'content', 'created_at', 'updated_at'}

    def __init__(self, db_path: str):
        # 调用父类的构造函数来处理连接和通用验证
        super().__init__(db_path)

    def _create_table(self):
        """实现父类的抽象方法，定义 'memos' 表的创建SQL。"""
        if not self.conn: return
        with self.conn as conn:
            cursor = conn.cursor()
            cursor.execute(f"""
                CREATE TABLE IF NOT EXISTS {self.TABLE_NAME} (
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
        if not self.conn: return None
        now = datetime.now()
        with self.conn as conn:
            cursor = conn.cursor()
            cursor.execute(
                f"INSERT INTO {self.TABLE_NAME} (title, content, created_at, updated_at) VALUES (?, ?, ?, ?)",
                (title, content, now, now)
            )
            conn.commit()
            new_id = cursor.lastrowid
            return Memo(id=new_id, title=title, content=content, created_at=now, updated_at=now)

    def get_all_memos(self) -> List[Memo]:
        """获取所有的备忘录。"""
        if not self.conn: return []
        with self.conn as conn:
            cursor = conn.cursor()
            cursor.execute(f"SELECT * FROM {self.TABLE_NAME} ORDER BY updated_at DESC")
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
        if not self.conn: return None
        now = datetime.now()
        with self.conn as conn:
            cursor = conn.cursor()
            cursor.execute(
                f"UPDATE {self.TABLE_NAME} SET title = ?, content = ?, updated_at = ? WHERE id = ?",
                (title, content, now, memo_id)
            )
            conn.commit()
            if cursor.rowcount > 0:
                return self.get_memo(memo_id)
        return None

    def delete_memo(self, memo_id: int) -> bool:
        """删除一条备忘录。"""
        if not self.conn: return False
        with self.conn as conn:
            cursor = conn.cursor()
            cursor.execute(f"DELETE FROM {self.TABLE_NAME} WHERE id = ?", (memo_id,))
            conn.commit()
            return cursor.rowcount > 0

    def get_memo(self, memo_id: int) -> Optional[Memo]:
        """根据ID获取单条备忘录。"""
        if not self.conn: return None
        with self.conn as conn:
            cursor = conn.cursor()
            cursor.execute(f"SELECT * FROM {self.TABLE_NAME} WHERE id = ?", (memo_id,))
            row = cursor.fetchone()
            if not row:
                return None
            row_dict = dict(row)
            row_dict['created_at'] = datetime.fromisoformat(row_dict['created_at'])
            row_dict['updated_at'] = datetime.fromisoformat(row_dict['updated_at'])
            return Memo(**row_dict)
