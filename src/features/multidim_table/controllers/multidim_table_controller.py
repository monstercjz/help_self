# src/features/multidim_table/controllers/multidim_table_controller.py
import os
import pandas as pd
import sys
import logging
import shutil # 新增导入
from PySide6.QtCore import QObject, QTimer
from PySide6.QtWidgets import QFileDialog
from src.core.context import ApplicationContext
from src.features.multidim_table.models.multidim_table_model import MultidimTableModel
from src.features.multidim_table.services.data_service import DataService
from src.features.multidim_table.views.db_management_view import DbManagementView
from src.features.multidim_table.views.table_designer_view import TableDesignerView
from src.features.multidim_table.views.add_data_dialog import AddDataDialog
from src.features.multidim_table.views.statistics_tab_view import StatisticsTabView # 导入新的统计标签页视图

class MultidimTableController(QObject):
    """
    多维表格的控制器，负责协调模型和所有视图。![1752058308567](images/multidim_table_controller/1752058308567.png)![1752058310795](images/multidim_table_controller/1752058310795.png)![1752058326203](images/multidim_table_controller/1752058326203.png)![1752058332085](images/multidim_table_controller/1752058332085.png)
    """
    def __init__(self, model: MultidimTableModel, db_view: DbManagementView, context: ApplicationContext):
        super().__init__()
        self._model = model
        self._db_view = db_view
        self._data_service = DataService(self._model)
        self.context = context
        
        # 分页状态
        self.page_size = 100  # 每页显示100条
        self.current_page = 1
        self.total_rows = 0
        self.total_pages = 1
        self.current_table_name = None
        self.is_full_data_mode = False
        self.analysis_df = pd.DataFrame() # 用于分析的全量数据
        self.last_analysis_result_df = pd.DataFrame() # 用于存储上次分析结果
        self.db_filter_criteria = {'column': None, 'value': None} # 数据库筛选条件
        
        stats_config_relative_path = self.context.config_service.get_value(
            "MultiDimTable",
            "stats_config_path"
        )
        if not stats_config_relative_path:
            stats_config_relative_path = "plugins/multidim_table/statistics_config.json"
            
        self.current_stats_config_path = self.context.get_data_path(stats_config_relative_path)

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
            # 保存成功连接的路径到 config.ini
            self.context.config_service.set_option("MultiDimTable", "last_db_path", db_path)
            self.context.config_service.save_config()

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
        self.is_full_data_mode = False # 每次打开都重置为分页模式
        self.db_filter_criteria = {'column': None, 'value': None} # 重置筛选条件
        
        # 获取总行数和总页数
        self.total_rows, err = self._model.get_total_row_count(table_name)
        if err:
            self._db_view.show_error("错误", f"无法获取总行数: {err}")
            return
        self.total_pages = (self.total_rows + self.page_size - 1) // self.page_size
        if self.total_pages == 0: self.total_pages = 1
        
        # 如果已经有打开的设计器窗口，先关闭它
        current_designer = self._get_current_designer_view()
        if current_designer:
            current_designer.close() # 关闭旧的对话框

        designer = TableDesignerView(table_name, self._db_view)
        self._load_designer_style(designer)
        self._connect_designer_signals(designer, table_name)
        self._initialize_designer_data_and_ui(designer)
        
        # 填充表切换下拉框
        all_tables, _ = self._model.get_table_list()
        designer.set_table_list(all_tables, table_name)
        
        # 使用 show() 而不是 exec()，避免阻塞，允许同时存在多个窗口（如果需要）
        # 但这里我们希望是切换，所以旧的关闭，新的显示
        designer.show()

    def _load_designer_style(self, designer: TableDesignerView):
        """为表设计器对话框应用独立的暗色样式。"""
        qss_path = os.path.join(os.path.dirname(__file__), "..", "assets", "style.qss")
        if os.path.exists(qss_path):
            with open(qss_path, "r", encoding="utf-8") as f:
                style = f.read()
                designer.setStyleSheet(style)

    def _connect_designer_signals(self, designer: TableDesignerView, table_name: str):
        """连接表设计器视图的信号。"""
        designer.page_changed.connect(self._on_page_changed)
        designer.pivot_table_requested.connect(self._on_pivot_table_requested)
        designer.analysis_tab_view.custom_analysis_requested.connect(self._on_custom_analysis_requested)
        designer.toggle_full_data_mode_requested.connect(self._on_toggle_full_data_mode)
        designer.add_column_requested.connect(lambda name, type: self._on_add_column(designer, table_name, name, type))
        designer.delete_column_requested.connect(lambda col_name: self._on_delete_column(designer, table_name, col_name))
        designer.change_column_requested.connect(lambda old_name, new_name, new_type: self._on_change_column(designer, table_name, old_name, new_name, new_type))
        designer.add_row_requested.connect(lambda: self._on_add_row(designer))
        designer.rows_deleted_in_view.connect(lambda count: self._on_rows_deleted_in_view(designer, count))
        designer.save_data_requested.connect(lambda df: self._on_save_data(table_name, df))
        designer.import_requested.connect(lambda path: self._on_import_data(designer, path))
        designer.export_requested.connect(lambda path: self._on_export_data(designer, path))
        designer.switch_table_requested.connect(lambda new_table: self._on_switch_table(designer, new_table))
        
        # 连接统计计算信号
        designer.statistics_tab_view.calculate_button.clicked.connect(self._on_calculate_statistics_requested)
        designer.statistics_tab_view.load_config_button.clicked.connect(self._on_load_statistics_config)
        designer.statistics_tab_view.edit_config_button.clicked.connect(self._on_open_statistics_config)

        # 连接数据库筛选信号
        data_tab = designer.data_tab_view
        data_tab.apply_db_filter_button.clicked.connect(self._on_apply_db_filter)
        data_tab.clear_db_filter_button.clicked.connect(self._on_clear_db_filter)
        data_tab.filter_by_cell_requested.connect(self._on_filter_by_cell)

    def _initialize_designer_data_and_ui(self, designer: TableDesignerView):
        """加载第一页数据和分析所需的全量数据，并初始化UI。"""
        self._load_page_data(designer)
        self._load_full_data_for_analysis(designer)
        self._load_statistics_data(designer) # 初始化统计UI
        designer.statistics_tab_view.set_config_path(self.current_stats_config_path)

        # 填充数据库筛选字段下拉框
        schema, err = self._model.get_table_schema(self.current_table_name)
        if not err:
            columns = [col['name'] for col in schema]
            designer.data_tab_view.set_db_filter_columns(columns)

    def _on_rows_deleted_in_view(self, designer, deleted_count):
        """响应视图中行被删除的信号，更新控制器状态和UI。"""
        self.total_rows -= deleted_count
        self.total_pages = (self.total_rows + self.page_size - 1) // self.page_size
        if self.total_pages == 0: self.total_pages = 1

        # 更新内存中的DataFrame，确保与UI同步
        current_df = designer.get_data() # 从UI获取最新数据
        self._model._original_df = current_df.copy()
        self._model._df = current_df.copy()

        designer.update_pagination_controls(self.current_page, self.total_pages, self.is_full_data_mode)
        designer.status_bar.showMessage(f"总行数: {self.total_rows}") # 持久更新
        # 标题已在视图中更新，这里不再重复

    def _on_add_row(self, designer):
        schema, err = self._model.get_table_schema(self.current_table_name)
        if err:
            designer.show_error("错误", f"无法获取表结构: {err}")
            return

        add_dialog = AddDataDialog(schema, designer)
        if add_dialog.exec():
            new_data = add_dialog.get_data()
            designer.add_data_row(list(new_data.values()))

            # 更新内存中的DataFrame，确保与UI同步
            current_df = designer.get_data()
            self._model._original_df = current_df.copy()
            self._model._df = current_df.copy()

            # 更新总行数并刷新UI
            self.total_rows += 1
            self.total_pages = (self.total_rows + self.page_size - 1) // self.page_size
            designer.update_pagination_controls(self.current_page, self.total_pages, self.is_full_data_mode)
            designer.status_bar.showMessage(f"总行数: {self.total_rows}") # 持久更新
            designer.setWindowTitle(f"设计表: {designer.table_name} (有未保存的更改)")

    def _on_delete_column(self, designer, table_name, column_name):
        success, err = self._model.delete_column(table_name, column_name)
        if success:
            # 重新加载数据和结构
            self._refresh_all_data_and_views(designer)
        else:
            designer.show_error("删除失败", f"无法删除字段: {err}")

    def _on_add_column(self, designer, table_name, column_name, column_type):
        success, err = self._model.add_column(table_name, column_name, column_type)
        if success:
            # 重新加载数据和结构
            self._refresh_all_data_and_views(designer)
        else:
            designer.show_error("添加失败", f"无法添加字段: {err}")

    def _on_save_data(self, table_name, dataframe):
        # 增加一层保护，如果不是全量模式，则不允许保存
        if not self.is_full_data_mode:
            self._db_view.show_error("保存失败", "请先点击“加载全部数据”再进行保存。")
            return

        success, err = self._data_service.save_table_data(table_name, dataframe)
        if not success:
            self._db_view.show_error("保存失败", f"无法保存数据: {err}")
        else:
            # 找到对应的designer并显示状态消息
            self._update_designer_after_save(table_name)

    def _update_designer_after_save(self, table_name):
        """保存数据后，更新对应的TableDesignerView的状态。"""
        designer = self._get_current_designer_view(table_name)
        if designer:
            designer.show_status_message("数据保存成功！", 4000)  # 显示4秒
            designer.setWindowTitle(f"设计表: {table_name}")  # 移除未保存提示
            # 保存后刷新数据
            self._refresh_all_data_and_views(designer)
            # 临时消息消失后，确保总行数持久显示
            QTimer.singleShot(4000, lambda: designer.status_bar.showMessage(f"总行数: {self.total_rows}"))

    def _get_current_designer_view(self, table_name=None):
        """
        获取当前可见的TableDesignerView实例。
        如果提供了table_name，则返回与该表名匹配的视图。
        """
        for widget in self._db_view.parent().findChildren(TableDesignerView):
            if widget.isVisible():
                if table_name is None or widget.table_name == table_name:
                    return widget
        return None

    def _on_rename_table(self, old_name, new_name):
        success, err = self._model.rename_table(old_name, new_name)
        if not success:
            self._db_view.show_error("重命名失败", f"无法重命名表: {err}")

    def _on_change_column(self, designer: TableDesignerView, table_name: str, old_name: str, new_name: str, new_type: str):
        """处理字段名称或类型的更改请求。"""
        schema, _ = self._model.get_table_schema(table_name)
        old_type = next((col['type'] for col in schema if col['name'] == old_name), None)

        type_changed = (old_type != new_type)
        name_changed = (old_name != new_name)

        if not type_changed and not name_changed:
            return  # 没有变化

        final_success = True
        error_messages = []

        if type_changed:
            success, err = self._handle_column_type_change(table_name, old_name, new_type)
            if not success:
                final_success = False
                error_messages.append(f"更改类型失败: {err}")

        if name_changed and final_success:
            success, err = self._handle_column_name_change(table_name, old_name, new_name)
            if not success:
                final_success = False
                error_messages.append(f"重命名失败: {err}")

        if final_success:
            self._refresh_all_data_and_views(designer)
        else:
            designer.show_error("修改字段失败", "\n".join(error_messages))

    def _handle_column_type_change(self, table_name: str, column_name: str, new_type: str) -> tuple[bool, str]:
        """处理字段类型更改的逻辑。"""
        return self._model.change_column_type(table_name, column_name, new_type)

    def _handle_column_name_change(self, table_name: str, old_name: str, new_name: str) -> tuple[bool, str]:
        """处理字段名称更改的逻辑。"""
        return self._model.rename_column(table_name, old_name, new_name)

    def _on_rename_column(self, designer, table_name, old_name, new_name):
        # 此方法已被 _on_change_column 替代
        pass

    def _on_import_data(self, designer: TableDesignerView, file_path: str):
        """处理数据导入请求。"""
        try:
            imported_df = self._load_dataframe_from_file(file_path)
            if imported_df is None:
                designer.show_error("导入失败", "不支持的文件格式或文件读取失败。")
                return

            headers = imported_df.columns.tolist()
            data = imported_df.values.tolist()
            # 导入时，我们没有schema信息，所以委托不会被激活，这是符合预期的
            designer.set_data(headers, data)

            self.total_rows = len(imported_df)
            self.is_full_data_mode = True  # 导入后即为全量模式
            self.total_pages = 1  # 全量模式只有一页
            designer.update_pagination_controls(1, 1, True)
            designer.status_bar.showMessage(f"总行数: {self.total_rows}")
            designer.setWindowTitle(f"设计表: {designer.table_name} (导入未保存)")
            designer.show_status_message("数据已导入，请手动保存以应用更改。", 5000)
        except Exception as e:
            designer.show_error("导入失败", f"无法从文件加载数据: {e}")

    def _load_dataframe_from_file(self, file_path: str) -> pd.DataFrame | None:
        """根据文件扩展名加载DataFrame。"""
        if file_path.endswith('.csv'):
            return pd.read_csv(file_path)
        elif file_path.endswith('.xlsx'):
            return pd.read_excel(file_path)
        return None

    def _on_export_data(self, designer: TableDesignerView, file_path: str):
        """处理数据导出请求。"""
        try:
            current_df = designer.get_data()
            self._save_dataframe_to_file(current_df, file_path)
            designer.show_status_message(f"成功导出到 {file_path}", 5000)
            QTimer.singleShot(5000, lambda: designer.status_bar.showMessage(f"总行数: {self.total_rows}"))
        except Exception as e:
            designer.show_error("导出失败", f"无法将数据保存到文件: {e}")

    def _save_dataframe_to_file(self, dataframe: pd.DataFrame, file_path: str):
        """根据文件扩展名保存DataFrame。"""
        if file_path.endswith('.csv'):
            dataframe.to_csv(file_path, index=False)
        elif file_path.endswith('.xlsx'):
            dataframe.to_excel(file_path, index=False)
        else:
            # 如果用户没有在文件名中指定扩展名，默认使用.xlsx
            file_path += '.xlsx'
            dataframe.to_excel(file_path, index=False)

    def _load_page_data(self, designer):
        """加载并显示当前页的数据。"""
        offset = (self.current_page - 1) * self.page_size
        filter_col = self.db_filter_criteria['column']
        filter_val = self.db_filter_criteria['value']
        
        data_success, data_err = self._model.load_from_db(
            self.current_table_name, 
            limit=self.page_size, 
            offset=offset,
            filter_column=filter_col,
            filter_value=filter_val
        )
        schema, schema_err = self._model.get_table_schema(self.current_table_name)

        if not data_success or schema_err:
            designer.show_error("加载失败", f"无法加载表 '{self.current_table_name}': {data_err or schema_err}")
            return

        headers = self._model._original_df.columns.tolist()
        data = self._model._original_df.values.tolist()
        designer.set_data(headers, data, schema)
        designer.set_schema(schema)
        designer.update_pagination_controls(self.current_page, self.total_pages, self.is_full_data_mode)
        designer.status_bar.showMessage(f"总行数: {self.total_rows}")

    def _on_page_changed(self, direction):
        """处理翻页请求。"""
        new_page = self.current_page + direction
        if 1 <= new_page <= self.total_pages:
            self.current_page = new_page
            # 找到当前打开的设计器窗口并更新它
            # 注意：这是一个简化的实现，假设只有一个设计器窗口
            designer = self._get_current_designer_view()
            if designer:
                self._load_page_data(designer)

    def _load_full_data_for_analysis(self, designer):
        """在后台加载全量数据用于分析。"""
        try:
            # 分析时，我们忽略数据库筛选，总是加载全量数据
            self.analysis_df = pd.read_sql(f'SELECT * FROM "{self.current_table_name}"', self._model.conn)
            designer.populate_analysis_columns(self.analysis_df.columns.tolist())
        except Exception as e:
            designer.show_error("分析数据加载失败", str(e))

    def _on_analyze_column(self, column_name: str):
        """当用户选择一个字段进行分析时调用。"""
        designer = self._get_current_designer_view()
        if not designer or column_name not in self.analysis_df.columns:
            return

        try:
            series = self.analysis_df[column_name]
            result_text = self._data_service.generate_column_analysis_report(series)
            designer.display_analysis_result(result_text)
        except Exception as e:
            designer.display_analysis_result(f"分析时发生错误: {e}")

    def _on_pivot_table_requested(self, pivot_config: dict):
        """处理透视表分析请求。"""
        designer = self._get_current_designer_view()
        if not designer:
            return

        if self.analysis_df.empty:
            designer.display_analysis_result("请先加载数据进行分析。")
            return

        success, result_df, err = self._data_service.create_pivot_table(self.analysis_df, pivot_config)
        if success:
            processed_df = self._process_pivot_table_dataframe(result_df, pivot_config)
            self.last_analysis_result_df = processed_df.copy() # 存储结果
            designer.display_analysis_result(processed_df)  # 直接传递DataFrame
        else:
            self.last_analysis_result_df = pd.DataFrame() # 清空历史结果
            designer.display_analysis_result(f"透视表分析失败: {err}")  # 传递错误信息字符串

    def _on_custom_analysis_requested(self, query: str):
        """处理自定义分析请求。"""
        designer = self._get_current_designer_view()
        if not designer:
            return

        # 决定是在原始数据上查询还是在上次分析结果上查询
        if not self.last_analysis_result_df.empty:
            df_to_query = self.last_analysis_result_df
            source_info = "当前分析结果"
        elif not self.analysis_df.empty:
            df_to_query = self.analysis_df
            source_info = "原始数据"
        else:
            designer.display_analysis_result("请先加载数据或执行分析。")
            return

        success, result, err = self._data_service.execute_custom_analysis(df_to_query, query)
        if success:
            designer.display_analysis_result(result)
            designer.show_status_message(f"已在“{source_info}”上执行查询", 4000)
        else:
            designer.display_analysis_result(f"自定义分析失败: {err}")

    def _process_pivot_table_dataframe(self, df: pd.DataFrame, pivot_config: dict) -> pd.DataFrame:
        """处理透视表结果DataFrame，包括索引重置和多级列扁平化。"""
        if pivot_config.get("rows"):
            df = df.reset_index()

        if isinstance(df.columns, pd.MultiIndex):
            df.columns = ['_'.join(map(str, col)).strip() if isinstance(col, tuple) else str(col) for col in df.columns.values]
            df.columns = [col.rstrip('_') for col in df.columns]
        return df

    def _load_last_db(self):
        """加载上次成功打开的数据库。"""
        last_db_path = self.context.config_service.get_value("MultiDimTable", "last_db_path")
        if last_db_path and os.path.exists(last_db_path):
            self._on_db_connect(last_db_path)

    def _on_toggle_full_data_mode(self):
        """切换全量数据加载模式。"""
        self.is_full_data_mode = not self.is_full_data_mode

        designer = self._get_current_designer_view()
        if not designer:
            return

        if self.is_full_data_mode:
            self._load_full_data_into_designer(designer)
            designer.show_status_message("已加载全部数据，现在可以编辑和保存。", 5000)
            QTimer.singleShot(5000, lambda: designer.status_bar.showMessage(f"总行数: {self.total_rows}"))
            designer.setWindowTitle(f"设计表: {designer.table_name}")
        else:
            self._return_to_paginated_mode(designer)
            designer.show_status_message("已返回分页浏览模式。", 3000)
            QTimer.singleShot(3000, lambda: designer.status_bar.showMessage(f"总行数: {self.total_rows}"))
            designer.setWindowTitle(f"设计表: {designer.table_name}")

        designer.update_pagination_controls(self.current_page, self.total_pages, self.is_full_data_mode)

    def _load_full_data_into_designer(self, designer: TableDesignerView):
        """将全量数据加载到设计器视图。"""
        filter_col = self.db_filter_criteria['column']
        filter_val = self.db_filter_criteria['value']
        self._model.load_from_db(self.current_table_name, filter_column=filter_col, filter_value=filter_val)
        headers = self._model._original_df.columns.tolist()
        data = self._model._original_df.values.tolist()
        schema, _ = self._model.get_table_schema(self.current_table_name)
        designer.set_data(headers, data, schema)
        self.total_rows = len(self._model._original_df)
        designer.status_bar.showMessage(f"总行数: {self.total_rows}")

    def _return_to_paginated_mode(self, designer: TableDesignerView):
        """返回分页浏览模式。"""
        self.current_page = 1
        # 清除筛选条件并重新获取总数
        self.db_filter_criteria = {'column': None, 'value': None}
        designer.data_tab_view.clear_db_filter_inputs()
        
        self.total_rows, err = self._model.get_total_row_count(self.current_table_name)
        if err:
            designer.show_error("错误", f"无法获取总行数: {err}")
            return
        self.total_pages = (self.total_rows + self.page_size - 1) // self.page_size
        if self.total_pages == 0:
            self.total_pages = 1
        self._load_page_data(designer)

    def _load_statistics_data(self, designer: TableDesignerView):
        """
        初始化统计标签页，清空旧数据。
        """
        # 清空视图，等待用户点击按钮进行计算
        designer.statistics_tab_view.display_statistics_data(pd.DataFrame())

    def _on_calculate_statistics_requested(self):
        """
        响应“执行计算”按钮的点击事件，调用服务层执行查询。
        """
        designer = self._get_current_designer_view()
        if not designer:
            return

        if not self.current_table_name:
            designer.show_error("计算失败", "未选择任何表格。")
            return

        success, result_df, err = self._data_service.get_custom_statistics(self.current_table_name, self.current_stats_config_path)
        
        if success:
            designer.statistics_tab_view.display_statistics_data(result_df)
            designer.show_status_message("统计计算完成。", 3000)
        else:
            designer.show_error("计算失败", err)
            designer.statistics_tab_view.display_statistics_data(pd.DataFrame())

    def _on_load_statistics_config(self):
        """
        打开文件对话框，让用户选择一个新的统计配置文件。
        """
        designer = self._get_current_designer_view()
        if not designer:
            return
            
        file_path, _ = QFileDialog.getOpenFileName(
            designer,
            "选择统计配置文件",
            "",
            "JSON Files (*.json)"
        )
        if file_path:
            self.current_stats_config_path = file_path
            designer.statistics_tab_view.set_config_path(file_path)
            designer.show_status_message(f"已加载新配置: {os.path.basename(file_path)}", 4000)

    def _on_open_statistics_config(self):
        """
        打开当前加载的统计配置文件以供用户编辑。
        如果文件不存在，尝试从包内复制一份默认的。
        """
        try:
            # 定义需要复制的JSON文件列表
            json_files_to_copy = [
                "statistics_config.json",
                "filter_example.json",
                "group_by_example.json"
            ]
            
            copied_files = []
            for filename in json_files_to_copy:
                source_path = os.path.join(os.path.dirname(__file__), "..", "assets", filename)
                destination_path = self.context.get_data_path(os.path.join("plugins", "multidim_table", filename))
                
                # 确保目标目录存在
                os.makedirs(os.path.dirname(destination_path), exist_ok=True)

                if not os.path.exists(destination_path):
                    if os.path.exists(source_path):
                        shutil.copy(source_path, destination_path)
                        copied_files.append(filename)
                        logging.info(f"默认配置文件 '{filename}' 已复制到: {destination_path}")
                    else:
                        logging.warning(f"默认配置文件 '{filename}' 丢失，无法复制。")

            if copied_files:
                designer = self._get_current_designer_view()
                if designer:
                    designer.show_status_message(f"已复制以下默认配置文件: {', '.join(copied_files)}", 5000)
            
            # 尝试打开主统计配置文件
            if os.path.exists(self.current_stats_config_path):
                os.startfile(self.current_stats_config_path)
            else:
                designer = self._get_current_designer_view()
                if designer:
                    designer.show_error("错误", f"主配置文件 '{self.current_stats_config_path}' 不存在，请检查。")
        except Exception as e:
            designer = self._get_current_designer_view()
            if designer:
                designer.show_error("打开失败", f"无法打开配置文件或复制文件时出错: {e}")

    def _get_resource_path(self, relative_path):
        """获取资源的绝对路径，兼容开发环境和PyInstaller打包环境。"""
        if getattr(sys, 'frozen', False):
            # 如果是打包后的 exe
            base_path = sys._MEIPASS
        else:
            # 如果是正常的开发环境
            base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        return os.path.join(base_path, relative_path)

    def _refresh_all_data_and_views(self, designer):
        """一个统一的方法，用于在结构或数据发生重大变化后刷新所有内容。"""
        # 重新获取总行数等信息
        filter_col = self.db_filter_criteria['column']
        filter_val = self.db_filter_criteria['value']
        self.total_rows, _ = self._model.get_total_row_count(self.current_table_name, filter_column=filter_col, filter_value=filter_val)
        self.total_pages = (self.total_rows + self.page_size - 1) // self.page_size
        if self.total_pages == 0: self.total_pages = 1
        
        # 如果当前页超出范围（例如，删除数据后），则重置为第一页
        if self.current_page > self.total_pages:
            self.current_page = 1
            self.is_full_data_mode = False # 强制返回分页模式

        # 根据当前模式刷新页面数据或全量数据
        if self.is_full_data_mode:
            self._load_full_data_into_designer(designer)
        else:
            self._load_page_data(designer)

        # 刷新分析用的全量数据和字段列表
        designer.clear_analysis_config() # 先清空旧的配置
        self.last_analysis_result_df = pd.DataFrame() # 清空分析结果
        self._load_full_data_for_analysis(designer)
        
        # 刷新结构视图
        schema, _ = self._model.get_table_schema(self.current_table_name)
        designer.set_schema(schema)
        
        # 更新UI控件状态
        designer.update_pagination_controls(self.current_page, self.total_pages, self.is_full_data_mode)
        designer.status_bar.showMessage(f"总行数: {self.total_rows}") # 确保刷新后总行数显示正确

    def _on_apply_db_filter(self):
        """应用数据库层面的筛选。"""
        designer = self._get_current_designer_view()
        if not designer:
            return
            
        column, value = designer.data_tab_view.get_db_filter()
        self.db_filter_criteria['column'] = column
        self.db_filter_criteria['value'] = value
        
        # 应用筛选后，总是回到第一页
        self.current_page = 1
        self.is_full_data_mode = False # 筛选时强制分页
        self._refresh_all_data_and_views(designer)
        designer.show_status_message(f"已应用筛选: {column} LIKE '%{value}%'", 4000)
        QTimer.singleShot(4000, lambda: designer.status_bar.showMessage(f"总行数: {self.total_rows} (筛选后)"))

    def _on_clear_db_filter(self):
        """清除数据库层面的筛选。"""
        designer = self._get_current_designer_view()
        if not designer:
            return
            
        self.db_filter_criteria['column'] = None
        self.db_filter_criteria['value'] = None
        designer.data_tab_view.clear_db_filter_inputs()
        
        # 清除筛选后，回到第一页
        self.current_page = 1
        self.is_full_data_mode = False
        self._refresh_all_data_and_views(designer)
        designer.show_status_message("数据库筛选已清除", 3000)
        QTimer.singleShot(3000, lambda: designer.status_bar.showMessage(f"总行数: {self.total_rows}"))

    def _on_filter_by_cell(self, column_name, value):
        """处理通过右键菜单发起的单元格筛选请求。"""
        designer = self._get_current_designer_view()
        if not designer:
            return
        
        # 1. 更新UI上的筛选输入框
        designer.data_tab_view.update_db_filter_inputs(column_name, value)
        
        # 2. 直接调用应用筛选的逻辑
        self._on_apply_db_filter()

    def _on_switch_table(self, designer: TableDesignerView, new_table_name: str):
        """当用户从下拉框切换表格时调用。"""
        if new_table_name == self.current_table_name:
            return

        # 更新当前表名并重新加载所有内容
        self.current_table_name = new_table_name
        self.current_page = 1
        self.is_full_data_mode = False
        self._refresh_all_data_and_views(designer)
        
        # 更新下拉框的当前选项
        all_tables, _ = self._model.get_table_list()
        designer.set_table_list(all_tables, new_table_name)
