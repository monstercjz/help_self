# desktop_center/src/features/app_launcher/views/launcher_page_view.py
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                               QListWidget, QAbstractItemView, QListWidgetItem,
                               QLabel, QFileDialog, QLineEdit, QDialog, QDialogButtonBox)
from PySide6.QtCore import Signal, Qt

# 【新增】导入 os 和 sys 模块以修复 NameError
import os
import sys

from typing import List, Dict

class AddAppDialog(QDialog):
    """一个用于添加新应用程序的对话框。"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("添加新应用")
        
        self.layout = QVBoxLayout(self)
        
        # 应用名称输入
        self.name_label = QLabel("应用名称:")
        self.name_input = QLineEdit()
        self.layout.addWidget(self.name_label)
        self.layout.addWidget(self.name_input)
        
        # 应用路径输入
        self.path_label = QLabel("应用路径:")
        path_layout = QHBoxLayout()
        self.path_input = QLineEdit()
        self.browse_button = QPushButton("浏览...")
        self.browse_button.clicked.connect(self.browse_file)
        path_layout.addWidget(self.path_input)
        path_layout.addWidget(self.browse_button)
        self.layout.addWidget(self.path_label)
        self.layout.addLayout(path_layout)

        # 按钮
        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        self.layout.addWidget(self.button_box)

    def browse_file(self):
        """打开文件对话框以选择应用程序。"""
        # 在Windows上筛选.exe, 在macOS上筛选.app, 其他系统不筛选
        file_filter = "Applications (*.exe)" if os.name == 'nt' else "Applications (*.app)" if sys.platform == 'darwin' else "All files (*)"
        file_path, _ = QFileDialog.getOpenFileName(self, "选择应用程序", "", file_filter)
        if file_path:
            self.path_input.setText(file_path)
            # 自动填充应用名称（不带扩展名）
            if not self.name_input.text():
                app_name = os.path.basename(file_path)
                app_name = os.path.splitext(app_name)[0]
                self.name_input.setText(app_name)

    def get_data(self):
        """获取用户输入的数据。"""
        return self.name_input.text(), self.path_input.text()

class LauncherPageView(QWidget):
    """
    应用启动器插件的UI视图。
    负责显示应用程序列表和操作按钮，并发出用户交互信号。
    """
    # 定义信号
    add_app_requested = Signal(str, str)
    remove_app_requested = Signal(int)
    launch_app_requested = Signal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()

    def setup_ui(self):
        """构建UI界面。"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)

        # 标题
        title_label = QLabel("应用启动器")
        title_label.setStyleSheet("font-size: 22px; font-weight: bold; color: #333;")
        main_layout.addWidget(title_label)

        # 应用程序列表
        self.app_list_widget = QListWidget()
        self.app_list_widget.setSelectionMode(QAbstractItemView.SingleSelection)
        self.app_list_widget.itemDoubleClicked.connect(self.on_item_double_clicked)
        main_layout.addWidget(self.app_list_widget)

        # 按钮布局
        button_layout = QHBoxLayout()
        self.add_button = QPushButton("＋ 添加")
        self.remove_button = QPushButton("－ 删除")
        self.launch_button = QPushButton("▶ 启动")
        
        button_layout.addWidget(self.add_button)
        button_layout.addWidget(self.remove_button)
        button_layout.addStretch()
        button_layout.addWidget(self.launch_button)
        main_layout.addLayout(button_layout)
        
        # 连接按钮信号到槽函数
        self.add_button.clicked.connect(self.on_add_button_clicked)
        self.remove_button.clicked.connect(self.on_remove_button_clicked)
        self.launch_button.clicked.connect(self.on_launch_button_clicked)

    def on_add_button_clicked(self):
        """处理添加按钮的点击事件，弹出对话框。"""
        dialog = AddAppDialog(self)
        if dialog.exec():
            name, path = dialog.get_data()
            if name and path:
                self.add_app_requested.emit(name, path)

    def on_remove_button_clicked(self):
        """处理删除按钮的点击事件。"""
        selected_item = self.app_list_widget.currentItem()
        if selected_item:
            row = self.app_list_widget.row(selected_item)
            self.remove_app_requested.emit(row)

    def on_launch_button_clicked(self):
        """处理启动按钮的点击事件。"""
        selected_item = self.app_list_widget.currentItem()
        if selected_item:
            row = self.app_list_widget.row(selected_item)
            self.launch_app_requested.emit(row)
            
    def on_item_double_clicked(self, item: QListWidgetItem):
        """处理列表项双击事件，等同于启动。"""
        row = self.app_list_widget.row(item)
        self.launch_app_requested.emit(row)

    def update_app_list(self, apps: List[Dict[str, str]]):
        """
        用新的数据更新应用程序列表。

        Args:
            apps (List[Dict[str, str]]): 应用程序字典列表。
        """
        self.app_list_widget.clear()
        for app in apps:
            item = QListWidgetItem(f"{app['name']} ({app['path']})")
            self.app_list_widget.addItem(item)