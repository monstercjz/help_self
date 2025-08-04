# desktop_center/src/features/program_launcher/models/launcher_model.py
import logging
import uuid
from PySide6.QtCore import QObject, Signal

from src.core.context import ApplicationContext
from src.features.program_launcher.services.program_launcher_database_service import ProgramLauncherDatabaseService

class LauncherModel(QObject):
    data_changed = Signal()

    def __init__(self, db_service: ProgramLauncherDatabaseService, parent=None):
        super().__init__(parent)
        self.db_service = db_service
        self.data = {"groups": [], "programs": {}}
        self.load_data()

    def set_db_service(self, new_db_service: ProgramLauncherDatabaseService):
        self.db_service = new_db_service
        self.load_data()
        self.data_changed.emit()

    def load_data(self):
        try:
            self.data["groups"] = self.db_service.get_groups()
            self.data["programs"] = self.db_service.get_programs()
            logging.info("已从数据库加载启动器数据。")
        except Exception as e:
            logging.error(f"从数据库加载启动器数据失败: {e}")
            self.data = {"groups": [], "programs": {}}

    def save_data(self):
        # 数据库操作是即时保存的，此方法可以留空或用于将来的批量操作
        pass

    def get_db_path(self) -> str:
        return self.db_service.db_path

    def get_all_data(self):
        return self.data

    def add_group(self, name: str) -> str:
        new_group_id = str(uuid.uuid4())
        order_index = len(self.data["groups"])
        self.db_service.add_group(new_group_id, name, order_index)
        self.load_data()
        self.data_changed.emit()
        return new_group_id

    def edit_group(self, group_id: str, new_name: str):
        self.db_service.update_group(group_id, new_name)
        self.load_data()
        self.data_changed.emit()

    def reorder_groups(self, group_ids: list[str]):
        self.db_service.reorder_groups(group_ids)
        self.load_data()
        self.data_changed.emit()
        logging.info(f"Model: Group order has been updated to: {group_ids}")

    def delete_group(self, group_id: str, delete_programs: bool = False):
        # The database handles cascading deletes if configured with ON DELETE CASCADE
        self.db_service.delete_group(group_id)
        self.load_data()
        self.data_changed.emit()

    def add_program(self, group_id: str, name: str, path: str, run_as_admin: bool = False):
        program_id = str(uuid.uuid4())
        order_index = len(self.get_programs_in_group(group_id))
        self.db_service.add_program(program_id, group_id, name, path, run_as_admin, order_index)
        self.load_data()
        self.data_changed.emit()

    def edit_program(self, program_id: str, new_group_id: str, new_name: str, new_path: str, new_run_as_admin: bool):
        self.db_service.update_program(program_id, new_group_id, new_name, new_path, new_run_as_admin)
        self.load_data()
        self.data_changed.emit()
        logging.info(f"程序已编辑: ID={program_id}, Name={new_name}, Admin={new_run_as_admin}")

    def delete_program(self, program_id: str):
        program_to_delete = self.data['programs'].get(program_id)
        if not program_to_delete: return

        self.db_service.delete_program(program_id)
        
        # Reorder remaining programs in the group
        group_id = program_to_delete['group_id']
        remaining_progs = [p for p in self.data["programs"].values() if p.get('group_id') == group_id and p.get('id') != program_id]
        remaining_progs.sort(key=lambda p: p.get("order_index", 0))
        program_ids = [p['id'] for p in remaining_progs]
        self.db_service.reorder_programs_in_group(group_id, program_ids)

        self.load_data()
        self.data_changed.emit()
            
    def get_program_by_id(self, program_id: str) -> dict | None:
        return self.data["programs"].get(program_id)
        
    def get_group_by_id(self, group_id: str) -> dict | None:
        for group in self.data["groups"]:
            if group["id"] == group_id: return group
        return None

    def get_programs_in_group(self, group_id: str) -> list:
        programs = [p for p in self.data["programs"].values() if p.get('group_id') == group_id]
        programs.sort(key=lambda p: p.get("order_index", 0))
        return programs
        
    def get_other_groups(self, group_id_to_exclude: str) -> list:
        return [g for g in self.data["groups"] if g["id"] != group_id_to_exclude]

    def move_programs_to_group(self, old_group_id: str, new_group_id: str):
        programs_to_move = self.get_programs_in_group(old_group_id)
        for program in programs_to_move:
            self.db_service.update_program(program['id'], new_group_id, program['name'], program['path'], program['run_as_admin'])
        self.load_data()
        self.data_changed.emit()

    def filter_data(self, text: str) -> dict:
        if not text:
            return self.get_all_data()

        text = text.lower()
        
        filtered_programs = {}
        visible_group_ids = set()

        for prog_id, prog_data in self.data["programs"].items():
            if text in prog_data.get('name', '').lower():
                filtered_programs[prog_id] = prog_data
                visible_group_ids.add(prog_data.get('group_id'))

        filtered_groups = []
        for group_data in self.data["groups"]:
            group_id = group_data.get('id')
            if text in group_data.get('name', '').lower() or group_id in visible_group_ids:
                filtered_groups.append(group_data)

        return {"groups": filtered_groups, "programs": filtered_programs}

    def move_program(self, program_id: str, target_group_id: str, target_index: int):
        program_to_move = self.data['programs'].get(program_id)
        if not program_to_move:
            logging.error(f"move_program: Program with id {program_id} not found.")
            return

        source_group_id = program_to_move['group_id']
        
        # Update program's group
        self.db_service.update_program(program_id, target_group_id, program_to_move['name'], program_to_move['path'], program_to_move['run_as_admin'])

        # Reorder target group
        target_progs = self.get_programs_in_group(target_group_id)
        target_progs = [p for p in target_progs if p['id'] != program_id]
        target_progs.insert(target_index, program_to_move)
        self.db_service.reorder_programs_in_group(target_group_id, [p['id'] for p in target_progs])

        # Reorder source group if different
        if source_group_id != target_group_id:
            source_progs = self.get_programs_in_group(source_group_id)
            self.db_service.reorder_programs_in_group(source_group_id, [p['id'] for p in source_progs])
        
        self.load_data()
        self.data_changed.emit()
        logging.info(f"Model: Program {program_id} moved to group {target_group_id} at index {target_index}. Triggering refresh.")
