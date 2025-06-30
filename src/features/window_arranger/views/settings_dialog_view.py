# desktop_center/src/features/window_arranger/views/settings_dialog_view.py
import logging
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QPushButton,
                                   QGroupBox, QFormLayout, QSpinBox, QLabel,
                                   QComboBox, QDialogButtonBox)
from PySide6.QtCore import Qt
from PySide6.QtGui import QScreen

from src.core.context import ApplicationContext
from src.features.window_arranger.controllers.sorting_strategy_manager import SortingStrategyManager

class SettingsDialog(QDialog):
    """
    一个独立的对话框，用于管理窗口排列的所有设置。
    """
    def __init__(self, context: ApplicationContext, strategy_manager: SortingStrategyManager, parent=None):
        super().__init__(parent)
        self.context = context
        self.strategy_manager = strategy_manager
        self.setWindowTitle("排列设置")
        self.setMinimumWidth(550)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)

        columns_layout = QHBoxLayout()
        columns_layout.setSpacing(20)

        # --- 左列：网格排列设置 ---
        grid_group = QGroupBox("网格排列设置")
        grid_group.setStyleSheet("QGroupBox { font-size: 14px; font-weight: bold; }")
        grid_form_layout = QFormLayout(grid_group)
        grid_form_layout.setSpacing(12)
        
        self.sorting_strategy_combobox = QComboBox()
        self.sorting_strategy_combobox.setMaximumWidth(200)
        grid_form_layout.addRow("排序方案:", self.sorting_strategy_combobox)

        self.screen_selection_combobox = QComboBox()
        self.screen_selection_combobox.setMaximumWidth(200)
        grid_form_layout.addRow("目标屏幕:", self.screen_selection_combobox)

        self.grid_direction_combobox = QComboBox()
        self.grid_direction_combobox.addItems(["先排满行 (→)", "先排满列 (↓)"])
        self.grid_direction_combobox.setMaximumWidth(200)
        grid_form_layout.addRow("排列方向:", self.grid_direction_combobox)

        self.rows_spinbox = QSpinBox()
        self.rows_spinbox.setRange(1, 20)
        self.rows_spinbox.setMaximumWidth(200)
        grid_form_layout.addRow("行数:", self.rows_spinbox)

        self.cols_spinbox = QSpinBox()
        self.cols_spinbox.setRange(1, 20)
        self.cols_spinbox.setMaximumWidth(200)
        grid_form_layout.addRow("列数:", self.cols_spinbox)
        
        self.margin_top_spinbox = QSpinBox(); self.margin_top_spinbox.setRange(-500, 500); self.margin_top_spinbox.setMaximumWidth(60)
        self.margin_bottom_spinbox = QSpinBox(); self.margin_bottom_spinbox.setRange(-500, 500); self.margin_bottom_spinbox.setMaximumWidth(60)
        self.margin_left_spinbox = QSpinBox(); self.margin_left_spinbox.setRange(-500, 500); self.margin_left_spinbox.setMaximumWidth(60)
        self.margin_right_spinbox = QSpinBox(); self.margin_right_spinbox.setRange(-500, 500); self.margin_right_spinbox.setMaximumWidth(60)
        margin_layout = QHBoxLayout()
        margin_layout.addWidget(QLabel("上:")); margin_layout.addWidget(self.margin_top_spinbox)
        margin_layout.addWidget(QLabel("下:")); margin_layout.addWidget(self.margin_bottom_spinbox)
        margin_layout.addWidget(QLabel("左:")); margin_layout.addWidget(self.margin_left_spinbox)
        margin_layout.addWidget(QLabel("右:")); margin_layout.addWidget(self.margin_right_spinbox)
        margin_layout.addStretch()
        grid_form_layout.addRow("屏幕边距 (px):", margin_layout)

        self.spacing_horizontal_spinbox = QSpinBox(); self.spacing_horizontal_spinbox.setRange(-100, 100); self.spacing_horizontal_spinbox.setMaximumWidth(80)
        self.spacing_vertical_spinbox = QSpinBox(); self.spacing_vertical_spinbox.setRange(-100, 100); self.spacing_vertical_spinbox.setMaximumWidth(80)
        spacing_layout = QHBoxLayout()
        spacing_layout.addWidget(QLabel("水平:")); spacing_layout.addWidget(self.spacing_horizontal_spinbox)
        spacing_layout.addWidget(QLabel("垂直:")); spacing_layout.addWidget(self.spacing_vertical_spinbox)
        spacing_layout.addStretch()
        grid_form_layout.addRow("窗口间距 (px):", spacing_layout)

        self.animation_delay_spinbox = QSpinBox()
        self.animation_delay_spinbox.setRange(0, 500)
        self.animation_delay_spinbox.setSuffix(" ms")
        self.animation_delay_spinbox.setMaximumWidth(200)
        grid_form_layout.addRow("排列动画延时:", self.animation_delay_spinbox)
        
        columns_layout.addWidget(grid_group)

        # --- 右列：其他设置 ---
        other_group = QGroupBox("其他设置")
        other_group.setStyleSheet("QGroupBox { font-size: 14px; font-weight: bold; }")
        
        other_v_layout = QVBoxLayout(other_group)
        other_form_layout = QFormLayout()
        other_form_layout.setSpacing(12)
        
        self.cascade_x_offset_spinbox = QSpinBox(); self.cascade_x_offset_spinbox.setRange(0, 100); self.cascade_x_offset_spinbox.setMaximumWidth(200)
        self.cascade_y_offset_spinbox = QSpinBox(); self.cascade_y_offset_spinbox.setRange(0, 100); self.cascade_y_offset_spinbox.setMaximumWidth(200)
        other_form_layout.addRow("级联X偏移 (px):", self.cascade_x_offset_spinbox)
        other_form_layout.addRow("级联Y偏移 (px):", self.cascade_y_offset_spinbox)
        
        self.enable_notifications_combobox = QComboBox()
        self.enable_notifications_combobox.addItems(["启用", "禁用"])
        self.enable_notifications_combobox.setMaximumWidth(200)
        other_form_layout.addRow("插件操作通知:", self.enable_notifications_combobox)
        
        other_v_layout.addLayout(other_form_layout)
        other_v_layout.addStretch()
        columns_layout.addWidget(other_group, 1)

        main_layout.addLayout(columns_layout)

        button_box = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.save_and_accept)
        button_box.rejected.connect(self.reject)
        main_layout.addWidget(button_box)

        self._populate_sorting_strategies()
        self._populate_screen_selection()
        self.load_settings()

    def _populate_sorting_strategies(self):
        """填充排序策略下拉框。"""
        strategy_names = self.strategy_manager.get_strategy_names()
        self.sorting_strategy_combobox.addItems(strategy_names)

    def _populate_screen_selection(self):
        """填充屏幕选择下拉框。"""
        screens = self.context.app.screens()
        screen_names = []
        for i, screen in enumerate(screens):
            screen_name = f"屏幕 {i+1} ({screen.geometry().width()}x{screen.geometry().height()})"
            if screen == self.context.app.primaryScreen():
                screen_name += " (主屏幕)"
            screen_names.append(screen_name)
        
        self.screen_selection_combobox.clear()
        if not screen_names:
            self.screen_selection_combobox.addItem("未检测到屏幕")
            self.screen_selection_combobox.setEnabled(False)
        else:
            self.screen_selection_combobox.addItems(screen_names)
            self.screen_selection_combobox.setEnabled(True)

    def load_settings(self):
        """从 ConfigService 加载设置到UI。"""
        config = self.context.config_service
        strategy_name = config.get_value("WindowArranger", "sorting_strategy", "默认排序 (按标题)")
        self.sorting_strategy_combobox.setCurrentText(strategy_name)

        self.screen_selection_combobox.setCurrentIndex(int(config.get_value("WindowArranger", "target_screen_index", "0")))
        
        enable_notifications = config.get_value("WindowArranger", "enable_notifications", "true")
        self.enable_notifications_combobox.setCurrentIndex(0 if enable_notifications == 'true' else 1)
        
        direction = config.get_value("WindowArranger", "grid_direction", "row-major")
        self.grid_direction_combobox.setCurrentIndex(0 if direction == "row-major" else 1)
        self.rows_spinbox.setValue(int(config.get_value("WindowArranger", "grid_rows", "2")))
        self.cols_spinbox.setValue(int(config.get_value("WindowArranger", "grid_cols", "3")))
        self.margin_top_spinbox.setValue(int(config.get_value("WindowArranger", "grid_margin_top", "0")))
        self.margin_bottom_spinbox.setValue(int(config.get_value("WindowArranger", "grid_margin_bottom", "0")))
        self.margin_left_spinbox.setValue(int(config.get_value("WindowArranger", "grid_margin_left", "0")))
        self.margin_right_spinbox.setValue(int(config.get_value("WindowArranger", "grid_margin_right", "0")))
        self.spacing_horizontal_spinbox.setValue(int(config.get_value("WindowArranger", "grid_spacing_h", "10")))
        self.spacing_vertical_spinbox.setValue(int(config.get_value("WindowArranger", "grid_spacing_v", "10")))
        self.animation_delay_spinbox.setValue(int(config.get_value("WindowArranger", "animation_delay", "50")))
        self.cascade_x_offset_spinbox.setValue(int(config.get_value("WindowArranger", "cascade_x_offset", "30")))
        self.cascade_y_offset_spinbox.setValue(int(config.get_value("WindowArranger", "cascade_y_offset", "30")))
        logging.info("[WindowArranger] 设置对话框已加载配置。")
        
    def save_settings(self):
        """将UI上的设置保存到 ConfigService。"""
        config = self.context.config_service
        config.set_option("WindowArranger", "sorting_strategy", self.sorting_strategy_combobox.currentText())

        enable_notifications = "true" if self.enable_notifications_combobox.currentIndex() == 0 else "false"
        config.set_option("WindowArranger", "enable_notifications", enable_notifications)
        
        config.set_option("WindowArranger", "target_screen_index", str(self.screen_selection_combobox.currentIndex()))
        direction = "row-major" if self.grid_direction_combobox.currentIndex() == 0 else "col-major"
        config.set_option("WindowArranger", "grid_direction", direction)
        config.set_option("WindowArranger", "grid_rows", str(self.rows_spinbox.value()))
        config.set_option("WindowArranger", "grid_cols", str(self.cols_spinbox.value()))
        config.set_option("WindowArranger", "grid_margin_top", str(self.margin_top_spinbox.value()))
        config.set_option("WindowArranger", "grid_margin_bottom", str(self.margin_bottom_spinbox.value()))
        config.set_option("WindowArranger", "grid_margin_left", str(self.margin_left_spinbox.value()))
        config.set_option("WindowArranger", "grid_margin_right", str(self.margin_right_spinbox.value()))
        config.set_option("WindowArranger", "grid_spacing_h", str(self.spacing_horizontal_spinbox.value()))
        config.set_option("WindowArranger", "grid_spacing_v", str(self.spacing_vertical_spinbox.value()))
        config.set_option("WindowArranger", "animation_delay", str(self.animation_delay_spinbox.value()))
        config.set_option("WindowArranger", "cascade_x_offset", str(self.cascade_x_offset_spinbox.value()))
        config.set_option("WindowArranger", "cascade_y_offset", str(self.cascade_y_offset_spinbox.value()))
        config.save_config()
        logging.info("[WindowArranger] 排列设置已保存。")

    def save_and_accept(self):
        """保存设置并关闭对话框。"""
        self.save_settings()
        self.accept()