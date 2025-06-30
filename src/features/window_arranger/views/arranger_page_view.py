# desktop_center/src/features/window_arranger/views/arranger_page_view.py
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                                   QGroupBox, QFormLayout, QSpinBox, QLabel,
                                   QScrollArea, QListWidget, QListWidgetItem, QLineEdit)
from PySide6.QtCore import Signal, Qt

class ArrangerPageView(QWidget):
    """
    桌面窗口排列功能的主UI页面。
    包含窗口过滤输入、检测到的窗口列表、排列参数设置和操作按钮。
    """
    # 信号，用于通知控制器执行操作
    detect_windows_requested = Signal()
    arrange_grid_requested = Signal(int, int, int) # rows, cols, spacing
    arrange_cascade_requested = Signal(int, int) # x_offset, y_offset

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("窗口排列器") # 内部标题，显示名称由插件定义

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)

        title_label = QLabel("桌面窗口排列")
        title_label.setStyleSheet("font-size: 22px; font-weight: bold; margin-bottom: 10px; color: #333;")
        main_layout.addWidget(title_label)

        # 窗口过滤组
        filter_group = QGroupBox("窗口过滤")
        filter_group.setStyleSheet("""
            QGroupBox { font-size: 16px; font-weight: bold; color: #333; margin-top: 10px; }
            QGroupBox::title { subcontrol-origin: margin; subcontrol-position: top left; padding: 0 10px; left: 10px; }
        """)
        filter_layout = QFormLayout(filter_group)
        filter_layout.setSpacing(12)
        filter_layout.setContentsMargins(20, 30, 20, 20)
        
        self.filter_keyword_input = QLineEdit("完全控制") # 基于图片预设默认关键词
        self.filter_keyword_input.setPlaceholderText("输入窗口标题包含的关键词")
        filter_layout.addRow("标题关键词:", self.filter_keyword_input)
        main_layout.addWidget(filter_group)

        # 检测到的窗口列表组
        windows_list_group = QGroupBox("检测到的窗口")
        windows_list_group.setStyleSheet("""
            QGroupBox { font-size: 16px; font-weight: bold; color: #333; margin-top: 10px; }
            QGroupBox::title { subcontrol-origin: margin; subcontrol-position: top left; padding: 0 10px; left: 10px; }
        """)
        windows_list_layout = QVBoxLayout(windows_list_group)
        windows_list_layout.setContentsMargins(20, 30, 20, 20)

        self.detected_windows_list_widget = QListWidget()
        self.detected_windows_list_widget.setMinimumHeight(150)
        self.detected_windows_list_widget.setStyleSheet("""
            QListWidget { border: 1px solid #ddd; border-radius: 5px; padding: 5px; }
            QListWidget::item { padding: 5px; }
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
        main_layout.addWidget(windows_list_group)

        # 排列设置组
        settings_group = QGroupBox("排列设置")
        settings_group.setStyleSheet("""
            QGroupBox { font-size: 16px; font-weight: bold; color: #333; margin-top: 10px; }
            QGroupBox::title { subcontrol-origin: margin; subcontrol-position: top left; padding: 0 10px; left: 10px; }
        """)
        settings_layout = QFormLayout(settings_group)
        settings_layout.setSpacing(12)
        settings_layout.setContentsMargins(20, 30, 20, 20)

        self.rows_spinbox = QSpinBox()
        self.rows_spinbox.setRange(1, 10)
        self.rows_spinbox.setValue(2)
        settings_layout.addRow("网格行数:", self.rows_spinbox)

        self.cols_spinbox = QSpinBox()
        self.cols_spinbox.setRange(1, 10)
        self.cols_spinbox.setValue(3)
        settings_layout.addRow("网格列数:", self.cols_spinbox)
        
        self.spacing_spinbox = QSpinBox()
        self.spacing_spinbox.setRange(0, 100)
        self.spacing_spinbox.setValue(10)
        settings_layout.addRow("网格间距 (px):", self.spacing_spinbox)

        self.cascade_x_offset_spinbox = QSpinBox()
        self.cascade_x_offset_spinbox.setRange(0, 100)
        self.cascade_x_offset_spinbox.setValue(30)
        settings_layout.addRow("级联X偏移 (px):", self.cascade_x_offset_spinbox)

        self.cascade_y_offset_spinbox = QSpinBox()
        self.cascade_y_offset_spinbox.setRange(0, 100)
        self.cascade_y_offset_spinbox.setValue(30)
        settings_layout.addRow("级联Y偏移 (px):", self.cascade_y_offset_spinbox)

        main_layout.addWidget(settings_group)

        # 动作按钮
        action_buttons_layout = QHBoxLayout()
        self.arrange_grid_button = QPushButton("网格排列")
        self.arrange_grid_button.setMinimumHeight(35)
        self.arrange_grid_button.setStyleSheet("""
            QPushButton { font-size: 14px; font-weight: bold; background-color: #007bff; color: white; border: none; border-radius: 5px; padding: 0 20px; }
            QPushButton:hover { background-color: #0056b3; }
            QPushButton:pressed { background-color: #004085; }
        """)
        self.arrange_grid_button.clicked.connect(self._emit_arrange_grid)
        action_buttons_layout.addWidget(self.arrange_grid_button)

        self.arrange_cascade_button = QPushButton("级联排列")
        self.arrange_cascade_button.setMinimumHeight(35)
        self.arrange_cascade_button.setStyleSheet("""
            QPushButton { font-size: 14px; font-weight: bold; background-color: #17a2b8; color: white; border: none; border-radius: 5px; padding: 0 20px; }
            QPushButton:hover { background-color: #138496; }
            QPushButton:pressed { background-color: #117a8b; }
        """)
        self.arrange_cascade_button.clicked.connect(self._emit_arrange_cascade)
        action_buttons_layout.addWidget(self.arrange_cascade_button)
        main_layout.addLayout(action_buttons_layout)

        main_layout.addStretch(1) # 将内容推到顶部

    def _emit_arrange_grid(self):
        """当网格排列按钮被点击时，发射带参数的信号。"""
        rows = self.rows_spinbox.value()
        cols = self.cols_spinbox.value()
        spacing = self.spacing_spinbox.value()
        self.arrange_grid_requested.emit(rows, cols, spacing)

    def _emit_arrange_cascade(self):
        """当级联排列按钮被点击时，发射带参数的信号。"""
        x_offset = self.cascade_x_offset_spinbox.value()
        y_offset = self.cascade_y_offset_spinbox.value()
        self.arrange_cascade_requested.emit(x_offset, y_offset)

    def update_detected_windows_list(self, window_titles: list[str]):
        """
        更新UI上的检测到的窗口列表。
        
        Args:
            window_titles (list[str]): 检测到的窗口标题列表。
        """
        self.detected_windows_list_widget.clear()
        if not window_titles:
            self.detected_windows_list_widget.addItem("未检测到符合条件的窗口。")
        else:
            for title in window_titles:
                self.detected_windows_list_widget.addItem(title)

    def get_filter_keyword(self) -> str:
        """获取当前设置的窗口过滤关键词。"""
        return self.filter_keyword_input.text().strip()

    def get_grid_params(self) -> tuple[int, int, int]:
        """获取当前设置的网格排列参数：行数、列数、间距。"""
        return self.rows_spinbox.value(), self.cols_spinbox.value(), self.spacing_spinbox.value()
    
    def get_cascade_params(self) -> tuple[int, int]:
        """获取当前设置的级联排列参数：X偏移、Y偏移。"""
        return self.cascade_x_offset_spinbox.value(), self.cascade_y_offset_spinbox.value()

    def load_settings_to_ui(self, settings_data: dict):
        """
        将配置服务中加载的设置数据同步到UI控件中。
        
        Args:
            settings_data (dict): 从配置文件加载的键值对字典。
        """
        self.filter_keyword_input.setText(settings_data.get("filter_keyword", "完全控制"))
        self.rows_spinbox.setValue(int(settings_data.get("grid_rows", 2)))
        self.cols_spinbox.setValue(int(settings_data.get("grid_cols", 3)))
        self.spacing_spinbox.setValue(int(settings_data.get("grid_spacing", 10)))
        self.cascade_x_offset_spinbox.setValue(int(settings_data.get("cascade_x_offset", 30)))
        self.cascade_y_offset_spinbox.setValue(int(settings_data.get("cascade_y_offset", 30)))