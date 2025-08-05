# src/services/ini_data_service.py
import os
import logging
import configparser

from src.services.generic_data_service import GenericDataService, DataType, DataValidationError

class INIDataService(GenericDataService):
    """
    INI配置文件数据服务。
    """
    
    def __init__(self, file_path: str):
        super().__init__(file_path, DataType.INI)
            
    def load_data(self) -> configparser.ConfigParser:
        """加载INI配置数据"""
        try:
            config = configparser.ConfigParser()
            config.read(self.file_path, encoding='utf-8')
            logging.info(f"[{self.service_name}] 成功加载INI配置: {self.file_path}")
            return config
        except Exception as e:
            logging.error(f"[{self.service_name}] 加载INI配置失败: {e}")
            raise DataValidationError(f"无法加载INI文件: {e}")
            
    def save_data(self, data: configparser.ConfigParser) -> bool:
        """保存INI配置数据"""
        try:
            with open(self.file_path, 'w', encoding='utf-8') as f:
                data.write(f)
            logging.info(f"[{self.service_name}] 成功保存INI配置: {self.file_path}")
            return True
        except Exception as e:
            logging.error(f"[{self.service_name}] 保存INI配置失败: {e}")
            return False
            
    def validate_data_structure(self) -> bool:
        """验证INI文件结构"""
        try:
            # 如果文件不存在，则创建一个空的ConfigParser对象并保存
            if not os.path.exists(self.file_path):
                config = configparser.ConfigParser()
                with open(self.file_path, 'w', encoding='utf-8') as f:
                    config.write(f)
                return True

            config = configparser.ConfigParser()
            config.read(self.file_path, encoding='utf-8')
            return True
        except Exception as e:
            logging.warning(f"[{self.service_name}] INI文件结构验证失败: {e}")
            return False