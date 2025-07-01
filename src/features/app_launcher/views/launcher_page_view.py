# desktop_center/src/features/app_launcher/views/launcher_page_view.py
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                               QLabel, QFileDialog, QLineEdit, QDialog, QDialogButtonBox,
                               QScrollArea, QGridLayout, QMenu, QFileIconProvider, QToolButton,
                               QGroupBox, QComboBox, QInputDialog, QMessageBox, QStyle)
from PySide6.QtCore import Signal, Qt, QSize, QFileInfo
from PySide6.QtGui import QIcon, QCursor, QAction
import os
from typing import Dict, Any, Optional

class AddAppDialog(QDialog):
    def __init__(self, groups_map: Dict[str, str], parent=None):
        super().__init__(parent)
        self.setWindowTitle("添加新应用"); self.layout = QVBoxLayout(self)
        self.group_combo = QComboBox(); self.group_combo.setEditable(True)
        for group_id, name in groups_map.items(): self.group_combo.addItem(name, userData=group_id)
        self.layout.addWidget(QLabel("分组:")); self.layout.addWidget(self.group_combo)
        self.name_input=QLineEdit(); self.path_input=QLineEdit(); self.browse_button=QPushButton("浏览...")
        self.browse_button.clicked.connect(self.browse_file)
        path_layout=QHBoxLayout(); path_layout.addWidget(self.path_input); path_layout.addWidget(self.browse_button)
        self.layout.addWidget(QLabel("应用名称:")); self.layout.addWidget(self.name_input)
        self.layout.addWidget(QLabel("应用路径:")); self.layout.addLayout(path_layout)
        self.button_box=QDialogButtonBox(QDialogButtonBox.Ok|QDialogButtonBox.Cancel); self.button_box.accepted.connect(self.accept); self.button_box.rejected.connect(self.reject)
        self.layout.addWidget(self.button_box)
    def browse_file(self):
        file_path,_ = QFileDialog.getOpenFileName(self,"选择应用程序","");
        if file_path: self.path_input.setText(file_path); self.name_input.setText(os.path.splitext(os.path.basename(file_path))[0])
    def get_data(self):
        idx = self.group_combo.currentIndex(); group_id = self.group_combo.itemData(idx) if idx != -1 else None
        return group_id, self.group_combo.currentText(), self.name_input.text(), self.path_input.text()

class LauncherPageView(QWidget):
    """【重构】实现完全动态和用户驱动的分组管理界面。"""
    add_app_requested = Signal(str, str, str, str)
    remove_app_requested = Signal(str, int)
    launch_app_requested = Signal(str, int)
    move_app_requested = Signal(str, int, str)
    rename_group_requested = Signal(str, str)
    delete_group_requested = Signal(str)
    add_group_requested = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.icon_provider = QFileIconProvider()
        self._groups_map: Dict[str, str] = {}
        self._total_app_count = 0
        self.setup_ui()

    def setup_ui(self):
        main_layout=QVBoxLayout(self);main_layout.setContentsMargins(20,20,20,20);main_layout.setSpacing(15)
        top_layout=QHBoxLayout();title_label=QLabel("应用启动器");title_label.setStyleSheet("font-size:22px;font-weight:bold;color:#333;")
        self.search_box=QLineEdit();self.search_box.setPlaceholderText("搜索应用…");self.search_box.setClearButtonEnabled(True);self.search_box.setFixedWidth(250)
        self.add_group_button=QPushButton("＋ 添加分组");self.add_group_button.clicked.connect(self.on_add_group)
        self.add_app_button=QPushButton("＋ 添加应用");self.add_app_button.clicked.connect(self.on_add_app_button_clicked)
        top_layout.addWidget(title_label);top_layout.addStretch();top_layout.addWidget(self.search_box)
        top_layout.addWidget(self.add_group_button);top_layout.addWidget(self.add_app_button)
        main_layout.addLayout(top_layout)
        scroll_area=QScrollArea();scroll_area.setWidgetResizable(True);scroll_area.setStyleSheet("QScrollArea{border:none;background:transparent;}")
        self.scroll_content_widget=QWidget();self.groups_layout=QVBoxLayout(self.scroll_content_widget)
        self.groups_layout.setSpacing(20);self.groups_layout.setAlignment(Qt.AlignTop)
        scroll_area.setWidget(self.scroll_content_widget);main_layout.addWidget(scroll_area)

    def update_view(self, data: Dict[str, Any], total_app_count: int, group_app_counts: Dict[str, int]):
        self._groups_map = {gid: ginfo['name'] for gid, ginfo in data.get('groups', {}).items()}
        self._total_app_count = total_app_count
        self._group_app_counts = group_app_counts
        
        while (item := self.groups_layout.takeAt(0)) is not None:
            if item.widget(): item.widget().deleteLater()

        # 【修复】直接迭代从控制器传入的完整数据，而不是本地缓存
        for group_id, group_info in data.get('groups', {}).items():
            group_box = QGroupBox()
            grid_layout = QGridLayout(group_box); grid_layout.setSpacing(15); grid_layout.setContentsMargins(10, 10, 10, 10)
            
            group_name = group_info['name']
            group_title_label = QLabel(group_name, group_box); group_title_label.setStyleSheet("font-size:16px;font-weight:bold;padding:5px;margin-left:5px;")
            group_title_label.setContextMenuPolicy(Qt.CustomContextMenu); group_title_label.customContextMenuRequested.connect(lambda _, gid=group_id: self._show_group_context_menu(gid))
            grid_layout.addWidget(group_title_label, 0, 0, 1, 5)

            apps = data.get('apps', {}).get(group_id, [])
            for i, app in enumerate(apps):
                row, col = divmod(i, 5)
                button = QToolButton(); button.setFixedSize(100, 100); button.setText(app['name']); button.setToolTip(app['path'])
                button.setIcon(self.icon_provider.icon(QFileInfo(app['path']))); button.setIconSize(QSize(48, 48))
                button.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
                button.setStyleSheet("QToolButton{border:1px solid #ccc;border-radius:8px;padding:5px} QToolButton:hover{background-color:#f0f0f0}")
                button.clicked.connect(lambda _, gid=group_id, idx=i: self.launch_app_requested.emit(gid, idx))
                button.setContextMenuPolicy(Qt.CustomContextMenu)
                button.customContextMenuRequested.connect(lambda _, gid=group_id, idx=i: self._show_app_context_menu(gid, idx))
                grid_layout.addWidget(button, row + 1, col)
            
            grid_layout.setColumnStretch(5, 1)
            self.groups_layout.addWidget(group_box)

    def on_add_app_button_clicked(self):
        dialog = AddAppDialog(self._groups_map, self)
        if dialog.exec():
            group_id, group_input, name, path = dialog.get_data()
            if name and path: self.add_app_requested.emit(group_id, group_input, name, path)

    def on_add_group(self):
        group_name, ok = QInputDialog.getText(self, "添加新分组", "请输入新分组的名称:")
        if ok and group_name.strip(): self.add_group_requested.emit(group_name)

    def _show_group_context_menu(self, group_id: str):
        context_menu = QMenu(self)
        rename_action = context_menu.addAction("重命名分组")
        delete_action = context_menu.addAction("删除分组")
        
        can_delete = len(self._groups_map) > 1 or self._total_app_count == 0
        delete_action.setEnabled(can_delete)
        delete_action.setToolTip("只有一个分组且其中有应用时不可删除" if not can_delete else "")
        
        rename_action.triggered.connect(lambda: self._rename_group_dialog(group_id))
        delete_action.triggered.connect(lambda: self.delete_group_requested.emit(group_id))
        context_menu.exec(QCursor.pos())

    def _rename_group_dialog(self, group_id: str):
        old_name = self._groups_map.get(group_id, "")
        new_name, ok = QInputDialog.getText(self, "重命名分组", "输入新名称:", text=old_name)
        if ok and new_name.strip() and new_name != old_name: self.rename_group_requested.emit(group_id, new_name)

    def show_delete_multi_group_dialog(self, group_id_to_delete: str) -> Optional[str]:
        group_name = self._groups_map[group_id_to_delete]
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("确认删除分组"); msg_box.setText(f"如何处理分组 '{group_name}' 内的应用？")
        msg_box.setInformativeText("您可以将它们移动到另一个分组，或将它们一起删除。"); msg_box.setIcon(QMessageBox.Warning)
        move_button = msg_box.addButton("移动到...", QMessageBox.ActionRole)
        delete_all_button = msg_box.addButton("全部删除", QMessageBox.DestructiveRole)
        msg_box.addButton("取消", QMessageBox.RejectRole)
        msg_box.exec()
        if msg_box.clickedButton() == delete_all_button: return "delete_all"
        if msg_box.clickedButton() == move_button:
            other_groups = {gid: name for gid, name in self._groups_map.items() if gid != group_id_to_delete}
            target_group_name, ok = QInputDialog.getItem(self, "选择目标分组", "请选择要移入的分组:", list(other_groups.values()), 0, False)
            if ok and target_group_name:
                for gid, name in other_groups.items():
                    if name == target_group_name: return gid
        return None

    def show_delete_last_group_dialog(self) -> Optional[str]:
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("警告：这是最后一个分组"); msg_box.setText("删除此分组将同时删除其内所有应用。")
        msg_box.setInformativeText("您确定要继续吗？"); msg_box.setIcon(QMessageBox.Critical)
        delete_all_button = msg_box.addButton("删除所有应用和分组", QMessageBox.DestructiveRole)
        msg_box.addButton("取消", QMessageBox.RejectRole)
        msg_box.exec()
        if msg_box.clickedButton() == delete_all_button: return "delete_all"
        return None

    def _show_app_context_menu(self, group_id: str, index: int):
        context_menu=QMenu(self); move_menu=context_menu.addMenu("移动到分组")
        other_groups={gid:name for gid,name in self._groups_map.items() if gid!=group_id}
        move_menu.setEnabled(bool(other_groups))
        for other_gid,other_gname in other_groups.items():
            action=QAction(other_gname,self); action.triggered.connect(lambda _,g_from=group_id,idx=index,g_to=other_gid: self.move_app_requested.emit(g_from,idx,g_to))
            move_menu.addAction(action)
        context_menu.addSeparator(); delete_action=context_menu.addAction("删除此应用")
        delete_action.triggered.connect(lambda _,g=group_id,idx=index: self.remove_app_requested.emit(g,idx))
        context_menu.exec(QCursor.pos())