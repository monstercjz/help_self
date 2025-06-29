# desktop_center/src/ui/alerts_page.py
import logging
from functools import partial
from PySide6.QtWidgets import (QWidget, QTableWidget, QTableWidgetItem,
                               QHeaderView, QVBoxLayout, QLabel, QPushButton,
                               QMessageBox, QHBoxLayout, QMenu, QSizePolicy)
from PySide6.QtCore import Slot, Qt, QEvent, QSize
from PySide6.QtGui import QColor, QIcon, QAction

from datetime import datetime
from src.services.config_service import ConfigService
from src.services.database_service import DatabaseService
from .history_dialog import HistoryDialog
from .statistics_dialog import StatisticsDialog

SEVERITY_COLORS = {
    "CRITICAL": QColor("#FFDDDD"),
    "WARNING": QColor("#FFFFCC"),
    "INFO": QColor("#FFFFFF")
}

# 定义级别映射字典
LEVEL_DISPLAY_MAP = {
    "INFO": "ℹ️ 正常级别",
    "WARNING": "⚠️ 警告级别",
    "CRITICAL": "❗ 危及级别"
}

# 1. 普通扁平按钮 (用于“启用/禁用”弹窗按钮)
class FlatButton(QPushButton):
    """一个自定义的扁平化按钮，不带菜单。"""
    def __init__(self, text="", parent=None):
        super().__init__(text, parent)
        self.setStyleSheet("""
            QPushButton {
                border: none;
                background-color: transparent;
                text-align: left; /* 图标和文本左对齐 */
                padding: 4px 8px; /* 调整内边距 */
                color: #333;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #e8e8e8;
                border-radius: 4px;
            }
            QPushButton::menu-indicator {
                image: none; /* 确保不显示任何菜单指示器 */
            }
        """)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFlat(True)

# 2. 带有下拉菜单的扁平按钮 (用于“通知级别”和“操作”按钮)
class FlatMenuButton(QPushButton):
    """一个自定义的扁平化按钮，点击后弹出菜单，箭头包含在文本中。"""
    def __init__(self, text="", parent=None):
        super().__init__(text, parent)
        self.setStyleSheet("""
            QPushButton {
                border: none;
                background-color: transparent;
                text-align: left; /* 图标和文本左对齐 */
                padding: 4px 8px;
                color: #333;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #e8e8e8;
                border-radius: 4px;
            }
            QPushButton::menu-indicator {
                image: none; /* 必须隐藏 QPushButton 的默认菜单指示器 */
            }
        """)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFlat(True)
        # 注意：这里我们主动连接clicked信号到showMenu，
        # 因为FlatMenuButton不再是QToolButton，它没有默认的popupMode
        self.clicked.connect(self.showMenu)


class AlertsPageWidget(QWidget):
    """“信息接收中心”功能页面。"""
    def __init__(self, config_service: ConfigService, db_service: DatabaseService, parent=None):
        super().__init__(parent)
        self.config_service = config_service
        self.db_service = db_service
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(15, 0, 15, 15) # 顶部无内边距，让工具栏贴近
        main_layout.setSpacing(10)

        # 工具栏容器
        toolbar_container = self._create_toolbar()
        main_layout.addWidget(toolbar_container)

        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["接收时间", "严重等级", "信息类型", "来源IP", "详细内容"])
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        main_layout.addWidget(self.table)
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        self.clear_button = QPushButton("清空当前显示")
        self.clear_button.setFixedWidth(120)
        self.clear_button.clicked.connect(self.clear_table_display)
        button_layout.addWidget(self.clear_button)
        main_layout.addLayout(button_layout)
        
        self.installEventFilter(self)
        self._load_history_on_startup()
        self._update_toolbar_labels() # 初始加载时更新一次标签

    def _create_toolbar(self):
        """创建工具栏内容，并将其放置在一个带背景和边框的容器中。"""
        toolbar_container = QWidget()
        toolbar_container.setObjectName("ToolbarContainer") # 设置对象名，用于QSS选择器
        toolbar_container.setStyleSheet("""
            #ToolbarContainer {
                background-color: #F8F8F8;
                border-top: 1px solid #E0E0E0;                        
                border-bottom: 1px solid #E0E0E0;
            }
        """)
        toolbar_container.setContentsMargins(15, 10, 15, 10) # 容器内边距
        toolbar_container.setFixedHeight(60) # 固定高度

        toolbar_layout = QHBoxLayout(toolbar_container)
        toolbar_layout.setContentsMargins(0, 0, 0, 0) # 布局的内边距，0让内容贴紧容器
        
        title_label = QLabel("实时信息接收中心")
        title_label.setStyleSheet("font-size: 20px; font-weight: bold;")
        toolbar_layout.addWidget(title_label)
        
        toolbar_layout.addStretch() # 将所有后续内容推到右侧

        # 【新增容器】包裹三个按钮，以便统一设置样式和内边距
        buttons_group_container = QWidget()
        buttons_group_container.setObjectName("ButtonsGroupContainer")
        buttons_group_container.setStyleSheet("""
            #ButtonsGroupContainer {
                border: 1px solid #E0E0E0; /* 细边框 */
                border-radius: 8px; /* 圆角 */
                background-color: transparent; /* 背景透明 */
            }
        """)
        buttons_group_layout = QHBoxLayout(buttons_group_container)
        buttons_group_layout.setContentsMargins(2, 2, 2, 2) # 按钮组内部的微小边距
        buttons_group_layout.setSpacing(0) # 按钮之间无间距，靠边框来分隔

        # 启用/禁用桌面弹窗按钮
        self.popup_status_button = FlatButton("")
        self.popup_status_button.setToolTip("点击切换启用/禁用桌面弹窗")
        self.popup_status_button.clicked.connect(self.toggle_popup_status)
        self.popup_status_button.setFixedWidth(153)
        buttons_group_layout.addWidget(self.popup_status_button)

        # 通知级别阈值按钮
        self.level_status_button = FlatMenuButton()
        self.level_status_button.setToolTip("点击选择通知级别阈值")
        # self.level_status_button.setFixedWidth(145)
        
        level_menu = QMenu(self)
        # 菜单项仍然使用英文值作为内部标识
        for level_key in LEVEL_DISPLAY_MAP.keys():
            # 【修改点】菜单项显示中文文本
            display_text = LEVEL_DISPLAY_MAP[level_key]
            action = QAction(display_text, self)
            # 使用 lambda 来捕获当前的 level_key
            action.triggered.connect(lambda checked=False, key=level_key: self.set_notification_level(key))
            level_menu.addAction(action)
        self.level_status_button.setMenu(level_menu) # 设置菜单
        buttons_group_layout.addWidget(self.level_status_button)

        # 操作菜单按钮
        self.ops_button = FlatMenuButton(" 操作 ▾") # 文本和箭头
        self.ops_button.setToolTip("更多操作")
        ops_icon = QIcon.fromTheme("preferences-system") # 标准齿轮图标
        if not ops_icon.isNull():
            self.ops_button.setIcon(ops_icon)
            self.ops_button.setIconSize(QSize(16, 16))
        else:
            self.ops_button.setText("⚙️ 操作 ▾") # 备用文字
        
        ops_menu = QMenu(self)
        history_action = ops_menu.addAction(QIcon.fromTheme("document-open-recent"), "查看历史记录...")
        stats_action = ops_menu.addAction(QIcon.fromTheme("utilities-system-monitor"), "打开统计分析...")
        ops_menu.addSeparator() # 分隔线
        clear_db_action = ops_menu.addAction(QIcon.fromTheme("edit-delete"), "清空历史记录...")
        
        # 为危险操作设置特殊样式
        font = clear_db_action.font()
        font.setBold(True)
        clear_db_action.setFont(font)
        
        # 连接Action到槽函数
        history_action.triggered.connect(self.show_history_dialog)
        stats_action.triggered.connect(self.show_statistics_dialog)
        clear_db_action.triggered.connect(self.clear_database)
        
        self.ops_button.setMenu(ops_menu) # 设置菜单
        # self.ops_button.setFixedWidth(100)
        buttons_group_layout.addWidget(self.ops_button) # 添加到布局
        
        toolbar_layout.addWidget(buttons_group_container) # 将按钮组容器添加到主工具栏布局
        
        return toolbar_container # 返回整个工具栏容器

    def _update_toolbar_labels(self):
        """根据当前配置更新工具栏上按钮的文本，并显示中文级别。"""
        # 更新桌面弹窗状态按钮文本
        is_enabled = self.config_service.get_value("InfoService", "enable_desktop_popup", "true").lower() == 'true'
        self.popup_status_button.setText(f"  📢 {'桌面通知：启用  ' if is_enabled else '桌面通知：禁用  '}")

        # 获取配置中的英文级别，如 "INFO"
        level_key = self.config_service.get_value("InfoService", "notification_level", "WARNING")
        # 【修改点】使用映射字典来获取中文显示文本，如 "正常"
        display_text = LEVEL_DISPLAY_MAP.get(level_key, level_key) # 如果找不到，则显示原始key
        self.level_status_button.setText(f"{display_text} ▾")

        pass

    def toggle_popup_status(self):
        """切换桌面弹窗的启用/禁用状态。"""
        is_enabled = self.config_service.get_value("InfoService", "enable_desktop_popup", "true").lower() == 'true'
        new_status = not is_enabled
        self.config_service.set_option("InfoService", "enable_desktop_popup", str(new_status).lower())
        self.config_service.save_config()
        self._update_toolbar_labels() # 立即更新UI，反映最新状态
        logging.info(f"桌面弹窗状态已切换为: {'启用' if new_status else '禁用'}")

    def set_notification_level(self, level: str):
        """设置新的通知级别（接收的是英文key，如"INFO"）。"""
        self.config_service.set_option("InfoService", "notification_level", level)
        self.config_service.save_config()
        self._update_toolbar_labels() # 立即更新UI，反映最新状态
        logging.info(f"通知级别已设置为: {level}")

    def show_history_dialog(self):
        """创建并显示历史记录对话框。"""
        # 将对话框作为窗口的子项，确保其生命周期管理和居中显示
        dialog = HistoryDialog(self.db_service, self.config_service, self.window())
        dialog.exec() # exec()使其成为模态对话框

    def show_statistics_dialog(self):
        """创建并显示统计分析对话框。"""
        dialog = StatisticsDialog(self.db_service, self.config_service, self.window())
        dialog.exec() # exec()使其成为模态对话框

    def eventFilter(self, obj, event: QEvent) -> bool:
        """事件过滤器，用于捕获本页面的Show事件，实现工具栏状态同步。"""
        if obj is self and event.type() == QEvent.Type.Show:
            logging.info("信息接收中心页面变为可见，正在同步工具栏状态...")
            self._update_toolbar_labels() # 每次显示页面时更新标签
        return super().eventFilter(obj, event)

    def _load_history_on_startup(self):
        """在程序启动时，根据配置加载历史告警记录。"""
        try:
            limit_str = self.config_service.get_value("InfoService", "load_history_on_startup", "100")
            limit = int(limit_str)
            if limit > 0:
                logging.info(f"正在从数据库加载最近 {limit} 条历史记录...")
                records = self.db_service.get_recent_alerts(limit)
                for record in reversed(records): # 反转列表，让最新记录在顶部
                    self.add_alert(record, is_history=True)
        except (ValueError, TypeError) as e:
            logging.warning(f"无效的 'load_history_on_startup' 配置值: '{limit_str}'. 错误: {e}")

    @Slot(dict)
    def add_alert(self, alert_data: dict, is_history: bool = False):
        """公开的槽函数，用于向表格添加新行并根据严重等级上色。"""
        timestamp = alert_data.get('timestamp')
        if not timestamp or not is_history:
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        self.table.insertRow(0) # 在顶部插入新行
        
        severity = alert_data.get('severity', 'INFO')
        
        items = [
            QTableWidgetItem(timestamp),
            QTableWidgetItem(severity),
            QTableWidgetItem(alert_data.get('type', '未知')),
            QTableWidgetItem(alert_data.get('source_ip', 'N/A')),
            QTableWidgetItem(alert_data.get('message', '无内容'))
        ]
        
        color = SEVERITY_COLORS.get(severity, SEVERITY_COLORS["INFO"])
        
        for col, item in enumerate(items):
            item.setBackground(color) # 设置背景色
            self.table.setItem(0, col, item) # 填充数据

    def clear_table_display(self):
        """只清空UI表格的显示内容。"""
        self.table.setRowCount(0)
        logging.info("UI表格显示已被用户清空。")

    def clear_database(self):
        """清空数据库中的所有历史记录，并带有严格的确认。"""
        reply = QMessageBox.warning(
            self, # 父窗口
            "危险操作确认", # 标题
            "您确定要永久删除所有历史告警记录吗？\n此操作无法撤销！", # 消息
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, # 按钮
            QMessageBox.StandardButton.No # 默认焦点
        )
        if reply == QMessageBox.StandardButton.Yes:
            if self.db_service.clear_all_alerts():
                QMessageBox.information(self, "成功", "所有历史记录已成功清除。")
                self.clear_table_display() # 清空数据库后，同步清空当前显示
            else:
                QMessageBox.critical(self, "失败", "清除历史记录时发生错误，请查看日志。")