# src/features/game_data/models/game_data_model.py

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
    
    DEFAULT_CONFIG_TEXT = """41706:善良的恶魔|べ瓒。|べ辰。|べ墨。|べ褚。|べ连。
41601:雷ぃ傷う|べ谭°|べ藏。|べ黄。|べ陶。|べ王。
41301:べ曉゜|べ曉。|べ珏。|べ皢。|べ潋。|べ吴。
32401:べ孔。|べ施。|べ云。|べ沈。|べ柳。|べ邹。
32402:〆﹎oKingゝ|べ稠。|べ唐。|べ张。|べ戴。|べ鲁。
32403:笑尽天下英雄|べ祥。|归鹿．|べ秦。|べ费。|べ柯。
32404:☆浅月|べ劫。|べ彭。|べ于。|べ崔。|べ水。
32405:失魂の蟲|多情一刀|跑进∞新时代|べ伯。|べ魏。|べ戚。
32406:べ栤。|べ恧。|べ顾。|べ郝。|べ飛。|べ伍。|べ卫。
32408:单纯的宝贝|天￠闲★|伊ゞ辰メ|﹏冰慕筱筱ゞ|べ葛。|べ苗。
32409:べ倪。|べ吕。|べ卫。|べ韩。|べ尤。|べ姜。"""

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
        self._config_text = ""
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
    def config_text(self) -> str:
        return self._config_text

    @config_text.setter
    def config_text(self, value: str):
        self._config_text = value

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
        从ConfigService加载设置。如果不存在，则使用默认值。
        """
        logging.info("从配置服务加载GameData设置...")
        self._root_path = self.config_service.get_value("game_data", "root_path", "D:\\天龙相关\\临时处理")
        self._db_path = self.config_service.get_value("game_data", "db_path", "D:\\天龙相关\\临时处理\\TL_game.db")
        self._config_text = self.config_service.get_value("game_data", "config_text", self.DEFAULT_CONFIG_TEXT)
        logging.info(f"根目录加载为: {self._root_path}")
        logging.info(f"数据库路径加载为: {self._db_path}")

    def save_settings(self):
        """
        将当前设置保存到ConfigService。
        """
        logging.info("保存GameData设置到配置服务...")
        self.config_service.set_option("game_data", "root_path", self._root_path)
        self.config_service.set_option("game_data", "db_path", self._db_path)
        self.config_service.set_option("game_data", "config_text", self._config_text)
        self.config_service.save_config()  # 显式调用保存
        logging.info("GameData设置已保存。")
