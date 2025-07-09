from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QPushButton, QHBoxLayout,
    QListWidget, QInputDialog, QMessageBox, QMenu, QStyle
)
from PySide6.QtGui import QAction
from PySide6.QtCore import Signal, Qt
from .edit_column_dialog import EditColumnDialog
from .add_column_dialog import AddColumnDialog

class StructureTabView(QWidget):
    """
    表结构选项卡视图，用于管理表的字段。
    """
    add_column_requested = Signal(str, str) # name, type
    delete_column_requested = Signal(str)
    change_column_requested = Signal(str, str, str) # old_name, new_name, new_type

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

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

    def set_schema(self, schema):
        """设置并显示表结构（字段列表）。"""
        self.column_list_widget.clear()
        for col in schema:
            self.column_list_widget.addItem(f"{col['name']} ({col['type']})")

    def _on_add_column(self):
        dialog = AddColumnDialog(self)
        if dialog.exec():
            name, type = dialog.get_values()
            if name:
                self.add_column_requested.emit(name, type)
            else:
                QMessageBox.warning(self, "警告", "字段名不能为空。")

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

    def _show_structure_context_menu(self, position):
        menu = QMenu()
        
        add_action = QAction("添加新字段", self)
        add_action.triggered.connect(self._on_add_column)
        menu.addAction(add_action)

        if self.column_list_widget.itemAt(position):
            edit_action = QAction("修改选中字段", self)
            edit_action.triggered.connect(self._on_edit_column)
            menu.addAction(edit_action)

            delete_action = QAction("删除选中字段", self)
            delete_action.triggered.connect(self._on_delete_column)
            menu.addAction(delete_action)
            
        menu.exec(self.column_list_widget.mapToGlobal(position))