# desktop_center/src/features/app_launcher/models/launcher_model.py
import json
import logging
import os
import uuid
from typing import List, Dict, Any

class LauncherModel:
    """【重构】数据模型，使用UUID作为分组的稳定标识符。"""
    KEY_GROUPS = "groups"
    KEY_APPS = "apps"
    KEY_DEFAULT_ID = "default_group_id"

    def __init__(self, data_file: str = 'launcher_apps.json'):
        self.data_file = data_file
        self.data: Dict[str, Any] = {
            self.KEY_GROUPS: {},
            self.KEY_APPS: {},
            self.KEY_DEFAULT_ID: None
        }
        self.load_apps()

    def load_apps(self):
        """【重构】加载数据，并包含从旧格式到新UUID格式的迁移逻辑。"""
        if not os.path.exists(self.data_file): return
        try:
            with open(self.data_file, 'r', encoding='utf-8') as f:
                loaded_data = json.load(f)
            
            if isinstance(loaded_data, dict) and self.KEY_GROUPS in loaded_data:
                self.data = loaded_data
                if not self.data.get(self.KEY_DEFAULT_ID) and self.data[self.KEY_GROUPS]:
                    self.data[self.KEY_DEFAULT_ID] = next(iter(self.data[self.KEY_GROUPS]))
            else:
                logging.warning("检测到旧版数据格式，正在执行一次性迁移...")
                new_data = {self.KEY_GROUPS: {}, self.KEY_APPS: {}, self.KEY_DEFAULT_ID: None}
                
                for group_name, apps_list in loaded_data.items():
                    group_id = str(uuid.uuid4())
                    # 【修复】确保groups的值始终是字典
                    new_data[self.KEY_GROUPS][group_id] = {"name": group_name}
                    new_data[self.KEY_APPS][group_id] = apps_list
                    if not new_data[self.KEY_DEFAULT_ID]:
                        new_data[self.KEY_DEFAULT_ID] = group_id
                
                self.data = new_data
                self.save_apps()
                logging.info("数据迁移成功，已保存为新格式。")

        except Exception as e:
            logging.error(f"加载或迁移应用数据失败: {e}", exc_info=True)

    def save_apps(self) -> bool:
        try:
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(self.data, f, indent=4, ensure_ascii=False)
            logging.info("应用数据已成功保存。")
            return True
        except IOError as e:
            logging.error(f"保存应用数据失败: {e}")
            return False

    def get_all_data(self) -> Dict[str, Any]: return self.data
    def get_total_app_count(self) -> int: return sum(len(apps) for apps in self.data[self.KEY_APPS].values())
    def get_group_app_count(self, group_id: str) -> int: return len(self.data[self.KEY_APPS].get(group_id, []))

    def add_app(self, group_id: str, name: str, path: str):
        if not group_id and self.data[self.KEY_DEFAULT_ID]:
             group_id = self.data[self.KEY_DEFAULT_ID]
        elif not group_id:
             group_id = self.create_group("默认分组")

        if group_id not in self.data[self.KEY_APPS]: self.data[self.KEY_APPS][group_id] = []
        self.data[self.KEY_APPS][group_id].append({"name": name, "path": path})
        self.save_apps()

    def create_group(self, name: str) -> str:
        group_id = str(uuid.uuid4())
        # 【修复】确保groups的值始终是字典
        self.data[self.KEY_GROUPS][group_id] = {"name": name}
        self.data[self.KEY_APPS][group_id] = []
        if not self.data[self.KEY_DEFAULT_ID]: self.data[self.KEY_DEFAULT_ID] = group_id
        self.save_apps()
        return group_id

    def remove_app(self, group_id: str, index: int):
        if group_id in self.data[self.KEY_APPS] and 0 <= index < len(self.data[self.KEY_APPS][group_id]):
            self.data[self.KEY_APPS][group_id].pop(index)
            self.save_apps()

    def move_apps(self, from_group_id: str, to_group_id: str):
        apps_to_move = self.data[self.KEY_APPS].get(from_group_id, [])
        if to_group_id not in self.data[self.KEY_APPS]: self.data[self.KEY_APPS][to_group_id] = []
        self.data[self.KEY_APPS][to_group_id].extend(apps_to_move)

    def rename_group(self, group_id: str, new_name: str):
        if group_id in self.data[self.KEY_GROUPS] and new_name.strip():
            self.data[self.KEY_GROUPS][group_id]['name'] = new_name.strip()
            self.save_apps()

    def delete_group_and_apps(self, group_id: str):
        self.data[self.KEY_GROUPS].pop(group_id, None)
        self.data[self.KEY_APPS].pop(group_id, None)
        if self.data[self.KEY_DEFAULT_ID] == group_id:
            self.data[self.KEY_DEFAULT_ID] = next(iter(self.data[self.KEY_GROUPS]), None)
        self.save_apps()
        
    def delete_empty_group(self, group_id: str):
        self.data[self.KEY_GROUPS].pop(group_id, None)
        self.data[self.KEY_APPS].pop(group_id, None)
        if self.data[self.KEY_DEFAULT_ID] == group_id:
            self.data[self.KEY_DEFAULT_ID] = next(iter(self.data[self.KEY_GROUPS]), None)