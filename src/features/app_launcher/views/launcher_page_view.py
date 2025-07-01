# desktop_center/src/features/app_launcher/views/launcher_page_view.py
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                               QLabel, QFileDialog, QLineEdit, QDialog, QDialogButtonBox,
                               QScrollArea, QGridLayout, QMenu, QFileIconProvider, QToolButton,
                               QGroupBox, QComboBox, QInputDialog, QMessageBox, QStyle)
from PySide6.QtCore import Signal, Qt, QSize, QFileInfo
from PySide6.QtGui import QIcon, QCursor, QAction
import os
import sys
from typing import List, Dict, Set, Tuple

class AddAppDialog(QDialog):
    def __init__(self, existing_groups: List[str], parent=None):
        super().__init__(parent)
        self.setWindowTitle("添加新应用")
        self.layout = QVBoxLayout(self)
        self.group_label = QLabel("分组:")
        self.group_combo = QComboBox()
        self.group_combo.setEditable(True)
        self.group_combo.addItems(existing_groups)
        self.layout.addWidget(self.group_label)
        self.layout.addWidget(self.group_combo)
        self.name_label = QLabel("应用名称:")
        self.name_input = QLineEdit()
        self.layout.addWidget(self.name_label)
        self.layout.addWidget(self.name_input)
        self.path_label = QLabel("应用路径:")
        path_layout = QHBoxLayout()
        self.path_input = QLineEdit()
        self.browse_button = QPushButton("浏览...")
        self.browse_button.clicked.connect(self.browse_file)
        path_layout.addWidget(self.path_input)
        path_layout.addWidget(self.browse_button)
        self.layout.addWidget(self.path_label)
        self.layout.addLayout(path_layout)
        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        self.layout.addWidget(self.button_box)
    def browse_file(self):
        file_filter = "Applications (*.exe)" if os.name == 'nt' else "Applications (*.app)" if sys.platform == 'darwin' else "All files (*)"
        file_path, _ = QFileDialog.getOpenFileName(self, "选择应用程序", "", file_filter)
        if file_path:
            self.path_input.setText(file_path)
            if not self.name_input.text():
                app_name = os.path.basename(file_path)
                app_name = os.path.splitext(app_name)[0]
                self.name_input.setText(app_name)
    def get_data(self): return self.group_combo.currentText(), self.name_input.text(), self.path_input.text()

class LauncherPageView(QWidget):
    """【重构】应用启动器插件的UI视图，增强分组管理和搜索。"""
    add_app_requested = Signal(str, str, str)
    remove_app_requested = Signal(str, int)
    launch_app_requested = Signal(str, int)
    move_app_requested = Signal(str, int, str)
    rename_group_requested = Signal(str, str)
    delete_group_requested = Signal(str)
    add_group_requested = Signal(str)
    search_text_changed = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.icon_provider = QFileIconProvider()
        self._groups: List[str] = []
        self.setup_ui()

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)
        top_layout = QHBoxLayout()
        title_label = QLabel("应用启动器")
        title_label.setStyleSheet("font-size: 22px; font-weight: bold; color: #333;")
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("搜索应用…")
        self.search_box.setClearButtonEnabled(True)
        self.search_box.setFixedWidth(250)
        self.search_box.textChanged.connect(self.search_text_changed)
        self.add_group_button = QPushButton("＋ 添加分组")
        self.add_group_button.clicked.connect(self.on_add_group)
        self.add_app_button = QPushButton("＋ 添加应用")
        self.add_app_button.clicked.connect(self.on_add_app_button_clicked)
        
        top_layout.addWidget(title_label)
        top_layout.addStretch()
        top_layout.addWidget(self.search_box)
        top_layout.addWidget(self.add_group_button)
        top_layout.addWidget(self.add_app_button)
        main_layout.addLayout(top_layout)
        
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet("QScrollArea { border: none; background-color: transparent; }")
        self.scroll_content_widget = QWidget()
        self.groups_layout = QVBoxLayout(self.scroll_content_widget)
        self.groups_layout.setSpacing(20)
        self.groups_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        scroll_area.setWidget(self.scroll_content_widget)
        main_layout.addWidget(scroll_area)
        
    def update_groups_view(self, apps_by_group: Dict[str, List[Dict[str, str]]], highlight_apps: Set[Tuple[str, int]] = None):
        """【重构】使用QGroupBox和右键菜单进行分组管理，并修复对齐问题。"""
        self._groups = sorted(list(apps_by_group.keys()))
        while (item := self.groups_layout.takeAt(0)) is not None:
            if item.widget(): item.widget().deleteLater()
        
        for group_name in self._groups:
            apps = apps_by_group.get(group_name, [])
            if not apps and highlight_apps is None: continue
            
            group_box = QGroupBox()
            grid_layout = QGridLayout(group_box)
            grid_layout.setSpacing(15)
            grid_layout.setContentsMargins(10, 10, 10, 10)
            
            group_title_label = QLabel(group_name, group_box)
            group_title_label.setStyleSheet("font-size: 16px; font-weight: bold; padding: 5px; margin-left: 5px;")
            group_title_label.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
            group_title_label.customContextMenuRequested.connect(lambda _, g=group_name: self._show_group_context_menu(g))
            
            grid_layout.addWidget(group_title_label, 0, 0, 1, 5) # 标题占满第一行

            has_visible_apps = False
            cols = 5
            visible_app_count = 0
            for i, app in enumerate(apps):
                is_highlighted = highlight_apps is not None and (group_name, i) in highlight_apps
                if highlight_apps is not None and not is_highlighted: continue
                has_visible_apps = True
                
                row, col = divmod(visible_app_count, cols)
                visible_app_count += 1
                
                button = QToolButton()
                button.setText(app['name'])
                button.setFixedSize(100, 100)
                file_info = QFileInfo(app['path'])
                icon = self.icon_provider.icon(file_info)
                if icon.isNull(): icon = QIcon.fromTheme("application-x-executable")
                button.setIcon(icon)
                button.setIconSize(QSize(48, 48))
                button.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextUnderIcon)
                button.setToolTip(app['path'])
                
                base_style = "QToolButton { border: 1px solid #ccc; border-radius: 8px; padding: 5px; } QToolButton:hover { background-color: #f0f0f0; }"
                highlight_style = "QToolButton { border: 2px solid #0078d4; border-radius: 8px; padding: 5px; background-color: #e6f2fa; }"
                button.setStyleSheet(highlight_style if is_highlighted else base_style)
                
                button.clicked.connect(lambda _, g=group_name, idx=i: self.launch_app_requested.emit(g, idx))
                button.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
                button.customContextMenuRequested.connect(lambda _, g=group_name, idx=i: self._show_app_context_menu(g, idx))
                
                grid_layout.addWidget(button, row + 1, col) # 【修复】应用从第二行开始放

            # 【修复】添加一个可伸展的列，将所有内容推到左边
            grid_layout.setColumnStretch(cols, 1)

            if has_visible_apps or (highlight_apps is None and not apps):
                self.groups_layout.addWidget(group_box)
            else:
                group_box.deleteLater()

    def on_add_app_button_clicked(self):
        dialog = AddAppDialog(self._groups, self)
        if dialog.exec():
            group, name, path = dialog.get_data()
            if name and path: self.add_app_requested.emit(group, name, path)

    def on_add_group(self):
        group_name, ok = QInputDialog.getText(self, "添加新分组", "请输入新分组的名称:")
        if ok and group_name.strip(): self.add_group_requested.emit(group_name)

    def on_rename_group(self, old_name: str):
        new_name, ok = QInputDialog.getText(self, "重命名分组", f"为分组 '{old_name}' 输入新名称:", QLineEdit.Normal, old_name)
        if ok and new_name.strip() and new_name != old_name: self.rename_group_requested.emit(old_name, new_name)

    def on_delete_group(self, group_name: str):
        reply = QMessageBox.warning(self, "确认删除", f"您确定要删除分组 '{group_name}' 吗？\n该分组内的所有应用将被移动到“默认分组”。", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes: self.delete_group_requested.emit(group_name)
        
    def _show_group_context_menu(self, group_name: str):
        """【优化】处理分组标题的右键菜单，为默认分组提供禁用反馈。"""
        context_menu = QMenu(self)
        
        if group_name == "默认分组":
            info_action = context_menu.addAction("（默认分组不可修改）")
            info_action.setEnabled(False)
        else:
            rename_action = context_menu.addAction("重命名分组")
            delete_action = context_menu.addAction("删除分组")
            rename_action.triggered.connect(lambda: self.on_rename_group(group_name))
            delete_action.triggered.connect(lambda: self.on_delete_group(group_name))
        
        context_menu.exec(QCursor.pos())

    def _show_app_context_menu(self, group_name: str, index: int):
        context_menu = QMenu(self)
        move_menu = context_menu.addMenu("移动到分组")
        has_other_groups = False
        for other_group in self._groups:
            if other_group != group_name:
                has_other_groups = True
                action = QAction(other_group, self)
                action.triggered.connect(lambda _, g_from=group_name, idx=index, g_to=other_group: self.move_app_requested.emit(g_from, idx, g_to))
                move_menu.addAction(action)
        move_menu.setEnabled(has_other_groups)
        context_menu.addSeparator()
        delete_action = context_menu.addAction("删除此应用")
        delete_action.triggered.connect(lambda _, g=group_name, idx=index: self.remove_app_requested.emit(g, idx))
        context_menu.exec(QCursor.pos())