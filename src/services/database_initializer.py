# src/services/database_initializer.py
import os
import logging
from datetime import datetime
from typing import Type, Callable, Optional

class DatabaseInitializerService:
    """
    一个可重用的服务，用于处理插件数据库的初始化、验证和回退逻辑。
    """
    def initialize_db(
        self,
        context: 'ApplicationContext',
        plugin_name: str,
        config_section: str,
        config_key: str,
        db_service_class: Type,
        default_relative_path: str
    ) -> Optional[Type]:
        """
        执行标准的数据库初始化流程。

        Args:
            context: 当前应用的 ApplicationContext。
            plugin_name: 调用此功能的插件名称（用于日志）。
            config_section: 要在 config.ini 中读写的区段名。
            config_key: 要在 config.ini 中读写的键名。
            db_service_class: 数据库服务的类（例如 MemoDatabaseService）。
            default_relative_path: 默认的数据库相对路径。

        Returns:
            一个成功初始化的数据库服务实例，如果所有尝试都失败则返回 None。
        """
        config_service = context.config_service
        path_from_config = config_service.get_value(config_section, config_key)

        if not path_from_config:
            path_from_config = default_relative_path
            config_service.set_option(config_section, config_key, path_from_config)
            config_service.save_config()
            logging.info(f"[{plugin_name}] No DB path found, setting default: {path_from_config}")

        if os.path.isabs(path_from_config):
            db_path = path_from_config
        else:
            db_path = context.get_data_path(path_from_config)

        # --- Validation and Fallback Logic ---
        db_service = None
        validation_passed = False

        if os.path.exists(db_path):
            temp_service = db_service_class(db_path)
            if temp_service.validate_database_schema():
                db_service = temp_service
                validation_passed = True
            else:
                logging.warning(f"[{plugin_name}] DB at '{db_path}' exists but failed validation.")
        else:
            logging.warning(f"[{plugin_name}] DB file at '{db_path}' does not exist.")

        if not validation_passed:
            original_failed_path = db_path
            logging.warning(f"[{plugin_name}] Starting fallback for '{original_failed_path}'.")

            # Fallback 1: Try standard default DB
            default_absolute_path = context.get_data_path(default_relative_path)
            if os.path.exists(default_absolute_path):
                db_service = db_service_class(default_absolute_path)
                if db_service.validate_database_schema():
                    config_service.set_option(config_section, config_key, default_relative_path)
                    config_service.save_config()
                    logging.info(f"[{plugin_name}] Fell back to default DB. Config updated.")
                    context.notification_service.show(
                        f"{plugin_name} 插件提示",
                        f"由于无法访问 '{os.path.basename(original_failed_path)}'，已自动切换到默认数据库。",
                        "WARNING"
                    )
                    validation_passed = True

            # Fallback 2: Create timestamped DB
            if not validation_passed:
                logging.warning(f"[{plugin_name}] Default DB missing or invalid. Creating new timestamped DB.")
                timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
                path_parts = os.path.splitext(default_relative_path)
                new_relative_path = f"{path_parts[0]}_{timestamp}{path_parts[1]}"
                
                db_path = context.get_data_path(new_relative_path)
                db_service = db_service_class(db_path)

                if db_service.validate_database_schema():
                    config_service.set_option(config_section, config_key, new_relative_path)
                    config_service.save_config()
                    logging.info(f"[{plugin_name}] Created and switched to new DB '{db_path}'.")
                    context.notification_service.show(
                        f"{plugin_name} 插件恢复通知",
                        f"默认数据库已损坏。已自动创建新的备用数据库 '{os.path.basename(db_path)}'。",
                        "WARNING"
                    )
                    validation_passed = True
        
        if not validation_passed:
            logging.critical(f"[{plugin_name}] All DB fallback attempts failed.")
            context.notification_service.show(
                f"{plugin_name} 插件严重错误",
                f"无法初始化任何数据库。请检查程序数据目录的写入权限。",
                "CRITICAL"
            )
            return None

        return db_service