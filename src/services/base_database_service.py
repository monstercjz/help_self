# src/services/base_database_service.py
import sqlite3
import os
import logging
from typing import Set

class ValidationFlags:
    """定义用于数据库验证的位字段标志。"""
    CHECK_WRITE_ACCESS = 1  # 0001
    CHECK_TABLE_EXISTS = 2  # 0010
    CHECK_COLUMNS      = 4  # 0100
    CHECK_READABLE     = 8  # 1000
    
    # 默认进行所有检查
    FULL_CHECK = CHECK_WRITE_ACCESS | CHECK_TABLE_EXISTS | CHECK_COLUMNS | CHECK_READABLE

class BaseDatabaseService:
    """
    一个包含通用数据库功能（如连接、验证）的基类。
    所有特定功能的数据库服务都应继承自此类。
    """
    # --- 子类必须覆盖的属性 ---
    TABLE_NAME: str = ""
    EXPECTED_COLUMNS: Set[str] = set()
    # --- 子类可以按需覆盖的属性 ---
    VALIDATION_FLAGS: int = ValidationFlags.FULL_CHECK

    def __init__(self, db_path: str):
        """
        初始化数据库服务。
        """
        if not self.TABLE_NAME or not self.EXPECTED_COLUMNS:
            raise NotImplementedError("Subclasses must define TABLE_NAME and EXPECTED_COLUMNS.")

        self.db_path = db_path
        self.conn = None
        try:
            os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
            self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
            self.conn.row_factory = sqlite3.Row
            logging.info(f"[{self.TABLE_NAME}] 数据库连接已建立: {self.db_path}")
            self._create_table()
        except sqlite3.Error as e:
            logging.error(f"[{self.TABLE_NAME}] 数据库连接或初始化失败: {e}", exc_info=True)
            raise

    def _create_table(self):
        """子类必须实现此方法来定义其表的创建SQL。"""
        raise NotImplementedError("Subclasses must implement _create_table.")

    def _check_write_access(self) -> bool:
        """
        验证数据库的写入权限。
        """
        if not self.conn:
            return False
        try:
            cursor = self.conn.cursor()
            cursor.execute("CREATE TABLE IF NOT EXISTS _temp_write_test (id INTEGER)")
            cursor.execute("DROP TABLE IF EXISTS _temp_write_test")
            self.conn.commit()
            return True
        except sqlite3.Error as e:
            logging.error(f"[{self.TABLE_NAME}] 数据库写入权限检查失败: {e}")
            return False

    def validate_database_schema(self) -> bool:
        """
        执行通用的数据库模式验证。
        """
        if not self.conn:
            return False
        try:
            logging.debug(f"[{self.TABLE_NAME}] [验证流程开始] 使用标志: {self.VALIDATION_FLAGS}")
            
            # 1. 检查写入权限
            if self.VALIDATION_FLAGS & ValidationFlags.CHECK_WRITE_ACCESS:
                logging.debug(f"[{self.TABLE_NAME}] [验证 1/4] 检查写入权限...")
                if not self._check_write_access():
                    logging.warning(f"[{self.TABLE_NAME}] [验证 1/4] 写入权限检查失败。")
                    return False
                logging.debug(f"[{self.TABLE_NAME}] [验证 1/4] 写入权限检查通过。")

            cursor = self.conn.cursor()
            # 2. 检查表是否存在
            if self.VALIDATION_FLAGS & ValidationFlags.CHECK_TABLE_EXISTS:
                logging.debug(f"[{self.TABLE_NAME}] [验证 2/4] 检查表 '{self.TABLE_NAME}' 是否存在...")
                cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{self.TABLE_NAME}'")
                table_exists = cursor.fetchone() is not None
                if not table_exists:
                    logging.info(f"[{self.TABLE_NAME}] [验证 2/4] 表不存在，验证通过 (将被创建)。")
                    return True
                logging.debug(f"[{self.TABLE_NAME}] [验证 2/4] 表已存在。")

            # 3. 检查表结构
            if self.VALIDATION_FLAGS & ValidationFlags.CHECK_COLUMNS:
                logging.debug(f"[{self.TABLE_NAME}] [验证 3/4] 检查列结构...")
                if not self.EXPECTED_COLUMNS:
                     logging.warning(f"[{self.TABLE_NAME}] [验证 3/4] 配置了列检查，但期望列集合为空。")
                else:
                    cursor.execute(f"PRAGMA table_info({self.TABLE_NAME})")
                    columns = {col[1] for col in cursor.fetchall()}
                    if not self.EXPECTED_COLUMNS.issubset(columns):
                        logging.warning(f"[{self.TABLE_NAME}] [验证 3/4] 列结构不匹配。期望: {self.EXPECTED_COLUMNS}, 实际: {columns}")
                        return False
                    logging.debug(f"[{self.TABLE_NAME}] [验证 3/4] 列结构检查通过。")
            
            # 4. 检查可读性
            if self.VALIDATION_FLAGS & ValidationFlags.CHECK_READABLE:
                logging.debug(f"[{self.TABLE_NAME}] [验证 4/4] 检查数据库可读性...")
                cursor.execute(f"SELECT COUNT(*) FROM {self.TABLE_NAME}")
                cursor.fetchone()
                logging.debug(f"[{self.TABLE_NAME}] [验证 4/4] 可读性检查通过。")

            logging.info(f"[{self.TABLE_NAME}] [验证流程结束] 所有已配置的检查项均通过。")
            return True
        except sqlite3.Error as e:
            logging.error(f"[{self.TABLE_NAME}] 数据库模式验证因 SQLite 错误而失败: {e}")
            return False

    def close(self):
        """关闭数据库连接。"""
        if self.conn:
            self.conn.close()
            logging.info(f"Database connection closed for {self.TABLE_NAME}.")