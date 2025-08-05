# src/services/csv_data_service.py
import os
import logging
try:
    import pandas as pd
except ImportError:
    pd = None

from src.services.generic_data_service import GenericDataService, DataType, DataValidationError

class CSVDataService(GenericDataService):
    """
    CSV文件数据服务。
    """
    
    def __init__(self, file_path: str):
        super().__init__(file_path, DataType.CSV)
        if pd is None:
            raise ImportError("pandas库未安装，无法处理CSV文件")
            
    def load_data(self) -> pd.DataFrame:
        """加载CSV数据"""
        try:
            df = pd.read_csv(self.file_path)
            logging.info(f"[{self.service_name}] 成功加载CSV数据: {self.file_path}")
            return df
        except Exception as e:
            logging.error(f"[{self.service_name}] 加载CSV数据失败: {e}")
            raise DataValidationError(f"无法加载CSV文件: {e}")
            
    def save_data(self, data: pd.DataFrame) -> bool:
        """保存CSV数据"""
        try:
            data.to_csv(self.file_path, index=False)
            logging.info(f"[{self.service_name}] 成功保存CSV数据: {self.file_path}")
            return True
        except Exception as e:
            logging.error(f"[{self.service_name}] 保存CSV数据失败: {e}")
            return False
            
    def validate_data_structure(self) -> bool:
        """验证CSV文件结构"""
        try:
            # 如果文件不存在，则创建一个空的DataFrame并保存
            if not os.path.exists(self.file_path):
                if pd is None:
                    raise ImportError("pandas库未安装，无法创建CSV文件")
                pd.DataFrame().to_csv(self.file_path, index=False)
                return True

            # 尝试读取CSV文件头来验证结构
            pd.read_csv(self.file_path, nrows=1)
            return True
        except Exception as e:
            logging.warning(f"[{self.service_name}] CSV文件结构验证失败: {e}")
            return False