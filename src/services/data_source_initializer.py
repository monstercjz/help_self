# src/services/data_source_initializer.py
import os
import logging
from datetime import datetime
from typing import Optional

from src.services.sqlite_base_service import SchemaType
from src.services.generic_data_service import GenericDataService, create_data_service, DataType

class DataSourceInitializerService:
    """
    数据源初始化服务。
    该服务提供可重用的逻辑，用于处理插件所需数据源的初始化、路径解析、有效性验证以及在遇到问题时的回退机制。
    它确保了即使在配置缺失或数据源损坏的情况下，插件也能尝试以可靠的方式启动。
    """
    def initialize(
        self,
        context: 'ApplicationContext',
        plugin_name: str,
        config_section: str,
        config_key: str,
        default_relative_path: str,
        data_type: Optional[DataType] = None,
        schema_type: SchemaType = SchemaType.FIXED,
        db_service_class: Optional[type] = None  # 针对数据库类型服务，可指定具体的数据库服务类
    ) -> Optional[GenericDataService]:
        """
        执行标准的数据源初始化流程。

        此方法是数据源初始化的核心入口，它会尝试从配置中读取数据源路径，
        如果路径无效或不存在，则会尝试使用默认路径或执行回退策略。

        Args:
            context: 当前应用的 ApplicationContext 实例，提供对配置服务、通知服务等的访问。
            plugin_name: 调用此功能的插件的名称（例如 "alert_center"），用于日志记录和通知。
            config_section: 在 `config.ini` 配置文件中，用于读取和写入数据源路径的配置区段名称。
                            例如，对于告警中心，可能是 "alert_center"。
            config_key: 在 `config_section` 下，用于存储数据源文件路径的键名。例如 "db_path"。
            default_relative_path: 当配置中未指定数据源路径或指定路径无效时，
                                   将使用的默认数据源文件的相对路径。例如 "plugins/alert_center/history.db"。
            data_type: 数据源的预期类型（例如 DataType.SQLITE, DataType.EXCEL）。
                       如果未提供，服务将尝试根据文件扩展名自动判断。
            schema_type: 数据源的模式验证类型。
                         - `SchemaType.FIXED` (默认): 对数据源进行严格的结构验证，确保其符合预期的模式。
                         - `SchemaType.DYNAMIC`: 仅检查数据源的可访问性，不进行严格的模式验证。
            db_service_class: 可选参数，当 `data_type` 为 `DataType.SQLITE` 或其他数据库类型时，
                              可以指定一个继承自 `SqlDataService` 或其他通用数据服务基类的具体数据库服务类。
                              例如，对于告警中心，这里会传入 `AlertDatabaseService`。

        Returns:
            一个成功初始化并验证通过的 `GenericDataService` 实例（或其子类实例），
            如果所有初始化和回退尝试都失败，则返回 `None`。
        """
        config_service = context.config_service
        logging.info(f"[src.services.data_source_initializer.DataSourceInitializerService.initialize] [{plugin_name}] [步骤 1/3] 开始数据源路径解析和配置读取...")
        logging.debug(f"[src.services.data_source_initializer.DataSourceInitializerService.initialize] [{plugin_name}] 尝试从配置项 [section='{config_section}', key='{config_key}'] 读取数据源路径。")
        path_from_config = config_service.get_value(config_section, config_key)

        logging.debug(f"[src.services.data_source_initializer.DataSourceInitializerService.initialize] [{plugin_name}] [步骤 1.1/3] 检查配置中是否存在数据源路径。")
        if not path_from_config:
            # 如果配置中未找到路径，则使用默认相对路径，并将其保存到配置中
            logging.info(f"[src.services.data_source_initializer.DataSourceInitializerService.initialize] [{plugin_name}] [步骤 1.2/3] 配置中未找到数据源路径，将使用并保存默认相对路径: '{default_relative_path}'")
            path_from_config = default_relative_path
            config_service.set_option(config_section, config_key, path_from_config)
            config_service.save_config()
        else:
            logging.debug(f"[src.services.data_source_initializer.DataSourceInitializerService.initialize] [{plugin_name}] [步骤 1.2/3] 从配置中成功读取到数据源路径: '{path_from_config}'")

        # 将数据源路径转换为绝对路径
        logging.debug(f"[src.services.data_source_initializer.DataSourceInitializerService.initialize] [{plugin_name}] [步骤 1.3/3] 将数据源路径转换为绝对路径。")
        if os.path.isabs(path_from_config):
            data_path = path_from_config
            logging.debug(f"[src.services.data_source_initializer.DataSourceInitializerService.initialize] [{plugin_name}] 检测到数据源路径为绝对路径，直接使用: '{data_path}'")
        else:
            data_path = context.get_data_path(path_from_config)
            logging.debug(f"[src.services.data_source_initializer.DataSourceInitializerService.initialize] [{plugin_name}] 检测到数据源路径为相对路径，已解析为绝对路径: '{data_path}'")

        logging.info(f"[src.services.data_source_initializer.DataSourceInitializerService.initialize] [{plugin_name}] [步骤 2/3] 尝试创建并验证数据服务实例。")
        data_service = self._validate_and_create_service(data_path, data_type, schema_type, plugin_name, db_service_class)

        if data_service:
            logging.info(f"[src.services.data_source_initializer.DataSourceInitializerService.initialize] [{plugin_name}] [步骤 3/3] 数据源初始化流程成功完成。")
            return data_service

        original_failed_path = data_path
        logging.warning(f"[src.services.data_source_initializer.DataSourceInitializerService.initialize] [{plugin_name}] [步骤 3/3] 数据源 '{original_failed_path}' 验证失败，启动回退程序...")

        logging.debug(f"[src.services.data_source_initializer.DataSourceInitializerService.initialize] [{plugin_name}] [回退策略] 尝试回退尝试 1: 使用标准默认文件。")
        data_service = self._try_fallback_default(context, plugin_name, config_section, config_key, default_relative_path, data_type, schema_type, original_failed_path, db_service_class)
        if data_service:
            return data_service

        logging.debug(f"[src.services.data_source_initializer.DataSourceInitializerService.initialize] [{plugin_name}] [回退策略] 尝试回退尝试 2: 创建带时间戳的新文件。")
        data_service = self._try_fallback_timestamped(context, plugin_name, config_section, config_key, default_relative_path, data_type, schema_type, db_service_class)
        if data_service:
            return data_service

        logging.critical(f"[src.services.data_source_initializer.DataSourceInitializerService.initialize] [{plugin_name}] [致命错误] 所有数据源初始化和回退尝试均失败，无法为插件 '{plugin_name}' 初始化数据源。")
        context.notification_service.show(
            f"{plugin_name} 插件严重错误",
            f"无法初始化任何数据源。请检查程序数据目录的写入权限或数据源文件是否损坏。",
            "CRITICAL"
        )
        return None

    def _validate_and_create_service(self, data_path: str, data_type: Optional[DataType], schema_type: SchemaType, plugin_name: str, db_service_class: Optional[type] = None) -> Optional[GenericDataService]:
        logging.info(f"[src.services.data_source_initializer.DataSourceInitializerService._validate_and_create_service] [{plugin_name}] [步骤 2.1/3] 开始验证数据源文件: {data_path}")
        try:
            logging.debug(f"[src.services.data_source_initializer.DataSourceInitializerService._validate_and_create_service] [{plugin_name}] [步骤 2.2/3] 尝试创建数据服务实例。")
            temp_service = create_data_service(data_path, data_type, db_service_class=db_service_class)
            logging.debug(f"[src.services.data_source_initializer.DataSourceInitializerService._validate_and_create_service] [{plugin_name}] [步骤 2.3/3] 调用服务实例的 validate_data_source 方法进行模式验证。")
            if temp_service.validate_data_source(schema_type):
                logging.info(f"[src.services.data_source_initializer.DataSourceInitializerService._validate_and_create_service] [{plugin_name}] [步骤 2.4/3] 数据源 '{data_path}' 验证成功。")
                return temp_service
            else:
                logging.warning(f"[src.services.data_source_initializer.DataSourceInitializerService._validate_and_create_service] [{plugin_name}] [步骤 2.4/3] 数据源 '{data_path}' 存在，但其内部结构验证失败。")
                return None
        except Exception as e:
            logging.warning(f"[src.services.data_source_initializer.DataSourceInitializerService._validate_and_create_service] [{plugin_name}] [步骤 2.4/3] 验证数据源 '{data_path}' 时发生错误: {e}", exc_info=True)
            return None

    def _try_fallback_default(self, context, plugin_name, config_section, config_key, default_relative_path, data_type, schema_type, original_failed_path, db_service_class) -> Optional[GenericDataService]:
        logging.debug(f"[src.services.data_source_initializer.DataSourceInitializerService._try_fallback_default] [{plugin_name}] [回退 1/2] 尝试使用标准默认数据源文件。")
        default_absolute_path = context.get_data_path(default_relative_path)
        
        if default_absolute_path == original_failed_path:
            logging.debug(f"[src.services.data_source_initializer.DataSourceInitializerService._try_fallback_default] [{plugin_name}] 默认数据源路径与原始失败路径相同，跳过重复验证。")
            return None

        logging.debug(f"[src.services.data_source_initializer.DataSourceInitializerService._try_fallback_default] [{plugin_name}] 尝试验证并创建默认数据源的服务实例: '{default_absolute_path}'。")
        service = self._validate_and_create_service(default_absolute_path, data_type, schema_type, plugin_name, db_service_class)
        if service:
            logging.info(f"[src.services.data_source_initializer.DataSourceInitializerService._try_fallback_default] [{plugin_name}] 成功回退到默认数据源 '{default_absolute_path}'。配置已更新。")
            context.config_service.set_option(config_section, config_key, default_relative_path)
            context.config_service.save_config()
            context.notification_service.show(
                f"{plugin_name} 插件提示",
                f"由于无法访问原始数据源 '{os.path.basename(original_failed_path)}'，已自动切换到默认数据源。",
                "WARNING"
            )
        return service

    def _try_fallback_timestamped(self, context, plugin_name, config_section, config_key, default_relative_path, data_type, schema_type, db_service_class) -> Optional[GenericDataService]:
        logging.warning(f"[src.services.data_source_initializer.DataSourceInitializerService._try_fallback_timestamped] [{plugin_name}] [回退 2/2] 标准默认数据源同样无效，尝试创建带时间戳的新数据源文件。")
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        path_parts = os.path.splitext(default_relative_path)
        new_relative_path = f"{path_parts[0]}_{timestamp}{path_parts[1]}"
        logging.debug(f"[src.services.data_source_initializer.DataSourceInitializerService._try_fallback_timestamped] [{plugin_name}] 生成新的带时间戳的相对路径: '{new_relative_path}'")
        
        new_absolute_path = context.get_data_path(new_relative_path)
        logging.debug(f"[src.services.data_source_initializer.DataSourceInitializerService._try_fallback_timestamped] [{plugin_name}] 尝试验证并创建新的带时间戳数据源的服务实例: '{new_absolute_path}'。")
        service = self._validate_and_create_service(new_absolute_path, data_type, schema_type, plugin_name, db_service_class)
        
        if service:
            logging.info(f"[src.services.data_source_initializer.DataSourceInitializerService._try_fallback_timestamped] [{plugin_name}] 成功创建并切换到新的带时间戳数据源 '{new_absolute_path}'。配置已更新。")
            context.config_service.set_option(config_section, config_key, new_relative_path)
            context.config_service.save_config()
            context.notification_service.show(
                f"{plugin_name} 插件恢复通知",
                f"默认数据源已损坏或无法访问。已自动创建新的备用数据源 '{os.path.basename(new_absolute_path)}'。",
                "WARNING"
            )
        return service