# src/features/ssh_client/models/SshConnectionModel.py
from PySide6.QtCore import QObject, Property, Signal

class SshConnectionModel(QObject):
    """
    SSH连接配置的数据模型。
    """
    # 当连接数据发生变化时发出的信号
    dataChanged = Signal()

    def __init__(self, connection_id: str = None, name: str = "", host: str = "", port: int = 22,
                 username: str = "", auth_method: str = "password", password: str = "",
                 private_key_path: str = "", parent=None):
        super().__init__(parent)
        self._id = connection_id
        self._name = name
        self._host = host
        self._port = port
        self._username = username
        self._auth_method = auth_method  # "password" or "private_key"
        self._password = password
        self._private_key_path = private_key_path

    @Property(str, constant=True)
    def id(self) -> str:
        return self._id

    @Property(str, notify=dataChanged)
    def name(self) -> str:
        return self._name

    @name.setter
    def name(self, value: str):
        if self._name != value:
            self._name = value
            self.dataChanged.emit()

    @Property(str, notify=dataChanged)
    def host(self) -> str:
        return self._host

    @host.setter
    def host(self, value: str):
        if self._host != value:
            self._host = value
            self.dataChanged.emit()

    @Property(int, notify=dataChanged)
    def port(self) -> int:
        return self._port

    @port.setter
    def port(self, value: int):
        if self._port != value:
            self._port = value
            self.dataChanged.emit()

    @Property(str, notify=dataChanged)
    def username(self) -> str:
        return self._username

    @username.setter
    def username(self, value: str):
        if self._username != value:
            self._username = value
            self.dataChanged.emit()

    @Property(str, notify=dataChanged)
    def auth_method(self) -> str:
        return self._auth_method

    @auth_method.setter
    def auth_method(self, value: str):
        if self._auth_method != value:
            self._auth_method = value
            self.dataChanged.emit()

    @Property(str, notify=dataChanged)
    def password(self) -> str:
        return self._password

    @password.setter
    def password(self, value: str):
        if self._password != value:
            self._password = value
            self.dataChanged.emit()

    @Property(str, notify=dataChanged)
    def private_key_path(self) -> str:
        return self._private_key_path

    @private_key_path.setter
    def private_key_path(self, value: str):
        if self._private_key_path != value:
            self._private_key_path = value
            self.dataChanged.emit()

    def to_dict(self) -> dict:
        """将模型数据转换为字典，便于存储。"""
        return {
            "id": self._id,
            "name": self._name,
            "host": self._host,
            "port": self._port,
            "username": self._username,
            "auth_method": self._auth_method,
            "password": self._password,
            "private_key_path": self._private_key_path
        }

    @classmethod
    def from_dict(cls, data: dict):
        """从字典创建模型实例。"""
        return cls(
            connection_id=data.get("id"),
            name=data.get("name", ""),
            host=data.get("host", ""),
            port=data.get("port", 22),
            username=data.get("username", ""),
            auth_method=data.get("auth_method", "password"),
            password=data.get("password", ""),
            private_key_path=data.get("private_key_path", "")
        )