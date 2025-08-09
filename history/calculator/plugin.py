# src/features/calculator/plugin.py
import logging
from src.core.plugin_interface import IFeaturePlugin
from src.core.context import ApplicationContext

# 导入插件内部的MVC组件
from .views.calculator_view import CalculatorView
from .controllers.calculator_controller import CalculatorController
from .models.calculator_model import CalculatorModel

class CalculatorPlugin(IFeaturePlugin):
    """
    一个简单的计算器插件。
    """
    def name(self) -> str:
        """返回插件的唯一内部名称。"""
        return "calculator"

    def display_name(self) -> str:
        """返回插件在UI上显示的名称。"""
        return "计算器"

    def load_priority(self) -> int:
        """返回插件的加载优先级。"""
        return 200 # 普通功能插件

    def initialize(self, context: ApplicationContext):
        """
        初始化插件，创建并连接MVC组件。
        """
        super().initialize(context)
        logging.info(f"[{self.name()}]-> 插件初始化开始...")

        # 1. 创建模型
        self.model = CalculatorModel()

        # 2. 创建视图
        self.view = CalculatorView()
        self.view.hide() # 确保在添加到主窗口前，它不会作为独立窗口闪烁

        # 3. 创建控制器
        self.controller = CalculatorController(self.model, self.view, context, self)

        # 4. 将视图（主页面）设置为插件的UI页面
        self.page_widget = self.view
        
        logging.info(f"[{self.name()}]-> 插件初始化完成。")

    def shutdown(self):
        """
        插件关闭时的清理工作。
        """
        logging.info(f"[{self.name()}]-> 插件已关闭。")
        super().shutdown()