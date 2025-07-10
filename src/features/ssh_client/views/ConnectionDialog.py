# src/features/ssh_client/views/ConnectionDialog.py
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QFormLayout, QLineEdit,
                                QSpinBox, QPushButton, QComboBox, QFileDialog,
                                QHBoxLayout, QMessageBox)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QIcon
import os

from ..models import SshConnectionModel

class ConnectionDialog(QDialog):
    """
    用于添加或编辑SSH连接配置的对话框。
    """
    connectionSaved = Signal(SshConnectionModel)

    def __init__(self, connection: SshConnectionModel = None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("SSH连接配置")
        self.setMinimumWidth(400)

        self.connection = connection if connection else SshConnectionModel()
        self._is_editing = connection is not None

        self._init_ui()
        self._load_connection_data()

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        form_layout = QFormLayout()

        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("连接名称 (例如: My Server)")
        form_layout.addRow("名称:", self.name_input)

        self.host_input = QLineEdit()
        self.host_input.setPlaceholderText("主机地址 (例如: example.com 或 192.168.1.1)")
        form_layout.addRow("主机:", self.host_input)

        self.port_input = QSpinBox()
        self.port_input.setRange(1, 65535)
        self.port_input.setValue(22)
        form_layout.addRow("端口:", self.port_input)

        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("用户名 (例如: root)")
        form_layout.addRow("用户名:", self.username_input)

        self.auth_method_combo = QComboBox()
        self.auth_method_combo.addItems(["密码", "私钥"])
        self.auth_method_combo.currentIndexChanged.connect(self._on_auth_method_changed)
        form_layout.addRow("认证方式:", self.auth_method_combo)

        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setPlaceholderText("SSH密码")
        form_layout.addRow("密码:", self.password_input)

        self.private_key_path_input = QLineEdit()
        self.private_key_path_input.setPlaceholderText("私钥文件路径 (例如: ~/.ssh/id_rsa)")
        self.browse_key_button = QPushButton("浏览...")
        self.browse_key_button.clicked.connect(self._browse_private_key)
        
        key_layout = QHBoxLayout()
        key_layout.addWidget(self.private_key_path_input)
        key_layout.addWidget(self.browse_key_button)
        form_layout.addRow("私钥路径:", key_layout)

        main_layout.addLayout(form_layout)

        button_layout = QHBoxLayout()
        self.save_button = QPushButton("保存")
        self.save_button.clicked.connect(self._save_connection)
        self.cancel_button = QPushButton("取消")
        self.cancel_button.clicked.connect(self.reject)
        
        button_layout.addStretch()
        button_layout.addWidget(self.save_button)
        button_layout.addWidget(self.cancel_button)
        button_layout.addStretch()

        main_layout.addLayout(button_layout)

        self._on_auth_method_changed(self.auth_method_combo.currentIndex()) # 初始化显示

    def _load_connection_data(self):
        """加载现有连接数据到UI。"""
        self.name_input.setText(self.connection.name)
        self.host_input.setText(self.connection.host)
        self.port_input.setValue(self.connection.port)
        self.username_input.setText(self.connection.username)
        
        if self.connection.auth_method == "private_key":
            self.auth_method_combo.setCurrentIndex(1)
            self.private_key_path_input.setText(self.connection.private_key_path)
        else:
            self.auth_method_combo.setCurrentIndex(0)
            self.password_input.setText(self.connection.password)

    def _on_auth_method_changed(self, index: int):
        """根据认证方式切换密码和私钥输入框的可见性。"""
        if index == 0:  # 密码
            self.password_input.setVisible(True)
            self.private_key_path_input.setVisible(False)
            self.browse_key_button.setVisible(False)
        else:  # 私钥
            self.password_input.setVisible(False)
            self.private_key_path_input.setVisible(True)
            self.browse_key_button.setVisible(True)

    def _browse_private_key(self):
        """打开文件对话框选择私钥文件。"""
        file_path, _ = QFileDialog.getOpenFileName(self, "选择私钥文件", os.path.expanduser("~/.ssh/"),
                                                   "所有文件 (*);;PEM文件 (*.pem);;PPK文件 (*.ppk)")
        if file_path:
            self.private_key_path_input.setText(file_path)

    def _save_connection(self):
        """保存连接配置并发出信号。"""
        name = self.name_input.text().strip()
        host = self.host_input.text().strip()
        port = self.port_input.value()
        username = self.username_input.text().strip()
        auth_method = "password" if self.auth_method_combo.currentIndex() == 0 else "private_key"
        password = self.password_input.text()
        private_key_path = self.private_key_path_input.text().strip()

        if not name or not host or not username:
            QMessageBox.warning(self, "输入错误", "名称、主机和用户名不能为空。")
            return
        
        if auth_method == "password" and not password:
            QMessageBox.warning(self, "输入错误", "密码认证方式下，密码不能为空。")
            return
        
        if auth_method == "private_key" and not private_key_path:
            QMessageBox.warning(self, "输入错误", "私钥认证方式下，私钥路径不能为空。")
            return

        self.connection.name = name
        self.connection.host = host
        self.connection.port = port
        self.connection.username = username
        self.connection.auth_method = auth_method
        self.connection.password = password if auth_method == "password" else ""
        self.connection.private_key_path = private_key_path if auth_method == "private_key" else ""

        self.connectionSaved.emit(self.connection)
        self.accept()