# src/services/data_source_switch_service.py
import os
import logging
from PySide6.QtWidgets import QFileDialog, QMessageBox, QWidget
from typing import Optional, Callable, Tuple, Union

from src.services.sqlite_base_service import SchemaType
from src.services.generic_data_service import GenericDataService, create_data_service, DataType
from src.services.config_service import ConfigService

class DataSourceSwitchService:
    """
    一个可重用的服务，用于处理插件数据源的切换逻辑。
    """
    def switch(
        self,
        parent_widget: QWidget,
        current_path: str,
        config_service: ConfigService,
        config_section: str,
        config_key: str,
        data_type: Optional[DataType] = None,
        validation_callback: Optional[Callable[[str], Tuple[bool, str]]] = None,
        perform_validation: bool = True,
        schema_type: SchemaType = SchemaType.FIXED,
        file_filter: str = "所有文件 (*)",
        db_service_class: Optional[type] = None  # Re-add for DB-specific subclasses
    ) -> Optional[Union[str, GenericDataService]]:
        """
        执行标准的数据源切换流程。

        此方法是数据源切换的核心入口，它会引导用户选择新的数据源文件，
        并对其进行验证，然后更新配置。

        Args:
            parent_widget: 用于显示文件对话框和消息框的父组件。
            current_path: 当前数据源的绝对路径。
            config_service: 用于读写配置的服务。
            config_section: config.ini 中的区段名。
            config_key: config.ini 中的键名。
            data_type: (可选) 数据类型，如果未提供则根据文件扩展名自动判断。
            validation_callback: (可选) 一个函数，接受文件路径(str)并返回 (bool, str) 表示验证结果和消息。
            perform_validation: (可选) 如果为 False，则跳过所有验证，只进行文件选择和路径保存。默认为 True。
            schema_type: (可选) 数据的模式类型 (FIXED 或 DYNAMIC)。
            file_filter: (可选) 文件对话框中显示的文件类型过滤器。
            db_service_class: (可选) 针对数据库类型服务，可指定具体的数据库服务类。

        Returns:
            如果 perform_validation 为 True，则返回一个新的、验证通过的 GenericDataService 实例。
            否则，返回一个新的文件路径。
            如果用户取消或操作失败则返回 None。
        """
        logging.info(f"[src.services.data_source_switch_service.DataSourceSwitchService.switch] [{config_section}] [步骤 1/3] 开始数据源切换流程。")
        logging.debug(f"[src.services.data_source_switch_service.DataSourceSwitchService.switch] [{config_section}] [步骤 1.1/3] 打开文件选择对话框。当前路径: '{current_path}'，文件过滤器: '{file_filter}'。")
        new_path, _ = QFileDialog.getOpenFileName(
            parent_widget, "选择新的数据源文件",
            os.path.dirname(current_path) if current_path else "", # 如果没有当前路径，则从空字符串开始
            file_filter
        )

        if not new_path:
            logging.info(f"[src.services.data_source_switch_service.DataSourceSwitchService.switch] [{config_section}] [步骤 1.2/3] 用户取消了文件选择。数据源切换操作中止。")
            return None
        
        if new_path == current_path:
            logging.info(f"[src.services.data_source_switch_service.DataSourceSwitchService.switch] [{config_section}] [步骤 1.2/3] 用户选择了当前已加载的数据源。无需切换。")
            QMessageBox.information(parent_widget, "提示", "您选择了当前已加载的数据库，无需切换。")
            return None

        logging.info(f"[src.services.data_source_switch_service.DataSourceSwitchService.switch] [{config_section}] [步骤 1.3/3] 用户选择了新的数据源文件: '{new_path}'。")

        try:
            if perform_validation:
                logging.info(f"[src.services.data_source_switch_service.DataSourceSwitchService.switch] [{config_section}] [步骤 2/3] 开始对新数据源 '{new_path}' 进行验证。")
                
                # 优先使用自定义验证回调
                if validation_callback:
                    logging.debug(f"[src.services.data_source_switch_service.DataSourceSwitchService.switch] [{config_section}] [步骤 2.1/3] 使用自定义验证回调。")
                    is_valid, validation_msg = validation_callback(new_path)
                    if not is_valid:
                        logging.warning(f"[src.services.data_source_switch_service.DataSourceSwitchService.switch] [{config_section}] [步骤 2.2/3] 自定义验证回调失败: {validation_msg}")
                        raise ValueError(f"所选数据源不符合要求: {validation_msg}")
                    logging.info(f"[src.services.data_source_switch_service.DataSourceSwitchService.switch] [{config_section}] [步骤 2.2/3] 自定义验证回调通过。")
                else:
                    # 否则，使用内置的 GenericDataService 验证
                    logging.debug(f"[src.services.data_source_switch_service.DataSourceSwitchService.switch] [{config_section}] [步骤 2.1/3] 使用内置 GenericDataService 验证。")
                    temp_service = create_data_service(new_path, data_type, db_service_class=db_service_class)
                    if not temp_service.validate_data_source(schema_type):
                        logging.warning(f"[src.services.data_source_switch_service.DataSourceSwitchService.switch] [{config_section}] [步骤 2.2/3] 内置 GenericDataService 验证失败。")
                        raise ValueError(f"所选数据源验证失败。")
                    logging.info(f"[src.services.data_source_switch_service.DataSourceSwitchService.switch] [{config_section}] [步骤 2.2/3] 内置 GenericDataService 验证通过。")
            else:
                logging.info(f"[src.services.data_source_switch_service.DataSourceSwitchService.switch] [{config_section}] [步骤 2/3] 按要求跳过数据源验证。")

            # 验证通过（或跳过验证），更新配置
            logging.info(f"[src.services.data_source_switch_service.DataSourceSwitchService.switch] [{config_section}] [步骤 3/3] 验证通过，更新配置项 [section='{config_section}', key='{config_key}'] 为新路径: '{new_path}'。")
            config_service.set_option(config_section, config_key, new_path)
            config_service.save_config()
            
            QMessageBox.information(parent_widget, "成功", f"数据源已成功切换到:\n{new_path}")
            logging.info(f"[src.services.data_source_switch_service.DataSourceSwitchService.switch] [{config_section}] 数据源已成功切换到: {new_path}")
            
            # 根据模式返回不同类型的结果
            if perform_validation:
                # 返回一个新的服务实例
                logging.debug(f"[src.services.data_source_switch_service.DataSourceSwitchService.switch] [{config_section}] 返回新的 GenericDataService 实例。")
                return create_data_service(new_path, data_type, db_service_class=db_service_class)
            else:
                # 只返回路径
                logging.debug(f"[src.services.data_source_switch_service.DataSourceSwitchService.switch] [{config_section}] 返回新的数据源路径。")
                return new_path

        except Exception as e:
            error_message = f"无法加载或初始化数据源: {new_path}\n\n错误: {e}"
            QMessageBox.critical(parent_widget, "数据源切换失败", error_message)
            logging.error(f"[src.services.data_source_switch_service.DataSourceSwitchService.switch] [{config_section}] 数据源切换失败。路径: '{new_path}'。错误: {e}", exc_info=True)
            return None