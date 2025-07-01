# desktop_center/src/features/app_launcher/controllers/launcher_controller.py
from PySide6.QtCore import QObject, QProcess
from src.core.context import ApplicationContext
from src.features.app_launcher.models.launcher_model import LauncherModel
from src.features.app_launcher.views.launcher_page_view import LauncherPageView

class LauncherController(QObject):
    """【重构】控制器实现所有新的、用户驱动的业务逻辑。"""
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
        self.view.delete_group_requested.connect(self.handle_delete_group_request) # 【变更】连接到新的处理器
        self.view.add_group_requested.connect(self.add_group)

    def refresh_view(self):
        all_data = self.model.get_all_data()
        app_count = self.model.get_total_app_count()
        group_app_counts = {gid: self.model.get_group_app_count(gid) for gid in all_data.get('groups', {})}
        self.view.update_view(all_data, app_count, group_app_counts)

    def add_app(self, group_id: str, group_input: str, name: str, path: str):
        final_group_id = group_id
        if not final_group_id and group_input:
            final_group_id = self.model.create_group(group_input)
        
        self.model.add_app(final_group_id, name, path)
        self.refresh_view()

    def add_group(self, group_name: str):
        self.model.create_group(group_name)
        self.refresh_view()

    def handle_delete_group_request(self, group_id: str):
        """【新增】核心业务逻辑处理器，根据上下文决定如何删除。"""
        group_app_count = self.model.get_group_app_count(group_id)
        total_group_count = len(self.model.get_all_data().get('groups', {}))

        if group_app_count == 0: # 如果分组为空，直接删除
            self.model.delete_group_and_apps(group_id)
            self.refresh_view()
            return
        
        # 场景1：多分组存在
        if total_group_count > 1:
            choice = self.view.show_delete_multi_group_dialog(group_id)
            if choice == "delete_all":
                self.model.delete_group_and_apps(group_id)
            elif choice: # choice是目标分组ID
                self.model.move_apps(group_id, choice)
                self.model.delete_empty_group(group_id)
                self.model.save_apps()
        # 场景2：只剩一个分组
        else:
            choice = self.view.show_delete_last_group_dialog()
            if choice == "delete_all":
                self.model.delete_group_and_apps(group_id)
        
        self.refresh_view()

    def remove_app(self, group_id: str, index: int): self.model.remove_app(group_id, index); self.refresh_view()
    def move_app(self, from_gid: str, from_idx: int, to_gid: str): self.model.move_app(from_gid, from_idx, to_gid); self.refresh_view()
    def rename_group(self, group_id: str, new_name: str): self.model.rename_group(group_id, new_name); self.refresh_view()
    def delete_group(self, group_id: str): self.model.delete_group_and_apps(group_id); self.refresh_view()
    def launch_app(self, group_id: str, index: int):
        all_apps = self.model.get_all_data().get('apps', {}); apps_in_group = all_apps.get(group_id, [])
        if 0 <= index < len(apps_in_group):
            app_path = apps_in_group[index]['path']
            if app_path and os.path.exists(app_path): QProcess.startDetached(f'"{app_path}"', [])
            else: self.context.notification_service.show(title="启动失败", message=f"无法找到路径:\n{app_path}")