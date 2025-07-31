# src/features/game_data/plugin.py

import logging
from src.core.plugin_interface import IFeaturePlugin
from src.core.context import ApplicationContext

# 导入插件内部的MVC组件
from src.features.Game_data.controllers.game_data_controller import GameDataController
from src.features.Game_data.models.game_data_model import GameDataModel
from src.features.Game_data.views.game_data_view import GameDataView

class GameDataPlugin(IFeaturePlugin):
    """
    游戏数据处理插件，整合了数据提取、汇总和分发功能。
    """
    
    def name(self) -> str:
        """返回插件的唯一内部名称。"""
        return "game_data"

    def display_name(self) -> str:
        """返回插件在UI上显示的名称。"""
        return "游戏数据工具"
        
    def load_priority(self) -> int:
        """返回插件的加载优先级。"""
        return 110  # 普通独立功能插件

    def initialize(self, context: ApplicationContext):
        """
        初始化插件，创建并连接MVC组件。
        """
        super().initialize(context)
        logging.info(f"[{self.name()}]-> 插件初始化开始...")

        # 1. 创建模型，注入应用上下文
        self.model = GameDataModel(context=context)

        # 2. 创建视图
        self.view = GameDataView()

        # 3. 创建控制器，将模型、视图和上下文注入
        self.controller = GameDataController(self.model, self.view, context)

        # 4. 将视图（主页面）设置为插件的UI页面
        self.page_widget = self.view
        
        logging.info(f"[{self.name()}]-> 插件初始化完成。")

    def shutdown(self):
        """
        在应用程序关闭时，确保设置被保存。
        """
        logging.info(f"[{self.name()}]-> 插件关闭，正在保存数据...")
        if hasattr(self, 'model'):
            self.model.save_settings()
        super().shutdown()
        logging.info(f"[{self.name()}]-> 插件已关闭。")
