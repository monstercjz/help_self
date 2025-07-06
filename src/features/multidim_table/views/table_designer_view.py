# src/features/multidim_table/views/table_designer_view.py
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QTabWidget, QWidget, QTableView,
    QAbstractItemView, QHeaderView, QPushButton, QHBoxLayout,
    QListWidget, QInputDialog, QMessageBox
)
from PySide6.QtGui import QStandardItemModel, QStandardItem
from PySide6.QtCore import Signal, Qt

class TableDesignerView(QDialog):
    """
    一个用于设计表结构和编辑表数据的对话框。
    """
    add_column_requested = Signal(str)
    delete_column_requested = Signal(str)
    rename_column_requested = Signal(str, str)
    add_row_requested = Signal()
    delete_row_requested = Signal(list)
    save_data_requested = Signal(object)

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

        layout.addWidget(self.tabs)

    def setup_data_tab(self, layout):
        # --- Top button bar ---
        top_bar_layout = QHBoxLayout()
        self.add_row_button = QPushButton("添加行")
        self.add_row_button.clicked.connect(self.add_row_requested)
        top_bar_layout.addWidget(self.add_row_button)
        
        self.delete_row_button = QPushButton("删除选中行")
        self.delete_row_button.clicked.connect(self._on_delete_row)
        top_bar_layout.addWidget(self.delete_row_button)
        
        top_bar_layout.addStretch()
        
        self.save_data_button = QPushButton("保存更改")
        self.save_data_button.clicked.connect(self._on_save_data)
        top_bar_layout.addWidget(self.save_data_button)
        
        layout.addLayout(top_bar_layout)

        # --- Table View for Editing ---
        self.data_table_view = QTableView()
        self.data_table_view.setEditTriggers(QAbstractItemView.DoubleClicked)
        self.data_table_view.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.data_table_model = QStandardItemModel()
        self.data_table_view.setModel(self.data_table_model)
        layout.addWidget(self.data_table_view)

    def setup_structure_tab(self, layout):
        # --- Top button bar ---
        top_bar_layout = QHBoxLayout()
        self.add_column_button = QPushButton("添加字段")
        self.add_column_button.clicked.connect(self._on_add_column)
        top_bar_layout.addWidget(self.add_column_button)
        
        self.delete_column_button = QPushButton("删除选中字段")
        self.delete_column_button.clicked.connect(self._on_delete_column)
        top_bar_layout.addWidget(self.delete_column_button)

        self.rename_column_button = QPushButton("重命名字段")
        self.rename_column_button.clicked.connect(self._on_rename_column)
        top_bar_layout.addWidget(self.rename_column_button)
        
        top_bar_layout.addStretch()
        layout.addLayout(top_bar_layout)

        # --- Column List ---
        self.column_list_widget = QListWidget()
        layout.addWidget(self.column_list_widget)

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

    def _on_rename_column(self):
        selected_item = self.column_list_widget.currentItem()
        if not selected_item:
            QMessageBox.warning(self, "警告", "请先选择一个要重命名的字段。")
            return

        old_name = selected_item.text().split(" ")[0]
        new_name, ok = QInputDialog.getText(self, "重命名字段", f"请输入 '{old_name}' 的新名称:")
        if ok and new_name and new_name != old_name:
            self.rename_column_requested.emit(old_name, new_name)

    def _on_delete_row(self):
        selected_rows = self.data_table_view.selectionModel().selectedRows()
        if not selected_rows:
            QMessageBox.warning(self, "警告", "请先选择要删除的行。")
            return
        
        rows_to_delete = [index.row() for index in selected_rows]
        self.delete_row_requested.emit(rows_to_delete)

    def _on_save_data(self):
        headers = [self.data_table_model.horizontalHeaderItem(i).text() for i in range(self.data_table_model.columnCount())]
        data = []
        for row in range(self.data_table_model.rowCount()):
            row_data = [self.data_table_model.item(row, col).text() for col in range(self.data_table_model.columnCount())]
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
