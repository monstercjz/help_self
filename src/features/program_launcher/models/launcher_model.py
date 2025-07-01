# desktop_center/src/features/program_launcher/models/launcher_model.py
import json
import logging
import os
import uuid
from PySide6.QtCore import QObject, Signal

from src.services.config_service import ConfigService

CONFIG_SECTION = "ProgramLauncher"

class LauncherModel(QObject):
    data_changed = Signal()

    def __init__(self, config_service: ConfigService, parent=None):
        super().__init__(parent)
        self.config_service = config_service
        default_path = "launcher_data.json"
        self.data_file = self.config_service.get_value(CONFIG_SECTION, "data_file_path", default_path)
        self.data = {"groups": [], "programs": {}}
        self.load_data()

    def load_data(self):
        # ... 此方法保持不变 ...
        try:
            if os.path.exists(self.data_file):
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    if not content: self.data = {"groups": [], "programs": {}}
                    else: self.data = json.loads(content)
                    if "groups" not in self.data: self.data["groups"] = []
                    if "programs" not in self.data: self.data["programs"] = {}
                logging.info(f"已从 {self.data_file} 加载启动器数据。")
            else:
                logging.warning(f"启动器数据文件 {self.data_file} 不存在，将视为空配置。")
                self.data = {"groups": [], "programs": {}}
        except (json.JSONDecodeError, IOError) as e:
            logging.error(f"加载启动器数据文件 {self.data_file} 失败: {e}")
            self.data = {"groups": [], "programs": {}}
            raise e

    def save_data(self):
        # ... 此方法保持不变 ...
        try:
            logging.info(f"[MODEL] Saving data to {self.data_file}...")
            dir_name = os.path.dirname(self.data_file)
            if dir_name: os.makedirs(dir_name, exist_ok=True)
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(self.data, f, indent=4, ensure_ascii=False)
            logging.info(f"启动器数据已成功保存到 {self.data_file}。")
        except IOError as e:
            logging.error(f"保存启动器数据到 {self.data_file} 失败: {e}")

    def set_data_path(self, new_path: str):
        # ... 此方法保持不变 ...
        if new_path == self.data_file: return
        self.config_service.set_option(CONFIG_SECTION, "data_file_path", new_path)
        self.config_service.save_config()
        self.data_file = new_path
        try:
            self.load_data()
            self.data_changed.emit()
        except Exception:
            raise

    def update_full_structure(self, new_structure: dict):
        # ... 此方法保持不变 ...
        logging.info("[MODEL] Updating full data structure based on UI.")
        logging.debug(f"[MODEL] Received new structure for update: {new_structure}")
        self.data = new_structure
        self.save_data()
        self.data_changed.emit()

    def get_all_data(self):
        # ... 此方法保持不变 ...
        return json.loads(json.dumps(self.data))

    def add_group(self, name: str) -> str:
        # ... 此方法保持不变 ...
        new_group = {"id": str(uuid.uuid4()), "name": name}
        self.data["groups"].append(new_group)
        self.save_data()
        self.data_changed.emit()
        return new_group["id"]

    def edit_group(self, group_id: str, new_name: str):
        # ... 此方法保持不变 ...
        for group in self.data["groups"]:
            if group["id"] == group_id:
                group["name"] = new_name
                self.save_data()
                self.data_changed.emit()
                return

    def delete_group(self, group_id: str, delete_programs: bool = False):
        # ... 此方法保持不变 ...
        self.data["groups"] = [g for g in self.data["groups"] if g["id"] != group_id]
        if delete_programs:
            self.data["programs"] = {pid: p for pid, p in self.data["programs"].items() if p["group_id"] != group_id}
        self.save_data()
        self.data_changed.emit()

    def add_program(self, group_id: str, name: str, path: str):
        # ... 此方法保持不变 ...
        program_id = str(uuid.uuid4())
        self.data["programs"][program_id] = {
            "id": program_id, "group_id": group_id, "name": name, "path": path,
            "order": len(self.get_programs_in_group(group_id))
        }
        self.save_data()
        self.data_changed.emit()

    def edit_program(self, program_id: str, new_group_id: str, new_name: str, new_path: str):
        """【新增】编辑一个已存在的程序。"""
        if program_id in self.data['programs']:
            program = self.data['programs'][program_id]
            program['group_id'] = new_group_id
            program['name'] = new_name
            program['path'] = new_path
            # 注意：order 字段在这里不作修改，因为它只在组内排序时改变
            self.save_data()
            self.data_changed.emit()
            logging.info(f"程序已编辑: ID={program_id}, Name={new_name}")
        else:
            logging.warning(f"尝试编辑一个不存在的程序: ID={program_id}")

    def delete_program(self, program_id: str):
        # ... 此方法保持不变 ...
        if program_id in self.data["programs"]:
            del self.data["programs"][program_id]
            self.save_data()
            self.data_changed.emit()
            
    def get_program_by_id(self, program_id: str) -> dict | None:
        # ... 此方法保持不变 ...
        return self.data["programs"].get(program_id)
        
    def get_group_by_id(self, group_id: str) -> dict | None:
        # ... 此方法保持不变 ...
        for group in self.data["groups"]:
            if group["id"] == group_id: return group
        return None

    def get_programs_in_group(self, group_id: str) -> list:
        # ... 此方法保持不变 ...
        programs = [p for p in self.data["programs"].values() if p["group_id"] == group_id]
        programs.sort(key=lambda p: p.get("order", 0))
        return programs
        
    def get_other_groups(self, group_id_to_exclude: str) -> list:
        # ... 此方法保持不变 ...
        return [g for g in self.data["groups"] if g["id"] != group_id_to_exclude]

    def move_programs_to_group(self, old_group_id: str, new_group_id: str):
        # ... 此方法保持不变 ...
        for program in self.data["programs"].values():
            if program["group_id"] == old_group_id:
                program["group_id"] = new_group_id