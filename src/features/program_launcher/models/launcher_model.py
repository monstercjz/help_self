# desktop_center/src/features/program_launcher/models/launcher_model.py
import json
import logging
import os
import uuid
import shutil
from PySide6.QtCore import QObject, Signal

from src.services.config_service import ConfigService

# 【新增】定义插件在config.ini中的配置段名称
CONFIG_SECTION = "ProgramLauncher"

class LauncherModel(QObject):
    """
    模型层，负责处理程序启动器的数据，包括从JSON文件加载和保存。
    【修改】现在通过ConfigService来管理数据文件路径。
    """
    data_changed = Signal()

    def __init__(self, config_service: ConfigService, parent=None):
        super().__init__(parent)
        self.config_service = config_service
        
        # 【修改】从配置服务获取数据路径，若无则使用根目录下的默认值
        default_path = "launcher_data.json"
        self.data_file = self.config_service.get_value(CONFIG_SECTION, "data_file_path", default_path)
        
        self.data = {"groups": [], "programs": {}}
        self.load_data()

    def load_data(self):
        """从JSON文件加载数据。如果文件不存在，则使用空数据。"""
        try:
            if os.path.exists(self.data_file):
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    self.data = json.load(f)
                    # 数据兼容性检查
                    if "groups" not in self.data: self.data["groups"] = []
                    if "programs" not in self.data: self.data["programs"] = {}
                logging.info(f"已从 {self.data_file} 加载启动器数据。")
            else:
                logging.warning(f"启动器数据文件 {self.data_file} 不存在，将在首次保存时创建。")
                self.data = {"groups": [], "programs": {}}
        except (json.JSONDecodeError, IOError) as e:
            logging.error(f"加载启动器数据文件 {self.data_file} 失败: {e}")
            self.data = {"groups": [], "programs": {}}

    def save_data(self):
        """将当前数据保存到JSON文件。"""
        try:
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(self.data, f, indent=4, ensure_ascii=False)
        except IOError as e:
            logging.error(f"保存启动器数据到 {self.data_file} 失败: {e}")
            
    def set_data_path(self, new_path: str):
        """
        【新增】设置新的数据文件路径，并将现有数据迁移过去。
        """
        old_path = self.data_file
        if new_path == old_path:
            return

        # 确保当前数据已保存到旧文件，以便迁移
        self.save_data()

        try:
            # 如果旧文件存在，则迁移；否则只是创建一个空的新文件
            if os.path.exists(old_path):
                shutil.move(old_path, new_path)
                logging.info(f"已将数据文件从 {old_path} 迁移到 {new_path}")
            
            self.data_file = new_path
            # 更新配置并保存
            self.config_service.set_option(CONFIG_SECTION, "data_file_path", new_path)
            self.config_service.save_config()
            logging.info(f"启动器数据路径已在配置中更新为: {new_path}")
            
            # 重新加载数据以确保一致性（虽然move之后内容一样，但这是个好习惯）
            self.load_data()
            self.data_changed.emit()

        except (IOError, OSError) as e:
            logging.error(f"迁移数据文件从 {old_path} 到 {new_path} 失败: {e}")
            # 如果迁移失败，回滚到旧路径以保持程序稳定
            self.data_file = old_path
            raise e # 向上抛出异常，让控制器处理UI通知

    def get_all_data(self):
        """获取所有分组及其包含的程序。"""
        # 返回一个深拷贝以防止外部修改
        return json.loads(json.dumps(self.data))

    def add_group(self, name: str) -> str:
        """添加一个新分组。"""
        new_group = {
            "id": str(uuid.uuid4()),
            "name": name
        }
        self.data["groups"].append(new_group)
        self.save_data()
        self.data_changed.emit()
        return new_group["id"]

    def edit_group(self, group_id: str, new_name: str):
        """编辑一个分组的名称。"""
        for group in self.data["groups"]:
            if group["id"] == group_id:
                group["name"] = new_name
                self.save_data()
                self.data_changed.emit()
                return

    def delete_group(self, group_id: str, delete_programs: bool = False):
        """删除一个分组。"""
        self.data["groups"] = [g for g in self.data["groups"] if g["id"] != group_id]
        if delete_programs:
            self.data["programs"] = {
                pid: p for pid, p in self.data["programs"].items() if p["group_id"] != group_id
            }
        self.save_data()
        self.data_changed.emit()

    def add_program(self, group_id: str, name: str, path: str):
        """向指定分组添加一个新程序。"""
        program_id = str(uuid.uuid4())
        self.data["programs"][program_id] = {
            "id": program_id,
            "group_id": group_id,
            "name": name,
            "path": path,
            "order": len(self.get_programs_in_group(group_id))
        }
        self.save_data()
        self.data_changed.emit()

    def delete_program(self, program_id: str):
        """删除一个程序。"""
        if program_id in self.data["programs"]:
            del self.data["programs"][program_id]
            self.save_data()
            self.data_changed.emit()
            
    def get_program_by_id(self, program_id: str) -> dict | None:
        return self.data["programs"].get(program_id)
        
    def get_group_by_id(self, group_id: str) -> dict | None:
        for group in self.data["groups"]:
            if group["id"] == group_id:
                return group
        return None

    def get_programs_in_group(self, group_id: str) -> list:
        programs = [p for p in self.data["programs"].values() if p["group_id"] == group_id]
        # 根据order字段排序
        programs.sort(key=lambda p: p.get("order", 0))
        return programs
        
    def get_other_groups(self, group_id_to_exclude: str) -> list:
        """获取除指定ID外的所有分组。"""
        return [g for g in self.data["groups"] if g["id"] != group_id_to_exclude]

    def move_programs_to_group(self, old_group_id: str, new_group_id: str):
        """将一个分组的所有程序移动到另一个分组。"""
        for program in self.data["programs"].values():
            if program["group_id"] == old_group_id:
                program["group_id"] = new_group_id
        # 不需要保存和发信号，因为调用者会处理
        
    def reorder_groups(self, group_ids: list[str]):
        """根据ID列表重新排序分组。"""
        group_map = {g['id']: g for g in self.data['groups']}
        self.data['groups'] = [group_map[gid] for gid in group_ids if gid in group_map]
        self.save_data()
        self.data_changed.emit() # 通常拖拽结束时才触发一次，所以这里发信号是合适的
        
    def reorder_programs(self, group_id: str, program_ids: list[str]):
        """根据ID列表重新排序指定分组内的程序。"""
        for i, prog_id in enumerate(program_ids):
            if prog_id in self.data['programs']:
                self.data['programs'][prog_id]['order'] = i
        self.save_data()
        self.data_changed.emit()