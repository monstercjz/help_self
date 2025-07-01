# desktop_center/src/features/app_launcher/controllers/launcher_controller.py
import logging
import os
import sys
from PySide6.QtCore import QObject, QProcess

from src.core.context import ApplicationContext
from src.features.app_launcher.models.launcher_model import LauncherModel
from src.features.app_launcher.views.launcher_page_view import LauncherPageView

class LauncherController(QObject):
    """
    应用启动器插件的控制器。
    连接视图和模型，处理业务逻辑。
    """
    def __init__(self, model: LauncherModel, view: LauncherPageView, context: ApplicationContext, parent=None):
        super().__init__(parent)
        self.model = model
        self.view = view
        self.context = context
        self.process = QProcess() # 用于启动外部程序
        
        self._connect_signals()
        self.refresh_view()

    def _connect_signals(self):
        """连接视图发出的信号到本控制器的槽函数。"""
        self.view.add_app_requested.connect(self.add_app)
        self.view.remove_app_requested.connect(self.remove_app)
        self.view.launch_app_requested.connect(self.launch_app)
        self.process.errorOccurred.connect(self.on_launch_error)

    def refresh_view(self):
        """从模型获取数据并更新视图。"""
        apps = self.model.get_apps()
        self.view.update_app_list(apps)

    def add_app(self, name: str, path: str):
        """处理添加应用的逻辑。"""
        logging.info(f"控制器接收到添加应用请求: name='{name}', path='{path}'")
        self.model.add_app(name, path)
        self.refresh_view()

    def remove_app(self, index: int):
        """处理删除应用的逻辑。"""
        logging.info(f"控制器接收到删除应用请求: index={index}")
        self.model.remove_app(index)
        self.refresh_view()

    def launch_app(self, index: int):
        """处理启动应用的逻辑。"""
        app_path = self.model.get_app_path(index)
        if app_path and os.path.exists(app_path):
            logging.info(f"正在尝试启动应用: {app_path}")
            # 使用 QProcess.startDetached 启动，不阻塞主程序，且程序独立运行
            # 在macOS上，需要使用 `open` 命令来启动 .app 包
            if sys.platform == "darwin" and app_path.endswith(".app"):
                QProcess.startDetached('open', [app_path])
            else:
                QProcess.startDetached(f'"{app_path}"', [])
        else:
            logging.error(f"无法启动应用：路径 '{app_path}' 无效或文件不存在。")
            self.context.notification_service.show(
                title="启动失败",
                message=f"无法找到应用程序路径:\n{app_path}"
            )
            
    def on_launch_error(self, error: QProcess.ProcessError):
        """处理 QProcess 启动错误。"""
        error_string = self.process.errorString()
        logging.error(f"启动外部程序失败 (错误码: {error}): {error_string}")
        self.context.notification_service.show(
            title="启动失败",
            message=f"启动应用程序时发生错误:\n{error_string}"
        )