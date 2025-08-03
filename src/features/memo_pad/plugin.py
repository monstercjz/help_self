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
        
        # 1. 决定要使用的数据库路径 (Single Source of Truth: config.ini)
        config_service = self.context.config_service
        path_from_config = config_service.get_value("MemoPad", "last_db_path")
        
        default_relative_path = "plugins/memo_pad/memos.db"

        if not path_from_config:
            # 如果配置中没有记录，则使用默认相对路径并写回配置
            path_from_config = default_relative_path
            config_service.set_option("MemoPad", "last_db_path", path_from_config)
            config_service.save_config()
            logging.info(f"Plugin 'memo_pad': No DB path found, setting default relative path: {path_from_config}")

        # 判断路径是绝对还是相对，并获取最终的绝对路径
        if os.path.isabs(path_from_config):
            db_path = path_from_config
            logging.info(f"Plugin 'memo_pad': Using absolute DB path from config: {db_path}")
        else:
            db_path = self.context.get_data_path(path_from_config)
            logging.info(f"Plugin 'memo_pad': Resolved relative path '{path_from_config}' to absolute path: {db_path}")

        # 2. 初始化服务、视图和控制器
        db_service = None
        validation_passed = False

        # 必须先检查文件是否存在，防止MemoDatabaseService自动创建文件
        if os.path.exists(db_path):
            temp_service = MemoDatabaseService(db_path)
            if temp_service.validate_database_schema():
                db_service = temp_service
                validation_passed = True
            else:
                logging.warning(f"Plugin 'memo_pad': DB at '{db_path}' exists but failed schema validation.")
        else:
            logging.warning(f"Plugin 'memo_pad': DB file at '{db_path}' does not exist.")

        # 如果因任何原因（不存在或模式错误）验证失败，则启动回退程序
        if not validation_passed:
            original_failed_path = db_path
            logging.warning(f"Starting fallback procedure for '{original_failed_path}'.")

            # --- Fallback Attempt 1: Try the standard default DB ---
            default_absolute_path = self.context.get_data_path(default_relative_path)
            
            # 检查默认DB是否存在且有效
            if os.path.exists(default_absolute_path):
                db_service = MemoDatabaseService(default_absolute_path)
                if db_service.validate_database_schema():
                    db_path = default_absolute_path
                    config_service.set_option("MemoPad", "last_db_path", default_relative_path)
                    config_service.save_config()
                    logging.info(f"Plugin 'memo_pad': Successfully fell back to default DB. Config updated.")
                    self.context.notification_service.show(
                        "备忘录插件提示",
                        f"由于无法访问 '{os.path.basename(original_failed_path)}'，已自动切换到默认数据库。",
                        "WARNING"
                    )
                    validation_passed = True

            # --- Fallback Attempt 2: Create a new timestamped DB ---
            if not validation_passed:
                logging.warning(f"Plugin 'memo_pad': Default DB is missing or invalid. Attempting to create a new timestamped DB.")
                
                timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
                path_parts = os.path.splitext(default_relative_path)
                new_relative_path = f"{path_parts[0]}_{timestamp}{path_parts[1]}"
                
                db_path = self.context.get_data_path(new_relative_path)
                db_service = MemoDatabaseService(db_path) # This will create the new file

                if db_service.validate_database_schema():
                    config_service.set_option("MemoPad", "last_db_path", new_relative_path)
                    config_service.save_config()
                    logging.info(f"Plugin 'memo_pad': Successfully created and switched to new timestamped DB '{db_path}'.")
                    self.context.notification_service.show(
                        "备忘录插件恢复通知",
                        f"默认数据库已损坏或丢失。已自动创建新的备用数据库 '{os.path.basename(db_path)}'。",
                        "WARNING"
                    )
                    validation_passed = True
                
            # --- Final Step: Check if any fallback succeeded ---
            if not validation_passed:
                logging.critical(f"Plugin 'memo_pad': CRITICAL FAILURE. All fallback attempts failed. Could not initialize a valid DB.")
                self.context.notification_service.show(
                    "备忘录插件严重错误",
                    f"无法初始化任何备忘录数据库，包括创建新的备用数据库。请检查程序数据目录的写入权限。",
                    "CRITICAL"
                )
                return # Give up and prevent plugin from loading

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
