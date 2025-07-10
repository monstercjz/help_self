# src/features/ssh_client/services/SshService.py
import paramiko
import logging
from PySide6.QtCore import QObject, Signal, QThread

class SshService(QObject):
    """
    SSH服务类，负责处理SSH连接、命令执行和文件传输。
    使用Paramiko库。
    """
    # 信号：连接成功
    connected = Signal(str)
    # 信号：连接失败，附带错误信息
    connectionFailed = Signal(str, str)
    # 信号：收到新的输出
    outputReceived = Signal(str, bytes) # session_id, output_bytes (原始字节流)
    # 信号：命令执行完成
    commandExecuted = Signal(str, int) # session_id, exit_status
    # 信号：会话关闭
    sessionClosed = Signal(str) # session_id
    # 信号：文件传输进度
    sftpProgress = Signal(str, int, int) # session_id, transferred_bytes, total_bytes
    # 信号：文件传输完成![1752122120623](images/SshService/1752122120623.png)
    sftpFinished = Signal(str) # session_id
    # 信号：文件传输失败
    sftpFailed = Signal(str, str) # session_id, error_message

    def __init__(self, parent=None):
        super().__init__(parent)
        self.clients = {}  # 存储活动的SSH客户端实例 {session_id: SSHClient}
        self.transports = {} # 存储活动的Transport实例 {session_id: Transport}
        self.channels = {} # 存储活动的Channel实例 {session_id: Channel}
        self.sftp_clients = {} # 存储活动的SFTPClient实例 {session_id: SFTPClient}
        self.output_reader_threads = {} # {session_id: SshOutputReaderThread} 存储活跃的输出读取线程
        self.logger = logging.getLogger(self.__class__.__name__)

    def connect(self, session_id: str, host: str, port: int, username: str,
                password: str = None, private_key_path: str = None):
        """
        建立SSH连接。
        """
        self.logger.info(f"尝试连接到 {username}@{host}:{port} (会话ID: {session_id})")
        try:
            client = paramiko.SSHClient()
            client.load_system_host_keys()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

            if private_key_path:
                private_key = paramiko.RSAKey.from_private_key_file(private_key_path)
                client.connect(hostname=host, port=port, username=username, pkey=private_key, timeout=10)
            else:
                client.connect(hostname=host, port=port, username=username, password=password, timeout=10)
            
            self.clients[session_id] = client
            self.transports[session_id] = client.get_transport()
            self.connected.emit(session_id)
            self.logger.info(f"成功连接到 {host} (会话ID: {session_id})")

        except paramiko.AuthenticationException:
            error_msg = "认证失败，请检查用户名、密码或密钥。"
            self.connectionFailed.emit(session_id, error_msg)
            self.logger.error(f"连接失败: {error_msg}")
        except paramiko.SSHException as e:
            error_msg = f"SSH连接错误: {e}"
            self.connectionFailed.emit(session_id, error_msg)
            self.logger.error(f"连接失败: {error_msg}")
        except Exception as e:
            error_msg = f"未知错误: {e}"
            self.connectionFailed.emit(session_id, error_msg)
            self.logger.error(f"连接失败: {error_msg}")

    def execute_command(self, session_id: str, command: str):
        """
        在指定会话上执行命令。
        """
        if session_id not in self.clients:
            self.outputReceived.emit(session_id, "错误: SSH客户端未连接。")
            return

        self.logger.info(f"在会话 {session_id} 上执行命令: {command}")
        try:
            # 使用exec_command执行命令，并获取stdin, stdout, stderr
            stdin, stdout, stderr = self.clients[session_id].exec_command(command)
            
            # 读取标准输出
            output_bytes = stdout.read()
            if output_bytes:
                self.outputReceived.emit(session_id, output_bytes)
            
            # 读取标准错误
            error_bytes = stderr.read()
            if error_bytes:
                # 错误输出也作为原始字节发送，由SessionWidget处理解码和渲染
                # 将中文提示编码为UTF-8字节，避免非ASCII字符错误
                self.outputReceived.emit(session_id, "错误输出:\n".encode('utf-8') + error_bytes)
            
            # 获取退出状态码
            exit_status = stdout.channel.recv_exit_status()
            self.commandExecuted.emit(session_id, exit_status)
            self.logger.info(f"命令 '{command}' 在会话 {session_id} 上执行完成，退出状态: {exit_status}")

        except Exception as e:
            error_msg = f"执行命令时发生错误: {e}"
            self.outputReceived.emit(session_id, error_msg)
            self.logger.error(f"命令执行错误: {error_msg}")
            self.commandExecuted.emit(session_id, -1) # -1 表示错误

    def open_shell(self, session_id: str):
        """
        打开一个交互式shell会话。
        """
        if session_id not in self.clients:
            self.outputReceived.emit(session_id, "错误: SSH客户端未连接。")
            return

        self.logger.info(f"在会话 {session_id} 上打开交互式shell。")
        try:
            channel = self.clients[session_id].invoke_shell()
            self.channels[session_id] = channel
            # 启动一个线程来持续读取shell输出
            thread = SshOutputReaderThread(session_id, channel)
            thread.outputReceived.connect(self.outputReceived) # 保持连接，但现在发送的是bytes
            thread.finished.connect(lambda sid=session_id: self._on_output_reader_thread_finished(sid)) # 连接finished信号
            self.output_reader_threads[session_id] = thread # 存储线程引用
            thread.start()
            self.logger.info(f"会话 {session_id} 的shell已打开。")
        except Exception as e:
            error_msg = f"打开shell时发生错误: {e}"
            self.outputReceived.emit(session_id, error_msg)
            self.logger.error(f"打开shell错误: {error_msg}")
            self.sessionClosed.emit(session_id)

    def send_shell_data(self, session_id: str, data: str):
        """
        向交互式shell发送数据。
        """
        if session_id in self.channels and self.channels[session_id].active:
            try:
                self.logger.info(f"向会话 {session_id} 发送Shell数据: {data!r}") # 打印发送的数据
                self.channels[session_id].send(data.encode('utf-8')) # 将字符串编码为字节发送
            except Exception as e:
                self.logger.error(f"发送shell数据到会话 {session_id} 失败: {e}")
        else:
            self.logger.warning(f"会话 {session_id} 的shell不活跃或不存在，无法发送数据。")

    def close_session(self, session_id: str):
        """
        关闭指定的SSH会话。
        """
        self.logger.info(f"尝试关闭会话 {session_id}。")
        if session_id in self.output_reader_threads:
            thread = self.output_reader_threads.pop(session_id)
            thread.stop() # 停止线程
            thread.wait(1000) # 等待线程结束，最多1秒
            thread.deleteLater() # 标记为稍后删除
            self.logger.info(f"会话 {session_id} 的输出读取线程已停止并清理。")

        if session_id in self.channels and self.channels[session_id].active:
            try:
                self.channels[session_id].close()
                del self.channels[session_id]
                self.logger.info(f"会话 {session_id} 的channel已关闭。")
            except Exception as e:
                self.logger.error(f"关闭会话 {session_id} 的channel失败: {e}")

        if session_id in self.clients:
            try:
                self.clients[session_id].close()
                del self.clients[session_id]
                self.logger.info(f"会话 {session_id} 的客户端已关闭。")
            except Exception as e:
                self.logger.error(f"关闭会话 {session_id} 的客户端失败: {e}")
        
        if session_id in self.transports:
            try:
                self.transports[session_id].close()
                del self.transports[session_id]
                self.logger.info(f"会话 {session_id} 的transport已关闭。")
            except Exception as e:
                self.logger.error(f"关闭会话 {session_id} 的transport失败: {e}")

        if session_id in self.sftp_clients:
            try:
                self.sftp_clients[session_id].close()
                del self.sftp_clients[session_id]
                self.logger.info(f"会话 {session_id} 的SFTP客户端已关闭。")
            except Exception as e:
                self.logger.error(f"关闭会话 {session_id} 的SFTP客户端失败: {e}")

        self.sessionClosed.emit(session_id)
        self.logger.info(f"会话 {session_id} 已完全关闭。")

    def _on_output_reader_thread_finished(self, session_id: str):
        """输出读取线程完成时的清理槽函数。"""
        self.logger.info(f"输出读取线程 {session_id} 已完成。")
        # 线程已在close_session中处理，这里仅做日志记录

    def open_sftp(self, session_id: str):
        """
        为指定会话打开SFTP客户端。
        """
        if session_id not in self.clients:
            self.sftpFailed.emit(session_id, "错误: SSH客户端未连接。")
            return
        
        if session_id in self.sftp_clients:
            self.logger.warning(f"会话 {session_id} 的SFTP客户端已打开。")
            return

        self.logger.info(f"为会话 {session_id} 打开SFTP客户端。")
        try:
            sftp = self.clients[session_id].open_sftp()
            self.sftp_clients[session_id] = sftp
            self.logger.info(f"会话 {session_id} 的SFTP客户端已打开。")
        except Exception as e:
            error_msg = f"打开SFTP客户端时发生错误: {e}"
            self.sftpFailed.emit(session_id, error_msg)
            self.logger.error(f"打开SFTP客户端错误: {error_msg}")

    def put_file(self, session_id: str, local_path: str, remote_path: str):
        """
        上传文件到远程服务器。
        """
        if session_id not in self.sftp_clients:
            self.sftpFailed.emit(session_id, "错误: SFTP客户端未打开。")
            return
        
        self.logger.info(f"上传文件 {local_path} 到 {remote_path} (会话ID: {session_id})")
        try:
            sftp = self.sftp_clients[session_id]
            sftp.put(local_path, remote_path, callback=lambda x, y: self.sftpProgress.emit(session_id, x, y))
            self.sftpFinished.emit(session_id)
            self.logger.info(f"文件 {local_path} 上传完成。")
        except Exception as e:
            error_msg = f"上传文件失败: {e}"
            self.sftpFailed.emit(session_id, error_msg)
            self.logger.error(f"上传文件失败: {error_msg}")

    def get_file(self, session_id: str, remote_path: str, local_path: str):
        """
        从远程服务器下载文件。
        """
        if session_id not in self.sftp_clients:
            self.sftpFailed.emit(session_id, "错误: SFTP客户端未打开。")
            return
        
        self.logger.info(f"下载文件 {remote_path} 到 {local_path} (会话ID: {session_id})")
        try:
            sftp = self.sftp_clients[session_id]
            sftp.get(remote_path, local_path, callback=lambda x, y: self.sftpProgress.emit(session_id, x, y))
            self.sftpFinished.emit(session_id)
            self.logger.info(f"文件 {remote_path} 下载完成。")
        except Exception as e:
            error_msg = f"下载文件失败: {e}"
            self.sftpFailed.emit(session_id, error_msg)
            self.logger.error(f"下载文件失败: {error_msg}")

class SshOutputReaderThread(QThread):
    """
    用于在单独线程中读取SSH Channel输出的线程。
    """
    outputReceived = Signal(str, bytes) # session_id, output_bytes (原始字节流)

    def __init__(self, session_id: str, channel: paramiko.Channel, parent=None):
        super().__init__(parent)
        self.session_id = session_id
        self.channel = channel
        self.running = True
        self.logger = logging.getLogger(self.__class__.__name__)

    def run(self):
        while self.running and self.channel.active:
            try:
                if self.channel.recv_ready():
                    output_bytes = self.channel.recv(4096) # 读取原始字节
                    if output_bytes:
                        self.outputReceived.emit(self.session_id, output_bytes)
                if self.channel.recv_stderr_ready():
                    error_bytes = self.channel.recv_stderr(4096) # 读取原始字节
                    if error_bytes:
                        self.outputReceived.emit(self.session_id, error_bytes)
                
                # 短暂休眠以避免CPU占用过高
                self.msleep(50)
            except Exception as e:
                self.logger.error(f"读取SSH输出时发生错误 (会话ID: {self.session_id}): {e}")
                self.running = False
        self.logger.info(f"SSH输出读取线程 (会话ID: {self.session_id}) 结束。")
        self.finished.emit() # 线程结束时发出finished信号

    def stop(self):
        self.running = False
        self.wait() # 等待线程结束