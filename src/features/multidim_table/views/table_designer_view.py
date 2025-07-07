# src/features/multidim_table/views/table_designer_view.py
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QTabWidget, QWidget, QTableView,
    QAbstractItemView, QHeaderView, QPushButton, QHBoxLayout,
    QListWidget, QInputDialog, QMessageBox, QLineEdit, QFileDialog,
    QLabel, QStyle, QMenu, QStatusBar, QComboBox
)
from PySide6.QtGui import QStandardItemModel, QStandardItem, QAction
from PySide6.QtCore import Signal, Qt, QSortFilterProxyModel, QTimer
from .edit_column_dialog import EditColumnDialog
import pandas as pd # 导入pandas

class TableDesignerView(QDialog):
    """
    一个用于设计表结构和编辑表数据的对话框。
    """
    add_column_requested = Signal(str)
    delete_column_requested = Signal(str)
    rename_column_requested = Signal(str, str) # 保留，但稍后会修改
    change_column_requested = Signal(str, str, str) # old_name, new_name, new_type
    add_row_requested = Signal()
    delete_row_requested = Signal(list) # 保持这个信号，但其触发时机和参数会改变
    rows_deleted_in_view = Signal(int) # 新增信号，表示视图中删除了多少行
    save_data_requested = Signal(object)
    import_requested = Signal(str)
    export_requested = Signal(str)
    page_changed = Signal(int) # direction: 1 for next, -1 for prev
    analysis_requested = Signal(str) # column name (deprecated, will be removed)
    toggle_full_data_mode_requested = Signal()
    pivot_table_requested = Signal(object) # 新增信号，用于发送透视表配置

    def __init__(self, table_name, parent=None):
        super().__init__(parent)
        self.table_name = table_name
        self.setWindowTitle(f"设计表: {table_name}")
        self.setMinimumSize(900, 700)
        
        # 添加最小化和最大化按钮
        self.setWindowFlags(self.windowFlags() | Qt.WindowMinimizeButtonHint | Qt.WindowMaximizeButtonHint)
        
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        self.tabs = QTabWidget()
        
        # --- Data Tab ---
        self.data_tab = QWidget()
        data_layout = QVBoxLayout(self.data_tab)
        self.setup_data_tab(data_layout)
        self.tabs.addTab(self.data_tab, "数据")

        # --- Structure Tab ---
        self.structure_tab = QWidget()
        structure_layout = QVBoxLayout(self.structure_tab)
        self.setup_structure_tab(structure_layout)
        self.tabs.addTab(self.structure_tab, "结构")

        # --- Analysis Tab ---
        self.analysis_tab = QWidget()
        analysis_layout = QVBoxLayout(self.analysis_tab)
        self.setup_analysis_tab(analysis_layout)
        self.tabs.addTab(self.analysis_tab, "数据分析")

        layout.addWidget(self.tabs)

        # --- Status Bar ---
        self.status_bar = QStatusBar()
        self.status_bar.setSizeGripEnabled(False) # We have a resizable window, no need for the grip
        layout.addWidget(self.status_bar)

    def setup_data_tab(self, layout):
        # --- Top button bar ---
        top_bar_layout = QHBoxLayout()
        self.add_row_button = QPushButton("添加行")
        self.add_row_button.setIcon(self.style().standardIcon(QStyle.SP_FileDialogNewFolder))
        self.add_row_button.clicked.connect(self.add_row_requested)
        top_bar_layout.addWidget(self.add_row_button)
        
        self.delete_row_button = QPushButton("删除选中行")
        self.delete_row_button.setIcon(self.style().standardIcon(QStyle.SP_TrashIcon))
        self.delete_row_button.clicked.connect(self._on_delete_row)
        top_bar_layout.addWidget(self.delete_row_button)
        
        top_bar_layout.addStretch()

        self.import_button = QPushButton("导入")
        self.import_button.setIcon(self.style().standardIcon(QStyle.SP_ArrowDown))
        self.import_button.clicked.connect(self._on_import)
        top_bar_layout.addWidget(self.import_button)

        self.export_button = QPushButton("导出")
        self.export_button.setIcon(self.style().standardIcon(QStyle.SP_ArrowUp))
        self.export_button.clicked.connect(self._on_export)
        top_bar_layout.addWidget(self.export_button)
        
        self.save_data_button = QPushButton("保存更改")
        self.save_data_button.setIcon(self.style().standardIcon(QStyle.SP_DialogSaveButton))
        self.save_data_button.clicked.connect(self._on_save_data)
        top_bar_layout.addWidget(self.save_data_button)
        
        layout.addLayout(top_bar_layout)

        # --- Filter bar ---
        self.filter_input = QLineEdit()
        self.filter_input.setPlaceholderText("在此输入以筛选数据...")
        self.filter_input.textChanged.connect(self._on_filter_text_changed)
        layout.addWidget(self.filter_input)

        # --- Table View for Editing ---
        self.data_table_view = QTableView()
        self.data_table_view.setEditTriggers(QAbstractItemView.DoubleClicked)
        self.data_table_view.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.data_table_view.setSortingEnabled(True) # 启用排序
        self.data_table_view.setContextMenuPolicy(Qt.CustomContextMenu)
        self.data_table_view.customContextMenuRequested.connect(self._show_data_context_menu)

        self.data_table_model = QStandardItemModel()
        
        # 设置代理模型用于排序和筛选
        self.proxy_model = QSortFilterProxyModel()
        self.proxy_model.setSourceModel(self.data_table_model)
        self.proxy_model.setFilterCaseSensitivity(Qt.CaseInsensitive) # 忽略大小写
        self.proxy_model.setFilterKeyColumn(-1) # 在所有列中筛选

        self.data_table_view.setModel(self.proxy_model)
        layout.addWidget(self.data_table_view)

        # --- Pagination bar ---
        pagination_layout = QHBoxLayout()
        self.prev_page_button = QPushButton("上一页")
        self.prev_page_button.setIcon(self.style().standardIcon(QStyle.SP_ArrowLeft))
        self.prev_page_button.clicked.connect(lambda: self.page_changed.emit(-1))
        pagination_layout.addWidget(self.prev_page_button)

        self.page_label = QLabel("第 1 / 1 页")
        pagination_layout.addWidget(self.page_label)

        self.next_page_button = QPushButton("下一页")
        self.next_page_button.setIcon(self.style().standardIcon(QStyle.SP_ArrowRight))
        self.next_page_button.clicked.connect(lambda: self.page_changed.emit(1))
        pagination_layout.addWidget(self.next_page_button)

        pagination_layout.addStretch()

        self.toggle_full_data_button = QPushButton("加载全部数据")
        self.toggle_full_data_button.setCheckable(True)
        self.toggle_full_data_button.clicked.connect(self.toggle_full_data_mode_requested)
        pagination_layout.addWidget(self.toggle_full_data_button)

        layout.addLayout(pagination_layout)

    def setup_structure_tab(self, layout):
        # --- Top button bar ---
        top_bar_layout = QHBoxLayout()
        self.add_column_button = QPushButton("添加字段")
        self.add_column_button.setIcon(self.style().standardIcon(QStyle.SP_FileDialogNewFolder))
        self.add_column_button.clicked.connect(self._on_add_column)
        top_bar_layout.addWidget(self.add_column_button)
        
        self.delete_column_button = QPushButton("删除选中字段")
        self.delete_column_button.setIcon(self.style().standardIcon(QStyle.SP_TrashIcon))
        self.delete_column_button.clicked.connect(self._on_delete_column)
        top_bar_layout.addWidget(self.delete_column_button)

        self.edit_column_button = QPushButton("修改字段")
        self.edit_column_button.setIcon(self.style().standardIcon(QStyle.SP_DriveFDIcon))
        self.edit_column_button.clicked.connect(self._on_edit_column)
        top_bar_layout.addWidget(self.edit_column_button)
        
        top_bar_layout.addStretch()
        layout.addLayout(top_bar_layout)

        # --- Column List ---
        self.column_list_widget = QListWidget()
        self.column_list_widget.setContextMenuPolicy(Qt.CustomContextMenu)
        self.column_list_widget.customContextMenuRequested.connect(self._show_structure_context_menu)
        layout.addWidget(self.column_list_widget)

    def setup_analysis_tab(self, layout):
        """设置数据分析选项卡的用户界面，支持多字段联合分析。"""
        main_h_layout = QHBoxLayout()

        # 左侧：可用字段列表
        left_v_layout = QVBoxLayout()
        left_v_layout.addWidget(QLabel("可用字段:"))
        self.available_fields_list = QListWidget()
        self.available_fields_list.setDragEnabled(True)
        self.available_fields_list.setDragDropMode(QListWidget.DragDrop)
        self.available_fields_list.setDefaultDropAction(Qt.MoveAction)
        self.available_fields_list.setSelectionMode(QAbstractItemView.ExtendedSelection) # 允许多选和拖放
        left_v_layout.addWidget(self.available_fields_list)
        main_h_layout.addLayout(left_v_layout)

        # 中间：行、列、值字段区域
        center_v_layout = QVBoxLayout()

        # 行字段
        center_v_layout.addWidget(QLabel("行字段 (Rows): <small>（将源数据字段拖放到此处，作为透视表的行索引）</small>"))
        self.rows_fields_list = QListWidget()
        self.rows_fields_list.setAcceptDrops(True)
        self.rows_fields_list.setDropIndicatorShown(True)
        self.rows_fields_list.setDragDropMode(QListWidget.DragDrop)
        self.rows_fields_list.setDefaultDropAction(Qt.MoveAction)
        self.rows_fields_list.setSelectionMode(QAbstractItemView.ExtendedSelection) # 允许多选和拖放
        center_v_layout.addWidget(self.rows_fields_list)

        # 列字段
        center_v_layout.addWidget(QLabel("列字段 (Columns): <small>（将源数据字段拖放到此处，作为透视表的列索引）</small>"))
        self.columns_fields_list = QListWidget()
        self.columns_fields_list.setAcceptDrops(True)
        self.columns_fields_list.setDropIndicatorShown(True)
        self.columns_fields_list.setDragDropMode(QListWidget.DragDrop)
        self.columns_fields_list.setDefaultDropAction(Qt.MoveAction)
        self.columns_fields_list.setSelectionMode(QAbstractItemView.ExtendedSelection) # 允许多选和拖放
        center_v_layout.addWidget(self.columns_fields_list)

        # 值字段
        center_v_layout.addWidget(QLabel("值字段 (Values): <small>（将数值字段拖放到此处进行聚合计算）</small>"))
        self.values_fields_list = QListWidget()
        self.values_fields_list.setAcceptDrops(True)
        self.values_fields_list.setDropIndicatorShown(True)
        self.values_fields_list.setDragDropMode(QListWidget.DragDrop)
        self.values_fields_list.setDefaultDropAction(Qt.MoveAction)
        self.values_fields_list.setSelectionMode(QAbstractItemView.ExtendedSelection) # 允许多选和拖放
        center_v_layout.addWidget(self.values_fields_list)

        # 分析按钮
        self.analyze_button = QPushButton("执行分析")
        self.analyze_button.clicked.connect(self._on_analyze_data) # 连接到新的槽函数
        center_v_layout.addWidget(self.analyze_button)

        main_h_layout.addLayout(center_v_layout)

        # 右侧：分析结果显示
        right_v_layout = QVBoxLayout()
        right_v_layout.addWidget(QLabel("分析结果:"))
        
        self.analysis_result_view = QTableView()
        self.analysis_result_model = QStandardItemModel()
        self.analysis_result_proxy_model = QSortFilterProxyModel()
        self.analysis_result_proxy_model.setSourceModel(self.analysis_result_model)
        self.analysis_result_view.setModel(self.analysis_result_proxy_model)
        
        self.analysis_result_view.setEditTriggers(QAbstractItemView.NoEditTriggers) # 只读
        self.analysis_result_view.setSelectionBehavior(QAbstractItemView.SelectRows) # 整行选择
        self.analysis_result_view.setSortingEnabled(True) # 启用排序
        self.analysis_result_view.horizontalHeader().setStretchLastSection(True) # 最后一列填充剩余空间
        self.analysis_result_view.setAlternatingRowColors(True) # 交替行颜色
        
        right_v_layout.addWidget(self.analysis_result_view)
        main_h_layout.addLayout(right_v_layout)

        layout.addLayout(main_h_layout)

    def set_data(self, headers, data):
        self.data_table_model.clear()
        self.data_table_model.setHorizontalHeaderLabels(headers)
        for row_data in data:
            self.add_data_row(row_data)

    def add_data_row(self, row_data):
        row_items = [QStandardItem(str(item)) for item in row_data]
        self.data_table_model.appendRow(row_items)

    def set_schema(self, schema):
        self.column_list_widget.clear()
        for col in schema:
            self.column_list_widget.addItem(f"{col['name']} ({col['type']})")

    def _on_add_column(self):
        col_name, ok = QInputDialog.getText(self, "添加字段", "请输入新字段名:")
        if ok and col_name:
            self.add_column_requested.emit(col_name)

    def _on_delete_column(self):
        selected_item = self.column_list_widget.currentItem()
        if not selected_item:
            QMessageBox.warning(self, "警告", "请先选择一个要删除的字段。")
            return
        
        column_name = selected_item.text().split(" ")[0]
        self.delete_column_requested.emit(column_name)

    def _on_edit_column(self):
        selected_item = self.column_list_widget.currentItem()
        if not selected_item:
            QMessageBox.warning(self, "警告", "请先选择一个要修改的字段。")
            return

        parts = selected_item.text().replace(")", "").split(" (")
        old_name, old_type = parts[0], parts[1]

        dialog = EditColumnDialog(old_name, old_type, self)
        if dialog.exec():
            new_name, new_type = dialog.get_values()
            if new_name != old_name or new_type != old_type:
                self.change_column_requested.emit(old_name, new_name, new_type)

    def _on_rename_column(self):
        # 这个方法现在被 _on_edit_column 替代，但暂时保留以防万一
        pass

    def _on_delete_row(self):
        selected_proxy_indexes = self.data_table_view.selectionModel().selectedRows()
        if not selected_proxy_indexes:
            QMessageBox.warning(self, "警告", "请先选择要删除的行。")
            return
        
        # 将代理模型的索引映射到源模型索引
        source_indexes = [self.proxy_model.mapToSource(index) for index in selected_proxy_indexes]
        rows_to_delete_count = len(source_indexes) # 记录删除的行数
        
        # 直接在源模型上操作，从后往前删，避免索引变化导致错误
        for index in sorted(source_indexes, key=lambda x: x.row(), reverse=True):
            self.data_table_model.removeRow(index.row())
        
        # 通知控制器行已删除
        self.rows_deleted_in_view.emit(rows_to_delete_count)
        self.setWindowTitle(f"设计表: {self.table_name} (有未保存的更改)") # 立即更新标题

    def _on_save_data(self):
        source_model = self.proxy_model.sourceModel()
        headers = [source_model.horizontalHeaderItem(i).text() for i in range(source_model.columnCount())]
        data = []
        for row in range(source_model.rowCount()):
            row_data = [source_model.item(row, col).text() for col in range(source_model.columnCount())]
            data.append(row_data)
        
        import pandas as pd
        df = pd.DataFrame(data, columns=headers)
        self.save_data_requested.emit(df)

    def show_error(self, title: str, message: str):
        QMessageBox.critical(self, title, message)

    def get_data(self):
        """从UI表格中提取数据并返回一个DataFrame。"""
        headers = [self.data_table_model.horizontalHeaderItem(i).text() for i in range(self.data_table_model.columnCount())]
        data = []
        for row in range(self.data_table_model.rowCount()):
            row_data = [self.data_table_model.item(row, col).text() for col in range(self.data_table_model.columnCount())]
            data.append(row_data)
        
        import pandas as pd
        return pd.DataFrame(data, columns=headers)

    def _on_filter_text_changed(self, text):
        """当筛选文本框内容改变时，更新代理模型的筛选条件。"""
        self.proxy_model.setFilterRegularExpression(text)

    def _on_import(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "导入文件", "", "支持的文件 (*.csv *.xlsx)")
        if file_path:
            self.import_requested.emit(file_path)

    def _on_export(self):
        file_path, _ = QFileDialog.getSaveFileName(self, "导出文件", f"{self.table_name}", "Excel 文件 (*.xlsx);;CSV 文件 (*.csv)")
        if file_path:
            self.export_requested.emit(file_path)

    def _show_data_context_menu(self, position):
        """显示数据表格的右键上下文菜单。"""
        menu = QMenu()
        
        add_action = QAction("添加新行", self)
        add_action.triggered.connect(self.add_row_requested)
        menu.addAction(add_action)

        # 只有在选中行时才显示删除选项
        if self.data_table_view.selectionModel().hasSelection():
            delete_action = QAction("删除选中行", self)
            delete_action.triggered.connect(self._on_delete_row)
            menu.addAction(delete_action)
            
        menu.exec(self.data_table_view.viewport().mapToGlobal(position))

    def _show_structure_context_menu(self, position):
        """显示字段列表的右键上下文菜单。"""
        menu = QMenu()
        
        add_action = QAction("添加新字段", self)
        add_action.triggered.connect(self._on_add_column)
        menu.addAction(add_action)

        # 只有在选中项时才显示修改和删除选项
        if self.column_list_widget.itemAt(position):
            edit_action = QAction("修改选中字段", self)
            edit_action.triggered.connect(self._on_edit_column)
            menu.addAction(edit_action)

            delete_action = QAction("删除选中字段", self)
            delete_action.triggered.connect(self._on_delete_column)
            menu.addAction(delete_action)
            
        menu.exec(self.column_list_widget.mapToGlobal(position))

    def show_status_message(self, message, timeout=3000):
        """在状态栏显示一条临时消息。"""
        self.status_bar.showMessage(message, timeout)

    def _on_analyze_data(self):
        """收集透视表配置并发出信号。"""
        rows = [self.rows_fields_list.item(i).text() for i in range(self.rows_fields_list.count())]
        columns = [self.columns_fields_list.item(i).text() for i in range(self.columns_fields_list.count())]
        values = [self.values_fields_list.item(i).text() for i in range(self.values_fields_list.count())]
        
        # 暂时只支持默认聚合函数 'sum'，后续可以扩展UI让用户选择
        # 这里需要一个更复杂的结构来存储值字段和其对应的聚合函数
        # 暂时简化为只传递字段名，聚合函数在控制器中默认处理
        
        pivot_config = {
            "rows": rows,
            "columns": columns,
            "values": values,
            "aggfunc": "sum" # 默认聚合函数
        }
        self.pivot_table_requested.emit(pivot_config)

    def populate_analysis_columns(self, columns):
        """填充可用字段列表。"""
        self.available_fields_list.clear()
        self.available_fields_list.addItems(columns)

    def display_analysis_result(self, result):
        """
        显示分析结果。
        result 可以是 pandas.DataFrame 或字符串（错误信息）。
        """
        self.analysis_result_model.clear()
        if isinstance(result, pd.DataFrame):
            if result.empty:
                self.analysis_result_model.setHorizontalHeaderLabels(["无结果"])
                return

            headers = result.columns.tolist()
            self.analysis_result_model.setHorizontalHeaderLabels(headers)
            
            for r_idx, row_data in result.iterrows():
                row_items = [QStandardItem(str(item)) for item in row_data]
                self.analysis_result_model.appendRow(row_items)
            
            # 调整列宽以适应内容
            self.analysis_result_view.resizeColumnsToContents()
        elif isinstance(result, str):
            # 如果是字符串，显示为单列表格，内容为错误信息
            self.analysis_result_model.setHorizontalHeaderLabels(["错误/信息"])
            item = QStandardItem(result)
            self.analysis_result_model.appendRow(item)
        else:
            self.analysis_result_model.setHorizontalHeaderLabels(["未知结果类型"])
            item = QStandardItem(str(result))
            self.analysis_result_model.appendRow(item)

    def update_pagination_controls(self, current_page, total_pages, is_full_data_mode):
        """更新分页控件的状态和标签。"""
        is_paginated = total_pages > 1 and not is_full_data_mode

        self.page_label.setText(f"第 {current_page} / {total_pages} 页")
        self.page_label.setVisible(is_paginated)
        self.prev_page_button.setVisible(is_paginated)
        self.next_page_button.setVisible(is_paginated)

        self.prev_page_button.setEnabled(current_page > 1)
        self.next_page_button.setEnabled(current_page < total_pages)

        # 只有在全量模式下才允许保存
        self.save_data_button.setEnabled(is_full_data_mode)
        if not is_full_data_mode and total_pages > 1:
            self.save_data_button.setToolTip("请点击“加载全部数据”以进行编辑和保存。")
        else:
            self.save_data_button.setToolTip("")

        self.toggle_full_data_button.setText("返回分页模式" if is_full_data_mode else "加载全部数据")
        self.toggle_full_data_button.setChecked(is_full_data_mode)
