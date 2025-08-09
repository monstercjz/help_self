from src.core.plugin_interface import IFeaturePlugin
from src.core.context import ApplicationContext
from PySide6.QtWidgets import QWidget
import logging

class CalculatorPlugin(IFeaturePlugin):
    def name(self) -> str:
        return "calculator"

    def display_name(self) -> str:
        return "计算器"

    def load_priority(self) -> int:
        return 100

    def initialize(self, context: ApplicationContext):
        super().initialize(context)
        logging.info(f"插件 '{self.name()}' 正在初始化...")
        
        # 导入并实例化模型、视图、控制器
        from .models.calculator_model import CalculatorModel
        from .views.calculator_view import CalculatorView
        from .controllers.calculator_controller import CalculatorController

        self.model = CalculatorModel()
        self.view = CalculatorView()
        self.controller = CalculatorController(self.model, self.view, context.notification_service)
        
        self.page_widget = self.view # 将视图设置为插件的主页面
        logging.info(f"插件 '{self.name()}' 初始化完成。")

    def get_page_widget(self) -> QWidget | None:
        return self.page_widget

    def get_background_services(self) -> list:
        return [] # 计算器插件目前没有后台服务

    def shutdown(self):
        logging.info(f"插件 '{self.name()}' 正在关闭...")
        # 在这里可以添加清理逻辑，例如保存历史记录到文件等
        super().shutdown()
        logging.info(f"插件 '{self.name()}' 关闭完成。")