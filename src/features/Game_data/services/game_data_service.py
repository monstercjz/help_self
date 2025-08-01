# src/features/game_data/services/game_data_service.py

import sqlite3
import os
import shutil
import logging
from typing import Dict, List

try:
    import pandas as pd
    # openpyxl is a dependency of pandas for reading .xlsx files
    import openpyxl
except ImportError:
    raise ImportError("缺少必要的库，请通过 'pip install pandas openpyxl' 来安装。")

class GameDataService:
    """
    提供处理游戏数据的核心业务逻辑，替代原有的Lua脚本功能。
    """

    def __init__(self, db_path: str):
        """
        初始化服务。

        Args:
            db_path (str): 数据源文件的路径（可以是SQLite数据库或Excel文件）。
        """
        self.db_path = db_path
        logging.info(f"GameDataService 初始化，数据源路径: {self.db_path}")

    def extract_data(self, root_path: str, config: Dict[str, List[str]], db_config: Dict[str, str]):
        """
        根据配置从数据源提取账号信息，并生成对应的txt文件。
        根据db_path的扩展名自动选择使用数据库或Excel。
        """
        logging.info("开始执行数据提取...")
        
        file_ext = os.path.splitext(self.db_path)[1].lower()
        
        try:
            if file_ext in ['.db', '.sqlite', '.sqlite3']:
                self._extract_from_db(root_path, config, db_config)
            elif file_ext in ['.xlsx', '.xls', '.xlsm']:
                self._extract_from_excel(root_path, config, db_config)
            else:
                logging.error(f"不支持的数据源文件类型: {file_ext}")
                raise ValueError(f"不支持的数据源文件类型: {file_ext}")
        except Exception as e:
            logging.error(f"数据提取过程中发生错误: {e}", exc_info=True)
            # 可以在这里重新抛出异常，让上层控制器捕获并显示在UI
            raise

    def _extract_from_db(self, root_path: str, config: Dict[str, List[str]], db_config: Dict[str, str]):
        """从SQLite数据库提取数据。"""
        logging.info("从SQLite数据库提取数据...")
        table = db_config.get('table_name', '账号数据')
        member_col = db_config.get('member_col', '角色名')
        account_col = db_config.get('account_col', '账号')
        
        query = f'SELECT "{account_col}" FROM "{table}" WHERE "{member_col}" = ?'

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            for an_id, members in config.items():
                account_info_parts = []
                for member in members:
                    cursor.execute(query, (member,))
                    result = cursor.fetchone()
                    if result:
                        account_info_parts.append(str(result[0]))
                    else:
                        logging.warning(f"在数据库中未找到角色 '{member}' 的账号信息。")
                
                self._write_account_file(root_path, an_id, account_info_parts)

    def _extract_from_excel(self, root_path: str, config: Dict[str, List[str]], db_config: Dict[str, str]):
        """从Excel文件提取数据。"""
        logging.info("从Excel文件提取数据...")
        member_col = db_config.get('member_col', '角色名')
        account_col = db_config.get('account_col', '账号')

        try:
            # engine='openpyxl' is required for .xlsx files
            df = pd.read_excel(self.db_path, engine='openpyxl')
            
            # 确保列名是字符串类型，以便进行比较
            df.columns = df.columns.astype(str)

            if member_col not in df.columns or account_col not in df.columns:
                logging.error(f"Excel文件中缺少必要的列: '{member_col}' 或 '{account_col}'")
                raise ValueError(f"Excel文件中缺少必要的列: '{member_col}' 或 '{account_col}'")

            for an_id, members in config.items():
                account_info_parts = []
                for member in members:
                    # 查询匹配的行
                    result_df = df[df[member_col] == member]
                    if not result_df.empty:
                        # 获取第一个匹配项的账号信息
                        account = result_df.iloc[0][account_col]
                        account_info_parts.append(str(account))
                    else:
                        logging.warning(f"在Excel中未找到角色 '{member}' 的账号信息。")
                
                self._write_account_file(root_path, an_id, account_info_parts)

        except FileNotFoundError:
            logging.error(f"Excel文件未找到: {self.db_path}")
            raise
        except Exception as e:
            logging.error(f"读取或处理Excel文件时出错: {e}")
            raise

    def _write_account_file(self, root_path: str, an_id: str, account_info_parts: List[str]):
        """将账号信息写入文件。"""
        full_account_info = "\n".join(account_info_parts)
        output_dir = os.path.join(root_path, an_id, "游戏账号")
        os.makedirs(output_dir, exist_ok=True)
        
        output_file_path = os.path.join(output_dir, f"{an_id}.txt")
        with open(output_file_path, 'w', encoding='gbk') as f:
            f.write(full_account_info)
        logging.info(f"为ID '{an_id}' 成功创建账号文件: {output_file_path} (GBK编码)")

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
                                if os.path.exists(dest_item_path):
                                    shutil.rmtree(dest_item_path)
                                shutil.copytree(source_item_path, dest_item_path)
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
