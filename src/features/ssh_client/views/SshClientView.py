# src/features/ssh_client/views/SshClientView.py
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                                QListWidget, QListWidgetItem, QStackedWidget,
                                QMessageBox, QLabel, QLineEdit, QFileDialog) # 导入 QLineEdit, QFileDialog
from PySide6.QtCore import Qt, Signal, QPoint
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QMenu

from .ConnectionDialog import ConnectionDialog
from .SessionWidget import SessionWidget
from ..models import SshConnectionModel

class SshClientView(QWidget):
   """
   SSH客户端的主视图，管理连接列表和会话显示。
   """
   addConnectionRequested = Signal()
   editConnectionRequested = Signal(str) # connection_id
   deleteConnectionRequested = Signal(str) # connection_id
   connectRequested = Signal(str) # connection_id
   disconnectRequested = Signal(str) # session_id
   sendCommandRequested = Signal(str, str) # session_id, command
   sendShellDataRequested = Signal(str, str) # session_id, data
   connectionSaved = Signal(SshConnectionModel) # 新增信号，用于转发ConnectionDialog的信号
   connectionsFilePathChanged = Signal(str) # 新增信号，用于通知配置文件路径改变

   def __init__(self, parent=None):
       super().__init__(parent)
       self.setWindowTitle("SSH客户端")
       self.connections = {} # {connection_id: SshConnectionModel}
       self.session_widgets = {} # {session_id: SessionWidget}

       self._init_ui()

   def _init_ui(self):
       main_layout = QHBoxLayout(self)
       main_layout.setContentsMargins(0, 0, 0, 0)
       main_layout.setSpacing(5)

       # 左侧连接列表区域
       left_panel_layout = QVBoxLayout()
       left_panel_layout.setContentsMargins(5, 5, 5, 5)
       left_panel_layout.setSpacing(5)

       self.connection_list_widget = QListWidget()
       self.connection_list_widget.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
       self.connection_list_widget.customContextMenuRequested.connect(self._on_connection_list_context_menu)
       self.connection_list_widget.itemDoubleClicked.connect(self._on_connection_double_clicked)
       left_panel_layout.addWidget(self.connection_list_widget)

       button_layout = QHBoxLayout()
       self.add_button = QPushButton("添加连接")
       self.add_button.clicked.connect(self.addConnectionRequested.emit)
       self.edit_button = QPushButton("编辑连接")
       self.edit_button.clicked.connect(self._on_edit_connection_clicked)
       self.delete_button = QPushButton("删除连接")
       self.delete_button.clicked.connect(self._on_delete_connection_clicked)
       
       button_layout.addWidget(self.add_button)
       button_layout.addWidget(self.edit_button)
       button_layout.addWidget(self.delete_button)
       left_panel_layout.addLayout(button_layout)

       # 配置文件路径设置区域
       file_path_layout = QHBoxLayout()
       file_path_layout.addWidget(QLabel("配置文件路径:"))
       self.file_path_line_edit = QLineEdit()
       self.file_path_line_edit.setReadOnly(True)
       file_path_layout.addWidget(self.file_path_line_edit)
       
       self.open_button = QPushButton("打开...")
       self.open_button.clicked.connect(self._on_open_file_path)
       file_path_layout.addWidget(self.open_button)

       self.save_as_button = QPushButton("另存为...")
       self.save_as_button.clicked.connect(self._on_save_file_path_as)
       file_path_layout.addWidget(self.save_as_button)
       
       left_panel_layout.addLayout(file_path_layout)

       main_layout.addLayout(left_panel_layout, 1) # 左侧面板占据1份空间

       # 右侧会话显示区域
       right_panel_layout = QVBoxLayout()
       right_panel_layout.setContentsMargins(5, 5, 5, 5)
       right_panel_layout.setSpacing(5)

       self.stacked_widget = QStackedWidget()
       self.empty_label = QLabel("选择一个连接或添加新连接以开始。")
       self.empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
       self.stacked_widget.addWidget(self.empty_label) # 索引0是空状态
       right_panel_layout.addWidget(self.stacked_widget)
       self.stacked_widget.setCurrentIndex(0)

       main_layout.addLayout(right_panel_layout, 3) # 右侧面板占据3份空间

   def update_connections(self, connections: dict):
       """
       更新连接列表显示。
       connections: {connection_id: SshConnectionModel}
       """
       self.connections = connections
       self.connection_list_widget.clear()
       for conn_id, conn_model in connections.items():
           item = QListWidgetItem(conn_model.name)
           item.setData(Qt.ItemDataRole.UserRole, conn_id) # 存储connection_id
           self.connection_list_widget.addItem(item)

   def show_connection_dialog(self, connection: SshConnectionModel = None):
       """
       显示添加/编辑连接对话框。
       """
       dialog = ConnectionDialog(connection, self)
       dialog.connectionSaved.connect(self.connectionSaved.emit) # 转发信号
       dialog.exec()

   def add_session_widget(self, session_id: str, connection_name: str):
       """
       添加一个新的会话窗口到堆叠布局。
       """
       if session_id in self.session_widgets:
           self.stacked_widget.setCurrentWidget(self.session_widgets[session_id])
           return

       session_widget = SessionWidget(session_id, connection_name, self)
       session_widget.commandEntered.connect(self.sendCommandRequested.emit)
       session_widget.shellDataEntered.connect(self.sendShellDataRequested.emit)
       session_widget.sessionClosed.connect(self.remove_session_widget) # 连接会话关闭信号
       
       self.session_widgets[session_id] = session_widget
       self.stacked_widget.addWidget(session_widget)
       self.stacked_widget.setCurrentWidget(session_widget)

   def remove_session_widget(self, session_id: str):
       """
       从堆叠布局中移除会话窗口。
       """
       if session_id in self.session_widgets:
           widget = self.session_widgets.pop(session_id)
           self.stacked_widget.removeWidget(widget)
           widget.deleteLater()
           if not self.session_widgets: # 如果没有活跃会话，显示空状态
               self.stacked_widget.setCurrentIndex(0)
           self.disconnectRequested.emit(session_id) # 通知控制器断开连接

   def append_session_output(self, session_id: str, output_bytes: bytes):
       """
       向指定会话的终端追加输出。
       """
       if session_id in self.session_widgets:
           self.session_widgets[session_id].append_output(output_bytes)

   def show_error_message(self, title: str, message: str):
       """
       显示错误消息框。
       """
       QMessageBox.critical(self, title, message)

   def _on_connection_double_clicked(self, item: QListWidgetItem):
       """
       双击连接列表项时尝试连接。
       """
       connection_id = item.data(Qt.ItemDataRole.UserRole)
       if connection_id:
           self.connectRequested.emit(connection_id)

   def _on_edit_connection_clicked(self):
       """
       点击编辑按钮时，打开编辑对话框。
       """
       selected_items = self.connection_list_widget.selectedItems()
       if not selected_items:
           QMessageBox.warning(self, "编辑连接", "请选择一个要编辑的连接。")
           return
       
       connection_id = selected_items[0].data(Qt.ItemDataRole.UserRole)
       if connection_id in self.connections:
           self.editConnectionRequested.emit(connection_id)

   def _on_delete_connection_clicked(self):
       """
       点击删除按钮时，删除选定的连接。
       """
       selected_items = self.connection_list_widget.selectedItems()
       if not selected_items:
           QMessageBox.warning(self, "删除连接", "请选择一个要删除的连接。")
           return
       
       connection_id = selected_items[0].data(Qt.ItemDataRole.UserRole)
       reply = QMessageBox.question(self, "删除确认", f"确定要删除连接 '{self.connections[connection_id].name}' 吗？",
                                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
       if reply == QMessageBox.StandardButton.Yes:
           self.deleteConnectionRequested.emit(connection_id)

   def _on_connection_list_context_menu(self, pos: QPoint):
       """
       连接列表的右键菜单。
       """
       item = self.connection_list_widget.itemAt(pos)
       menu = QMenu(self)
       
       add_action = menu.addAction("添加连接")
       add_action.triggered.connect(self.addConnectionRequested.emit)

       if item:
           edit_action = menu.addAction("编辑连接")
           edit_action.triggered.connect(self._on_edit_connection_clicked)
           delete_action = menu.addAction("删除连接")
           delete_action.triggered.connect(self._on_delete_connection_clicked)
           menu.addSeparator()
           connect_action = menu.addAction("连接")
           connect_action.triggered.connect(lambda: self.connectRequested.emit(item.data(Qt.ItemDataRole.UserRole)))
       
       menu.exec_(self.connection_list_widget.mapToGlobal(pos))

   def _on_open_file_path(self):
       """
       打开文件选择对话框，让用户选择一个已存在的SSH连接配置文件。
       """
       file_path, _ = QFileDialog.getOpenFileName(
           self,
           "打开SSH连接配置文件",
           self.file_path_line_edit.text(), # 默认显示当前路径
           "JSON Files (*.json);;All Files (*)"
       )
       if file_path:
           self.set_connections_file_path(file_path)
           self.connectionsFilePathChanged.emit(file_path)

   def _on_save_file_path_as(self):
       """
       打开文件选择对话框，让用户选择一个路径来另存为SSH连接配置文件。
       """
       file_path, _ = QFileDialog.getSaveFileName(
           self,
           "另存为SSH连接配置文件",
           self.file_path_line_edit.text(), # 默认显示当前路径
           "JSON Files (*.json);;All Files (*)"
       )
       if file_path:
           self.set_connections_file_path(file_path)
           self.connectionsFilePathChanged.emit(file_path)

   def set_connections_file_path(self, path: str):
       """
       设置配置文件路径显示。
       """
       self.file_path_line_edit.setText(path)