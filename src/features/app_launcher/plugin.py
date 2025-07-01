# desktop_center/src/features/app_launcher/plugin.py
import logging
from PySide6.QtWidgets import QWidget

from src.core.context import ApplicationContext
from src.core.plugin_interface import IFeaturePlugin
from src.features.app_launcher.models.launcher_model import LauncherModel
from src.features.app_launcher.views.launcher_page_view import LauncherPageView
from src.features.app_launcher.controllers.launcher_controller import LauncherController

class AppLauncherPlugin(IFeaturePlugin):
    """
    “应用启动器”功能插件的实现。
    遵循IFeaturePlugin接口，负责组装并提供插件的UI和逻辑。
    """
    
    def name(self) -> str:
        """返回插件的唯一内部名称。"""
        return "app_launcher"

    def display_name(self) -> str:
        """返回插件在UI上显示的名称。"""
        return "应用启动器"
        
    def load_priority(self) -> int:
        """返回插件的加载优先级。"""
        return 100 # 普通独立功能插件

    def initialize(self, context: ApplicationContext):
        """
        初始化插件，创建并连接MVC组件。
        """
        super().initialize(context)
        logging.info(f"正在初始化插件: {self.display_name()}...")

        # 1. 创建 Model
        self.model = LauncherModel()

        # 2. 创建 View
        self.page_widget = LauncherPageView()

        # 3. 创建 Controller，并连接 M, V, 和 C
        self.controller = LauncherController(
            model=self.model,
            view=self.page_widget,
            context=self.context
        )
        
        logging.info(f"插件 '{self.display_name()}' 初始化完成。")

    def get_page_widget(self) -> QWidget | None:
        """返回此插件的主UI页面控件实例。"""
        return self.page_widget

    def shutdown(self):
        """
        在应用程序关闭时，安全地关闭插件。
        对于此插件，可以确保数据被最后一次保存。
        """
        logging.info(f"正在关闭插件: {self.display_name()}...")
        if hasattr(self, 'model'):
            self.model.save_apps()
        super().shutdown()
        logging.info(f"插件 '{self.display_name()}' 已关闭。")