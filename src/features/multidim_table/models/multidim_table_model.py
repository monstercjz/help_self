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

    def save_to_db(self):
        """将当前数据保存到数据库。"""
        if self.active_table is None:
            return False, "没有活动的表。"
        if self._original_df.empty:
            return False, "没有数据可保存。"
        
        try:
            if not self.conn: return False, "数据库未连接。"
            self._original_df.to_sql(self.active_table, self.conn, if_exists='replace', index=False)
            return True, None
        except Exception as e:
            return False, str(e)

    def load_from_db(self, table_name: str):
        """从数据库加载指定表的数据。"""
        try:
            if not self.conn: return False, "数据库未连接。"
            self._df = pd.read_sql(f'SELECT * FROM "{table_name}"', self.conn)
            self._original_df = self._df.copy()
            self.active_table = table_name
            self.data_changed.emit()
            return True, None
        except Exception as e:
            return False, str(e)

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
            cursor.execute(f'ALTER TABLE "{table_name}" ADD COLUMN "{column_name}" {column_type}')
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
        """从表中删除一个列。"""
        try:
            if not self.conn: return False, "数据库未连接。"
            # 1. 从数据库读取当前表
            df = pd.read_sql(f'SELECT * FROM "{table_name}"', self.conn)

            # 2. 在DataFrame中删除列
            if column_name in df.columns:
                df = df.drop(columns=[column_name])
            else:
                return False, f"列 '{column_name}' 不存在。"

            # 3. 将修改后的DataFrame写回数据库，覆盖原表
            df.to_sql(table_name, self.conn, if_exists='replace', index=False)
            
            return True, None
        except Exception as e:
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
