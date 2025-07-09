from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QTabWidget, QWidget,
    QMessageBox, QStatusBar, QComboBox, QHBoxLayout, QLabel
)
from PySide6.QtCore import Signal, Qt, QSettings
import pandas as pd # 导入 pandas

# 导入新的标签视图
from .data_tab_view import DataTabView
from .structure_tab_view import StructureTabView
from .analysis_tab_view import AnalysisTabView
from .statistics_tab_view import StatisticsTabView

class TableDesignerView(QDialog):
    """
    一个用于设计表结构和编辑表数据的对话框。
    作为主视图，协调数据、结构和分析三个标签页。
    """
    # 原始信号，现在将由子视图发出，并在此处转发
    add_column_requested = Signal(str, str) # name, type
    delete_column_requested = Signal(str)
    change_column_requested = Signal(str, str, str) # old_name, new_name, new_type
    add_row_requested = Signal()
    rows_deleted_in_view = Signal(int)
    save_data_requested = Signal(object)
    import_requested = Signal(str)
    export_requested = Signal(str)
    page_changed = Signal(int)
    toggle_full_data_mode_requested = Signal()
    pivot_table_requested = Signal(object)
    switch_table_requested = Signal(str)

    def __init__(self, table_name, parent=None):
        super().__init__(parent)
        self.table_name = table_name
        self.setWindowTitle(f"设计表: {table_name}")
        
        self.setWindowFlags(self.windowFlags() | Qt.WindowMinimizeButtonHint | Qt.WindowMaximizeButtonHint)
        
        self._setup_ui()
        self._connect_signals()
        self._load_window_state()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        # --- Table Switcher ---
        switcher_layout = QHBoxLayout()
        switcher_layout.addWidget(QLabel("切换表:"))
        self.table_switcher_combo = QComboBox()
        switcher_layout.addWidget(self.table_switcher_combo)
        switcher_layout.addStretch()
        layout.addLayout(switcher_layout)

        self.tabs = QTabWidget()
        
        # --- Data Tab ---
        self.data_tab_view = DataTabView(self)
        self.tabs.addTab(self.data_tab_view, "数据")

        # --- Structure Tab ---
        self.structure_tab_view = StructureTabView(self)
        self.tabs.addTab(self.structure_tab_view, "结构")

        # --- Analysis Tab ---
        self.analysis_tab_view = AnalysisTabView(self)
        self.tabs.addTab(self.analysis_tab_view, "数据分析")

        # --- Statistics Tab ---
        self.statistics_tab_view = StatisticsTabView(self)
        self.tabs.addTab(self.statistics_tab_view, "自定义统计")

        layout.addWidget(self.tabs)

        # --- Status Bar ---
        self.status_bar = QStatusBar()
        self.status_bar.setSizeGripEnabled(False)
        layout.addWidget(self.status_bar)

    def _connect_signals(self):
        # 连接 Table Switcher
        self.table_switcher_combo.currentTextChanged.connect(self._on_table_switched)

        # 连接 DataTabView 的信号到 TableDesignerView 的转发信号
        self.data_tab_view.add_row_requested.connect(self.add_row_requested)
        self.data_tab_view.rows_deleted_in_view.connect(self.rows_deleted_in_view)
        self.data_tab_view.save_data_requested.connect(self.save_data_requested)
        self.data_tab_view.import_requested.connect(self.import_requested)
        self.data_tab_view.export_requested.connect(self.export_requested)
        self.data_tab_view.page_changed.connect(self.page_changed)
        self.data_tab_view.toggle_full_data_mode_requested.connect(self.toggle_full_data_mode_requested)

        # 连接 StructureTabView 的信号到 TableDesignerView 的转发信号
        self.structure_tab_view.add_column_requested.connect(self.add_column_requested)
        self.structure_tab_view.delete_column_requested.connect(self.delete_column_requested)
        self.structure_tab_view.change_column_requested.connect(self.change_column_requested)

        # 连接 AnalysisTabView 的信号到 TableDesignerView 的转发信号
        self.analysis_tab_view.pivot_table_requested.connect(self.pivot_table_requested)

        # 当数据标签页的行被删除时，更新窗口标题
        self.data_tab_view.rows_deleted_in_view.connect(
            lambda count: self.setWindowTitle(f"设计表: {self.table_name} (有未保存的更改)")
        )

    # 以下方法将直接调用相应子视图的方法
    def set_data(self, headers, data, schema=None):
        self.data_tab_view.set_data(headers, data, schema)

    def add_data_row(self, row_data):
        self.data_tab_view.add_data_row(row_data)

    def set_schema(self, schema):
        self.structure_tab_view.set_schema(schema)

    def get_data(self):
        return self.data_tab_view.get_data()

    def show_error(self, title: str, message: str):
        QMessageBox.critical(self, title, message)

    def show_status_message(self, message, timeout=3000):
        self.status_bar.showMessage(message, timeout)

    def populate_analysis_columns(self, columns):
        self.analysis_tab_view.populate_analysis_columns(columns)

    def display_analysis_result(self, result):
        self.analysis_tab_view.display_analysis_result(result)

    def display_statistics_data(self, dataframe: pd.DataFrame):
        """
        将统计数据传递给统计标签页显示。
        """
        self.statistics_tab_view.display_statistics_data(dataframe)

    def clear_analysis_config(self):
        """清空分析配置区域。"""
        self.analysis_tab_view.clear_pivot_config_fields()

    def update_pagination_controls(self, current_page, total_pages, is_full_data_mode):
        self.data_tab_view.update_pagination_controls(current_page, total_pages, is_full_data_mode)

    def set_table_list(self, tables: list[str], current_table: str):
        """填充表切换下拉框。"""
        self.table_switcher_combo.blockSignals(True)
        self.table_switcher_combo.clear()
        self.table_switcher_combo.addItems(tables)
        # 使用索引设置当前选中项，更可靠
        index = self.table_switcher_combo.findText(current_table)
        if index != -1:
            self.table_switcher_combo.setCurrentIndex(index)
        self.table_switcher_combo.blockSignals(False)

    def _on_table_switched(self, table_name: str):
        """当用户从下拉框选择一个新表时触发。"""
        if table_name: # 确保不是空字符串
            # 即使是当前表名，也发出信号，让控制器决定是否需要重新加载
            self.table_name = table_name # 更新当前表名
            self.switch_table_requested.emit(table_name)

    def _load_window_state(self):
        """加载窗口的大小和位置。"""
        settings = QSettings("MyCompany", "MultidimTableApp")
        geometry = settings.value(f"geometry/{self.table_name}")
        if geometry:
            self.restoreGeometry(geometry)
        else:
            # 如果没有保存的几何信息，设置一个默认大小
            self.resize(1280, 800)

    def closeEvent(self, event):
        """在关闭事件中保存窗口的大小和位置。"""
        settings = QSettings("MyCompany", "MultidimTableApp")
        settings.setValue(f"geometry/{self.table_name}", self.saveGeometry())
        super().closeEvent(event)

    # 移除不再需要的旧方法
    # def _on_add_column(self): pass
    # def _on_delete_column(self): pass
    # def _on_edit_column(self): pass
    # def _on_rename_column(self): pass
    # def _on_delete_row(self): pass
    # def _on_save_data(self): pass
    # def _on_filter_text_changed(self, text): pass
    # def _on_import(self): pass
    # def _on_export(self): pass
    # def _show_data_context_menu(self, position): pass
    # def _show_structure_context_menu(self, position): pass
    # def _on_analyze_data(self): pass
