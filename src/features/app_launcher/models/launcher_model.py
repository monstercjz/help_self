# desktop_center/src/features/app_launcher/models/launcher_model.py
import json
import logging
import os
from typing import List, Dict, Optional

class LauncherModel:
    """【重构】负责管理按分组组织的应用程序列表的数据模型。"""
    DEFAULT_GROUP = "默认分组"

    def __init__(self, data_file: str = 'launcher_apps.json'):
        self.data_file = data_file
        self.apps_by_group: Dict[str, List[Dict[str, str]]] = {}
        self.load_apps()

    def load_apps(self):
        if not os.path.exists(self.data_file):
            self.apps_by_group = {}
            return

        try:
            with open(self.data_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            if isinstance(data, list):
                logging.warning("检测到旧版扁平数据格式，正在迁移到分组格式...")
                self.apps_by_group = {self.DEFAULT_GROUP: data}
                self.save_apps()
            elif isinstance(data, dict):
                self.apps_by_group = data
            else:
                logging.error("无法识别的数据格式，将使用空配置。")
                self.apps_by_group = {}

            logging.info(f"已成功从 '{self.data_file}' 加载应用分组。")
        except (json.JSONDecodeError, IOError) as e:
            logging.error(f"加载应用启动器数据文件 '{self.data_file}' 失败: {e}")
            self.apps_by_group = {}

    def save_apps(self) -> bool:
        cleaned_data = {group: apps for group, apps in self.apps_by_group.items() if apps}
        self.apps_by_group = cleaned_data

        try:
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(self.apps_by_group, f, indent=4, ensure_ascii=False)
            logging.info(f"应用分组列表已成功保存到 '{self.data_file}'。")
            return True
        except IOError as e:
            logging.error(f"保存应用启动器数据文件 '{self.data_file}' 失败: {e}")
            return False

    def get_apps_by_group(self) -> Dict[str, List[Dict[str, str]]]:
        return self.apps_by_group

    def get_groups(self) -> List[str]:
        return sorted(list(self.apps_by_group.keys()))

    def add_app(self, group: str, name: str, path: str):
        if not group.strip(): group = self.DEFAULT_GROUP
        if any(app['path'] == path for apps in self.apps_by_group.values() for app in apps):
            logging.warning(f"路径为 '{path}' 的应用程序已存在，添加操作已取消。")
            return

        if group not in self.apps_by_group: self.apps_by_group[group] = []
        self.apps_by_group[group].append({"name": name, "path": path})
        self.save_apps()
        logging.info(f"已添加新应用 '{name}' 到分组 '{group}'。")

    def remove_app(self, group: str, index: int):
        if group in self.apps_by_group and 0 <= index < len(self.apps_by_group[group]):
            removed_app = self.apps_by_group[group].pop(index)
            self.save_apps()
            logging.info(f"已从分组 '{group}' 删除应用: {removed_app['name']}")
        else:
            logging.warning(f"尝试从分组 '{group}' 删除一个无效的索引: {index}")

    def move_app(self, from_group: str, from_index: int, to_group: str):
        if from_group not in self.apps_by_group or not (0 <= from_index < len(self.apps_by_group[from_group])):
            logging.error(f"移动应用失败：源分组或索引无效。")
            return
        
        app_to_move = self.apps_by_group[from_group].pop(from_index)
        if to_group not in self.apps_by_group: self.apps_by_group[to_group] = []
        self.apps_by_group[to_group].append(app_to_move)
        self.save_apps()
        logging.info(f"已将应用 '{app_to_move['name']}' 从分组 '{from_group}' 移动到 '{to_group}'。")

    def rename_group(self, old_name: str, new_name: str) -> bool:
        if old_name not in self.apps_by_group or not new_name.strip() or new_name in self.apps_by_group:
            logging.warning(f"重命名分组失败：旧组名 '{old_name}' 不存在，或新组名 '{new_name}' 无效/已存在。")
            return False
        
        self.apps_by_group[new_name] = self.apps_by_group.pop(old_name)
        self.save_apps()
        logging.info(f"已将分组 '{old_name}' 重命名为 '{new_name}'。")
        return True
        
    def delete_group(self, group_name: str):
        if group_name not in self.apps_by_group or group_name == self.DEFAULT_GROUP:
            logging.warning(f"删除分组失败：分组 '{group_name}' 不可删除。")
            return
            
        apps_to_move = self.apps_by_group.pop(group_name, [])
        if not apps_to_move: # 如果分组为空，直接删除即可
            self.save_apps()
            logging.info(f"已删除空分组 '{group_name}'。")
            return
            
        if self.DEFAULT_GROUP not in self.apps_by_group: self.apps_by_group[self.DEFAULT_GROUP] = []
        self.apps_by_group[self.DEFAULT_GROUP].extend(apps_to_move)
        self.save_apps()
        logging.info(f"已删除分组 '{group_name}'，其内部应用已迁移到 '{self.DEFAULT_GROUP}'。")
        
    def create_empty_group(self, group_name: str) -> bool:
        """【新增】创建一个新的空分组。"""
        if not group_name.strip() or group_name in self.apps_by_group:
            logging.warning(f"创建分组失败：分组名 '{group_name}' 无效或已存在。")
            return False
        
        self.apps_by_group[group_name] = []
        # 注意：此处不调用save_apps，因为空分组默认不保存。用户添加应用后会自动保存。
        logging.info(f"已在内存中创建新分组 '{group_name}'。")
        return True