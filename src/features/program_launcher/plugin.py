# desktop_center/src/features/program_launcher/plugin.py
import logging
from src.core.plugin_interface import IFeaturePlugin
from src.core.context import ApplicationContext

# 导入插件内部的MVC组件
from .controllers.launcher_controller import LauncherController
from .models.launcher_model import LauncherModel
from .views.launcher_page_view import LauncherPageView

class ProgramLauncherPlugin(IFeaturePlugin):
    """
    程序启动器插件，提供管理和快速启动应用程序的功能。
    """
    
    def name(self) -> str:
        """返回插件的唯一内部名称。"""
        return "program_launcher"

    def display_name(self) -> str:
        """返回插件在UI上显示的名称。"""
        return "程序启动器"
        
    def load_priority(self) -> int:
        """返回插件的加载优先级。"""
        return 100 # 普通独立功能插件

    def initialize(self, context: ApplicationContext):
        """
        初始化插件，创建并连接MVC组件。
        """
        super().initialize(context)
        logging.info(f"[{self.name()}]-> 插件初始化开始...")

        # 1. 创建模型，并将ConfigService注入，以实现路径配置化
        # 【修改】将 context.config_service 传递给模型
        self.model = LauncherModel(config_service=context.config_service)

        # 2. 创建视图
        self.view = LauncherPageView()

        # 3. 创建控制器，将模型和视图注入
        self.controller = LauncherController(self.model, self.view, context)

        # 4. 将视图（主页面）设置为插件的UI页面
        self.page_widget = self.view
        
        logging.info(f"[{self.name()}]-> 插件初始化完成。")

    def shutdown(self):
        """
        在应用程序关闭时，确保数据被保存。
        """
        logging.info(f"[{self.name()}]-> 插件关闭，正在保存数据...")
        if hasattr(self, 'model'):
            self.model.save_data()
        super().shutdown()
        logging.info(f"[{self.name()}]-> 插件已关闭。")