# src/features/game_data/views/game_data_view.py

import os
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLineEdit,
    QGroupBox, QTextEdit, QLabel, QFileDialog, QTextBrowser
)
from PySide6.QtCore import Qt

class GameDataView(QWidget):
    """
    GameData插件的用户界面。
    提供路径选择、配置编辑、功能按钮和日志显示。
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("游戏数据工具")
        self._init_ui()

    def _init_ui(self):
        main_layout = QVBoxLayout(self)

        # 1. 路径设置区域
        path_group = QGroupBox("根目录设置")
        path_layout = QHBoxLayout()
        self.path_label = QLabel("操作根目录:")
        self.path_line_edit = QLineEdit()
        self.browse_button = QPushButton("浏览...")
        path_layout.addWidget(self.path_label)
        path_layout.addWidget(self.path_line_edit)
        path_layout.addWidget(self.browse_button)
        path_group.setLayout(path_layout)
        main_layout.addWidget(path_group)

        # 1.5. 数据源路径设置区域
        db_path_group = QGroupBox("数据源设置")
        db_path_layout = QHBoxLayout()
        self.db_path_label = QLabel("数据源文件:")
        self.db_path_line_edit = QLineEdit()
        self.db_browse_button = QPushButton("浏览...")
        db_path_layout.addWidget(self.db_path_label)
        db_path_layout.addWidget(self.db_path_line_edit)
        db_path_layout.addWidget(self.db_browse_button)
        db_path_group.setLayout(db_path_layout)
        main_layout.addWidget(db_path_group)

        # 2. 配置编辑区域
        config_group = QGroupBox("分机账号配置")
        config_layout = QVBoxLayout()
        
        # 增加一个加载按钮和路径显示
        config_top_layout = QHBoxLayout()
        self.config_path_display = QLineEdit()
        self.config_path_display.setReadOnly(True)
        self.config_path_display.setPlaceholderText("当前未加载配置文件")
        self.load_config_button = QPushButton("从文件加载配置...")
        
        config_top_layout.addWidget(QLabel("当前配置文件:"))
        config_top_layout.addWidget(self.config_path_display)
        config_top_layout.addWidget(self.load_config_button)
        
        config_layout.addLayout(config_top_layout)

        self.config_text_edit = QTextEdit()
        config_layout.addWidget(self.config_text_edit)
        config_group.setLayout(config_layout)
        main_layout.addWidget(config_group)

        # 3. 操作按钮区域
        action_group = QGroupBox("核心操作")
        action_layout = QHBoxLayout()
        self.extract_button = QPushButton("1. 提取账号信息")
        self.aggregate_button = QPushButton("2. 汇总角色配置")
        self.distribute_button = QPushButton("3. 分发角色配置")
        action_layout.addWidget(self.extract_button)
        action_layout.addWidget(self.aggregate_button)
        action_layout.addWidget(self.distribute_button)
        action_group.setLayout(action_layout)
        main_layout.addWidget(action_group)

        # 4. 日志显示区域
        log_group = QGroupBox("操作日志")
        log_layout = QVBoxLayout()
        self.log_browser = QTextBrowser()
        log_layout.addWidget(self.log_browser)
        log_group.setLayout(log_layout)
        main_layout.addWidget(log_group)

        self.setLayout(main_layout)

    def get_root_path(self) -> str:
        """获取根目录路径文本框的内容。"""
        return self.path_line_edit.text()

    def set_root_path(self, path: str):
        """设置根目录路径文本框的内容。"""
        self.path_line_edit.setText(path)

    def get_db_path(self) -> str:
        """获取数据库路径文本框的内容。"""
        return self.db_path_line_edit.text()

    def set_db_path(self, path: str):
        """设置数据库路径文本框的内容。"""
        self.db_path_line_edit.setText(path)

    def get_config_text(self) -> str:
        """获取配置文本编辑框的内容。"""
        return self.config_text_edit.toPlainText()

    def set_config_text(self, text: str):
        """设置配置文本编辑框的内容。"""
        self.config_text_edit.setPlainText(text)

    def set_config_path_display(self, path: str):
        """设置配置文件路径显示框的内容。"""
        self.config_path_display.setText(path)

    def append_log(self, message: str):
        """向日志浏览器追加一条消息。"""
        self.log_browser.append(message)

    def clear_log(self):
        """清空日志浏览器。"""
        self.log_browser.clear()

    def select_directory(self) -> str | None:
        """打开目录选择对话框。"""
        directory = QFileDialog.getExistingDirectory(
            self,
            "选择操作根目录",
            self.get_root_path() or os.path.expanduser("~")
        )
        return directory

    def select_db_file(self) -> str | None:
        """打开文件选择对话框选择数据源文件（数据库或Excel）。"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "选择数据源文件",
            self.get_db_path() or os.path.expanduser("~"),
            "数据文件 (*.db *.sqlite *.sqlite3 *.xlsx *.xls *.xlsm);;"
            "数据库文件 (*.db *.sqlite *.sqlite3);;"
            "Excel 文件 (*.xlsx *.xls *.xlsm);;"
            "所有文件 (*)"
        )
        return file_path

    def select_config_file(self) -> str | None:
        """打开文件选择对话框选择配置文件，使用智能默认路径。"""
        # 优先使用当前配置文件所在的目录
        current_config_path = self.config_path_display.text()
        if current_config_path and os.path.isfile(current_config_path):
            default_path = os.path.dirname(current_config_path)
        # 其次使用根目录
        elif self.get_root_path() and os.path.isdir(self.get_root_path()):
            default_path = self.get_root_path()
        # 最后使用用户主目录
        else:
            default_path = os.path.expanduser("~")

        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "选择分机账号配置文件",
            default_path,
            "文本文件 (*.txt);;所有文件 (*)"
        )
        return file_path
