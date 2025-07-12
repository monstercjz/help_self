import paramiko
from PySide6.QtCore import QObject, Signal, QThread, Slot, QTimer
from enum import Enum, auto

class ConnectionStatus(Enum):
    DISCONNECTED = auto()
    CONNECTING = auto()
    CONNECTED = auto()
    DISCONNECTING = auto()
    FAILED = auto()

class SSHWorker(QObject):
    """
    Manages the entire SSH lifecycle in a separate thread:
    connection, shell interaction, and disconnection.
    """
    # Emits (status, data) - data can be error message or shell output
    status_changed = Signal(ConnectionStatus, str)
    data_received = Signal(str) # For raw shell output
    
    def __init__(self, details):
        super().__init__()
        self.details = details
        self.client = None
        self.shell = None
        self._running = True
        self.reader_timer = None

    @Slot()
    def run(self):
        """Main worker execution loop."""
        try:
            self._connect()
        except Exception as e:
            self.status_changed.emit(ConnectionStatus.FAILED, str(e))
            self._cleanup()
            self.status_changed.emit(ConnectionStatus.DISCONNECTED, "Connection failed.")
            return

        # If connection is successful, setup and start the timer
        self.reader_timer = QTimer()
        self.reader_timer.timeout.connect(self._read_shell_output)
        self.reader_timer.start(100)  # Check for data every 100ms

    def _connect(self):
        """Establishes the SSH connection."""
        self.status_changed.emit(ConnectionStatus.CONNECTING, "Initializing connection...")
        self.client = paramiko.SSHClient()
        self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
        connect_kwargs = {
            "hostname": self.details["hostname"],
            "port": self.details["port"],
            "username": self.details["username"],
            "password": self.details["password"],
            "timeout": 10,
            "auth_timeout": 10,
            "banner_timeout": 10,
            "allow_agent": False,
            "look_for_keys": False,
        }
        
        self.client.connect(**connect_kwargs)
        self.status_changed.emit(ConnectionStatus.CONNECTING, "Connection established. Opening shell...")
        
        self.shell = self.client.invoke_shell(term='xterm-256color')
        self.status_changed.emit(ConnectionStatus.CONNECTED, "Shell is ready.")

    @Slot()
    def _read_shell_output(self):
        """Periodically reads from the SSH shell. Connected to a QTimer."""
        if not self.shell or self.shell.closed:
            if self.reader_timer:
                self.reader_timer.stop()
            self._cleanup()
            self.status_changed.emit(ConnectionStatus.DISCONNECTED, "Connection closed by peer.")
            return

        try:
            if self.shell.recv_ready():
                data = self.shell.recv(4096).decode('utf-8', errors='replace')
                if data:
                    self.data_received.emit(data)
        except Exception as e:
            if self.reader_timer:
                self.reader_timer.stop()
            self._cleanup()
            self.status_changed.emit(ConnectionStatus.FAILED, f"Shell read error: {e}")

    @Slot(str)
    def send_command(self, command):
        """Sends a command to the shell."""
        if self.shell and not self.shell.closed:
            try:
                self.shell.send(command)
            except Exception as e:
                self.status_changed.emit(ConnectionStatus.FAILED, f"Error sending command: {e}")

    @Slot()
    def stop(self):
        """Stops the worker and initiates cleanup."""
        self.status_changed.emit(ConnectionStatus.DISCONNECTING, "Disconnecting...")
        self._running = False
        if self.reader_timer:
            self.reader_timer.stop()
        self._cleanup()
        self.status_changed.emit(ConnectionStatus.DISCONNECTED, "Worker stopped.")

    def _cleanup(self):
        """Closes the shell and client."""
        if self.shell:
            self.shell.close()
            self.shell = None
        if self.client:
            self.client.close()
            self.client = None

class SSHService(QObject):
    """
    Service layer for managing the SSH connection lifecycle.
    """
    status_changed = Signal(ConnectionStatus, str)
    data_received = Signal(str)
    _command_to_send = Signal(str) # Internal signal for thread-safe command sending

    def __init__(self):
        super().__init__()
        self.worker_thread = None
        self.worker = None

    @Slot(dict)
    def connect(self, details):
        """Starts a new SSH connection in a background thread."""
        if self.worker_thread and self.worker_thread.isRunning():
            return

        self.worker = SSHWorker(details)
        self.worker_thread = QThread()
        self.worker.moveToThread(self.worker_thread)

        # Connect signals
        self.worker.status_changed.connect(self.status_changed)
        self.worker.data_received.connect(self.data_received)
        self._command_to_send.connect(self.worker.send_command) # Connect command signal to worker slot
        self.worker_thread.started.connect(self.worker.run)
        self.worker.status_changed.connect(self._on_worker_finished)
        
        # Cleanup
        self.worker_thread.finished.connect(self.worker.deleteLater)
        self.worker_thread.finished.connect(self.worker_thread.deleteLater)

        self.worker_thread.start()

    @Slot(str)
    def send_command(self, command):
        """Sends a command to the running worker via a thread-safe signal."""
        if self.worker:
            self._command_to_send.emit(command)

    @Slot()
    def disconnect(self):
        """Requests the worker to stop and disconnect."""
        if self.worker:
            self.worker.stop()

    @Slot(ConnectionStatus, str)
    def _on_worker_finished(self, status, message):
        """Cleans up the thread when the worker is done."""
        if status == ConnectionStatus.DISCONNECTED or status == ConnectionStatus.FAILED:
            if self.worker_thread and self.worker_thread.isRunning():
                self.worker_thread.quit()
                self.worker_thread.wait()
            self.worker_thread = None
            self.worker = None