# desktop_center/src/features/window_arranger/plugin.py
import logging
from PySide6.QtWidgets import QWidget
from src.core.plugin_interface import IFeaturePlugin
from src.core.context import ApplicationContext
from src.features.window_arranger.views.arranger_page_view import ArrangerPageView
from src.features.window_arranger.controllers.arranger_controller import ArrangerController

class WindowArrangerPlugin(IFeaturePlugin):
    """
    桌面窗口管理插件的入口。
    实现了 IFeaturePlugin 接口，负责插件的生命周期管理。
    """
    def name(self) -> str:
        """返回插件的唯一内部名称。"""
        return "window_arranger"

    def display_name(self) -> str:
        """返回插件在用户界面上显示的名称。"""
        return "桌面窗口管理"

    def load_priority(self) -> int:
        """
        返回插件的加载优先级。
        """
        return 110

    def initialize(self, context: ApplicationContext):
        """
        初始化窗口排列插件。
        """
        super().initialize(context)
        logging.info(f"  - 插件 '{self.name()}': 正在初始化视图和控制器...")
        self.page_widget = ArrangerPageView()
        self.controller = ArrangerController(self.context, self.page_widget)
        logging.info(f"  - 插件 '{self.name()}' 初始化完成。")

    def get_background_services(self) -> list:
        """此插件的核心后台服务(MonitorService)由其控制器管理，因此这里返回空。"""
        return []

    def shutdown(self):
        """
        在应用程序关闭时，安全地执行插件的关闭操作。
        """
        logging.info(f"  - 插件 '{self.name()}': 正在执行关闭前操作...")
        if hasattr(self, 'controller') and self.controller:
            self.controller._save_settings_from_view()
            if hasattr(self.controller, 'shutdown'):
                self.controller.shutdown()
        super().shutdown()