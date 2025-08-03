# src/features/memo_pad/plugin.py
import os
import logging
from datetime import datetime
from src.core.plugin_interface import IFeaturePlugin
from src.core.context import ApplicationContext
from src.features.memo_pad.views.memo_page_view import MemoPageView
from src.features.memo_pad.controllers.memo_page_controller import MemoPageController
from src.features.memo_pad.services.memo_database_service import MemoDatabaseService

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

        # 使用共享的数据库初始化服务
        db_service = self.context.db_initializer.initialize_db(
            context=self.context,
            plugin_name=self.name(),
            config_section=self.name(),  # 使用插件内部名作为统一的配置区段名
            config_key="db_path",       # 建议将key也统一为'db_path'
            db_service_class=MemoDatabaseService,
            default_relative_path="plugins/memo_pad/memos.db"
        )

        # 如果初始化失败，则插件不加载
        if not db_service:
            logging.error(f"Plugin '{self.name()}' could not be initialized due to a database error.")
            return

        # 初始化视图和控制器
        self.page_widget = MemoPageView()
        self.controller = MemoPageController(self.page_widget, db_service, self.context)
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
