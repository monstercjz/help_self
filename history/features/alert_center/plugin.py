# src/features/alert_center/plugin.py (【修正版】)
import logging
# 【修正】直接从具体模块导入，打破循环
from src.core.plugin_interface import IFeaturePlugin
from src.core.context import ApplicationContext

# 导入MVC组件
from .views.alerts_page_view import AlertsPageView
from .controllers.alerts_page_controller import AlertsPageController
from .controllers.history_controller import HistoryController
from .controllers.statistics_controller import StatisticsController

# 导入此插件的私有服务
from .services.alert_receiver import AlertReceiverThread

class AlertCenterPlugin(IFeaturePlugin):
    """告警中心功能插件，负责组装其内部的MVC组件。"""
    
    def name(self) -> str:
        return "AlertCenter"

    def display_name(self) -> str:
        return "信息接收中心"

    def initialize(self, context: ApplicationContext):
        super().initialize(context)
        
        # 1. 组装主页面的MVC
        self.alerts_page_view = AlertsPageView(context.action_manager)
        self.alerts_page_controller = AlertsPageController(
            view=self.alerts_page_view,
            config_service=context.config_service,
            db_service=context.db_service,
            parent_window=context.main_window
        )
        self.page_widget = self.alerts_page_view

        # 2. 组装对话框的MVC (Controller在需要时创建)
        self.history_controller = HistoryController(
            db_service=context.db_service,
            config_service=context.config_service,
            parent_window=context.main_window
        )
        self.statistics_controller = StatisticsController(
            db_service=context.db_service,
            parent_window=context.main_window
        )
        
        # 3. 创建此插件的后台服务
        host = context.config_service.get_value("InfoService", "host", "0.0.0.0")
        port = int(context.config_service.get_value("InfoService", "port", 5000))
        receiver_thread = AlertReceiverThread(
            config_service=context.config_service,
            db_service=context.db_service,
            host=host, port=port
        )
        # 服务 -> 控制器 -> 视图
        receiver_thread.new_alert_received.connect(self.alerts_page_controller.add_alert_from_thread)
        self.background_services.append(receiver_thread)

        # 4. 连接全局Action到此插件的控制器
        context.action_manager.show_history.triggered.connect(self.history_controller.show_dialog)
        context.action_manager.show_statistics.triggered.connect(self.statistics_controller.show_dialog)
        logging.info(f"插件 '{self.name()}' 的动作已连接。")

    def get_page_widget(self):
        return self.page_widget

    def get_background_services(self):
        return self.background_services