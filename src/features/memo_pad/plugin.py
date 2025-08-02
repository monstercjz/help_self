# src/features/memo_pad/plugin.py

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
        
        # 1. 设置数据库路径 (遵循项目约定)
        db_path = self.context.get_data_path("plugins/memo_pad/memos.db")
        
        # 2. 初始化服务、视图和控制器
        db_service = MemoDatabaseService(db_path)
        self.page_widget = MemoPageView()
        self.controller = MemoPageController(self.page_widget, db_service)
        
        print(f"Plugin '{self.name()}' initialized with db at: {db_path}")

    def get_page_widget(self):
        """返回此插件的主UI页面。"""
        return self.page_widget

    def get_background_services(self):
        """返回后台服务列表。"""
        return super().get_background_services()

    def shutdown(self):
        """关闭插件。"""
        print(f"Plugin '{self.name()}' is shutting down.")
        super().shutdown()
