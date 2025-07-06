# src/features/multidim_table/controllers/multidim_table_controller.py
from PySide6.QtCore import QObject
from src.features.multidim_table.models.multidim_table_model import MultidimTableModel
from src.features.multidim_table.views.db_management_view import DbManagementView
from src.features.multidim_table.views.table_designer_view import TableDesignerView
from src.features.multidim_table.views.add_data_dialog import AddDataDialog
import pandas as pd

class MultidimTableController(QObject):
    """
    多维表格的控制器，负责协调模型和所有视图。
    """
    def __init__(self, model: MultidimTableModel, db_view: DbManagementView):
        super().__init__()
        self._model = model
        self._db_view = db_view
        
        self._connect_signals()
        self._db_view.set_current_db(None) # Initially no db is open

    def _connect_signals(self):
        # 模型信号
        self._model.tables_changed.connect(self._update_table_list)
        self._model.db_connection_changed.connect(self._db_view.set_current_db)

        # 数据库管理视图信号
        self._db_view.create_db_requested.connect(self._on_db_connect)
        self._db_view.open_db_requested.connect(self._on_db_connect)
        self._db_view.create_table_requested.connect(self._on_create_table_requested)
        self._db_view.delete_table_requested.connect(self._on_delete_table_requested)
        self._db_view.rename_table_requested.connect(self._on_rename_table)
        self._db_view.table_selected.connect(self._on_table_selected)

    def _on_db_connect(self, db_path):
        success, err = self._model.connect_to_db(db_path)
        if not success:
            self._db_view.show_error("连接失败", f"无法连接到数据库: {err}")

    def _update_table_list(self):
        tables, err = self._model.get_table_list()
        if err:
            self._db_view.show_error("错误", f"无法加载表列表: {err}")
            self._db_view.update_table_list([])
        else:
            self._db_view.update_table_list(tables)

    def _on_create_table_requested(self, table_name, columns):
        success, err = self._model.create_table(table_name, columns)
        if not success:
            self._db_view.show_error("创建失败", f"无法创建表: {err}")
        else:
            # 创建成功后，立即打开设计器
            self._on_table_selected(table_name)

    def _on_delete_table_requested(self, table_name):
        success, err = self._model.delete_table(table_name)
        if not success:
            self._db_view.show_error("删除失败", f"无法删除表: {err}")

    def _on_table_selected(self, table_name):
        # 加载表的数据和结构
        data_success, data_err = self._model.load_from_db(table_name)
        schema, schema_err = self._model.get_table_schema(table_name)

        if not data_success or schema_err:
            self._db_view.show_error("加载失败", f"无法加载表 '{table_name}': {data_err or schema_err}")
            return

        # 创建并显示表设计器对话框
        designer = TableDesignerView(table_name, self._db_view)
        
        # 填充数据和结构
        headers = self._model._original_df.columns.tolist()
        data = self._model._original_df.values.tolist()
        designer.set_data(headers, data)
        designer.set_schema(schema)
        
        # 连接设计器信号
        designer.add_column_requested.connect(lambda col_name: self._on_add_column(designer, table_name, col_name))
        designer.delete_column_requested.connect(lambda col_name: self._on_delete_column(designer, table_name, col_name))
        designer.rename_column_requested.connect(lambda old, new: self._on_rename_column(designer, table_name, old, new))
        designer.add_row_requested.connect(lambda: self._on_add_row(designer))
        designer.delete_row_requested.connect(lambda rows: self._on_delete_rows(designer, rows))
        designer.save_data_requested.connect(lambda df: self._on_save_data(table_name, df))

        designer.exec()

    def _on_delete_rows(self, designer, rows_to_delete):
        # 从UI模型中直接删除行以获得即时反馈
        # 从后往前删，避免索引变化导致错误
        for row in sorted(rows_to_delete, reverse=True):
            designer.data_table_model.removeRow(row)
        
        # 更新内存中的DataFrame，但不立即保存到数据库
        # 等待用户点击“保存更改”按钮
        current_df = designer.get_data()
        self._model._original_df = current_df
        self._model._df = current_df.copy()

    def _on_add_row(self, designer):
        headers = [designer.data_table_model.horizontalHeaderItem(i).text() for i in range(designer.data_table_model.columnCount())]
        add_dialog = AddDataDialog(headers, designer)
        if add_dialog.exec():
            new_data = add_dialog.get_data()
            designer.add_data_row(list(new_data.values()))

    def _on_delete_column(self, designer, table_name, column_name):
        success, err = self._model.delete_column(table_name, column_name)
        if success:
            # 重新加载数据和结构
            self._model.load_from_db(table_name)
            schema, _ = self._model.get_table_schema(table_name)
            headers = self._model._original_df.columns.tolist()
            data = self._model._original_df.values.tolist()
            designer.set_schema(schema)
            designer.set_data(headers, data)
        else:
            designer.show_error("删除失败", f"无法删除字段: {err}")

    def _on_add_column(self, designer, table_name, column_name):
        success, err = self._model.add_column(table_name, column_name)
        if success:
            # 重新加载数据和结构
            self._model.load_from_db(table_name)
            schema, _ = self._model.get_table_schema(table_name)
            headers = self._model._original_df.columns.tolist()
            data = self._model._original_df.values.tolist()
            designer.set_schema(schema)
            designer.set_data(headers, data)
        else:
            designer.show_error("添加失败", f"无法添加字段: {err}")

    def _on_save_data(self, table_name, dataframe):
        self._model.active_table = table_name
        self._model._original_df = dataframe
        success, err = self._model.save_to_db()
        if not success:
            self._db_view.show_error("保存失败", f"无法保存数据: {err}")

    def _on_rename_table(self, old_name, new_name):
        success, err = self._model.rename_table(old_name, new_name)
        if not success:
            self._db_view.show_error("重命名失败", f"无法重命名表: {err}")

    def _on_rename_column(self, designer, table_name, old_name, new_name):
        success, err = self._model.rename_column(table_name, old_name, new_name)
        if success:
            # 重新加载数据和结构以确保UI完全同步
            self._model.load_from_db(table_name)
            schema, _ = self._model.get_table_schema(table_name)
            headers = self._model._original_df.columns.tolist()
            data = self._model._original_df.values.tolist()
            designer.set_schema(schema)
            designer.set_data(headers, data)
        else:
            designer.show_error("重命名失败", f"无法重命名字段: {err}")
