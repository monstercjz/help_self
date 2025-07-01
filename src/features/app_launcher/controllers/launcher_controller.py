# desktop_center/src/features/app_launcher/controllers/launcher_controller.py
import logging
import os
import sys
from PySide6.QtCore import QObject, QProcess
from typing import Set, Tuple

from src.core.context import ApplicationContext
from src.features.app_launcher.models.launcher_model import LauncherModel
from src.features.app_launcher.views.launcher_page_view import LauncherPageView

class LauncherController(QObject):
    """【重构】应用启动器插件的控制器，增加分组管理和搜索逻辑。"""
    def __init__(self, model: LauncherModel, view: LauncherPageView, context: ApplicationContext, parent=None):
        super().__init__(parent)
        self.model = model
        self.view = view
        self.context = context
        self._connect_signals()
        self.refresh_view()

    def _connect_signals(self):
        self.view.add_app_requested.connect(self.add_app)
        self.view.remove_app_requested.connect(self.remove_app)
        self.view.launch_app_requested.connect(self.launch_app)
        self.view.move_app_requested.connect(self.move_app)
        self.view.rename_group_requested.connect(self.rename_group)
        self.view.delete_group_requested.connect(self.delete_group)
        self.view.add_group_requested.connect(self.add_group) # 【新增】
        self.view.search_text_changed.connect(self.on_search_text_changed)

    def refresh_view(self, highlight_apps: Set[Tuple[str, int]] = None):
        apps_by_group = self.model.get_apps_by_group()
        self.view.update_groups_view(apps_by_group, highlight_apps)

    def add_app(self, group: str, name: str, path: str):
        self.model.add_app(group, name, path)
        self.refresh_view()

    def add_group(self, group_name: str):
        """【新增】处理添加新分组的逻辑。"""
        if self.model.create_empty_group(group_name):
            self.refresh_view()

    def remove_app(self, group: str, index: int):
        self.model.remove_app(group, index)
        self.refresh_view()
        
    def move_app(self, from_group: str, from_index: int, to_group: str):
        self.model.move_app(from_group, from_index, to_group)
        self.refresh_view()

    def rename_group(self, old_name: str, new_name: str):
        if self.model.rename_group(old_name, new_name):
            self.refresh_view()

    def delete_group(self, group_name: str):
        self.model.delete_group(group_name)
        self.refresh_view()

    def on_search_text_changed(self, text: str):
        search_text = text.strip().lower()
        if not search_text:
            self.refresh_view()
            return
            
        highlight_apps: Set[Tuple[str, int]] = set()
        all_apps = self.model.get_apps_by_group()
        for group_name, apps in all_apps.items():
            for i, app in enumerate(apps):
                if search_text in app['name'].lower():
                    highlight_apps.add((group_name, i))
        
        self.refresh_view(highlight_apps)

    def launch_app(self, group: str, index: int):
        apps_in_group = self.model.get_apps_by_group().get(group, [])
        if 0 <= index < len(apps_in_group):
            app_path = apps_in_group[index]['path']
            if app_path and os.path.exists(app_path):
                logging.info(f"正在尝试启动应用: {app_path}")
                if sys.platform == "darwin" and app_path.endswith(".app"):
                    QProcess.startDetached('open', [app_path])
                else:
                    QProcess.startDetached(f'"{app_path}"', [])
            else:
                logging.error(f"无法启动应用：路径 '{app_path}' 无效或文件不存在。")
                self.context.notification_service.show(
                    title="启动失败", message=f"无法找到应用程序路径:\n{app_path}"
                )