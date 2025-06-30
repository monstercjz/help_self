# desktop_center/src/features/window_arranger/views/arranger_page_view.py
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                                   QGroupBox, QFormLayout, QLabel,
                                   QListWidget, QListWidgetItem, QLineEdit,
                                   QAbstractItemView)
from PySide6.QtCore import Signal, Qt
from PySide6.QtGui import QIcon, QFont

class ArrangerPageView(QWidget):
    """
    桌面窗口排列功能的主UI页面。
    """
    detect_windows_requested = Signal()
    open_settings_requested = Signal()
    arrange_grid_requested = Signal()
    arrange_cascade_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("窗口排列器")

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)
        
        # --- 标题和设置按钮行 ---
        header_layout = QHBoxLayout()
        title_label = QLabel("桌面窗口排列")
        title_label.setStyleSheet("font-size: 22px; font-weight: bold; color: #333;")
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        
        self.settings_button = QPushButton("排列设置")
        try:
            settings_icon = self.style().standardIcon(self.style().StandardPixmap.SP_FileDialogDetailedView)
            self.settings_button.setIcon(settings_icon)
        except:
            pass
        self.settings_button.setMinimumHeight(30)
        self.settings_button.clicked.connect(self.open_settings_requested.emit)
        header_layout.addWidget(self.settings_button)
        main_layout.addLayout(header_layout)
        
        # 窗口过滤组
        filter_group = QGroupBox("窗口过滤")
        filter_group.setStyleSheet("""
            QGroupBox { font-size: 16px; font-weight: bold; color: #333; margin-top: 10px; }
            QGroupBox::title { subcontrol-origin: margin; subcontrol-position: top left; padding: 0 10px; left: 10px; }
        """)
        filter_layout = QFormLayout(filter_group)
        filter_layout.setSpacing(12)
        filter_layout.setContentsMargins(20, 30, 20, 20)
        
        self.filter_keyword_input = QLineEdit()
        self.filter_keyword_input.setPlaceholderText("输入标题关键词, 用逗号分隔多个")
        filter_layout.addRow("标题关键词:", self.filter_keyword_input)

        self.process_name_input = QLineEdit()
        self.process_name_input.setPlaceholderText("输入进程名, 用逗号分隔多个")
        filter_layout.addRow("进程名称:", self.process_name_input)
        
        self.exclude_title_input = QLineEdit()
        self.exclude_title_input.setPlaceholderText("输入要排除的标题关键词，用逗号分隔")
        filter_layout.addRow("排除标题包含:", self.exclude_title_input)
        
        main_layout.addWidget(filter_group)

        # 检测到的窗口列表组
        self.windows_list_group = QGroupBox("检测到的窗口")
        self.windows_list_group.setStyleSheet("""
            QGroupBox { font-size: 16px; font-weight: bold; color: #333; margin-top: 10px; }
            QGroupBox::title { subcontrol-origin: margin; subcontrol-position: top left; padding: 0 10px; left: 10px; }
        """)
        windows_list_layout = QVBoxLayout(self.windows_list_group)
        windows_list_layout.setContentsMargins(20, 30, 20, 20)

        self.detected_windows_list_widget = QListWidget()
        self.detected_windows_list_widget.setMinimumHeight(200)
        self.detected_windows_list_widget.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.detected_windows_list_widget.setStyleSheet("""
            QListWidget { border: 1px solid #ddd; border-radius: 5px; padding: 5px; }
            QListWidget::item { padding: 5px; }
            QListWidget::indicator { width: 16px; height: 16px; }
        """)
        windows_list_layout.addWidget(self.detected_windows_list_widget)
        
        detect_button = QPushButton("检测桌面窗口")
        detect_button.setMinimumHeight(30)
        detect_button.setStyleSheet("""
            QPushButton { font-size: 14px; background-color: #5cb85c; color: white; border: none; border-radius: 5px; padding: 5px 15px; }
            QPushButton:hover { background-color: #4cae4c; }
            QPushButton:pressed { background-color: #449d44; }
        """)
        detect_button.clicked.connect(self.detect_windows_requested.emit)
        windows_list_layout.addWidget(detect_button)
        main_layout.addWidget(self.windows_list_group)
        
        # 动作按钮
        action_buttons_layout = QHBoxLayout()
        self.arrange_grid_button = QPushButton("网格排列")
        self.arrange_grid_button.setMinimumHeight(35)
        self.arrange_grid_button.setStyleSheet("""
            QPushButton { font-size: 14px; font-weight: bold; background-color: #007bff; color: white; border: none; border-radius: 5px; padding: 0 20px; }
            QPushButton:hover { background-color: #0056b3; }
            QPushButton:pressed { background-color: #004085; }
        """)
        self.arrange_grid_button.clicked.connect(self.arrange_grid_requested.emit)
        action_buttons_layout.addWidget(self.arrange_grid_button)

        self.arrange_cascade_button = QPushButton("级联排列")
        self.arrange_cascade_button.setMinimumHeight(35)
        self.arrange_cascade_button.setStyleSheet("""
            QPushButton { font-size: 14px; font-weight: bold; background-color: #17a2b8; color: white; border: none; border-radius: 5px; padding: 0 20px; }
            QPushButton:hover { background-color: #138496; }
            QPushButton:pressed { background-color: #117a8b; }
        """)
        self.arrange_cascade_button.clicked.connect(self.arrange_cascade_requested.emit)
        action_buttons_layout.addWidget(self.arrange_cascade_button)
        main_layout.addLayout(action_buttons_layout)

        main_layout.addStretch(1)

    def update_detected_windows_list(self, window_infos: list[object]):
        """更新UI上的检测到的窗口列表，并为每个项目添加复选框。"""
        self.detected_windows_list_widget.clear()
        if not window_infos:
            self.detected_windows_list_widget.addItem("未检测到符合条件的窗口。")
        else:
            for win_info in window_infos:
                display_text = f"{win_info.title} (进程: {win_info.process_name if win_info.process_name not in ['[未知进程]', '[PID获取失败]', '[进程不存在]', '[权限不足]', '[获取进程名失败]'] else 'N/A'})"
                item = QListWidgetItem(display_text)
                item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
                item.setCheckState(Qt.Checked)
                item.setData(Qt.UserRole, win_info)
                self.detected_windows_list_widget.addItem(item)
    
    def get_selected_window_infos(self) -> list[object]:
        """获取当前列表中所有被勾选的窗口的 WindowInfo 对象。"""
        selected_windows = []
        for i in range(self.detected_windows_list_widget.count()):
            item = self.detected_windows_list_widget.item(i)
            if item.checkState() == Qt.Checked:
                window_info = item.data(Qt.UserRole)
                if window_info:
                    selected_windows.append(window_info)
        return selected_windows

    def get_filter_keyword(self) -> str:
        """获取当前设置的窗口标题过滤关键词。"""
        return self.filter_keyword_input.text().strip()

    def get_process_name_filter(self) -> str:
        """获取当前设置的进程名过滤关键词。"""
        return self.process_name_input.text().strip()
    
    def get_exclude_keywords(self) -> str:
        """获取排除关键词字符串。"""
        return self.exclude_title_input.text().strip()