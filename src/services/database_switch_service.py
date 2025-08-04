# src/services/database_switch_service.py
import os
import logging
from PySide6.QtWidgets import QFileDialog, QMessageBox, QWidget
from typing import Type, Optional, Callable, Tuple, Union

from src.services.base_database_service import BaseDatabaseService
from src.services.config_service import ConfigService

class DatabaseSwitchService:
    """
    一个可重用的服务，用于处理插件数据库的切换逻辑。
    现在支持更通用的验证机制和无验证模式。
    """
    def switch_database(
        self,
        parent_widget: QWidget,
        current_db_path: str,
        config_service: ConfigService,
        config_section: str,
        config_key: str,
        db_service_class: Optional[Type[BaseDatabaseService]] = None, # 保持向后兼容
        validation_callback: Optional[Callable[[str], Tuple[bool, str]]] = None, # 新增通用验证回调
        perform_validation: bool = True # 新增控制是否执行验证的标志
    ) -> Optional[Union[str, BaseDatabaseService]]:
        """
        执行标准的数据库切换流程。

        Args:
            parent_widget: 用于显示文件对话框和消息框的父组件。
            current_db_path: 当前数据库的绝对路径。
            config_service: 用于读写配置的服务。
            config_section: config.ini 中的区段名。
            config_key: config.ini 中的键名。
            db_service_class: (可选) 目标数据库服务的类 (e.g., MemoDatabaseService)。用于向后兼容。
            validation_callback: (可选) 一个函数，接受数据库路径(str)并返回 (bool, str) 表示验证结果和消息。
                                 如果提供，将优先于 db_service_class 的验证。
            perform_validation: (可选) 如果为 False，则跳过所有数据库模式验证，只进行文件选择和路径保存。默认为 True。

        Returns:
            如果提供了 db_service_class，则返回一个新的、验证通过的数据库服务实例。
            否则，返回一个新的、验证通过的数据库文件路径。
            如果用户取消或操作失败则返回 None。
        """
        new_path, _ = QFileDialog.getOpenFileName(
            parent_widget, "选择新的数据库文件",
            os.path.dirname(current_db_path), "数据库文件 (*.db);;所有文件 (*)"
        )

        if not new_path or new_path == current_db_path:
            return None

        try:
            if perform_validation:
                logging.debug(f"[{config_section}] 开始数据库验证: {new_path}")
                # 1. 检查可写性
                is_writable, write_err = BaseDatabaseService.check_db_writability(new_path)
                if not is_writable:
                    raise ValueError(f"所选数据库文件不可写入: {write_err}")
                logging.debug(f"[{config_section}] 写入权限检查通过。")

                # 2. 执行自定义验证回调
                if validation_callback:
                    logging.debug(f"[{config_section}] 使用自定义验证回调。")
                    is_valid, validation_msg = validation_callback(new_path)
                    if not is_valid:
                        raise ValueError(f"所选数据库文件不符合要求: {validation_msg}")
                    logging.debug(f"[{config_section}] 自定义验证回调通过。")
                # 3. 向后兼容：使用 db_service_class 验证
                elif db_service_class:
                    logging.debug(f"[{config_section}] 使用 db_service_class '{db_service_class.__name__}' 进行验证。")
                    temp_db_service = db_service_class(new_path)
                    if not temp_db_service.validate_database_schema():
                        raise ValueError(f"所选数据库文件不符合 {db_service_class.__name__} 的结构要求。")
                    temp_db_service.close()
                    logging.debug(f"[{config_section}] db_service_class 验证通过。")
                else:
                    logging.debug(f"[{config_section}] 除写入权限外，未提供特定的验证方法。")
            else:
                logging.debug(f"[{config_section}] 按要求跳过数据库验证。")

            # 验证通过（或跳过验证），更新配置
            config_service.set_option(config_section, config_key, new_path)
            config_service.save_config()
            
            QMessageBox.information(parent_widget, "成功", f"数据源已成功切换到:\n{new_path}")
            logging.info(f"插件 [{config_section}] 的数据库已成功切换到: {new_path}")
            
            # 根据是否提供了 db_service_class 返回不同类型
            if db_service_class:
                return db_service_class(new_path)
            else:
                return new_path

        except Exception as e:
            QMessageBox.critical(parent_widget, "数据库切换失败", f"无法加载或初始化数据库: {new_path}\n\n错误: {e}")
            logging.error(f"Failed to switch {config_section} database to: {new_path}. Error: {e}")
            return None