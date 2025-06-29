# desktop_center/src/ui/action_manager.py
from PySide6.QtCore import QObject
from PySide6.QtGui import QAction
from typing import Dict

class ActionManager(QObject):
    """
    【修改】中央动作管理器，作为一个通用的动作注册中心。
    插件或其他组件可以注册全局可用的QAction，实现功能触发和UI组件的解耦。
    它本身不应持有任何特定功能的动作实例。
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self._actions: Dict[str, QAction] = {}

    def register_action(self, name: str, action: QAction) -> None:
        """
        【新增】注册一个全局动作。

        Args:
            name (str): 动作的唯一标识符，例如 'alert_center.show_history'。
            action (QAction): 要注册的QAction实例。
        
        Raises:
            ValueError: 如果同名动作已被注册。
        """
        if name in self._actions:
            raise ValueError(f"动作 '{name}' 已经被注册。")
        self._actions[name] = action

    def get_action(self, name: str) -> QAction | None:
        """
        【新增】根据名称获取一个已注册的动作。

        Args:
            name (str): 动作的唯一标识符。

        Returns:
            QAction | None: 返回找到的QAction实例，如果未找到则返回None。
        """
        return self._actions.get(name)