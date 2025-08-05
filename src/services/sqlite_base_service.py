# src/services/sqlite_base_service.py
import sqlite3
import os
import logging
from typing import Set
from enum import Enum, auto

class SchemaType(Enum):
    """定义数据库的模式类型，以控制验证级别。"""
    FIXED = auto()    # 固定的、需要严格验证的模式
    DYNAMIC = auto()  # 动态的、仅需基本连接和可写性检查的模式

class ValidationFlags:
    """定义用于数据库验证的位字段标志。"""
    CHECK_WRITE_ACCESS = 1  # 0001
    CHECK_TABLE_EXISTS = 2  # 0010
    CHECK_COLUMNS      = 4  # 0100
    CHECK_READABLE     = 8  # 1000
    
    # 默认进行所有检查
    FULL_CHECK = CHECK_WRITE_ACCESS | CHECK_TABLE_EXISTS | CHECK_COLUMNS | CHECK_READABLE

class SqlDataService:
    """
    一个包含通用数据库功能（如连接、验证）的基类。
    支持单表（旧版兼容）和多表（新版）模式。
    """
    # --- 新版：用于定义多个表 ---
    TABLE_SCHEMAS: dict[str, Set[str]] = {}
    
    # --- 旧版（将被弃用）：用于向后兼容 ---
    TABLE_NAME: str = ""
    EXPECTED_COLUMNS: Set[str] = set()

    # --- 子类可以按需覆盖的属性 ---
    VALIDATION_FLAGS: int = ValidationFlags.FULL_CHECK

    def __init__(self, db_path: str):
        """
        初始化数据库服务。
        自动处理新旧两种模式的子类。
        """
        self.service_name = self.__class__.__name__
        self.schema_type = SchemaType.FIXED  # 默认为严格模式
        
        # --- 向后兼容层 ---
        # 如果子类使用的是旧的单表定义，则自动转换为新的多表结构
        if not self.TABLE_SCHEMAS and self.TABLE_NAME:
            logging.warning(
                f"[src.services.sqlite_base_service.{self.service_name}.__init__] [SqlDataService] The use of TABLE_NAME and EXPECTED_COLUMNS is deprecated. "
                f"Please migrate to TABLE_SCHEMAS."
            )
            self.TABLE_SCHEMAS = {self.TABLE_NAME: self.EXPECTED_COLUMNS}

        # 不再在此处进行 TABLE_SCHEMAS 的强制检查

        self.db_path = db_path
        self.conn = None
        try:
            os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
            self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
            self.conn.row_factory = sqlite3.Row
            logging.info(f"[src.services.sqlite_base_service.{self.service_name}.__init__] [SqlDataService] 数据库连接已建立: {self.db_path}")
            self._create_tables()
        except sqlite3.Error as e:
            logging.error(f"[src.services.sqlite_base_service.{self.service_name}.__init__] [SqlDataService] 数据库连接或初始化失败: {e}", exc_info=True)
            raise

    def _create_tables(self):
        """
        为 TABLE_SCHEMAS 中的所有表创建表。
        新子类应覆盖此方法。为了向后兼容，此方法的默认实现会调用旧的 _create_table()。
        """
        self._create_table()

    def _create_table(self):
        """
        [已弃用] 子类应实现此方法来定义其表的创建SQL。_create_table() 方法 (第 76-81 行) 是抽象方法，raise NotImplementedError 明确表示子类必须实现它
        请改用 _create_tables。
        """
        raise NotImplementedError("Subclasses must implement _create_tables() or the legacy _create_table().")

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
            logging.debug(f"[src.services.sqlite_base_service.{self.service_name}._check_write_access] [SqlDataService] 数据库写入权限检查成功")
            return True
        except sqlite3.Error as e:
            logging.error(f"[src.services.sqlite_base_service.{self.service_name}._check_write_access] [SqlDataService] 数据库写入权限检查失败: {e}")
            return False

    def set_schema_type(self, schema_type: SchemaType):
        """设置数据库的模式类型，以在验证时采用不同策略。"""
        self.schema_type = schema_type

    def validate_database_schema(self) -> bool:
        """
        根据 schema_type 对数据库执行不同级别的验证。
        - FIXED: 严格的模式验证。
        - DYNAMIC: 仅检查连接和可写性。
        """
        if not self.conn:
            return False
        
        service_name = self.service_name
        logging.info(f"[src.services.sqlite_base_service.{service_name}.validate_database_schema] [SqlDataService] [验证流程开始] 模式: {self.schema_type.name}, 标志: {self.VALIDATION_FLAGS}")

        # 步骤 1: 始终检查写入权限
        if not self._check_write_access():
            logging.warning(f"[src.services.sqlite_base_service.{service_name}.validate_database_schema] [SqlDataService] 写入权限检查失败。")
            return False
        logging.debug(f"[src.services.sqlite_base_service.{service_name}.validate_database_schema] [SqlDataService] 写入权限检查通过。")

        # 如果是动态模式，到此为止即为验证通过
        if self.schema_type == SchemaType.DYNAMIC:
            logging.info(f"[src.services.sqlite_base_service.{service_name}.validate_database_schema] [SqlDataService] [验证流程结束] DYNAMIC 模式验证通过（仅检查可写性）。")
            return True

        # --- 以下为 FIXED 模式的严格验证 ---
        if not self.TABLE_SCHEMAS:
            raise NotImplementedError(
                "Subclasses must define TABLE_SCHEMAS for FIXED schema_type validation."
            )
            
        try:
            cursor = self.conn.cursor()
            
            for table_name, expected_columns in self.TABLE_SCHEMAS.items():
                # 1. 检查表是否存在
                if self.VALIDATION_FLAGS & ValidationFlags.CHECK_TABLE_EXISTS:
                    logging.debug(f"[src.services.sqlite_base_service.{service_name}.validate_database_schema] [SqlDataService] [FIXED 验证 1/3] 检查表 '{table_name}' 是否存在...")
                    cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table_name}'")
                    if cursor.fetchone() is None:
                        logging.info(f"[src.services.sqlite_base_service.{service_name}.validate_database_schema] [SqlDataService] [FIXED 验证 1/3] 表 '{table_name}' 不存在，跳过后续检查 (将被创建)。")
                        continue
                    logging.debug(f"[src.services.sqlite_base_service.{service_name}.validate_database_schema] [SqlDataService] [FIXED 验证 1/3] 表 '{table_name}' 已存在。")

                # 2. 检查表结构
                if self.VALIDATION_FLAGS & ValidationFlags.CHECK_COLUMNS:
                    logging.debug(f"[src.services.sqlite_base_service.{service_name}.validate_database_schema] [SqlDataService] [FIXED 验证 2/3] 检查表 '{table_name}' 的列结构...")
                    if not expected_columns:
                        logging.warning(f"[src.services.sqlite_base_service.{service_name}.validate_database_schema] [SqlDataService] [FIXED 验证 2/3] 为表 '{table_name}' 配置了列检查，但期望列集合为空。")
                    else:
                        cursor.execute(f"PRAGMA table_info({table_name})")
                        current_columns = {col[1] for col in cursor.fetchall()}
                        if not expected_columns.issubset(current_columns):
                            missing = expected_columns - current_columns
                            logging.warning(f"[src.services.sqlite_base_service.{service_name}.validate_database_schema] [SqlDataService] [FIXED 验证 2/3] 表 '{table_name}' 列结构不匹配。缺少列: {missing}。")
                            return False
                        logging.debug(f"[src.services.sqlite_base_service.{service_name}.validate_database_schema] [SqlDataService] [FIXED 验证 2/3] 表 '{table_name}' 列结构检查通过。")

                # 3. 检查可读性
                if self.VALIDATION_FLAGS & ValidationFlags.CHECK_READABLE:
                    logging.debug(f"[src.services.sqlite_base_service.{service_name}.validate_database_schema] [SqlDataService] [FIXED 验证 3/3] 检查表 '{table_name}' 的可读性...")
                    cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                    cursor.fetchone()
                    logging.debug(f"[src.services.sqlite_base_service.{service_name}.validate_database_schema] [SqlDataService] [FIXED 3/3] 表 '{table_name}' 可读性检查通过。")

            logging.info(f"[src.services.sqlite_base_service.{service_name}.validate_database_schema] [SqlDataService] [验证流程结束] 所有已配置的检查项均通过。")
            return True
        except sqlite3.Error as e:
            logging.error(f"[src.services.sqlite_base_service.{service_name}.validate_database_schema] [SqlDataService] 数据库模式验证因 SQLite 错误而失败: {e}")
            return False

    def close(self):
        """关闭数据库连接。"""
        if self.conn:
            self.conn.close()
            logging.info(f"[src.services.sqlite_base_service.{self.service_name}.close] [SqlDataService] [连接关闭] Database connection closed for {self.service_name}.")

    @staticmethod
    def check_db_writability(db_path: str) -> (bool, str):
        """
        检查指定的SQLite数据库文件是否具有写入权限。

        Args:
            db_path (str): 数据库文件的路径。

        Returns:
            tuple[bool, str]: 一个元组 (is_writable, error_message)。
                              如果可写，返回 (True, "")。
                              如果不可写，返回 (False, "具体的错误信息")。
        """
        conn = None
        try:
            # 确保目录存在
            dir_name = os.path.dirname(db_path)
            if dir_name:
                os.makedirs(dir_name, exist_ok=True)
            
            conn = sqlite3.connect(db_path, check_same_thread=False)
            cursor = conn.cursor()
            cursor.execute("CREATE TABLE IF NOT EXISTS _temp_write_test (id INTEGER)")
            cursor.execute("DROP TABLE IF EXISTS _temp_write_test")
            conn.commit()
            return True, ""
        except sqlite3.Error as e:
            error_msg = f"[src.services.sqlite_base_service.SqlDataService.check_db_writability] [SqlDataService] [检查失败] 数据库 '{db_path}' 写入权限检查失败: {e}"
            logging.warning(error_msg)
            return False, str(e)
        finally:
            if conn:
                conn.close()