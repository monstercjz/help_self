# src/features/game_data/services/game_data_service.py

import sqlite3
import os
import shutil
import logging
from typing import Dict, List

class GameDataService:
    """
    提供处理游戏数据的核心业务逻辑，替代原有的Lua脚本功能。
    """

    def __init__(self, db_path: str):
        """
        初始化服务。

        Args:
            db_path (str): SQLite数据库文件的路径。
        """
        self.db_path = db_path
        logging.info(f"GameDataService 初始化，数据库路径: {self.db_path}")

    def extract_data(self, root_path: str, config: Dict[str, List[str]]):
        """
        根据配置从数据库提取账号信息，并生成对应的txt文件。
        对应原 '1-findname3.0.lua' 的功能。

        Args:
            root_path (str): 操作的根目录，例如 "D:\\天龙相关\\临时处理"。
            config (Dict[str, List[str]]): 分机ID到角色名列表的映射。
        """
        logging.info("开始执行数据提取...")
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                for an_id, members in config.items():
                    account_info_parts = []
                    for member in members:
                        cursor.execute("SELECT 账号 FROM 账号数据 WHERE 角色名 = ?", (member,))
                        result = cursor.fetchone()
                        if result:
                            account_info_parts.append(result[0])
                        else:
                            logging.warning(f"在数据库中未找到角色 '{member}' 的账号信息。")
                    
                    full_account_info = "\n".join(account_info_parts)

                    # 创建输出目录和文件
                    output_dir = os.path.join(root_path, an_id, "游戏账号")
                    os.makedirs(output_dir, exist_ok=True)
                    
                    output_file_path = os.path.join(output_dir, f"{an_id}.txt")
                    with open(output_file_path, 'w', encoding='gbk') as f:
                        f.write(full_account_info)
                    logging.info(f"为ID '{an_id}' 成功创建账号文件: {output_file_path} (GBK编码)")

        except sqlite3.Error as e:
            logging.error(f"数据库操作失败: {e}")
        except IOError as e:
            logging.error(f"文件写入失败: {e}")

    def aggregate_files(self, root_path: str, config: Dict[str, List[str]]):
        """
        将各ID目录下的角色配置，根据角色名聚合到'all'目录。
        对应原 '2-copy-onetoall3.0.lua' 的功能。

        Args:
            root_path (str): 操作的根目录。
            config (Dict[str, List[str]]): 分机ID到角色名列表的映射。
        """
        logging.info("开始执行文件汇总...")
        all_dir = os.path.join(root_path, "all")
        os.makedirs(all_dir, exist_ok=True)

        try:
            for an_id, members in config.items():
                source_sub_dir = os.path.join(root_path, an_id, "角色配置")
                if not os.path.isdir(source_sub_dir):
                    logging.warning(f"源目录不存在，跳过: {source_sub_dir}")
                    continue

                for item_name in os.listdir(source_sub_dir):
                    for member in members:
                        if member in item_name:
                            source_item_path = os.path.join(source_sub_dir, item_name)
                            dest_item_path = os.path.join(all_dir, item_name)
                            
                            if os.path.isdir(source_item_path):
                                shutil.copytree(source_item_path, dest_item_path, dirs_exist_ok=True)
                                logging.info(f"复制目录 '{source_item_path}' 到 '{dest_item_path}'")
                            else:
                                shutil.copy2(source_item_path, dest_item_path)
                                logging.info(f"复制文件 '{source_item_path}' 到 '{dest_item_path}'")
                            # 找到一个匹配项后，即可处理下一个文件/目录
                            break
        except (IOError, shutil.Error) as e:
            logging.error(f"文件汇总操作失败: {e}")

    def distribute_files(self, root_path: str, config: Dict[str, List[str]]):
        """
        将'all'目录中的文件，根据角色名分发到对应的ID目录。
        对应原 '3-copy-alltoone3.0.lua' 的功能。

        Args:
            root_path (str): 操作的根目录。
            config (Dict[str, List[str]]): 分机ID到角色名列表的映射。
        """
        logging.info("开始执行文件分发...")
        source_dir = os.path.join(root_path, "all")
        if not os.path.isdir(source_dir):
            logging.error(f"源目录 'all' 不存在，无法执行分发: {source_dir}")
            return

        try:
            for an_id, members in config.items():
                dest_sub_dir = os.path.join(root_path, an_id, "角色配置")
                os.makedirs(dest_sub_dir, exist_ok=True)

                for item_name in os.listdir(source_dir):
                    for member in members:
                        if member in item_name:
                            source_item_path = os.path.join(source_dir, item_name)
                            dest_item_path = os.path.join(dest_sub_dir, item_name)

                            if os.path.isdir(source_item_path):
                                shutil.copytree(source_item_path, dest_item_path, dirs_exist_ok=True)
                                logging.info(f"复制目录 '{source_item_path}' 到 '{dest_item_path}'")
                            else:
                                shutil.copy2(source_item_path, dest_item_path)
                                logging.info(f"复制文件 '{source_item_path}' 到 '{dest_item_path}'")
                            # 找到一个匹配项后，即可处理下一个文件/目录
                            break
        except (IOError, shutil.Error) as e:
            logging.error(f"文件分发操作失败: {e}")
