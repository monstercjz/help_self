# src/features/memo_pad/plugin.py
import os
import logging
from datetime import datetime
from src.core.plugin_interface import IFeaturePlugin
from src.core.context import ApplicationContext
from src.features.memo_pad.views.memo_page_view import MemoPageView
from src.features.memo_pad.controllers.memo_page_controller import MemoPageController
from src.features.memo_pad.services.memo_database_service import MemoDatabaseService
from src.services.generic_data_service import DataType

class MemoPadPlugin(IFeaturePlugin):
    """
    备忘录插件，提供记录和管理笔记的功能。
    """
    def name(self) -> str:
        """返回插件的唯一内部名称。"""
        return "memo_pad"

    def display_name(self) -> str:
        """返回插件在UI上显示的名称。"""
        return "备忘录"

    def load_priority(self) -> int:
        """返回插件的加载优先级。"""
        return 100

    def initialize(self, context: ApplicationContext):
        """初始化插件，连接MVC组件。"""
        super().initialize(context)
        
        logging.info(f"Plugin '{self.name()}' is initializing...")

        # 使用重构后的通用数据源初始化服务
        # 注意：返回的是一个包装过的服务实例，需要通过 .db_service 访问原始的 MemoDatabaseService
        generic_service = self.context.initializer.initialize(
            context=self.context,
            plugin_name=self.name(),
            config_section=self.name(),
            config_key="db_path",
            default_relative_path="plugins/memo_pad/memos.db",
            data_type=DataType.SQLITE,  # 明确指定数据类型
            db_service_class=MemoDatabaseService  # 传入特定的数据库服务类
        )

        # 如果初始化失败，则插件不加载
        if not generic_service:
            logging.error(f"Plugin '{self.name()}' could not be initialized due to a data source error.")
            return
        
        db_service = generic_service.load_data()


        # 初始化视图和控制器
        self.page_widget = MemoPageView()
        self.controller = MemoPageController(self.page_widget, db_service, self.context, self.name())
        logging.info(f"Plugin '{self.name()}' initialized successfully.")

    def get_page_widget(self):
        """返回此插件的主UI页面。"""
        return self.page_widget

    def get_background_services(self):
        """返回后台服务列表。"""
        return super().get_background_services()

    def shutdown(self):
        """关闭插件。"""
        logging.info(f"Plugin '{self.name()}' is shutting down.")
        super().shutdown()
