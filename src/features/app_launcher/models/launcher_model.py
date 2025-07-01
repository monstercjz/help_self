# desktop_center/src/features/app_launcher/models/launcher_model.py
import json
import logging
import os
from typing import List, Dict, Optional

class LauncherModel:
    """
    负责管理应用程序列表的数据模型。
    处理数据的加载、保存、添加和删除，并与JSON文件进行交互。
    """
    def __init__(self, data_file: str = 'launcher_apps.json'):
        """
        初始化模型。

        Args:
            data_file (str): 用于持久化存储应用列表的JSON文件名。
        """
        self.data_file = data_file
        self.apps: List[Dict[str, str]] = []
        self.load_apps()

    def load_apps(self):
        """从JSON文件中加载应用程序列表。"""
        if not os.path.exists(self.data_file):
            logging.warning(f"应用启动器数据文件 '{self.data_file}' 不存在，将使用空列表。")
            self.apps = []
            return

        try:
            with open(self.data_file, 'r', encoding='utf-8') as f:
                self.apps = json.load(f)
            logging.info(f"已成功从 '{self.data_file}' 加载 {len(self.apps)} 个应用程序。")
        except (json.JSONDecodeError, IOError) as e:
            logging.error(f"加载应用启动器数据文件 '{self.data_file}' 失败: {e}")
            self.apps = []

    def save_apps(self) -> bool:
        """将当前的应用程序列表保存到JSON文件。"""
        try:
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(self.apps, f, indent=4, ensure_ascii=False)
            logging.info(f"应用程序列表已成功保存到 '{self.data_file}'。")
            return True
        except IOError as e:
            logging.error(f"保存应用启动器数据文件 '{self.data_file}' 失败: {e}")
            return False

    def get_apps(self) -> List[Dict[str, str]]:
        """获取所有应用程序的列表。"""
        return self.apps

    def add_app(self, name: str, path: str):
        """
        添加一个新的应用程序。

        Args:
            name (str): 应用程序的名称。
            path (str): 应用程序可执行文件的路径。
        """
        # 检查是否已存在同名或同路径的应用
        if any(app['path'] == path for app in self.apps):
            logging.warning(f"路径为 '{path}' 的应用程序已存在，添加操作已取消。")
            return
        
        self.apps.append({"name": name, "path": path})
        self.save_apps()
        logging.info(f"已添加新应用: {name} ({path})")

    def remove_app(self, index: int):
        """
        根据索引删除一个应用程序。

        Args:
            index (int): 要删除的应用程序在列表中的索引。
        """
        if 0 <= index < len(self.apps):
            removed_app = self.apps.pop(index)
            self.save_apps()
            logging.info(f"已删除应用: {removed_app['name']}")
        else:
            logging.warning(f"尝试删除一个无效的索引: {index}")

    def get_app_path(self, index: int) -> Optional[str]:
        """
        根据索引获取应用程序的路径。

        Args:
            index (int): 应用程序在列表中的索引。

        Returns:
            Optional[str]: 应用程序的路径，如果索引无效则返回None。
        """
        if 0 <= index < len(self.apps):
            return self.apps[index]['path']
        return None