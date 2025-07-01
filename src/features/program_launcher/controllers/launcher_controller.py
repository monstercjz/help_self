# desktop_center/src/features/program_launcher/controllers/launcher_controller.py
import logging
import os
import subprocess
import sys
from PySide6.QtWidgets import QFileDialog, QMessageBox
from PySide6.QtCore import QObject

from ..models.launcher_model import LauncherModel
from ..views.launcher_page_view import LauncherPageView
from ..widgets.group_dialog import GroupDialog
from ..widgets.delete_group_dialog import DeleteGroupDialog
from src.core.context import ApplicationContext

class LauncherController(QObject):
    """
    程序启动器功能的控制器，负责连接视图和模型。
    """
    def __init__(self, model: LauncherModel, view: LauncherPageView, context: ApplicationContext, parent=None):
        super().__init__(parent)
        self.model = model
        self.view = view
        self.context = context

        self._connect_signals()
        self.refresh_view()

    def _connect_signals(self):
        """连接所有视图和模型的信号。"""
        # --- View -> Controller ---
        self.view.add_group_requested.connect(self.add_group)
        self.view.add_program_requested.connect(self.add_program)
        self.view.item_double_clicked.connect(self.launch_program)
        self.view.edit_item_requested.connect(self.edit_item)
        self.view.delete_item_requested.connect(self.delete_item)
        self.view.search_text_changed.connect(self.filter_view)
        self.view.group_order_changed.connect(self.model.reorder_groups)
        self.view.program_order_changed.connect(self.model.reorder_programs)

        # --- Model -> Controller ---
        self.model.data_changed.connect(self.refresh_view)

    def refresh_view(self):
        """使用模型的数据刷新视图。"""
        groups = self.model.get_all_data()
        self.view.rebuild_ui(groups)
        # 刷新后重新应用搜索过滤器
        self.filter_view(self.view.search_bar.text())

    def add_group(self):
        """处理添加新分组的请求。"""
        dialog = GroupDialog(self.view)
        if dialog.exec():
            group_name = dialog.get_group_name()
            if group_name:
                self.model.add_group(group_name)
                logging.info(f"新增分组: {group_name}")

    def add_program(self, group_id: str):
        """处理添加新程序的请求。"""
        if not group_id:
            # 边缘情况：如果没有分组，先提示创建分组
            if not self.model.get_all_data():
                 # 自动创建一个默认分组
                default_group_name = "默认分组"
                group_id = self.model.add_group(default_group_name)
                logging.info("无可用分组，已自动创建'默认分组'")
            else:
                QMessageBox.warning(self.view, "操作失败", "请先选择一个分组。")
                return

        file_path, _ = QFileDialog.getOpenFileName(
            self.view,
            "选择一个可执行文件",
            "",
            "可执行文件 (*.exe);;所有文件 (*)"
        )

        if file_path:
            program_name = os.path.splitext(os.path.basename(file_path))[0]
            self.model.add_program(group_id, program_name, file_path)
            logging.info(f"向分组 {group_id} 添加新程序: {program_name}")

    def launch_program(self, program_id: str):
        """处理启动程序的请求。"""
        program = self.model.get_program_by_id(program_id)
        if program and os.path.exists(program['path']):
            try:
                # 使用 subprocess.Popen 在新进程中启动，不阻塞UI
                subprocess.Popen(program['path'])
                logging.info(f"正在启动程序: {program['name']} ({program['path']})")
                self.context.notification_service.show(
                    title="程序已启动",
                    message=f"{program['name']} 正在启动。"
                )
            except Exception as e:
                logging.error(f"启动程序 {program['path']} 失败: {e}")
                QMessageBox.critical(self.view, "启动失败", f"无法启动程序：\n{program['path']}\n\n错误: {e}")
        else:
            logging.warning(f"尝试启动的程序不存在或信息有误: ID={program_id}")
            QMessageBox.warning(self.view, "启动失败", "程序路径不存在或已被移动，请编辑或删除此条目。")
    
    def edit_item(self, item_id: str, item_type: str):
        """处理编辑分组或程序的请求。"""
        if item_type == 'group':
            group = self.model.get_group_by_id(item_id)
            if not group: return
            
            dialog = GroupDialog(self.view, current_name=group['name'])
            if dialog.exec():
                new_name = dialog.get_group_name()
                if new_name and new_name != group['name']:
                    self.model.edit_group(item_id, new_name)
                    logging.info(f"分组 '{group['name']}' 已重命名为 '{new_name}'")

        elif item_type == 'program':
            # 当前版本编辑程序主要是移动分组，未来可扩展
            QMessageBox.information(self.view, "提示", "要移动程序，请直接将其拖拽到目标分组。")

    def delete_item(self, item_id: str, item_type: str):
        """处理删除分组或程序的请求。"""
        if item_type == 'group':
            self._handle_delete_group(item_id)
        elif item_type == 'program':
            program = self.model.get_program_by_id(item_id)
            if not program: return
            
            reply = QMessageBox.question(self.view, "确认删除", f"您确定要删除程序 '{program['name']}' 吗？",
                                         QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                         QMessageBox.StandardButton.No)
            if reply == QMessageBox.StandardButton.Yes:
                self.model.delete_program(item_id)
                logging.info(f"程序已删除: {program['name']} (ID: {item_id})")

    def _handle_delete_group(self, group_id: str):
        """专门处理删除分组的复杂逻辑。"""
        group = self.model.get_group_by_id(group_id)
        if not group: return

        other_groups = self.model.get_other_groups(group_id)
        programs_in_group = self.model.get_programs_in_group(group_id)

        if not programs_in_group:
            # 如果分组为空，直接删除
            reply = QMessageBox.question(self.view, "确认删除", f"您确定要删除空分组 '{group['name']}' 吗？",
                                         QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                         QMessageBox.StandardButton.No)
            if reply == QMessageBox.StandardButton.Yes:
                self.model.delete_group(group_id)
                logging.info(f"空分组已删除: {group['name']}")
            return

        dialog = DeleteGroupDialog(group['name'], other_groups, self.view)
        if dialog.exec():
            choice, target_group_id = dialog.get_result()
            
            if choice == 'move':
                if not target_group_id and not other_groups:
                    # 边缘情况：没有其他分组可选，自动创建默认分组
                    target_group_id = self.model.add_group("默认分组")
                    logging.info("删除分组时无其他分组可选，已自动创建'默认分组'用于转移程序。")
                
                self.model.move_programs_to_group(group_id, target_group_id)
                self.model.delete_group(group_id)
                logging.info(f"分组 '{group['name']}' 已删除，其程序已移至分组ID: {target_group_id}")

            elif choice == 'delete_all':
                self.model.delete_group(group_id, delete_programs=True)
                logging.info(f"分组 '{group['name']}' 及其所有程序均已删除。")

    def filter_view(self, text: str):
        """根据搜索文本过滤视图中的项目。"""
        self.view.filter_items(text)