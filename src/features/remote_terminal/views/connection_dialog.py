from PySide6.QtWidgets import (QDialog, QVBoxLayout, QFormLayout, QLineEdit,
                               QPushButton, QDialogButtonBox)

class ConnectionDialog(QDialog):
    """
    A dialog for adding or editing an SSH connection configuration.
    """
    def __init__(self, config=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Connection Details")
        
        self.name_input = QLineEdit()
        self.host_input = QLineEdit()
        self.port_input = QLineEdit()
        self.user_input = QLineEdit()
        self.pass_input = QLineEdit()
        self.pass_input.setEchoMode(QLineEdit.Password)

        if config:
            self.name_input.setText(config.get("name", ""))
            self.host_input.setText(config.get("hostname", ""))
            self.port_input.setText(str(config.get("port", "")))
            self.user_input.setText(config.get("username", ""))
            self.pass_input.setText(config.get("password", ""))

        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        form_layout = QFormLayout()
        
        form_layout.addRow("Name:", self.name_input)
        form_layout.addRow("Host:", self.host_input)
        form_layout.addRow("Port:", self.port_input)
        form_layout.addRow("Username:", self.user_input)
        form_layout.addRow("Password:", self.pass_input)
        
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
            "hostname": self.host_input.text(),
            "port": int(self.port_input.text()) if self.port_input.text().isdigit() else 22,
            "username": self.user_input.text(),
            "password": self.pass_input.text()
        }