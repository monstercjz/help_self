# src/features/memo_pad/plugin.py
import os
import logging
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
        
        # 1. 决定要使用的数据库路径 (Single Source of Truth: config.ini)
        config_service = self.context.config_service
        db_path = config_service.get_value("MemoPad", "last_db_path")

        if not db_path:
            # 如果配置中没有记录，则创建默认路径并写回配置
            db_path = self.context.get_data_path("plugins/memo_pad/memos.db")
            config_service.set_option("MemoPad", "last_db_path", db_path)
            config_service.save_config()
            logging.info(f"Plugin 'memo_pad': No last DB path found, setting default and saving to config: {db_path}")

        # 2. 初始化服务、视图和控制器
        # MemoDatabaseService 会在路径不存在时自动创建文件
        db_service = MemoDatabaseService(db_path)
        
        # 验证数据库模式和写入权限
        if not db_service.validate_database_schema():
            logging.warning(f"Plugin 'memo_pad': Current DB '{db_path}' failed validation. Attempting to switch to default DB.")
            # 尝试回退到默认数据库路径
            default_db_path = self.context.get_data_path("plugins/memo_pad/memos.db")
            
            # 如果当前路径已经是默认路径，或者默认路径与当前路径相同，则不再尝试回退
            if db_path == default_db_path:
                logging.error(f"Plugin 'memo_pad': Default DB '{default_db_path}' also failed validation or is the problematic DB. Plugin will not load.")
                self.context.notification_service.show(
                    "备忘录插件错误",
                    f"备忘录数据库 '{db_path}' 无法访问或模式不匹配，且无法回退到默认数据库。请检查文件权限或数据库文件是否损坏。",
                    "CRITICAL"
                )
                return # 阻止插件加载
            
            # 更新配置为默认路径并保存
            config_service.set_option("MemoPad", "last_db_path", default_db_path)
            config_service.save_config()
            logging.info(f"Plugin 'memo_pad': Switched to default DB path: {default_db_path}")
            
            # 重新初始化db_service
            db_path = default_db_path
            db_service = MemoDatabaseService(db_path)
            
            # 再次验证回退后的数据库
            if not db_service.validate_database_schema():
                logging.error(f"Plugin 'memo_pad': Default DB '{db_path}' failed validation after fallback. Plugin will not load.")
                self.context.notification_service.show(
                    "备忘录插件错误",
                    f"备忘录数据库 '{db_path}' 无法访问或模式不匹配，请检查文件权限或数据库文件是否损坏。",
                    "CRITICAL"
                )
                return # 阻止插件加载
            else:
                logging.info(f"Plugin 'memo_pad': Successfully fell back to default DB: {db_path}")
                self.context.notification_service.show(
                    "备忘录插件提示",
                    f"当前备忘录数据库 '{db_path}' 存在问题，已自动切换到默认数据库。",
                    "WARNING"
                )

        self.page_widget = MemoPageView()
        self.controller = MemoPageController(self.page_widget, db_service, self.context)

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
