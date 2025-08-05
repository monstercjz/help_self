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

        Returns:
            如果 perform_validation 为 True，则返回一个新的、验证通过的 GenericDataService 实例。
            否则，返回一个新的文件路径。
            如果用户取消或操作失败则返回 None。
        """
        new_path, _ = QFileDialog.getOpenFileName(
            parent_widget, "选择新的数据源文件",
            os.path.dirname(current_path), file_filter
        )

        if not new_path or new_path == current_path:
            return None

        try:
            if perform_validation:
                logging.debug(f"[{config_section}] 开始数据源验证: {new_path}")
                
                # 优先使用自定义验证回调
                if validation_callback:
                    is_valid, validation_msg = validation_callback(new_path)
                    if not is_valid:
                        raise ValueError(f"所选数据源不符合要求: {validation_msg}")
                    logging.debug(f"[{config_section}] 自定义验证回调通过。")
                else:
                    # 否则，使用内置的 GenericDataService 验证
                    temp_service = create_data_service(new_path, data_type, db_service_class=db_service_class)
                    if not temp_service.validate_data_source(schema_type):
                        raise ValueError(f"所选数据源验证失败。")
                    logging.debug(f"[{config_section}] GenericDataService 验证通过。")
            else:
                logging.debug(f"[{config_section}] 按要求跳过数据源验证。")

            # 验证通过（或跳过验证），更新配置
            config_service.set_option(config_section, config_key, new_path)
            config_service.save_config()
            
            QMessageBox.information(parent_widget, "成功", f"数据源已成功切换到:\n{new_path}")
            logging.info(f"插件 [{config_section}] 的数据源已成功切换到: {new_path}")
            
            # 根据模式返回不同类型的结果
            if perform_validation:
                # 返回一个新的服务实例
                return create_data_service(new_path, data_type, db_service_class=db_service_class)
            else:
                # 只返回路径
                return new_path

        except Exception as e:
            QMessageBox.critical(parent_widget, "数据源切换失败", f"无法加载或初始化数据源: {new_path}\n\n错误: {e}")
            logging.error(f"Failed to switch {config_section} data source to: {new_path}. Error: {e}")
            return None