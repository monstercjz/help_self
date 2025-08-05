from src.services.sqlite_base_service import SchemaType

# src/services/generic_data_service.py
import os
import json
import logging
import configparser
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Union, Optional
from enum import Enum, auto

from src.services.sqlite_base_service import SchemaType

class DataType(Enum):
    """
    定义应用程序支持的各种数据文件类型。
    这使得数据服务能够根据文件类型进行分发和处理。
    """
    SQLITE = auto() # SQLite 数据库文件 (.db, .sqlite, .sqlite3)
    EXCEL = auto()  # Excel 文件 (.xlsx, .xls)
    JSON = auto()   # JSON 文件 (.json)
    INI = auto()    # INI 配置文件 (.ini)
    CSV = auto()    # CSV 文件 (.csv)
    TXT = auto()    # 纯文本文件 (.txt)

class DataValidationError(Exception):
    """
    自定义异常类，用于表示数据验证失败的情况。
    当数据源的结构不符合预期模式时抛出。
    """
    pass

class GenericDataService(ABC):
    """
    通用数据服务抽象基类。
    该类定义了所有数据服务应遵循的通用接口和基本行为，
    例如文件路径管理、目录创建和写入权限检查。
    不同的数据格式（如 SQLite, Excel, JSON 等）将继承此基类并实现其抽象方法。
    """
    
    def __init__(self, file_path: str, data_type: DataType):
        """
        初始化通用数据服务实例。

        Args:
            file_path: 数据源文件的绝对路径。
            data_type: 数据源的类型，来自 DataType 枚举。
        """
        self.file_path = file_path
        self.data_type = data_type
        # 服务名称通常是子类的类名，用于日志记录
        self.service_name = self.__class__.__name__
        
        # 确保数据文件所在的目录存在，如果不存在则创建
        dir_name = os.path.dirname(self.file_path)
        if dir_name: # 只有当路径包含目录时才尝试创建
            os.makedirs(dir_name, exist_ok=True)
            logging.debug(f"[src.services.generic_data_service.{self.service_name}.__init__] [GenericDataService 基础初始化] [步骤 1/2] 确保数据文件目录 '{dir_name}' 已存在。")
            
        logging.debug(f"[src.services.generic_data_service.{self.service_name}.__init__] [GenericDataService 基础初始化] [步骤 2/2] 数据服务已初始化，文件路径: '{self.file_path}' (类型: {self.data_type.name})")
        logging.info(f"[src.services.generic_data_service.{self.service_name}.__init__] [GenericDataService 基础初始化] 数据服务已初始化，文件路径: '{self.file_path}' (类型: {self.data_type.name})")

    @abstractmethod
    def load_data(self) -> Any:
        """
        抽象方法：从数据源加载数据。
        子类必须实现此方法以定义如何读取特定类型的数据。
        返回的数据类型可以是任意的，取决于具体的数据服务。
        """
        pass

    @abstractmethod
    def save_data(self, data: Any) -> bool:
        """
        抽象方法：将数据保存到数据源。
        子类必须实现此方法以定义如何将数据写入特定类型的文件。
        Args:
            data: 要保存的数据。
        Returns:
            bool: 如果数据保存成功则返回 True，否则返回 False。
        """
        pass

    @abstractmethod
    def validate_data_structure(self) -> bool:
        """
        抽象方法：验证数据源的内部结构是否符合预期。
        例如，对于数据库，可能检查表是否存在；对于Excel，可能检查特定工作表或列。
        子类必须实现此方法。
        Returns:
            bool: 如果数据结构有效则返回 True，否则返回 False。
        """
        pass

    def check_write_access(self) -> bool:
        """
        检查数据文件或其父目录的写入权限。
        这是一个通用的检查方法，子类可以根据需要覆盖此方法以提供更精确的检查（例如，针对数据库文件的锁定机制）。
        Returns:
            bool: 如果有写入权限则返回 True，否则返回 False。
        """
        try:
            # 尝试在文件路径旁创建一个临时文件来测试写入权限
            test_file = self.file_path + ".tmp_write_test"
            with open(test_file, "w") as f:
                f.write("test_write_access")
            os.remove(test_file) # 测试成功后删除临时文件
            logging.debug(f"[src.services.generic_data_service.{self.service_name}.check_write_access] [GenericDataService check_write_access] [检查通过] 文件写入权限检查通过: '{self.file_path}'")
            return True
        except Exception as e:
            logging.warning(f"[src.services.generic_data_service.{self.service_name}.check_write_access] [GenericDataService check_write_access] [检查失败] 文件写入权限检查失败，无法写入文件 '{self.file_path}': {e}")
            return False

    def validate_data_source(self, schema_type: SchemaType = SchemaType.FIXED) -> bool:
        """
        验证数据源的整体有效性，包括文件存在性、写入权限和内部结构。

        Args:
            schema_type: 模式验证类型。
                         - `SchemaType.FIXED` (默认): 执行严格的结构验证 (`validate_data_structure`)。
                         - `SchemaType.DYNAMIC`: 仅检查文件或目录的可访问性，不进行内部结构验证。

        Returns:
            bool: 如果数据源有效则返回 True，否则返回 False。
        """
        logging.debug(f"[src.services.generic_data_service.{self.service_name}.validate_data_source] [GenericDataService validate_data_source] [1/3 验证流程开始] 开始验证数据源: '{self.file_path}' (模式: {schema_type.name})")
        
        parent_dir = os.path.dirname(self.file_path)
        logging.debug(f"[src.services.generic_data_service.{self.service_name}.validate_data_source] [GenericDataService validate_data_source] [1/3 数据源父目录检测] 检查数据源父目录: '{parent_dir}'。")
        # 如果文件路径包含目录，且该目录不存在，则尝试创建
        if parent_dir and not os.path.exists(parent_dir):
            try:
                os.makedirs(parent_dir, exist_ok=True)
                logging.info(f"[src.services.generic_data_service.{self.service_name}.validate_data_source] [GenericDataService validate_data_source] [1/3 目录创建] 已创建数据源的父目录: '{parent_dir}'。")
            except Exception as e:
                logging.error(f"[src.services.generic_data_service.{self.service_name}.validate_data_source] [GenericDataService validate_data_source] [1/3 目录创建失败] 无法创建数据源的父目录 '{parent_dir}'，请检查权限: {e}")
                return False
        else:
            logging.info(f"[src.services.generic_data_service.{self.service_name}.validate_data_source] [GenericDataService validate_data_source] [1/3 数据源父目录检测] 已经存在数据源父目录: '{parent_dir}'。")
            
        # 检查文件是否存在      
        logging.debug(f"[src.services.generic_data_service.{self.service_name}.validate_data_source] [GenericDataService validate_data_source] [2/3 数据文件检查] 检查数据文件的存在与写入权限: '{self.file_path}'。")
        if os.path.exists(self.file_path):
            # 如果文件存在，检查其写入权限
            if not self.check_write_access():
                logging.warning(f"[src.services.generic_data_service.{self.service_name}.validate_data_source] [GenericDataService validate_data_source] [2/3 数据文件检查] 数据文件 '{self.file_path}' 存在但无写入权限。")
                return False
            logging.info(f"[src.services.generic_data_service.{self.service_name}.validate_data_source] [GenericDataService validate_data_source] [2/3 数据文件检查] 数据文件 '{self.file_path}' 存在且可写入。")
        else:
            # 如果文件不存在，检查其父目录是否有创建文件的权限
            # os.access(path, os.W_OK) 检查路径是否可写
            # parent_dir or '.' 用于处理文件路径就是当前目录的情况
            if not os.access(parent_dir or '.', os.W_OK):
                 logging.warning(f"[src.services.generic_data_service.{self.service_name}.validate_data_source] [GenericDataService validate_data_source] [2/3 数据文件检查] 父目录 '{parent_dir or '.'}' 无写入权限，无法创建文件 '{self.file_path}'。")
                 return False
            logging.warning(f"[src.services.generic_data_service.{self.service_name}.validate_data_source] [GenericDataService validate_data_source] [2/3 数据文件检查] 数据文件 '{self.file_path}' 不存在，但父目录可写入。")
            
        # 根据 schema_type 执行不同的验证逻辑
        logging.debug(f"[src.services.generic_data_service.{self.service_name}.validate_data_source] [GenericDataService validate_data_source] [3/3 数据文件结构测试] 当前测试模式: {schema_type.name}")
        if schema_type == SchemaType.DYNAMIC:
            # DYNAMIC 模式下，仅检查文件/目录可访问性，不深入验证结构
            logging.info(f"[src.services.generic_data_service.{self.service_name}.validate_data_source] [GenericDataService validate_data_source] [3/3 数据文件结构测试] 验证完成 DYNAMIC 模式验证通过（仅检查文件/目录可访问性）。")
            return True
            
        # FIXED 模式下，需要调用子类实现的 validate_data_structure 进行严格结构验证
        logging.info(f"[src.services.generic_data_service.{self.service_name}.validate_data_source] [GenericDataService validate_data_source] [3/3 数据文件结构测试] 执行 FIXED 模式结构验证。")
        return self.validate_data_structure()

class SQLiteDataService(GenericDataService):
    """
    SQLite 数据库服务。
    这是一个包装器，用于将通用的 GenericDataService 接口与具体的 SqlDataService (位于 sqlite_base_service.py) 功能连接起来。
    它允许在不直接修改 SqlDataService 的情况下，使其符合 GenericDataService 的抽象接口。
    """
    def __init__(self, file_path: str, db_service_class=None):
        """
        初始化 SQLiteDataService 实例。

        Args:
            file_path: SQLite 数据库文件的路径。
            db_service_class: 可选参数，指定一个继承自 SqlDataService 的具体数据库服务类。
                              例如，AlertDatabaseService 会在这里传入。
        """
        logging.debug(f"[src.services.generic_data_service.{self.__class__.__name__}.__init__] [SQLiteDataService] [1/5 开始] 开始初始化 SQLiteDataService 实例")
        super().__init__(file_path, DataType.SQLITE)
        logging.debug(f"[src.services.generic_data_service.{self.__class__.__name__}.__init__] [SQLiteDataService] [2/5 父类初始化完成] SQLiteDataService 父类初始化完成")
        # 延迟导入 SqlDataService 以避免模块间的循环依赖问题
        from src.services.sqlite_base_service import SqlDataService
        
        # 使用提供的具体数据库服务类，如果未提供则默认使用 SqlDataService
        # 这允许插件传入自己的数据库服务实现（如 AlertDatabaseService）
        # 这个实例被存储在 SQLiteDataService 实例的 db_service 属性中
        target_class = db_service_class if db_service_class else SqlDataService
        logging.debug(f"[src.services.generic_data_service.{self.__class__.__name__}.__init__] [SQLiteDataService] [3/5 准备创建内部服务] 将要创建的内部数据库服务类: {target_class.__name__}")
        self.db_service = target_class(file_path)
        logging.debug(f"[src.services.generic_data_service.{self.__class__.__name__}.__init__] [SQLiteDataService] [4/5 实例创建] SqlDataService 内部实例已创建: {target_class.__name__}")
        logging.debug(f"[src.services.generic_data_service.{self.__class__.__name__}.__init__] [SQLiteDataService] [5/5 完成] SQLiteDataService 实例初始化完成")
        
    def load_data(self) -> Any:
        """
        加载 SQLite 数据。
        对于 SQLite 服务，"加载数据"通常意味着获取数据库连接或返回其内部的数据库服务实例，
        因为实际的数据查询是通过 db_service 的特定方法完成的。
        Returns:
            Any: 返回内部的数据库服务实例 (`self.db_service`)。
        """
        logging.debug(f"[src.services.generic_data_service.{self.service_name}.load_data] [SQLiteDataService] [数据加载] 调用 load_data，返回SQLiteDataService实例的内部数据库服务实例。")
        return self.db_service # self.db_service = target_class(file_path)
        
    def save_data(self, data: Any) -> bool:
        """
        保存 SQLite 数据。
        对于 SQLite 服务，数据保存通常通过内部 db_service 的特定方法（如 insert, update）完成，
        而不是通过一个通用的 save_data 方法。因此，此方法通常只返回 True。
        Args:
            data: 要保存的数据（在此通用接口中可能不直接使用）。
        Returns:
            bool: 始终返回 True，表示操作成功（实际保存由 db_service 负责）。
        """
        logging.debug(f"[src.services.generic_data_service.{self.service_name}.save_data] [SQLiteDataService] [数据保存] 调用 save_data，实际保存由内部数据库服务处理。")
        return True
        
    def validate_data_structure(self) -> bool:
        """
        验证 SQLite 数据库的内部结构（例如，检查表是否存在，模式是否正确）。
        此方法委托给内部的 `SqlDataService.validate_database_schema()` 方法。
        Returns:
            bool: 如果数据库模式有效则返回 True，否则返回 False。
        """
        logging.debug(f"[src.services.generic_data_service.{self.service_name}.validate_data_structure] [SQLiteDataService] [3/3 数据文件结构测试] 调用 validate_data_structure，委托给内部数据库服务。")
        return self.db_service.validate_database_schema()
        
    def check_write_access(self) -> bool:
        """
        检查 SQLite 数据库文件的写入权限。
        此方法委托给 `SqlDataService.check_db_writability()` 静态方法，
        该方法能更准确地判断数据库文件的可写性。
        Returns:
            bool: 如果数据库文件可写则返回 True，否则返回 False。
        """
        from src.services.sqlite_base_service import SqlDataService
        is_writable, msg = SqlDataService.check_db_writability(self.file_path)
        if not is_writable:
            logging.warning(f"[src.services.generic_data_service.{self.service_name}.check_write_access] [SQLiteDataService] [检查失败] SQLite 文件写入权限检查失败: {msg}")
        else:
            logging.debug(f"[src.services.generic_data_service.{self.service_name}.check_write_access] [SQLiteDataService] [检查通过] SQLite 文件写入权限检查通过。")
        return is_writable

def create_data_service(file_path: str, data_type: Optional[DataType] = None, db_service_class=None) -> "GenericDataService":
    """
    工厂方法：根据文件路径或指定的数据类型创建并返回一个 `GenericDataService` 的具体实例。
    这个函数是获取数据服务实例的推荐方式，它会自动处理不同数据类型的服务实例化。

    Args:
        file_path: 数据源文件的路径。
        data_type: 可选参数，明确指定数据源的类型。如果未提供，函数将尝试根据文件扩展名自动判断。
        db_service_class: 可选参数，当 `data_type` 为 `DataType.SQLITE` 时，
                          可以指定一个继承自 `SqlDataService` 的具体数据库服务类。

    Returns:
        GenericDataService: 一个与指定文件类型相对应的 `GenericDataService` 子类实例。

    Raises:
        ValueError: 如果文件类型不支持或无法识别。
    """
    # 延迟导入具体的服务类，以避免模块间的循环依赖问题，并提高启动性能
    from src.services.excel_data_service import ExcelDataService
    from src.services.json_data_service import JSONDataService
    from src.services.ini_data_service import INIDataService
    from src.services.csv_data_service import CSVDataService
    from src.services.text_data_service import TextDataService

    # 如果未指定数据类型，则根据文件扩展名自动判断
    if data_type is None:
        ext = os.path.splitext(file_path)[1].lower() # 获取文件扩展名并转换为小写
        logging.debug(f"[src.services.generic_data_service.create_data_service] [类型判断] 尝试根据文件扩展名 '{ext}' 自动判断数据类型。")
        if ext in ['.db', '.sqlite', '.sqlite3']:
            data_type = DataType.SQLITE
        elif ext in ['.xlsx', '.xls']:
            data_type = DataType.EXCEL
        elif ext == '.json':
            data_type = DataType.JSON
        elif ext == '.ini':
            data_type = DataType.INI
        elif ext == '.csv':
            data_type = DataType.CSV
        elif ext == '.txt':
            data_type = DataType.TXT
        else:
            # 对于无法识别的扩展名，默认视为纯文本文件
            logging.warning(f"[src.services.generic_data_service.create_data_service] [类型判断] 无法识别文件扩展名 '{ext}'，默认使用 DataType.TXT。")
            data_type = DataType.TXT
    
    # 根据确定的数据类型实例化相应的服务类
    if data_type == DataType.SQLITE:
        logging.debug(f"[src.services.generic_data_service.create_data_service] 创建 SQLiteDataService 实例，路径: '{file_path}'")
        return SQLiteDataService(file_path, db_service_class=db_service_class)
    elif data_type == DataType.EXCEL:
        logging.debug(f"[src.services.generic_data_service.create_data_service] 创建 ExcelDataService 实例，路径: '{file_path}'")
        return ExcelDataService(file_path)
    elif data_type == DataType.JSON:
        logging.debug(f"[src.services.generic_data_service.create_data_service] 创建 JSONDataService 实例，路径: '{file_path}'")
        return JSONDataService(file_path)
    elif data_type == DataType.INI:
        logging.debug(f"[src.services.generic_data_service.create_data_service] 创建 INIDataService 实例，路径: '{file_path}'")
        return INIDataService(file_path)
    elif data_type == DataType.CSV:
        logging.debug(f"[src.services.generic_data_service.create_data_service] 创建 CSVDataService 实例，路径: '{file_path}'")
        return CSVDataService(file_path)
    elif data_type == DataType.TXT:
        logging.debug(f"[src.services.generic_data_service.create_data_service] 创建 TextDataService 实例，路径: '{file_path}'")
        return TextDataService(file_path)
    else:
        # 如果数据类型仍然无法匹配，则抛出错误
        logging.error(f"[src.services.generic_data_service.create_data_service] 尝试创建不支持的数据类型服务: {data_type.name}")
        raise ValueError(f"不支持的数据类型: {data_type}")