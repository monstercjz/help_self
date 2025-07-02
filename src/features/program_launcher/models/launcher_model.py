# desktop_center/src/features/program_launcher/models/launcher_model.py
import json
import logging
import os
import sys
import shutil
import uuid
from PySide6.QtCore import QObject, Signal
from PySide6.QtWidgets import QMessageBox

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
        try:
            if os.path.exists(self.data_file):
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    if not content:
                        self.data = {"groups": [], "programs": {}}
                        return
                    self.data = json.loads(content)
                    if "groups" not in self.data: self.data["groups"] = []
                    if "programs" not in self.data: self.data["programs"] = {}
                logging.info(f"已从 {self.data_file} 加载启动器数据。")
            else:
                logging.warning(f"启动器数据文件 {self.data_file} 不存在，将视为空配置。")
                self.data = {"groups": [], "programs": {}}
        except (json.JSONDecodeError, IOError) as e:
            logging.error(f"加载启动器数据文件 {self.data_file} 失败: {e}")
            
            # 备份损坏的文件
            backup_path = self.data_file + ".bak"
            try:
                shutil.copy(self.data_file, backup_path)
                backup_msg = f"损坏的文件已为您备份到:\n{backup_path}"
            except Exception as backup_e:
                backup_msg = f"尝试备份文件失败: {backup_e}"

            # 弹出错误对话框
            msg_box = QMessageBox()
            msg_box.setIcon(QMessageBox.Icon.Critical)
            msg_box.setWindowTitle("数据文件损坏")
            msg_box.setText(f"无法加载数据文件，它可能已损坏。\n{backup_msg}")
            msg_box.setInformativeText("您可以选择以一个全新的空配置启动，或退出程序以手动检查文件。")
            
            reset_btn = msg_box.addButton("以空配置启动", QMessageBox.ButtonRole.AcceptRole)
            exit_btn = msg_box.addButton("退出", QMessageBox.ButtonRole.RejectRole)
            msg_box.setDefaultButton(reset_btn)
            
            msg_box.exec()

            if msg_box.clickedButton() == exit_btn:
                sys.exit(1) # 退出程序
            
            # 用户选择重置
            self.data = {"groups": [], "programs": {}}

    def save_data(self):
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
        logging.info("[MODEL] Updating full data structure based on UI.")
        self.data = new_structure
        self.save_data()
        self.data_changed.emit()

    def get_all_data(self):
        return json.loads(json.dumps(self.data))

    def add_group(self, name: str) -> str:
        new_group = {"id": str(uuid.uuid4()), "name": name}
        self.data["groups"].append(new_group)
        self.save_data()
        self.data_changed.emit()
        return new_group["id"]

    def edit_group(self, group_id: str, new_name: str):
        for group in self.data["groups"]:
            if group["id"] == group_id:
                group["name"] = new_name
                self.save_data()
                self.data_changed.emit()
                return

    def reorder_groups(self, group_ids: list[str]):
        """
        根据给定的ID列表，对分组进行重新排序。

        Args:
            group_ids: 包含分组ID的新顺序列表。
        """
        if not group_ids: return
        
        # 创建一个从 group_id 到 group 对象的映射，以便快速查找
        group_map = {g['id']: g for g in self.data['groups']}
        
        # 根据传入的 group_ids 列表，构建一个新的、有序的分组列表
        # 这里会过滤掉任何可能不存在于 group_map 中的ID，以增加健壮性
        new_groups_order = [group_map[gid] for gid in group_ids if gid in group_map]
        
        # 安全检查：如果新旧列表的长度不匹配，说明可能丢失了数据或传入了无效ID。
        # 在这种情况下，我们选择不执行更新，以避免数据损坏。
        if len(new_groups_order) == len(self.data['groups']):
            self.data['groups'] = new_groups_order
            self.save_data()
            self.data_changed.emit()
            logging.info(f"Model: Group order has been updated to: {group_ids}")
        else:
            logging.warning(f"Group reorder failed due to ID mismatch. Expected {len(self.data['groups'])}, got {len(new_groups_order)}")


    def delete_group(self, group_id: str, delete_programs: bool = False):
        self.data["groups"] = [g for g in self.data["groups"] if g["id"] != group_id]
        if delete_programs:
            self.data["programs"] = {pid: p for pid, p in self.data["programs"].items() if p["group_id"] != group_id}
        self.save_data()
        self.data_changed.emit()

    def add_program(self, group_id: str, name: str, path: str):
        program_id = str(uuid.uuid4())
        self.data["programs"][program_id] = {
            "id": program_id, "group_id": group_id, "name": name, "path": path,
            "order": len(self.get_programs_in_group(group_id))
        }
        self.save_data()
        self.data_changed.emit()

    def edit_program(self, program_id: str, new_group_id: str, new_name: str, new_path: str):
        if program_id in self.data['programs']:
            program = self.data['programs'][program_id]
            # 如果分组发生了变化，需要调整两个分组的order
            if program['group_id'] != new_group_id:
                self.move_program(program_id, new_group_id, 9999) # 移动到新分组末尾
            program['group_id'] = new_group_id
            program['name'] = new_name
            program['path'] = new_path
            self.save_data()
            self.data_changed.emit()
            logging.info(f"程序已编辑: ID={program_id}, Name={new_name}")

    def delete_program(self, program_id: str):
        program_to_delete = self.data['programs'].pop(program_id, None)
        if not program_to_delete: return
        
        # 重新计算被删除程序所在分组的 order
        group_id = program_to_delete['group_id']
        remaining_progs = self.get_programs_in_group(group_id)
        for i, p in enumerate(remaining_progs):
            p['order'] = i
        
        self.save_data()
        self.data_changed.emit()
            
    def get_program_by_id(self, program_id: str) -> dict | None:
        return self.data["programs"].get(program_id)
        
    def get_group_by_id(self, group_id: str) -> dict | None:
        for group in self.data["groups"]:
            if group["id"] == group_id: return group
        return None

    def get_programs_in_group(self, group_id: str) -> list:
        programs = [p for p in self.data["programs"].values() if p.get('group_id') == group_id]
        programs.sort(key=lambda p: p.get("order", 0))
        return programs
        
    def get_other_groups(self, group_id_to_exclude: str) -> list:
        return [g for g in self.data["groups"] if g["id"] != group_id_to_exclude]

    def move_programs_to_group(self, old_group_id: str, new_group_id: str):
        for program in self.data["programs"].values():
            if program["group_id"] == old_group_id:
                program["group_id"] = new_group_id

    def filter_data(self, text: str) -> dict:
        """
        根据搜索文本过滤数据。

        Args:
            text: 用于搜索的文本。

        Returns:
            一个只包含匹配项的新的数据字典。
        """
        if not text:
            return self.get_all_data()

        text = text.lower()
        
        filtered_programs = {}
        visible_group_ids = set()

        # 过滤程序
        for prog_id, prog_data in self.data["programs"].items():
            if text in prog_data.get('name', '').lower():
                filtered_programs[prog_id] = prog_data
                visible_group_ids.add(prog_data.get('group_id'))

        # 过滤分组（如果分组名匹配，或其下有匹配的程序）
        filtered_groups = []
        for group_data in self.data["groups"]:
            group_id = group_data.get('id')
            if text in group_data.get('name', '').lower() or group_id in visible_group_ids:
                filtered_groups.append(group_data)

        return {"groups": filtered_groups, "programs": filtered_programs}

    def move_program(self, program_id: str, target_group_id: str, target_index: int):
        """
        移动一个程序到新的位置，这可能是在同一个分组内，也可能是在不同分组之间。
        此方法通过直接修改 self.data 并重新计算受影响分组的 order 来保证数据一致性。
        """
        program_to_move = self.data['programs'].get(program_id)
        if not program_to_move:
            logging.error(f"move_program: Program with id {program_id} not found.")
            return

        source_group_id = program_to_move['group_id']

        # 步骤 1: 立即在核心数据中更新被移动程序的 group_id
        program_to_move['group_id'] = target_group_id

        # 步骤 2: 重新生成并更新目标分组的顺序
        target_progs = self.get_programs_in_group(target_group_id)
        
        # 为了处理组内拖拽，我们需要从列表中移除旧的项
        # 使用列表推导式来安全地移除
        target_progs = [p for p in target_progs if p['id'] != program_id]
        
        # 确保索引有效
        if target_index > len(target_progs):
            target_index = len(target_progs)
        target_progs.insert(target_index, program_to_move)
        
        # 遍历这个顺序正确的列表，更新核心数据中的 order
        for i, prog in enumerate(target_progs):
            self.data['programs'][prog['id']]['order'] = i

        # 步骤 3: 如果是跨组移动，重新生成并更新源分组的顺序
        if source_group_id != target_group_id:
            source_progs = self.get_programs_in_group(source_group_id)
            for i, prog in enumerate(source_progs):
                self.data['programs'][prog['id']]['order'] = i
        
        logging.info(f"Model: Program {program_id} moved to group {target_group_id} at index {target_index}. Triggering save and refresh.")
        self.save_data()
        self.data_changed.emit()