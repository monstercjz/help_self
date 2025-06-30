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
        此插件不依赖于其他特定插件，但需要基础UI和配置服务，
        因此优先级设定为110，高于通用独立功能插件的默认值100。
        """
        return 110

    def initialize(self, context: ApplicationContext):
        """
        初始化窗口排列插件。
        创建视图和控制器，并建立它们之间的连接。
        """
        super().initialize(context) # 调用父类方法保存 context 引用

        logging.info(f"  - 插件 '{self.name()}': 正在初始化视图和控制器...")
        # 实例化视图和控制器
        self.page_widget = ArrangerPageView()
        self.controller = ArrangerController(self.context, self.page_widget)
        
        logging.info(f"  - 插件 '{self.name()}' 初始化完成。")

    def get_background_services(self) -> list:
        """
        此插件目前没有需要后台运行的服务（如 QThread）。
        """
        return []

    def shutdown(self):
        """
        在应用程序关闭时，安全地执行插件的关闭操作。
        这里主要用于保存插件当前的设置到配置文件。
        """
        logging.info(f"  - 插件 '{self.name()}': 正在执行关闭前操作 (保存设置)...")
        # 确保控制器存在且有保存设置的方法
        if hasattr(self, 'controller') and self.controller:
            self.controller._save_settings() # 调用控制器中的私有方法来保存设置
        super().shutdown() # 调用父类方法确保所有后台服务（如果有）被停止