# desktop_center/src/features/program_launcher/controllers/launcher_controller.py
import logging
import os
import subprocess
import sys
from PySide6.QtWidgets import QFileDialog, QMessageBox, QDialog
from PySide6.QtCore import QObject, Slot

from ..models.launcher_model import LauncherModel
from ..views.launcher_page_view import LauncherPageView
from ..widgets.group_dialog import GroupDialog
from ..widgets.delete_group_dialog import DeleteGroupDialog
from ..widgets.add_program_dialog import AddProgramDialog
from src.core.context import ApplicationContext

class LauncherController(QObject):
    def __init__(self, model: LauncherModel, view: LauncherPageView, context: ApplicationContext, parent=None):
        super().__init__(parent)
        self.model = model
        self.view = view
        self.context = context
        
        # 读取树状视图的配置，遵循项目通用模式
        self.tree_view_icon_size = int(self.context.config_service.get_value(
            "ProgramLauncher", "treeview_iconsize", fallback="20"
        ))
        self.tree_view_font_size = int(self.context.config_service.get_value(
            "ProgramLauncher", "treeview_fontsize", fallback="10"
        ))

        self._connect_signals()
        self.refresh_view()

    def _connect_signals(self):
        self.view.add_group_requested.connect(self.add_group)
        self.view.add_program_requested.connect(self.handle_add_program_request)
        self.view.item_double_clicked.connect(self.launch_program)
        self.view.edit_item_requested.connect(self.edit_item)
        self.view.delete_item_requested.connect(self.delete_item)
        self.view.search_text_changed.connect(self.filter_view)
        self.view.change_data_path_requested.connect(self.change_data_path)
        self.view.program_dropped.connect(self.handle_program_drop)
        
        # 【核心修复】移除对具体子视图的监听，改为监听主视图的统一信号出口。
        # 这样，无论哪个视图模式发起了分组排序，控制器都能收到并处理。
        # self.view.icon_view.group_order_changed.connect(self.model.reorder_groups) <-- 移除
        # self.view.tree_view.group_order_changed.connect(self.model.reorder_groups) <-- 移除
        self.view.group_order_changed.connect(self.model.reorder_groups)
        
        self.model.data_changed.connect(self.refresh_view)

    # ... 其他所有方法 (refresh_view, handle_program_drop, add_group, 等) 保持完全不变 ...
    def refresh_view(self):
        logging.info("[CONTROLLER] Refreshing view from model data.")
        data = self.model.get_all_data()
        # 将配置传递给视图
        data['tree_view_config'] = {
            'icon_size': self.tree_view_icon_size,
            'font_size': self.tree_view_font_size
        }
        self.view.rebuild_ui(data)
    @Slot(str, str, int)
    def handle_program_drop(self, program_id: str, target_group_id: str, target_index: int):
        logging.info(f"[CONTROLLER] Handling program drop: prog_id={program_id}, group_id={target_group_id}, index={target_index}")
        self.model.move_program(program_id, target_group_id, target_index)
    @Slot()
    def add_group(self):
        dialog = GroupDialog(self.view)
        if dialog.exec():
            group_name = dialog.get_group_name()
            if group_name:
                self.model.add_group(group_name)
                self.context.notification_service.show("成功", f"分组 '{group_name}' 已创建。")
    @Slot(str)
    def handle_add_program_request(self, group_id: str = None):
        all_groups = self.model.get_all_data().get('groups', [])
        if not all_groups:
            reply = QMessageBox.information(self.view, "需要分组", "目前没有程序分组，请先创建一个。",
                                            QMessageBox.StandardButton.Ok | QMessageBox.StandardButton.Cancel)
            if reply == QMessageBox.StandardButton.Ok: self.add_group()
            return
        dialog = AddProgramDialog(all_groups, default_group_id=group_id, parent=self.view)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            details = dialog.get_program_details()
            if details:
                gid, name, path = details
                self.model.add_program(gid, name, path)
                self.context.notification_service.show("成功", f"程序 '{name}' 已添加。")
    @Slot(str)
    def launch_program(self, program_id: str):
        program = self.model.get_program_by_id(program_id)
        if program and os.path.exists(program['path']):
            try:
                # 使用 startfile 在 Windows 上更健壮，对于非 .exe 文件（如快捷方式）也能更好地工作
                if sys.platform == "win32":
                    os.startfile(program['path'])
                else:
                    subprocess.Popen([program['path']])
                
                self.context.notification_service.show(
                    title="程序已启动", message=f"{program['name']} 正在启动。"
                )
            except Exception as e:
                logging.error(f"Failed to launch program {program['name']} ({program['path']}): {e}")
                QMessageBox.critical(self.view, "启动失败", f"无法启动程序：\n{program['path']}\n\n错误: {e}")
        else:
            QMessageBox.warning(self.view, "启动失败", "程序路径不存在或已被移动，请编辑或删除此条目。")
    @Slot(str, str)
    def edit_item(self, item_id: str, item_type: str):
        if item_type == 'group':
            group = self.model.get_group_by_id(item_id)
            if not group: return
            dialog = GroupDialog(self.view, current_name=group['name'])
            if dialog.exec():
                new_name = dialog.get_group_name()
                if new_name and new_name != group['name']:
                    self.model.edit_group(item_id, new_name)
                    self.context.notification_service.show("成功", f"分组已重命名为 '{new_name}'。")
        elif item_type == 'program':
            program_to_edit = self.model.get_program_by_id(item_id)
            if not program_to_edit: return
            all_groups = self.model.get_all_data().get('groups', [])
            dialog = AddProgramDialog(all_groups, program_to_edit=program_to_edit, parent=self.view)
            if dialog.exec() == QDialog.DialogCode.Accepted:
                new_group_id, new_name, new_path = dialog.get_program_details()
                self.model.edit_program(item_id, new_group_id, new_name, new_path)
                self.context.notification_service.show("成功", f"程序 '{new_name}' 已更新。")
    @Slot(str, str)
    def delete_item(self, item_id: str, item_type: str):
        if item_type == 'group': self._handle_delete_group(item_id)
        elif item_type == 'program':
            program = self.model.get_program_by_id(item_id)
            if not program: return
            reply = QMessageBox.question(self.view, "确认删除", f"您确定要删除程序 '{program['name']}' 吗？",
                                         QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                         QMessageBox.StandardButton.No)
            if reply == QMessageBox.StandardButton.Yes:
                self.model.delete_program(item_id)
                self.context.notification_service.show("成功", f"程序 '{program['name']}' 已删除。")
    def _handle_delete_group(self, group_id: str):
        group = self.model.get_group_by_id(group_id)
        if not group: return
        other_groups = self.model.get_other_groups(group_id)
        programs_in_group = self.model.get_programs_in_group(group_id)
        if not programs_in_group:
            reply = QMessageBox.question(self.view, "确认删除", f"您确定要删除空分组 '{group['name']}' 吗？",
                                         QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                         QMessageBox.StandardButton.No)
            if reply == QMessageBox.StandardButton.Yes:
                self.model.delete_group(group_id)
                self.context.notification_service.show("成功", f"分组 '{group['name']}' 已删除。")
            return
        dialog = DeleteGroupDialog(group['name'], other_groups, self.view)
        if dialog.exec():
            choice, target_group_id = dialog.get_result()
            if choice == 'move':
                if not target_group_id and not other_groups:
                    target_group_id = self.model.add_group("默认分组")
                self.model.move_programs_to_group(group_id, target_group_id)
                self.model.delete_group(group_id)
                self.context.notification_service.show("成功", f"分组 '{group['name']}' 已删除，其下所有程序已移动。")
            elif choice == 'delete_all':
                self.model.delete_group(group_id, delete_programs=True)
                self.context.notification_service.show("成功", f"分组 '{group['name']}' 及其下所有程序已删除。")
    @Slot(str)
    def filter_view(self, text: str):
        """
        根据文本过滤视图。
        如果文本为空，则显示所有数据；否则，显示过滤后的数据。
        """
        if not text:
            self.refresh_view()
        else:
            filtered_data = self.model.filter_data(text)
            self.view.rebuild_ui(filtered_data)
    @Slot()
    def change_data_path(self):
        current_path = self.model.data_file
        new_path, _ = QFileDialog.getOpenFileName(
            self.view, "选择或指定程序启动器数据文件",
            os.path.dirname(current_path), "JSON 文件 (*.json);;所有文件 (*)"
        )
        if new_path and new_path != current_path:
            try:
                self.model.set_data_path(new_path)
                QMessageBox.information(
                    self.view, "成功", f"数据源已成功切换到:\n{new_path}\n\n界面已刷新。"
                )
            except Exception as e:
                QMessageBox.critical(
                    self.view, "操作失败", f"无法切换数据源到: {new_path}\n\n设置未更改。"
                )