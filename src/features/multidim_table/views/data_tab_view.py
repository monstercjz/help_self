from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QTableView, QAbstractItemView,
    QPushButton, QHBoxLayout, QLineEdit, QFileDialog, QLabel,
    QStyle, QMenu, QMessageBox, QComboBox
)
from PySide6.QtGui import QStandardItemModel, QStandardItem, QAction, QGuiApplication
from PySide6.QtCore import Signal, Qt, QSortFilterProxyModel
import os
import pandas as pd
from src.features.multidim_table.widgets.custom_delegate import CustomItemDelegate

class RowNumberProxyModel(QSortFilterProxyModel):
    """一个自定义的代理模型，以确保垂直表头始终显示正确的行号。"""
    def headerData(self, section: int, orientation: Qt.Orientation, role: int = Qt.DisplayRole):
        if orientation == Qt.Vertical and role == Qt.DisplayRole:
            # 始终返回视图中的行号（section + 1），忽略源模型的排序
            return str(section + 1)
        return super().headerData(section, orientation, role)

class DataTabView(QWidget):
    """
    数据编辑选项卡视图，用于显示和编辑表格数据。
    """
    add_row_requested = Signal()
    rows_deleted_in_view = Signal(int)
    save_data_requested = Signal(object)
    import_requested = Signal(str)
    export_requested = Signal(str)
    page_changed = Signal(int)
    toggle_full_data_mode_requested = Signal()
    filter_by_cell_requested = Signal(str, str) # column_name, value

    def __init__(self, parent=None):
        super().__init__(parent)
        self._last_io_dir = os.path.expanduser("~")
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

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

        # --- Database Filter bar ---
        db_filter_layout = QHBoxLayout()
        db_filter_layout.addWidget(QLabel("数据库筛选:"))
        self.db_filter_column_combo = QComboBox()
        db_filter_layout.addWidget(self.db_filter_column_combo)
        self.db_filter_value_input = QLineEdit()
        self.db_filter_value_input.setPlaceholderText("输入筛选值...")
        db_filter_layout.addWidget(self.db_filter_value_input)
        
        self.apply_db_filter_button = QPushButton("应用")
        db_filter_layout.addWidget(self.apply_db_filter_button)

        self.clear_db_filter_button = QPushButton("清除")
        db_filter_layout.addWidget(self.clear_db_filter_button)

        layout.addLayout(db_filter_layout)

        # --- Table View for Editing ---
        self.data_table_view = QTableView()
        self.data_table_view.setEditTriggers(QAbstractItemView.DoubleClicked)
        self.data_table_view.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.data_table_view.setSortingEnabled(True)
        self.data_table_view.setContextMenuPolicy(Qt.CustomContextMenu)
        self.data_table_view.customContextMenuRequested.connect(self._show_data_context_menu)

        self.data_table_model = QStandardItemModel()
        
        self.proxy_model = RowNumberProxyModel()
        self.proxy_model.setSourceModel(self.data_table_model)
        self.proxy_model.setFilterCaseSensitivity(Qt.CaseInsensitive)
        self.proxy_model.setFilterKeyColumn(-1)

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

    def set_data(self, headers, data, schema=None):
        self.data_table_model.clear()
        self.data_table_model.setHorizontalHeaderLabels(headers)
        for row_data in data:
            self.add_data_row(row_data)
        
        if schema:
            delegate = CustomItemDelegate(schema, self.data_table_view)
            self.data_table_view.setItemDelegate(delegate)
        
        self.data_table_view.resizeColumnsToContents()

    def set_db_filter_columns(self, columns):
        """设置数据库筛选下拉框的字段列表。"""
        self.db_filter_column_combo.clear()
        self.db_filter_column_combo.addItems(columns)

    def get_db_filter(self):
        """获取当前数据库筛选的字段和值。"""
        column = self.db_filter_column_combo.currentText()
        value = self.db_filter_value_input.text()
        return column, value

    def clear_db_filter_inputs(self):
        """清空数据库筛选的输入。"""
        self.db_filter_column_combo.setCurrentIndex(0)
        self.db_filter_value_input.clear()

    def update_db_filter_inputs(self, column, value):
        """更新数据库筛选的输入框。"""
        self.db_filter_column_combo.setCurrentText(column)
        self.db_filter_value_input.setText(value)

    def add_data_row(self, row_data):
        row_items = [QStandardItem(str(item)) for item in row_data]
        self.data_table_model.appendRow(row_items)

    def _on_delete_row(self):
        selected_proxy_indexes = self.data_table_view.selectionModel().selectedRows()
        if not selected_proxy_indexes:
            QMessageBox.warning(self, "警告", "请先选择要删除的行。")
            return
        
        source_indexes = [self.proxy_model.mapToSource(index) for index in selected_proxy_indexes]
        rows_to_delete_count = len(source_indexes)
        
        for index in sorted(source_indexes, key=lambda x: x.row(), reverse=True):
            self.data_table_model.removeRow(index.row())
        
        self.rows_deleted_in_view.emit(rows_to_delete_count)

    def _on_save_data(self):
        source_model = self.proxy_model.sourceModel()
        headers = [source_model.horizontalHeaderItem(i).text() for i in range(source_model.columnCount())]
        data = []
        for row in range(source_model.rowCount()):
            row_data = [source_model.item(row, col).text() for col in range(source_model.columnCount())]
            data.append(row_data)
        
        df = pd.DataFrame(data, columns=headers)
        self.save_data_requested.emit(df)

    def get_data(self):
        headers = [self.data_table_model.horizontalHeaderItem(i).text() for i in range(self.data_table_model.columnCount())]
        data = []
        for row in range(self.data_table_model.rowCount()):
            row_data = [self.data_table_model.item(row, col).text() for col in range(self.data_table_model.columnCount())]
            data.append(row_data)
        
        return pd.DataFrame(data, columns=headers)

    def _on_filter_text_changed(self, text):
        self.proxy_model.setFilterRegularExpression(text)

    def _on_import(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "导入文件", self._last_io_dir, "支持的文件 (*.csv *.xlsx)")
        if file_path:
            self._last_io_dir = os.path.dirname(file_path)
            self.import_requested.emit(file_path)

    def _on_export(self):
        file_path, _ = QFileDialog.getSaveFileName(self, "导出文件", self._last_io_dir, "Excel 文件 (*.xlsx);;CSV 文件 (*.csv)")
        if file_path:
            self._last_io_dir = os.path.dirname(file_path)
            self.export_requested.emit(file_path)

    def _show_data_context_menu(self, position):
        menu = QMenu()
        
        # 获取当前点击的索引
        proxy_index = self.data_table_view.indexAt(position)
        if not proxy_index.isValid():
            return

        # 添加新行总是可用
        add_action = QAction("添加新行", self)
        add_action.triggered.connect(self.add_row_requested)
        menu.addAction(add_action)
        menu.addSeparator()

        # 复制和筛选操作
        copy_cell_action = QAction("复制单元格", self)
        copy_cell_action.triggered.connect(lambda: self._copy_cell_data(proxy_index))
        menu.addAction(copy_cell_action)

        copy_row_action = QAction("复制行", self)
        copy_row_action.triggered.connect(lambda: self._copy_row_data(proxy_index))
        menu.addAction(copy_row_action)
        
        menu.addSeparator()

        filter_action = QAction("以此值筛选", self)
        filter_action.triggered.connect(lambda: self._filter_by_cell(proxy_index))
        menu.addAction(filter_action)

        menu.addSeparator()

        # 删除操作（仅当有行被选中时）
        if self.data_table_view.selectionModel().hasSelection():
            delete_action = QAction("删除选中行", self)
            delete_action.triggered.connect(self._on_delete_row)
            menu.addAction(delete_action)
            
        menu.exec(self.data_table_view.viewport().mapToGlobal(position))

    def _copy_cell_data(self, proxy_index):
        """复制单元格数据到剪贴板。"""
        cell_data = self.proxy_model.data(proxy_index, Qt.DisplayRole)
        QGuiApplication.clipboard().setText(cell_data)

    def _copy_row_data(self, proxy_index):
        """复制整行数据到剪贴板。"""
        source_index = self.proxy_model.mapToSource(proxy_index)
        row = source_index.row()
        num_cols = self.data_table_model.columnCount()
        row_data = [self.data_table_model.item(row, col).text() for col in range(num_cols)]
        QGuiApplication.clipboard().setText("\t".join(row_data))

    def _filter_by_cell(self, proxy_index):
        """根据单元格内容进行筛选。"""
        source_index = self.proxy_model.mapToSource(proxy_index)
        column_index = source_index.column()
        column_name = self.data_table_model.horizontalHeaderItem(column_index).text()
        cell_value = self.data_table_model.item(source_index.row(), column_index).text()
        
        self.filter_by_cell_requested.emit(column_name, cell_value)

    def update_pagination_controls(self, current_page, total_pages, is_full_data_mode):
        is_paginated = total_pages > 1 and not is_full_data_mode

        self.page_label.setText(f"第 {current_page} / {total_pages} 页")
        self.page_label.setVisible(is_paginated)
        self.prev_page_button.setVisible(is_paginated)
        self.next_page_button.setVisible(is_paginated)

        self.prev_page_button.setEnabled(current_page > 1)
        self.next_page_button.setEnabled(current_page < total_pages)

        self.save_data_button.setEnabled(is_full_data_mode)
        if not is_full_data_mode and total_pages > 1:
            self.save_data_button.setToolTip("请点击“加载全部数据”以进行编辑和保存。")
        else:
            self.save_data_button.setToolTip("")

        self.toggle_full_data_button.setText("返回分页模式" if is_full_data_mode else "加载全部数据")
        self.toggle_full_data_button.setChecked(is_full_data_mode)