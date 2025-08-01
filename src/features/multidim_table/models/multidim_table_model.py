# src/features/multidim_table/models/multidim_table_model.py
import pandas as pd
import sqlite3
from PySide6.QtCore import QObject, Signal

class MultidimTableModel(QObject):
    """
    多维表格的数据模型，负责处理数据的加载、存储和操作。
    """
    data_changed = Signal()
    tables_changed = Signal()
    db_connection_changed = Signal(str)

    def __init__(self):
        super().__init__()
        self._df = pd.DataFrame()
        self._original_df = pd.DataFrame()
        self.conn = None
        self.active_table = None

    @property
    def dataframe(self) -> pd.DataFrame:
        return self._df

    def connect_to_db(self, db_path: str):
        """连接到一个新的数据库文件。"""
        try:
            if self.conn:
                self.conn.close()
            
            self.conn = sqlite3.connect(db_path, check_same_thread=False)
            self.db_connection_changed.emit(db_path)
            self.tables_changed.emit() # 触发刷新表列表
            return True, None
        except Exception as e:
            self.conn = None
            self.db_connection_changed.emit(None)
            return False, str(e)

    def load_from_excel(self, file_path: str):
        """从Excel文件加载数据。"""
        try:
            self._df = pd.read_excel(file_path)
            self._original_df = self._df.copy()
            self.data_changed.emit()
            return True, None
        except Exception as e:
            return False, str(e)

    def get_column_names(self) -> list[str]:
        """获取所有列名。"""
        return self._df.columns.tolist()

    def get_data_for_view(self):
        """返回用于视图展示的数据。"""
        if self._df.empty:
            return [], []
        if self._df.empty:
            return [], []
        
        # 对于多级索引的透视表，我们需要将其展平以便在QTableView中显示
        if isinstance(self._df.index, pd.MultiIndex):
            # 将多级索引转换为列
            df_reset = self._df.reset_index()
            headers = df_reset.columns.tolist()
            data = df_reset.values.tolist()
        else:
            headers = self._df.columns.tolist()
            data = self._df.values.tolist()
            # 如果索引有名字，也把它作为一列
            if self._df.index.name:
                headers.insert(0, self._df.index.name)
                for i, row in enumerate(data):
                    row.insert(0, self._df.index[i])

        return headers, data

    def create_pivot_table(self, config: dict):
        """根据配置创建数据透视表。"""
        if self._original_df.empty:
            return False, "请先加载数据。"
        
        rows = config.get("rows", [])
        columns = config.get("columns", [])
        values = config.get("values", [])

        if not values:
            return False, "请至少选择一个度量值。"
            
        try:
            # 使用aggfunc='sum'作为默认聚合函数
            pivot_df = self._original_df.pivot_table(
                index=rows,
                columns=columns,
                values=values,
                aggfunc='sum'
            )
            self._df = pivot_df
            self.data_changed.emit()
            return True, None
        except Exception as e:
            return False, str(e)

    def create_pivot_table_from_df(self, df: pd.DataFrame, pivot_config: dict):
        """
        根据配置从给定的DataFrame创建数据透视表。
        df: 要进行透视操作的DataFrame。
        pivot_config: 包含 'rows', 'columns', 'values', 'aggfunc' 的字典。
        """
        rows = pivot_config.get("rows", [])
        columns = pivot_config.get("columns", [])
        values = pivot_config.get("values", [])
        aggfunc = pivot_config.get("aggfunc", "sum") # 默认聚合函数为sum

        if not values:
            return False, None, "请至少选择一个度量值。"
        
        try:
            pivot_df = df.pivot_table(
                index=rows,
                columns=columns,
                values=values,
                aggfunc=aggfunc
            )
            return True, pivot_df, None
        except Exception as e:
            return False, None, str(e)

    def get_table_list(self):
        """获取数据库中所有用户创建的表的列表。"""
        if not self.conn:
            return [], "数据库未连接。"
        try:
            cursor = self.conn.cursor()
            # 查询所有非系统表的表名
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
            tables = [row[0] for row in cursor.fetchall()]
            return tables, None
        except Exception as e:
            return [], str(e)

    def create_table(self, table_name: str, columns: list[str]):
        """创建一个新表。"""
        if not table_name or not columns:
            return False, "表名和列名不能为空。"
        
        try:
            if not self.conn: return False, "数据库未连接。"
            # 创建一个包含指定列的空DataFrame，然后用to_sql来创建表
            empty_df = pd.DataFrame(columns=columns)
            empty_df.to_sql(table_name, self.conn, index=False, if_exists='fail')
            self.conn.commit() # 显式提交事务，确保表被真正创建
            self.tables_changed.emit()
            return True, None
        except Exception as e:
            return False, str(e)

    def replace_table_data_transaction(self, table_name: str, dataframe: pd.DataFrame) -> tuple[bool, str | None]:
        """
        在一个事务中，安全地替换一个表的所有数据。
        此方法首先删除表中的所有现有行，然后插入DataFrame中的新行。
        """
        if table_name is None:
            return False, "没有活动的表。"
        if dataframe.empty:
            # 允许保存一个空表（即清空表）
            pass

        cursor = self.conn.cursor()
        try:
            if not self.conn: return False, "数据库未连接。"
            
            cursor.execute("BEGIN TRANSACTION;")
            
            # 1. 清空表
            cursor.execute(f'DELETE FROM "{table_name}";')
            
            # 2. 插入新数据
            dataframe.to_sql(table_name, self.conn, if_exists='append', index=False)
            
            # 3. 提交事务
            self.conn.commit()
            
            return True, None
        except Exception as e:
            self.conn.rollback()
            return False, str(e)

    def load_from_db(self, table_name: str, limit: int = -1, offset: int = 0, filter_column: str = None, filter_value: str = None):
        """从数据库加载指定表的数据，支持分页和筛选。"""
        try:
            if not self.conn: return False, "数据库未连接。"
            
            params = []
            query = f'SELECT * FROM "{table_name}"'
            
            where_clauses = []
            if filter_column and filter_value:
                # 使用 LIKE 进行模糊匹配
                where_clauses.append(f'"{filter_column}" LIKE ?')
                params.append(f'%{filter_value}%')

            if where_clauses:
                query += " WHERE " + " AND ".join(where_clauses)

            if limit > 0:
                query += f" LIMIT {limit} OFFSET {offset}"

            self._df = pd.read_sql(query, self.conn, params=params)
            self._original_df = self._df.copy()
            self.active_table = table_name
            self.data_changed.emit()
            return True, None
        except Exception as e:
            return False, str(e)

    def get_total_row_count(self, table_name: str, filter_column: str = None, filter_value: str = None):
        """获取表的总行数，支持筛选。"""
        try:
            if not self.conn: return 0, "数据库未连接。"
            
            params = []
            query = f'SELECT COUNT(*) FROM "{table_name}"'
            
            where_clauses = []
            if filter_column and filter_value:
                where_clauses.append(f'"{filter_column}" LIKE ?')
                params.append(f'%{filter_value}%')

            if where_clauses:
                query += " WHERE " + " AND ".join(where_clauses)

            cursor = self.conn.cursor()
            cursor.execute(query, params)
            count = cursor.fetchone()[0]
            return count, None
        except Exception as e:
            return 0, str(e)

    def add_row(self, data: dict):
        """向DataFrame中添加新的一行。"""
        new_row_df = pd.DataFrame([data])
        self._original_df = pd.concat([self._original_df, new_row_df], ignore_index=True)
        # 立即更新主视图的数据，以便用户可以看到变化
        self._df = self._original_df.copy()
        self.data_changed.emit()

    def delete_table(self, table_name: str):
        """删除一个数据库表。"""
        try:
            if not self.conn: return False, "数据库未连接。"
            cursor = self.conn.cursor()
            cursor.execute(f'DROP TABLE IF EXISTS "{table_name}"')
            self.conn.commit()
            self.tables_changed.emit()
            return True, None
        except Exception as e:
            return False, str(e)

    def add_column(self, table_name: str, column_name: str, column_type: str = "TEXT"):
        """向表中添加一个新列。"""
        try:
            if not self.conn: return False, "数据库未连接。"
            cursor = self.conn.cursor()
            # 将类型用引号括起来，以支持包含特殊字符的类型名，如 ENUM(A,B,C)
            cursor.execute(f'ALTER TABLE "{table_name}" ADD COLUMN "{column_name}" "{column_type}"')
            self.conn.commit()
            return True, None
        except Exception as e:
            return False, str(e)

    def get_table_schema(self, table_name: str):
        """获取表的结构信息。"""
        try:
            if not self.conn: return [], "数据库未连接。"
            cursor = self.conn.cursor()
            cursor.execute(f'PRAGMA table_info("{table_name}")')
            schema = [{"name": row[1], "type": row[2]} for row in cursor.fetchall()]
            return schema, None
        except Exception as e:
            return [], str(e)

    def delete_column(self, table_name: str, column_name: str):
        """从表中删除一个列（通过重建表实现以保证类型安全）。"""
        try:
            if not self.conn: return False, "数据库未连接。"
            
            cursor = self.conn.cursor()

            # 1. 获取当前表结构
            cursor.execute(f'PRAGMA table_info("{table_name}")')
            columns_info = cursor.fetchall()
            
            if not any(col[1] == column_name for col in columns_info):
                return False, f"列 '{column_name}' 不存在。"

            # 2. 创建新的表结构定义（排除要删除的列）
            new_columns_defs = []
            kept_column_names = []
            for col in columns_info:
                name, ctype = col[1], col[2]
                if name != column_name:
                    new_columns_defs.append(f'"{name}" "{ctype}"')
                    kept_column_names.append(f'"{name}"')

            new_table_name = f"{table_name}_new_for_delete"
            columns_def_str = ", ".join(new_columns_defs)
            columns_names_str = ", ".join(kept_column_names)

            # 3. 事务开始
            cursor.execute("BEGIN TRANSACTION;")
            
            # 4. 创建新表
            cursor.execute(f'CREATE TABLE "{new_table_name}" ({columns_def_str})')
            
            # 5. 复制数据
            cursor.execute(f'INSERT INTO "{new_table_name}" ({columns_names_str}) SELECT {columns_names_str} FROM "{table_name}"')
            
            # 6. 删除旧表
            cursor.execute(f'DROP TABLE "{table_name}"')
            
            # 7. 重命名新表
            cursor.execute(f'ALTER TABLE "{new_table_name}" RENAME TO "{table_name}"')
            
            # 8. 提交事务
            self.conn.commit()
            
            return True, None
        except Exception as e:
            if self.conn:
                self.conn.rollback()
            return False, str(e)

    def rename_table(self, old_name: str, new_name: str):
        """重命名一个数据库表。"""
        try:
            if not self.conn: return False, "数据库未连接。"
            cursor = self.conn.cursor()
            cursor.execute(f'ALTER TABLE "{old_name}" RENAME TO "{new_name}"')
            self.conn.commit()
            self.tables_changed.emit()
            return True, None
        except Exception as e:
            return False, str(e)

    def change_column_type(self, table_name: str, column_name: str, new_type: str):
        """更改表中列的数据类型（通过重建表实现）。"""
        try:
            if not self.conn: return False, "数据库未连接。"
            
            # 1. 获取当前表结构
            cursor = self.conn.cursor()
            cursor.execute(f'PRAGMA table_info("{table_name}")')
            columns_info = cursor.fetchall()
            
            # 2. 创建新的表结构定义
            new_columns_defs = []
            column_names = []
            for col in columns_info:
                name = col[1]
                ctype = col[2]
                if name == column_name:
                    # 为新类型加上引号
                    new_columns_defs.append(f'"{name}" "{new_type}"')
                else:
                    # 为旧类型也加上引号，以防万一
                    new_columns_defs.append(f'"{name}" "{ctype}"')
                column_names.append(f'"{name}"')

            new_table_name = f"{table_name}_new"
            columns_def_str = ", ".join(new_columns_defs)
            columns_names_str = ", ".join(column_names)

            # 3. 事务开始
            cursor.execute("BEGIN TRANSACTION;")
            
            # 4. 创建新表
            cursor.execute(f'CREATE TABLE "{new_table_name}" ({columns_def_str})')
            
            # 5. 复制数据
            cursor.execute(f'INSERT INTO "{new_table_name}" ({columns_names_str}) SELECT {columns_names_str} FROM "{table_name}"')
            
            # 6. 删除旧表
            cursor.execute(f'DROP TABLE "{table_name}"')
            
            # 7. 重命名新表
            cursor.execute(f'ALTER TABLE "{new_table_name}" RENAME TO "{table_name}"')
            
            # 8. 提交事务
            self.conn.commit()
            
            return True, None
        except Exception as e:
            self.conn.rollback()
            return False, str(e)

    def rename_column(self, table_name: str, old_name: str, new_name: str):
        """重命名表中的一个列。"""
        try:
            if not self.conn: return False, "数据库未连接。"
            cursor = self.conn.cursor()
            cursor.execute(f'ALTER TABLE "{table_name}" RENAME COLUMN "{old_name}" TO "{new_name}"')
            self.conn.commit()
            return True, None
        except Exception as e:
            return False, str(e)

    def delete_rows(self, indexes: list[int]):
        """根据索引列表从DataFrame中删除行。"""
        if self._original_df.empty:
            return False, "没有数据可删除。"
        
        try:
            self._original_df = self._original_df.drop(index=indexes).reset_index(drop=True)
            self._df = self._original_df.copy()
            # 注意：这里我们不立即触发data_changed，因为这只是内存中的操作
            # 等待用户点击“保存”后，再统一写入数据库
            return True, None
        except Exception as e:
            return False, str(e)
