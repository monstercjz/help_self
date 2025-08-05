# src/services/text_data_service.py
import os
import logging

from src.services.generic_data_service import GenericDataService, DataType, DataValidationError

class TextDataService(GenericDataService):
    """
    文本文件数据服务。
    """
    
    def __init__(self, file_path: str):
        super().__init__(file_path, DataType.TXT)
            
    def load_data(self) -> str:
        """加载文本数据"""
        try:
            with open(self.file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            logging.info(f"[{self.service_name}] 成功加载文本数据: {self.file_path}")
            return content
        except Exception as e:
            logging.error(f"[{self.service_name}] 加载文本数据失败: {e}")
            raise DataValidationError(f"无法加载文本文件: {e}")
            
    def save_data(self, data: str) -> bool:
        """保存文本数据"""
        try:
            with open(self.file_path, 'w', encoding='utf-8') as f:
                f.write(data)
            logging.info(f"[{self.service_name}] 成功保存文本数据: {self.file_path}")
            return True
        except Exception as e:
            logging.error(f"[{self.service_name}] 保存文本数据失败: {e}")
            return False
            
    def validate_data_structure(self) -> bool:
        """验证文本文件（任何文本文件都是有效的）"""
        try:
            # 如果文件不存在，则创建一个空文件
            if not os.path.exists(self.file_path):
                with open(self.file_path, 'w', encoding='utf-8') as f:
                    f.write("")
                return True

            with open(self.file_path, 'r', encoding='utf-8') as f:
                f.read(1)  # 读取一个字符来验证文件可读
            return True
        except Exception as e:
            logging.warning(f"[{self.service_name}] 文本文件验证失败: {e}")
            return False