# desktop_center/src/services/config_service.py
import configparser
import logging
from typing import List, Tuple

class ConfigService:
    """
    健壮的配置服务，负责所有 config.ini 文件的读写逻辑。
    设计目标是即使在配置文件损坏或丢失的情况下也能让主程序安全启动。
    """
    def __init__(self, filepath: str):
        """
        初始化配置服务。

        Args:
            filepath (str): config.ini 文件的路径。
        """
        self.filepath = filepath
        self.config = configparser.ConfigParser()
        self.load_config()

    def load_config(self) -> None:
        """
        从磁盘加载配置文件。
        如果文件不存在或无法解析，将记录一个错误并使用一个空的配置对象，
        这可以防止应用程序在启动时崩溃。
        """
        try:
            # 使用utf-8-sig可以处理带有BOM头的UTF-8文件
            read_files = self.config.read(self.filepath, encoding='utf-8-sig')
            if not read_files:
                logging.warning(f"配置文件 '{self.filepath}' 未找到。将使用空配置。")
            else:
                logging.info(f"成功加载配置文件: {self.filepath}")
        except configparser.Error as e:
            logging.error(f"解析配置文件 '{self.filepath}' 失败: {e}")
            # 解析失败时重置为一个空对象，保证程序健壮性
            self.config = configparser.ConfigParser()

    def get_sections(self) -> List[str]:
        """获取所有配置区段的名称列表。"""
        return self.config.sections()

    def get_options(self, section: str) -> List[Tuple[str, str]]:
        """获取指定区段下的所有键值对。"""
        if self.config.has_section(section):
            return self.config.items(section)
        return []

    def get_value(self, section: str, option: str, fallback: str = None) -> str:
        """安全地获取一个配置值，可提供默认值。"""
        return self.config.get(section, option, fallback=fallback)

    def set_option(self, section: str, option: str, value: str) -> None:
        """设置一个配置值。如果区段不存在，则自动创建。"""
        if not self.config.has_section(section):
            self.config.add_section(section)
        self.config.set(section, option, str(value))

    def save_config(self) -> bool:
        """
        将当前配置状态写回文件。

        Returns:
            bool: 如果保存成功则返回 True，否则返回 False。
        """
        try:
            with open(self.filepath, 'w', encoding='utf-8') as configfile:
                self.config.write(configfile)
            logging.info(f"配置文件已成功保存到: {self.filepath}")
            return True
        except IOError as e:
            logging.error(f"保存配置文件到 '{self.filepath}' 失败: {e}")
            return False