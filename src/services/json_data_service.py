# src/services/json_data_service.py
import os
import json
import logging
from typing import Union, Dict, List

from src.services.generic_data_service import GenericDataService, DataType, DataValidationError

class JSONDataService(GenericDataService):
    """
    JSON文件数据服务。
    """
    
    def __init__(self, file_path: str):
        super().__init__(file_path, DataType.JSON)
            
    def load_data(self) -> Union[Dict, List]:
        """加载JSON数据"""
        try:
            with open(self.file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            logging.info(f"[{self.service_name}] 成功加载JSON数据: {self.file_path}")
            return data
        except Exception as e:
            logging.error(f"[{self.service_name}] 加载JSON数据失败: {e}")
            raise DataValidationError(f"无法加载JSON文件: {e}")
            
    def save_data(self, data: Union[Dict, List]) -> bool:
        """保存JSON数据"""
        try:
            with open(self.file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            logging.info(f"[{self.service_name}] 成功保存JSON数据: {self.file_path}")
            return True
        except Exception as e:
            logging.error(f"[{self.service_name}] 保存JSON数据失败: {e}")
            return False
            
    def validate_data_structure(self) -> bool:
        """验证JSON文件结构"""
        try:
            # 如果文件不存在，则创建一个空的JSON对象或数组
            if not os.path.exists(self.file_path):
                with open(self.file_path, 'w', encoding='utf-8') as f:
                    json.dump({}, f) # 默认创建一个空对象
                return True
            
            with open(self.file_path, 'r', encoding='utf-8') as f:
                json.load(f)
            return True
        except Exception as e:
            logging.warning(f"[{self.service_name}] JSON文件结构验证失败: {e}")
            return False