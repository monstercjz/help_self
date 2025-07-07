# src/features/multidim_table/controllers/multidim_table_controller.py
from PySide6.QtCore import QObject, QSettings
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
        
        # 分页状态
        self.page_size = 100  # 每页显示100条
        self.current_page = 1
        self.total_rows = 0
        self.total_pages = 1
        self.current_table_name = None

        self._connect_signals()
        self._db_view.set_current_db(None) # Initially no db is open
        self._load_last_db()

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
        else:
            # 保存成功连接的路径
            settings = QSettings("MyCompany", "MultidimTableApp")
            settings.setValue("last_db_path", db_path)

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
        self.current_table_name = table_name
        self.current_page = 1
        
        # 获取总行数和总页数
        self.total_rows, err = self._model.get_total_row_count(table_name)
        if err:
            self._db_view.show_error("错误", f"无法获取总行数: {err}")
            return
        self.total_pages = (self.total_rows + self.page_size - 1) // self.page_size
        if self.total_pages == 0: self.total_pages = 1

        # 创建并显示表设计器对话框
        designer = TableDesignerView(table_name, self._db_view)
        
        # 连接设计器信号
        designer.page_changed.connect(self._on_page_changed)
        designer.add_column_requested.connect(lambda col_name: self._on_add_column(designer, table_name, col_name))
        designer.delete_column_requested.connect(lambda col_name: self._on_delete_column(designer, table_name, col_name))
        designer.change_column_requested.connect(lambda old_name, new_name, new_type: self._on_change_column(designer, table_name, old_name, new_name, new_type))
        designer.add_row_requested.connect(lambda: self._on_add_row(designer))
        designer.delete_row_requested.connect(lambda rows: self._on_delete_rows(designer, rows))
        designer.save_data_requested.connect(lambda df: self._on_save_data(table_name, df))
        designer.import_requested.connect(lambda path: self._on_import_data(designer, path))
        designer.export_requested.connect(lambda path: self._on_export_data(designer, path))

        # 加载第一页数据
        self._load_page_data(designer)
        
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

    def _on_change_column(self, designer, table_name, old_name, new_name, new_type):
        # 检查字段类型是否改变
        schema, _ = self._model.get_table_schema(table_name)
        old_type = next((col['type'] for col in schema if col['name'] == old_name), None)

        type_changed = (old_type != new_type)
        name_changed = (old_name != new_name)

        if not type_changed and not name_changed:
            return # 没有变化

        final_success = True
        error_message = ""

        # 1. 如果类型改变，则重建表
        if type_changed:
            success, err = self._model.change_column_type(table_name, old_name, new_type)
            if not success:
                final_success = False
                error_message += f"更改类型失败: {err}\n"
        
        # 2. 如果名称改变，则重命名
        # 如果类型已改变，新名称应在新表上操作，但我们的模型已处理
        # 如果类型未改变，则在原表上操作
        if name_changed and final_success:
            # 如果类型也变了，重命名操作需要针对新列名
            current_name = old_name if not type_changed else old_name
            success, err = self._model.rename_column(table_name, current_name, new_name)
            if not success:
                final_success = False
                error_message += f"重命名失败: {err}\n"

        # 3. 刷新UI
        if final_success:
            self._model.load_from_db(table_name)
            schema, _ = self._model.get_table_schema(table_name)
            headers = self._model._original_df.columns.tolist()
            data = self._model._original_df.values.tolist()
            designer.set_schema(schema)
            designer.set_data(headers, data)
        else:
            designer.show_error("修改字段失败", error_message)

    def _on_rename_column(self, designer, table_name, old_name, new_name):
        # 此方法已被 _on_change_column 替代
        pass

    def _on_import_data(self, designer, file_path):
        try:
            if file_path.endswith('.csv'):
                imported_df = pd.read_csv(file_path)
            elif file_path.endswith('.xlsx'):
                imported_df = pd.read_excel(file_path)
            else:
                designer.show_error("导入失败", "不支持的文件格式。")
                return

            # 将导入的数据加载到UI，但不立即保存
            headers = imported_df.columns.tolist()
            data = imported_df.values.tolist()
            designer.set_data(headers, data)
            # 提醒用户需要手动保存
            designer.setWindowTitle(f"设计表: {designer.table_name} (导入未保存)")
        except Exception as e:
            designer.show_error("导入失败", f"无法从文件加载数据: {e}")

    def _on_export_data(self, designer, file_path):
        try:
            # 从UI获取当前显示的数据（可能是筛选或排序后的）
            current_df = designer.get_data()
            
            if file_path.endswith('.csv'):
                current_df.to_csv(file_path, index=False)
            elif file_path.endswith('.xlsx'):
                current_df.to_excel(file_path, index=False)
            else:
                # 如果用户没有在文件名中指定扩展名，默认使用.xlsx
                if not any(file_path.endswith(ext) for ext in ['.csv', '.xlsx']):
                    file_path += '.xlsx'
                    current_df.to_excel(file_path, index=False)
                else:
                    designer.show_error("导出失败", "不支持的文件格式。")
                    return

        except Exception as e:
            designer.show_error("导出失败", f"无法将数据保存到文件: {e}")

    def _load_page_data(self, designer):
        """加载并显示当前页的数据。"""
        offset = (self.current_page - 1) * self.page_size
        data_success, data_err = self._model.load_from_db(self.current_table_name, limit=self.page_size, offset=offset)
        schema, schema_err = self._model.get_table_schema(self.current_table_name)

        if not data_success or schema_err:
            designer.show_error("加载失败", f"无法加载表 '{self.current_table_name}': {data_err or schema_err}")
            return

        headers = self._model._original_df.columns.tolist()
        data = self._model._original_df.values.tolist()
        designer.set_data(headers, data)
        designer.set_schema(schema)
        designer.update_pagination_controls(self.current_page, self.total_pages)

    def _on_page_changed(self, direction):
        """处理翻页请求。"""
        new_page = self.current_page + direction
        if 1 <= new_page <= self.total_pages:
            self.current_page = new_page
            # 找到当前打开的设计器窗口并更新它
            # 注意：这是一个简化的实现，假设只有一个设计器窗口
            for widget in self._db_view.parent().findChildren(TableDesignerView):
                if widget.isVisible() and widget.table_name == self.current_table_name:
                    self._load_page_data(widget)
                    break
    
    def _load_last_db(self):
        """加载上次成功打开的数据库。"""
        import os
        settings = QSettings("MyCompany", "MultidimTableApp")
        last_db_path = settings.value("last_db_path")
        if last_db_path and os.path.exists(last_db_path):
            self._on_db_connect(last_db_path)
