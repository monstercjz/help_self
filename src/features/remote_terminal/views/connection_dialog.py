from PySide6.QtWidgets import (QDialog, QVBoxLayout, QFormLayout, QLineEdit,
                               QPushButton, QDialogButtonBox, QComboBox)

class ConnectionDialog(QDialog):
    """
    A dialog for adding or editing an SSH connection configuration.
    """
    def __init__(self, config=None, existing_groups=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("连接详情")
        
        self.name_input = QLineEdit()
        self.group_input = QComboBox()
        self.group_input.setEditable(True)
        if existing_groups:
            self.group_input.addItems(existing_groups)
        self.host_input = QLineEdit()
        self.port_input = QLineEdit()
        self.user_input = QLineEdit()
        self.pass_input = QLineEdit()
        self.pass_input.setEchoMode(QLineEdit.Password)

        if config:
            self.name_input.setText(config.get("name", ""))
            self.group_input.setCurrentText(config.get("group_name", ""))
            self.host_input.setText(config.get("hostname", ""))
            self.port_input.setText(str(config.get("port", "")))
            self.user_input.setText(config.get("username", ""))
            self.pass_input.setText(config.get("password", ""))

        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        form_layout = QFormLayout()
        
        form_layout.addRow("名称:", self.name_input)
        form_layout.addRow("分组:", self.group_input)
        form_layout.addRow("主机:", self.host_input)
        form_layout.addRow("端口:", self.port_input)
        form_layout.addRow("用户名:", self.user_input)
        form_layout.addRow("密码:", self.pass_input)
        
        layout.addLayout(form_layout)
        
        # Standard buttons
        button_box = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        
        layout.addWidget(button_box)

    def get_data(self):
        """Returns the data entered in the form."""
        return {
            "name": self.name_input.text(),
            "group_name": self.group_input.currentText(),
            "hostname": self.host_input.text(),
            "port": int(self.port_input.text()) if self.port_input.text().isdigit() else 22,
            "username": self.user_input.text(),
            "password": self.pass_input.text()
        }