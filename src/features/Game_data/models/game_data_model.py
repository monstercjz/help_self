# src/features/game_data/models/game_data_model.py

import os
import logging
from typing import Dict, List
from src.core.context import ApplicationContext

class GameDataModel:
    """
    管理GameData插件的状态和业务逻辑。
    - 存储根目录路径和分机账号配置。
    - 提供加载和保存配置的方法。
    - 解析配置文本为可用的数据结构。
    """

    def __init__(self, context: ApplicationContext):
        """
        初始化模型。
        
        Args:
            context (ApplicationContext): 应用程序上下文，用于访问共享服务如ConfigService。
        """
        self.context = context
        self.config_service = context.config_service
        self._root_path = ""
        self._db_path = ""
        self._config_path = ""
        self._config_text = "" # 用于在UI上显示内容
        self.load_settings()

    @property
    def root_path(self) -> str:
        return self._root_path

    @root_path.setter
    def root_path(self, value: str):
        self._root_path = value

    @property
    def db_path(self) -> str:
        return self._db_path

    @db_path.setter
    def db_path(self, value: str):
        self._db_path = value

    @property
    def config_path(self) -> str:
        return self._config_path

    @config_path.setter
    def config_path(self, value: str):
        self._config_path = value
        self.load_config_from_file()

    @property
    def config_text(self) -> str:
        return self._config_text

    def get_parsed_config(self) -> Dict[str, List[str]]:
        """
        解析配置文本，返回一个ID到角色列表的字典。
        """
        parsed_config = {}
        lines = self._config_text.strip().split('\n')
        for line in lines:
            if ':' in line:
                parts = line.split(':', 1)
                an_id = parts[0].strip()
                members_str = parts[1].strip()
                members = [m.strip() for m in members_str.split('|')]
                if an_id and members:
                    parsed_config[an_id] = members
        return parsed_config

    def load_settings(self):
        """
        从ConfigService加载持久化的路径设置。
        """
        logging.info("从配置服务加载GameData设置...")
        self._root_path = self.config_service.get_value("game_data", "root_path", "D:\\天龙相关\\临时处理")
        self._db_path = self.config_service.get_value("game_data", "db_path", "D:\\天龙相关\\临时处理\\TL_game.db")
        self._config_path = self.config_service.get_value("game_data", "config_path", "")
        
        # 新增：从配置加载数据库表和字段名 (在 game_data 区段下)
        self.db_table_name = self.config_service.get_value("game_data", "db_table_name", "账号数据")
        self.db_member_col = self.config_service.get_value("game_data", "db_member_col", "角色名")
        self.db_account_col = self.config_service.get_value("game_data", "db_account_col", "账号")

        self.load_config_from_file() # 根据加载的路径读取文件内容
        logging.info(f"根目录加载为: {self._root_path}")
        logging.info(f"数据库路径加载为: {self._db_path}")
        logging.info(f"配置文件路径加载为: {self._config_path}")
        logging.info(f"数据库表配置: {self.db_table_name} / {self.db_member_col} / {self.db_account_col}")

    def load_config_from_file(self):
        """
        根据 config_path 从文件加载配置内容到 config_text。
        """
        if self._config_path and os.path.exists(self._config_path):
            try:
                # 尝试用 UTF-8 读取
                with open(self._config_path, 'r', encoding='utf-8') as f:
                    self._config_text = f.read()
                logging.info(f"成功从 '{self._config_path}' 加载配置内容 (UTF-8)。")
            except UnicodeDecodeError:
                logging.warning(f"使用UTF-8读取 '{self._config_path}' 失败，尝试使用GBK编码。")
                try:
                    # 如果UTF-8失败，尝试用 GBK 读取
                    with open(self._config_path, 'r', encoding='gbk') as f:
                        self._config_text = f.read()
                    logging.info(f"成功从 '{self._config_path}' 加载配置内容 (GBK)。")
                except (UnicodeDecodeError, IOError) as e:
                    self._config_text = f"无法读取文件: {e}"
                    logging.error(f"使用多种编码读取配置文件 '{self._config_path}' 均失败: {e}")
            except IOError as e:
                self._config_text = f"无法读取文件: {e}"
                logging.error(f"读取配置文件 '{self._config_path}' 时发生IO错误: {e}")
        else:
            self._config_text = "请选择一个有效的分机账号配置文件..."
            logging.warning(f"配置文件路径无效或文件不存在: '{self._config_path}'")

    def save_settings(self):
        """
        将当前设置保存到ConfigService。
        """
        logging.info("保存GameData设置到配置服务...")
        self.config_service.set_option("game_data", "root_path", self._root_path)
        self.config_service.set_option("game_data", "db_path", self._db_path)
        self.config_service.set_option("game_data", "config_path", self._config_path)
        
        # 新增：保存数据库表和字段名配置 (在 game_data 区段下)
        self.config_service.set_option("game_data", "db_table_name", self.db_table_name)
        self.config_service.set_option("game_data", "db_member_col", self.db_member_col)
        self.config_service.set_option("game_data", "db_account_col", self.db_account_col)
        # 移除对 config_text 的保存，因为它现在是动态加载的
        # self.config_service.set_option("game_data", "config_text", self._config_text)

        self.config_service.save_config()  # 显式调用保存
        logging.info("GameData设置已保存。")
