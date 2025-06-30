# desktop_center/src/features/window_arranger/views/arranger_page_view.py
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                                   QGroupBox, QFormLayout, QSpinBox, QLabel,
                                   QScrollArea, QListWidget, QListWidgetItem, QLineEdit,
                                   QComboBox, QAbstractItemView)
from PySide6.QtCore import Signal, Qt

class ArrangerPageView(QWidget):
    """
    桌面窗口排列功能的主UI页面。
    """
    detect_windows_requested = Signal()
    arrange_grid_requested = Signal()
    arrange_cascade_requested = Signal(int, int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("窗口排列器")

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)

        title_label = QLabel("桌面窗口排列")
        title_label.setStyleSheet("font-size: 22px; font-weight: bold; margin-bottom: 10px; color: #333;")
        main_layout.addWidget(title_label)

        # 窗口过滤组 (无变化)
        filter_group = QGroupBox("窗口过滤")
        filter_group.setStyleSheet("""
            QGroupBox { font-size: 16px; font-weight: bold; color: #333; margin-top: 10px; }
            QGroupBox::title { subcontrol-origin: margin; subcontrol-position: top left; padding: 0 10px; left: 10px; }
        """)
        filter_layout = QFormLayout(filter_group)
        filter_layout.setSpacing(12)
        filter_layout.setContentsMargins(20, 30, 20, 20)
        self.filter_keyword_input = QLineEdit("完全控制")
        self.filter_keyword_input.setPlaceholderText("输入标题关键词, 用逗号分隔多个")
        filter_layout.addRow("标题关键词:", self.filter_keyword_input)
        self.process_name_input = QLineEdit()
        self.process_name_input.setPlaceholderText("输入进程名, 用逗号分隔多个")
        filter_layout.addRow("进程名称:", self.process_name_input)
        self.exclude_title_input = QLineEdit("Radmin Viewer")
        self.exclude_title_input.setPlaceholderText("输入要排除的标题关键词，用逗号分隔")
        filter_layout.addRow("排除标题包含:", self.exclude_title_input)
        main_layout.addWidget(filter_group)

        # 检测到的窗口列表组 (无变化)
        windows_list_group = QGroupBox("检测到的窗口")
        windows_list_group.setStyleSheet("""
            QGroupBox { font-size: 16px; font-weight: bold; color: #333; margin-top: 10px; }
            QGroupBox::title { subcontrol-origin: margin; subcontrol-position: top left; padding: 0 10px; left: 10px; }
        """)
        windows_list_layout = QVBoxLayout(windows_list_group)
        windows_list_layout.setContentsMargins(20, 30, 20, 20)
        self.detected_windows_list_widget = QListWidget()
        self.detected_windows_list_widget.setMinimumHeight(150)
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

        self.screen_selection_combobox = QComboBox()
        settings_layout.addRow("目标屏幕:", self.screen_selection_combobox)

        self.grid_direction_combobox = QComboBox()
        self.grid_direction_combobox.addItems(["先排满行 (→)", "先排满列 (↓)"])
        settings_layout.addRow("网格排列方向:", self.grid_direction_combobox)

        self.rows_spinbox = QSpinBox()
        self.rows_spinbox.setRange(1, 20)
        self.rows_spinbox.setValue(2)
        settings_layout.addRow("网格行数:", self.rows_spinbox)

        self.cols_spinbox = QSpinBox()
        self.cols_spinbox.setRange(1, 20)
        self.cols_spinbox.setValue(3)
        settings_layout.addRow("网格列数:", self.cols_spinbox)
        
        # 【修改】允许边距和间距为负数
        margin_layout = QHBoxLayout()
        self.margin_top_spinbox = QSpinBox(); self.margin_top_spinbox.setRange(-500, 500);
        self.margin_bottom_spinbox = QSpinBox(); self.margin_bottom_spinbox.setRange(-500, 500);
        self.margin_left_spinbox = QSpinBox(); self.margin_left_spinbox.setRange(-500, 500);
        self.margin_right_spinbox = QSpinBox(); self.margin_right_spinbox.setRange(-500, 500);
        margin_layout.addWidget(QLabel("上:")); margin_layout.addWidget(self.margin_top_spinbox)
        margin_layout.addWidget(QLabel("下:")); margin_layout.addWidget(self.margin_bottom_spinbox)
        margin_layout.addWidget(QLabel("左:")); margin_layout.addWidget(self.margin_left_spinbox)
        margin_layout.addWidget(QLabel("右:")); margin_layout.addWidget(self.margin_right_spinbox)
        settings_layout.addRow("屏幕边距 (px):", margin_layout)

        spacing_layout = QHBoxLayout()
        self.spacing_horizontal_spinbox = QSpinBox(); self.spacing_horizontal_spinbox.setRange(-100, 100); self.spacing_horizontal_spinbox.setValue(10);
        self.spacing_vertical_spinbox = QSpinBox(); self.spacing_vertical_spinbox.setRange(-100, 100); self.spacing_vertical_spinbox.setValue(10);
        spacing_layout.addWidget(QLabel("水平:")); spacing_layout.addWidget(self.spacing_horizontal_spinbox)
        spacing_layout.addWidget(QLabel("垂直:")); spacing_layout.addWidget(self.spacing_vertical_spinbox)
        settings_layout.addRow("窗口间距 (px):", spacing_layout)

        self.cascade_x_offset_spinbox = QSpinBox(); self.cascade_x_offset_spinbox.setRange(0, 100); self.cascade_x_offset_spinbox.setValue(30);
        self.cascade_y_offset_spinbox = QSpinBox(); self.cascade_y_offset_spinbox.setRange(0, 100); self.cascade_y_offset_spinbox.setValue(30);
        settings_layout.addRow("级联X偏移 (px):", self.cascade_x_offset_spinbox)
        settings_layout.addRow("级联Y偏移 (px):", self.cascade_y_offset_spinbox)
        main_layout.addWidget(settings_group)
        
        # 动作按钮 (无变化)
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
        self.arrange_cascade_button.clicked.connect(self._emit_arrange_cascade)
        action_buttons_layout.addWidget(self.arrange_cascade_button)
        main_layout.addLayout(action_buttons_layout)

        main_layout.addStretch(1)

    def _emit_arrange_grid(self):
        self.arrange_grid_requested.emit()

    def _emit_arrange_cascade(self):
        x_offset = self.cascade_x_offset_spinbox.value()
        y_offset = self.cascade_y_offset_spinbox.value()
        self.arrange_cascade_requested.emit(x_offset, y_offset)

    def update_detected_windows_list(self, window_infos: list[object]):
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
        selected_windows = []
        for i in range(self.detected_windows_list_widget.count()):
            item = self.detected_windows_list_widget.item(i)
            if item.checkState() == Qt.Checked:
                window_info = item.data(Qt.UserRole)
                if window_info:
                    selected_windows.append(window_info)
        return selected_windows

    def get_filter_keyword(self) -> str:
        return self.filter_keyword_input.text().strip()

    def get_process_name_filter(self) -> str:
        return self.process_name_input.text().strip()
    
    def get_exclude_keywords(self) -> str:
        return self.exclude_title_input.text().strip()
        
    def get_grid_direction(self) -> str:
        return "row-major" if self.grid_direction_combobox.currentIndex() == 0 else "col-major"

    def get_grid_params(self) -> dict:
        return {
            "rows": self.rows_spinbox.value(),
            "cols": self.cols_spinbox.value(),
            "margin_top": self.margin_top_spinbox.value(),
            "margin_bottom": self.margin_bottom_spinbox.value(),
            "margin_left": self.margin_left_spinbox.value(),
            "margin_right": self.margin_right_spinbox.value(),
            "spacing_h": self.spacing_horizontal_spinbox.value(),
            "spacing_v": self.spacing_vertical_spinbox.value(),
        }
    
    def get_cascade_params(self) -> tuple[int, int]:
        return self.cascade_x_offset_spinbox.value(), self.cascade_y_offset_spinbox.value()
    
    def get_selected_screen_index(self) -> int:
        return self.screen_selection_combobox.currentIndex()

    def update_screen_list(self, screen_names: list[str], default_index: int):
        self.screen_selection_combobox.clear()
        if not screen_names:
            self.screen_selection_combobox.addItem("未检测到屏幕")
            self.screen_selection_combobox.setEnabled(False)
        else:
            self.screen_selection_combobox.addItems(screen_names)
            self.screen_selection_combobox.setEnabled(True)
            if 0 <= default_index < len(screen_names):
                self.screen_selection_combobox.setCurrentIndex(default_index)
            else:
                self.screen_selection_combobox.setCurrentIndex(0)

    def load_settings_to_ui(self, settings_data: dict):
        self.filter_keyword_input.setText(settings_data.get("filter_keyword", "完全控制"))
        self.process_name_input.setText(settings_data.get("process_name_filter", ""))
        self.screen_selection_combobox.setCurrentIndex(int(settings_data.get("target_screen_index", 0)))
        self.exclude_title_input.setText(settings_data.get("exclude_title_keywords", "Radmin Viewer"))
        
        direction = settings_data.get("grid_direction", "row-major")
        self.grid_direction_combobox.setCurrentIndex(0 if direction == "row-major" else 1)
        
        self.rows_spinbox.setValue(int(settings_data.get("grid_rows", 2)))
        self.cols_spinbox.setValue(int(settings_data.get("grid_cols", 3)))
        
        self.margin_top_spinbox.setValue(int(settings_data.get("grid_margin_top", 0)))
        self.margin_bottom_spinbox.setValue(int(settings_data.get("grid_margin_bottom", 0)))
        self.margin_left_spinbox.setValue(int(settings_data.get("grid_margin_left", 0)))
        self.margin_right_spinbox.setValue(int(settings_data.get("grid_margin_right", 0)))
        self.spacing_horizontal_spinbox.setValue(int(settings_data.get("grid_spacing_h", 10)))
        self.spacing_vertical_spinbox.setValue(int(settings_data.get("grid_spacing_v", 10)))

        self.cascade_x_offset_spinbox.setValue(int(settings_data.get("cascade_x_offset", 30)))
        self.cascade_y_offset_spinbox.setValue(int(settings_data.get("cascade_y_offset", 30)))