# src/features/ssh_client/controllers/SshClientController.py
import uuid
import logging
import json # 新增导入json模块
from PySide6.QtCore import QObject, Signal, QThread

from ..models import SshConnectionModel
from ..views import SshClientView
from ..services import SshService
from src.core.context import ApplicationContext # 修正导入名称

class SshClientController(QObject):
    """
    SSH客户端的控制器，负责连接视图、模型和服务。
    管理SSH连接的增删改查，以及会话的生命周期。
    """
    # 信号：通知视图更新连接列表
    updateConnectionsView = Signal(dict)
    # 信号：通知视图添加新的会话窗口
    addSessionWidget = Signal(str, str) # session_id, connection_name
    # 信号：通知视图移除会话窗口
    removeSessionWidget = Signal(str) # session_id
    # 信号：通知视图向指定会话追加输出
    appendSessionOutput = Signal(str, bytes) # session_id, output_bytes
    # 信号：通知视图显示错误消息
    showErrorMessage = Signal(str, str) # title, message

    def __init__(self, view: SshClientView, ssh_service: SshService, context: ApplicationContext, parent=None): # 修正类型提示
        super().__init__(parent)
        self.view = view
        self.ssh_service = ssh_service
        self.context = context
        self.connections = {} # {connection_id: SshConnectionModel}
        self.active_sessions = {} # {session_id: connection_id}
        self.connection_threads = {} # {session_id: SshConnectionThread} 存储活跃的连接线程
        self.logger = logging.getLogger(self.__class__.__name__)

        self._connect_signals()
        self._load_connections()

    def _connect_signals(self):
        """连接视图和服务的信号到控制器槽函数。"""
        # 视图信号
        self.view.addConnectionRequested.connect(self._on_add_connection_requested)
        self.view.editConnectionRequested.connect(self._on_edit_connection_requested)
        self.view.deleteConnectionRequested.connect(self._on_delete_connection_requested)
        self.view.connectionSaved.connect(self._on_connection_saved)
        self.view.connectRequested.connect(self._on_connect_requested)
        self.view.disconnectRequested.connect(self._on_disconnect_requested)
        self.view.sendCommandRequested.connect(self._on_send_command_requested)
        self.view.sendShellDataRequested.connect(self._on_send_shell_data_requested)

        # 服务信号
        self.ssh_service.connected.connect(self._on_ssh_connected)
        self.ssh_service.connectionFailed.connect(self._on_ssh_connection_failed)
        self.ssh_service.outputReceived.connect(self._on_ssh_output_received)
        self.ssh_service.commandExecuted.connect(self._on_ssh_command_executed)
        self.ssh_service.sessionClosed.connect(self._on_ssh_session_closed)
        self.ssh_service.sftpProgress.connect(self._on_sftp_progress)
        self.ssh_service.sftpFinished.connect(self._on_sftp_finished)
        self.ssh_service.sftpFailed.connect(self._on_sftp_failed)

        # 控制器自身信号
        self.updateConnectionsView.connect(self.view.update_connections)
        self.addSessionWidget.connect(self.view.add_session_widget)
        self.removeSessionWidget.connect(self.view.remove_session_widget)
        self.appendSessionOutput.connect(self.view.append_session_output)
        self.showErrorMessage.connect(self.view.show_error_message)

    def _load_connections(self):
        """从配置服务加载所有SSH连接。"""
        # 使用ConfigService的通用方法读取JSON字符串
        connections_json = self.context.config_service.get_value("ssh_client", "connections", "{}")
        try:
            connections_data = json.loads(connections_json) # 移除内部导入
        except json.JSONDecodeError:
            self.logger.error("加载SSH连接配置时JSON解析失败，使用空配置。")
            connections_data = {}

        for conn_id, data in connections_data.items():
            connection = SshConnectionModel.from_dict(data)
            self.connections[conn_id] = connection
        self.updateConnectionsView.emit(self.connections)
        self.logger.info(f"加载了 {len(self.connections)} 个SSH连接。")

    def _save_connections(self):
        """将所有SSH连接保存到配置服务。"""
        connections_data = {conn_id: conn.to_dict() for conn_id, conn in self.connections.items()}
        # 将字典序列化为JSON字符串并保存
        connections_json = json.dumps(connections_data)
        self.context.config_service.set_option("ssh_client", "connections", connections_json)
        self.context.config_service.save_config() # 确保配置被写入文件
        self.logger.info(f"保存了 {len(self.connections)} 个SSH连接。")

    def _on_add_connection_requested(self):
        """处理添加连接请求。"""
        self.view.show_connection_dialog()

    def _on_edit_connection_requested(self, connection_id: str):
        """处理编辑连接请求。"""
        if connection_id in self.connections:
            self.view.show_connection_dialog(self.connections[connection_id])
        else:
            self.showErrorMessage.emit("错误", "未找到要编辑的连接。")

    def _on_delete_connection_requested(self, connection_id: str):
        """处理删除连接请求。"""
        if connection_id in self.connections:
            del self.connections[connection_id]
            self._save_connections()
            self.updateConnectionsView.emit(self.connections)
            self.logger.info(f"连接 {connection_id} 已删除。")
        else:
            self.showErrorMessage.emit("错误", "未找到要删除的连接。")

    def _on_connection_saved(self, connection: SshConnectionModel):
        """处理连接保存信号。"""
        if not connection.id:
            connection._id = str(uuid.uuid4()) # 为新连接生成ID
            self.logger.info(f"新连接已保存，ID: {connection.id}")
        else:
            self.logger.info(f"连接 {connection.id} 已更新。")
        self.connections[connection.id] = connection
        self._save_connections()
        self.updateConnectionsView.emit(self.connections)

    def _on_connect_requested(self, connection_id: str):
        """处理连接请求。"""
        if connection_id not in self.connections:
            self.showErrorMessage.emit("错误", "未找到指定的连接配置。")
            return
        
        connection = self.connections[connection_id]
        session_id = str(uuid.uuid4()) # 为新会话生成ID
        self.active_sessions[session_id] = connection_id
        self.addSessionWidget.emit(session_id, connection.name)
        self.logger.info(f"尝试连接到 {connection.name} (会话ID: {session_id})")

        # 在单独的线程中执行SSH连接操作，避免阻塞UI
        thread = SshConnectionThread(self.ssh_service, session_id, connection)
        thread.finished.connect(lambda: self._on_connection_thread_finished(session_id)) # 连接finished信号
        self.connection_threads[session_id] = thread # 存储线程引用
        thread.start() # 启动线程，连接结果将通过ssh_service的信号发出

    def _on_disconnect_requested(self, session_id: str):
        """处理断开连接请求。"""
        # 确保会话ID存在于active_sessions中，避免KeyError
        if session_id in self.active_sessions:
            self.ssh_service.close_session(session_id)
            del self.active_sessions[session_id]
            self.logger.info(f"会话 {session_id} 已从活动会话列表中移除。")
        else:
            self.logger.warning(f"尝试断开不存在的会话: {session_id}")

        # 无论active_sessions中是否存在，都尝试清理连接线程
        # 因为可能存在会话已关闭但线程未清理的情况
        self._cleanup_connection_thread(session_id)

    def _on_send_command_requested(self, session_id: str, command: str):
        """处理发送命令请求（非交互式）。"""
        if session_id in self.active_sessions:
            self.ssh_service.execute_command(session_id, command)
        else:
            self.appendSessionOutput.emit(session_id, "错误: 会话未激活或已断开。")

    def _on_send_shell_data_requested(self, session_id: str, data: str):
        """处理发送Shell数据请求（交互式）。"""
        if session_id in self.active_sessions:
            self.ssh_service.send_shell_data(session_id, data)
        else:
            self.appendSessionOutput.emit(session_id, "错误: 会话未激活或已断开。")

    # --- SSH服务信号槽函数 ---
    def _on_ssh_connected(self, session_id: str):
        """SSH连接成功。"""
        self.appendSessionOutput.emit(session_id, f"成功连接到SSH服务器。\n".encode('utf-8')) # 编码为字节
        # 连接成功后，立即打开交互式shell
        self.ssh_service.open_shell(session_id)

    def _on_ssh_connection_failed(self, session_id: str, error_message: str):
        """SSH连接失败。"""
        self.showErrorMessage.emit("SSH连接失败", error_message)
        self.removeSessionWidget.emit(session_id) # 移除会话窗口
        self._cleanup_connection_thread(session_id) # 清理连接线程

    def _on_connection_thread_finished(self, session_id: str):
        """连接线程完成时的清理槽函数。"""
        self.logger.info(f"连接线程 {session_id} 已完成。")
        self._cleanup_connection_thread(session_id)

    def _cleanup_connection_thread(self, session_id: str):
        """清理连接线程的引用。"""
        if session_id in self.connection_threads:
            thread = self.connection_threads.pop(session_id)
            # 确保线程已经退出，避免QThread: Destroyed while thread is still running
            if thread.isRunning():
                thread.quit()
                thread.wait(1000) # 等待线程结束，最多1秒
            thread.deleteLater() # 标记为稍后删除
            self.logger.info(f"连接线程 {session_id} 已清理。")

    def _on_ssh_output_received(self, session_id: str, output_bytes: bytes):
        """收到SSH输出。"""
        self.appendSessionOutput.emit(session_id, output_bytes)

    def _on_ssh_command_executed(self, session_id: str, exit_status: int):
        """命令执行完成。"""
        self.appendSessionOutput.emit(session_id, f"\n命令执行完成，退出状态: {exit_status}\n")

    def _on_ssh_session_closed(self, session_id: str):
        """SSH会话关闭。"""
        self.appendSessionOutput.emit(session_id, "\nSSH会话已关闭。\n")
        self.removeSessionWidget.emit(session_id) # 移除会话窗口

    def _on_sftp_progress(self, session_id: str, transferred_bytes: int, total_bytes: int):
        """SFTP传输进度。"""
        progress_percent = (transferred_bytes / total_bytes) * 100 if total_bytes > 0 else 0
        self.appendSessionOutput.emit(session_id, f"\rSFTP传输进度: {progress_percent:.2f}% ({transferred_bytes}/{total_bytes} bytes)")

    def _on_sftp_finished(self, session_id: str):
        """SFTP传输完成。"""
        self.appendSessionOutput.emit(session_id, "\nSFTP传输完成。\n")

    def _on_sftp_failed(self, session_id: str, error_message: str):
        """SFTP传输失败。"""
        self.appendSessionOutput.emit(session_id, f"\nSFTP传输失败: {error_message}\n")
        self.showErrorMessage.emit("SFTP传输失败", error_message)


class SshConnectionThread(QThread):
    """
    在单独线程中执行SSH连接操作，避免阻塞UI。
    """
    def __init__(self, ssh_service: SshService, session_id: str, connection: SshConnectionModel, parent=None):
        super().__init__(parent)
        self.ssh_service = ssh_service
        self.session_id = session_id
        self.connection = connection
        self.logger = logging.getLogger(self.__class__.__name__)

    def run(self):
        self.logger.info(f"SSH连接线程启动，会话ID: {self.session_id}")
        self.ssh_service.connect(
            session_id=self.session_id,
            host=self.connection.host,
            port=self.connection.port,
            username=self.connection.username,
            password=self.connection.password if self.connection.auth_method == "password" else None,
            private_key_path=self.connection.private_key_path if self.connection.auth_method == "private_key" else None
        )
        self.logger.info(f"SSH连接线程结束，会话ID: {self.session_id}")