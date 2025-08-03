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
        logging.info(f"[{plugin_name}] [步骤 1/3] 开始数据库路径解析...")
        logging.debug(f"[{plugin_name}] 正在从配置项读取: section='{config_section}', key='{config_key}'")
        path_from_config = config_service.get_value(config_section, config_key)

        if not path_from_config:
            logging.info(f"[{plugin_name}] 配置中未找到路径，将设置并保存默认相对路径: '{default_relative_path}'")
            path_from_config = default_relative_path
            config_service.set_option(config_section, config_key, path_from_config)
            config_service.save_config()
        else:
            logging.debug(f"[{plugin_name}] 从配置中找到路径: '{path_from_config}'")

        if os.path.isabs(path_from_config):
            db_path = path_from_config
            logging.debug(f"[{plugin_name}] 路径为绝对路径，直接使用: '{db_path}'")
        else:
            db_path = context.get_data_path(path_from_config)
            logging.debug(f"[{plugin_name}] 路径为相对路径，解析为绝对路径: '{db_path}'")

        # --- Validation and Fallback Logic ---
        db_service = None
        validation_passed = False

        logging.info(f"[{plugin_name}] [步骤 2/3] 开始验证数据库: {db_path}")
        if os.path.exists(db_path):
            logging.debug(f"[{plugin_name}] 文件存在，开始进行模式验证...")
            temp_service = db_service_class(db_path)
            if temp_service.validate_database_schema():
                db_service = temp_service
                validation_passed = True
                logging.info(f"[{plugin_name}] 数据库验证成功。")
            else:
                logging.warning(f"[{plugin_name}] 数据库 '{db_path}' 存在，但模式验证失败。")
        else:
            logging.warning(f"[{plugin_name}] 数据库文件 '{db_path}' 不存在。")

        if not validation_passed:
            original_failed_path = db_path
            logging.warning(f"[{plugin_name}] [步骤 3/3] 验证失败，启动回退程序...")

            # Fallback 1: Try standard default DB
            logging.debug(f"[{plugin_name}] [回退 1/2] 尝试使用标准默认数据库。")
            default_absolute_path = context.get_data_path(default_relative_path)
            if os.path.exists(default_absolute_path):
                logging.debug(f"[{plugin_name}] 默认数据库文件存在于 '{default_absolute_path}'，正在验证...")
                db_service = db_service_class(default_absolute_path)
                if db_service.validate_database_schema():
                    config_service.set_option(config_section, config_key, default_relative_path)
                    config_service.save_config()
                    logging.info(f"[{plugin_name}] 成功回退到默认数据库。配置已更新。")
                    context.notification_service.show(
                        f"{plugin_name} 插件提示",
                        f"由于无法访问 '{os.path.basename(original_failed_path)}'，已自动切换到默认数据库。",
                        "WARNING"
                    )
                    validation_passed = True
            else:
                logging.debug(f"[{plugin_name}] 标准默认数据库文件不存在。")

            # Fallback 2: Create timestamped DB
            if not validation_passed:
                logging.warning(f"[{plugin_name}] [回退 2/2] 默认数据库同样无效，尝试创建带时间戳的新数据库。")
                timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
                path_parts = os.path.splitext(default_relative_path)
                new_relative_path = f"{path_parts[0]}_{timestamp}{path_parts[1]}"
                logging.debug(f"[{plugin_name}] 生成新的相对路径: '{new_relative_path}'")
                
                db_path = context.get_data_path(new_relative_path)
                db_service = db_service_class(db_path)

                if db_service.validate_database_schema():
                    config_service.set_option(config_section, config_key, new_relative_path)
                    config_service.save_config()
                    logging.info(f"[{plugin_name}] 成功创建并切换到新的带时间戳数据库 '{db_path}'。配置已更新。")
                    context.notification_service.show(
                        f"{plugin_name} 插件恢复通知",
                        f"默认数据库已损坏。已自动创建新的备用数据库 '{os.path.basename(db_path)}'。",
                        "WARNING"
                    )
                    validation_passed = True
        
        if not validation_passed:
            logging.critical(f"[{plugin_name}] [致命错误] 所有回退尝试均失败，无法初始化数据库。")
            context.notification_service.show(
                f"{plugin_name} 插件严重错误",
                f"无法初始化任何数据库。请检查程序数据目录的写入权限。",
                "CRITICAL"
            )
            return None

        logging.info(f"[{plugin_name}] 数据库初始化流程成功结束。")
        return db_service