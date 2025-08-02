# src/features/multidim_table/views/db_management_view.py
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QListWidget,
    QInputDialog, QMessageBox, QListWidgetItem, QLabel, QFileDialog,
    QStyle, QMenu
)
from PySide6.QtCore import Signal, Qt
import os
from PySide6.QtGui import QAction

class DbManagementView(QWidget):
    """
    数据库管理视图，用于选择数据库文件，并显示、创建和删除表。
    """
    open_db_requested = Signal(str)
    create_db_requested = Signal(str)
    table_selected = Signal(str)
    create_table_requested = Signal(str, list)
    delete_table_requested = Signal(str)
    rename_table_requested = Signal(str, str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("数据库管理")
        self._current_db_path = None  # 增加专门的状态变量
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        
        # --- Database Selection Toolbar ---
        db_toolbar = QHBoxLayout()
        self.create_db_button = QPushButton("新建数据库")
        self.create_db_button.setIcon(self.style().standardIcon(QStyle.SP_FileIcon))
        self.create_db_button.clicked.connect(self._on_create_db)
        db_toolbar.addWidget(self.create_db_button)

        self.open_db_button = QPushButton("打开数据库")
        self.open_db_button.setIcon(self.style().standardIcon(QStyle.SP_DirOpenIcon))
        self.open_db_button.clicked.connect(self._on_open_db)
        db_toolbar.addWidget(self.open_db_button)
        
        self.current_db_label = QLabel("当前未打开数据库")
        db_toolbar.addWidget(self.current_db_label)
        db_toolbar.addStretch()
        layout.addLayout(db_toolbar)

        # --- Table Management Panel ---
        self.table_panel = QWidget()
        table_layout = QHBoxLayout(self.table_panel)
        self.create_table_button = QPushButton("创建新表")
        self.create_table_button.setIcon(self.style().standardIcon(QStyle.SP_FileDialogNewFolder))
        self.create_table_button.clicked.connect(self._on_create_table_clicked)
        table_layout.addWidget(self.create_table_button)

        self.delete_table_button = QPushButton("删除选中表")
        self.delete_table_button.setIcon(self.style().standardIcon(QStyle.SP_TrashIcon))
        self.delete_table_button.clicked.connect(self._on_delete_table_clicked)
        table_layout.addWidget(self.delete_table_button)

        self.rename_table_button = QPushButton("重命名选中表")
        self.rename_table_button.setIcon(self.style().standardIcon(QStyle.SP_DriveFDIcon)) # Using a floppy disk icon for 'rename'
        self.rename_table_button.clicked.connect(self._on_rename_table_clicked)
        table_layout.addWidget(self.rename_table_button)

        table_layout.addStretch()
        layout.addWidget(self.table_panel)

        # --- Table List ---
        self.table_list_widget = QListWidget()
        self.table_list_widget.itemDoubleClicked.connect(self._on_table_selected)
        self.table_list_widget.setContextMenuPolicy(Qt.CustomContextMenu)
        self.table_list_widget.customContextMenuRequested.connect(self._show_table_context_menu)
        layout.addWidget(self.table_list_widget)

    def _get_current_db_dir(self) -> str:
        """从状态变量获取当前数据库的目录，并提供回退。"""
        if self._current_db_path and os.path.exists(os.path.dirname(self._current_db_path)):
            return os.path.dirname(self._current_db_path)
        return os.path.expanduser("~")

    def _on_create_db(self):
        start_dir = self._get_current_db_dir()
        file_path, _ = QFileDialog.getSaveFileName(self, "创建新数据库", start_dir, "SQLite 数据库 (*.db)")
        if file_path:
            self.create_db_requested.emit(file_path)

    def _on_open_db(self):
        start_dir = self._get_current_db_dir()
        file_path, _ = QFileDialog.getOpenFileName(self, "打开数据库", start_dir, "SQLite 数据库 (*.db)")
        if file_path:
            self.open_db_requested.emit(file_path)

    def set_current_db(self, path: str):
        """设置并显示当前数据库路径。"""
        self._current_db_path = path  # 更新状态变量
        if path:
            self.current_db_label.setText(f"当前数据库: {path}")
            self.table_panel.setEnabled(True)
            self.table_list_widget.setEnabled(True)
        else:
            self.current_db_label.setText("当前未打开数据库")
            self.table_panel.setEnabled(False)
            self.table_list_widget.setEnabled(False)
            self.table_list_widget.clear()

    def update_table_list(self, tables: list[str]):
        """更新表列表。"""
        self.table_list_widget.clear()
        self.table_list_widget.addItems(tables)

    def _on_create_table_clicked(self):
        table_name, ok = QInputDialog.getText(self, "创建新表", "请输入新表名:")
        if ok and table_name:
            # 创建一个只包含id主键的空表
            self.create_table_requested.emit(table_name, ["id"])

    def _on_delete_table_clicked(self):
        selected_item = self.table_list_widget.currentItem()
        if not selected_item:
            QMessageBox.warning(self, "警告", "请先选择一个要删除的表。")
            return
        
        table_name = selected_item.text()
        reply = QMessageBox.question(
            self, "确认删除", f"您确定要永久删除表 '{table_name}' 吗？此操作不可恢复。",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            self.delete_table_requested.emit(table_name)

    def _on_table_selected(self, item: QListWidgetItem):
        self.table_selected.emit(item.text())

    def show_error(self, title: str, message: str):
        QMessageBox.critical(self, title, message)

    def _on_rename_table_clicked(self):
        selected_item = self.table_list_widget.currentItem()
        if not selected_item:
            QMessageBox.warning(self, "警告", "请先选择一个要重命名的表。")
            return

        old_name = selected_item.text()
        new_name, ok = QInputDialog.getText(self, "重命名表", f"请输入 '{old_name}' 的新名称:")
        if ok and new_name and new_name != old_name:
            self.rename_table_requested.emit(old_name, new_name)

    def _show_table_context_menu(self, position):
        """显示表列表的右键上下文菜单。"""
        selected_item = self.table_list_widget.itemAt(position)
        if not selected_item:
            return

        menu = QMenu()
        
        open_action = QAction("打开", self)
        open_action.triggered.connect(lambda: self._on_table_selected(selected_item))
        menu.addAction(open_action)

        rename_action = QAction("重命名", self)
        rename_action.triggered.connect(self._on_rename_table_clicked)
        menu.addAction(rename_action)

        delete_action = QAction("删除", self)
        delete_action.triggered.connect(self._on_delete_table_clicked)
        menu.addAction(delete_action)
        
        menu.exec(self.table_list_widget.mapToGlobal(position))
