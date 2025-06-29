## 项目目录结构**

```
desktop_center/
├── app.py                     # 【主入口】程序启动脚本 (已修改)
├── config.ini                 # 【配置文件】存储应用程序设置 (已修改)
├── icon.png                   # 图标文件
├── requirements.txt           # 【依赖列表】项目所需Python库 (已修改)
│
└── src/                       # 【核心源码包】
    ├── __init__.py            # 将src声明为一个包
    │
    ├── services/              # 存放所有后台服务逻辑
    │   ├── __init__.py
    │   ├── config_service.py    # 配置服务模块 (无修改)
    │   ├── alert_receiver.py    # 告警接收Web服务线程模块 (已修改)
    │   └── database_service.py  # 【新增】数据库服务模块 (已修改)
    │
    ├── ui/                    # 存放所有UI相关的组件
    │   ├── __init__.py
    │   ├── main_window.py       # 主窗口框架 (无修改)
    │   ├── alerts_page.py       # “告警中心”页面 (已修改)
    │   ├── settings_page.py     # “设置”页面 (已修改)
    │   ├── history_dialog.py    # 【新增】历史记录浏览器对话框 (已修改)
    │   └── statistics_dialog.py # 【新增】统计分析对话框 (已修改)
    │
    └── utils/                 # 存放通用工具或管理器
        ├── __init__.py
        └── tray_manager.py      # 系统托盘管理器 (已修改)
```
## app.py

```python
# desktop_center/app.py
import sys
import logging
from PySide6.QtWidgets import QApplication

# 导入核心架构组件
from src.ui.main_window import MainWindow
from src.services.config_service import ConfigService
from src.utils.tray_manager import TrayManager
from src.services.database_service import DatabaseService

# --- 导入功能模块 ---
from src.ui.alerts_page import AlertsPageWidget
from src.ui.settings_page import SettingsPageWidget
from src.services.alert_receiver import AlertReceiverThread
# 导入新的对话框类
from src.ui.history_dialog import HistoryDialog
from src.ui.statistics_dialog import StatisticsDialog

# --- 全局应用程序常量 ---
APP_NAME = "Desktop Control & Monitoring Center"
APP_VERSION = "3.0.1-critical-app-fix" # 版本号更新
CONFIG_FILE = 'config.ini'
ICON_FILE = 'icon.png'
LOG_FILE = 'app.log'
DB_FILE = 'history.db'

def setup_logging():
    """配置全局日志记录器。"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - [%(threadName)s] - %(message)s',
        handlers=[
            logging.FileHandler(LOG_FILE, encoding='utf-8', mode='a'),
            logging.StreamHandler(sys.stdout)
        ]
    )
    logging.info("="*50)
    logging.info("日志系统初始化完成。")

class ApplicationOrchestrator:
    """应用协调器。"""
    def __init__(self):
        logging.info(f"正在启动 {APP_NAME} v{APP_VERSION}...")
        
        # 1. 初始化Qt应用程序实例
        self.app = QApplication(sys.argv)
        self.app.setQuitOnLastWindowClosed(False)

        # 2. 初始化核心服务
        self.config_service = ConfigService(CONFIG_FILE)
        try:
            self.db_service = DatabaseService(DB_FILE)
            self.db_service.init_db()
        except Exception as e:
            logging.critical(f"数据库服务初始化失败，程序无法启动: {e}", exc_info=True)
            sys.exit(1)

        # 3. 初始化主UI框架
        self.window = MainWindow()
        self.window.setWindowTitle(self.config_service.get_value("General", "app_name", APP_NAME))
        
        # 4. 初始化并添加功能页面
        self._add_pages_to_main_window()
        
        # 5. 初始化并启动后台服务线程
        self.alert_receiver_thread = self._setup_background_services()
        
        # 6. 初始化系统托盘管理器
        try:
            self.tray_manager = TrayManager(self.app, self.window, ICON_FILE)
        except FileNotFoundError:
            logging.error(f"关键资源文件 '{ICON_FILE}' 未找到。程序即将退出。")
            sys.exit(1)
            
        # 确保在应用退出时关闭数据库连接
        self.app.aboutToQuit.connect(self.db_service.close)
        logging.info("所有组件初始化和集成完毕。")

    def _add_pages_to_main_window(self):
        """将所有功能页面添加到主窗口。"""
        logging.info("正在创建并添加功能页面...")
        self.alerts_page = AlertsPageWidget(self.config_service, self.db_service)
        self.settings_page = SettingsPageWidget(self.config_service)
        
        self.window.add_page("信息接收中心", self.alerts_page)
        self.window.add_page("设置", self.settings_page)
        logging.info("功能页面添加完成。")
        
    def _setup_background_services(self) -> AlertReceiverThread:
        """配置并启动后台服务线程。"""
        logging.info("正在配置和启动后台服务...")
        host = self.config_service.get_value("InfoService", "host", "0.0.0.0")
        port = int(self.config_service.get_value("InfoService", "port", 5000))
        
        receiver_thread = AlertReceiverThread(
            config_service=self.config_service, 
            db_service=self.db_service,
            host=host, 
            port=port
        )
        
        receiver_thread.new_alert_received.connect(self.alerts_page.add_alert)
        logging.info("后台服务信号已连接到UI槽函数。")
        
        receiver_thread.start()
        return receiver_thread

    def run(self):
        """启动应用程序的事件循环。"""
        logging.info("显示主窗口并启动Qt事件循环...")
        try:
            self.tray_manager.run()
            if self.config_service.get_value("General", "start_minimized", "false").lower() != 'true':
                self.window.show()
            sys.exit(self.app.exec())
        except Exception as e:
            logging.critical(f"应用程序顶层发生未捕获的异常: {e}", exc_info=True)
            sys.exit(1)

if __name__ == '__main__':
    setup_logging()
    main_app = ApplicationOrchestrator()
    main_app.run()
```

## config.ini
```config
[General]
app_name = Desktop Center
start_minimized = false

[InfoService]
host = 0.0.0.0
port = 5000
enable_desktop_popup = true
popup_timeout = 10
notification_level = INFO
load_history_on_startup = 100 

[User]
username = admin
last_login = 2023-10-27

[HistoryPage]
page_size = 50 

```
## tray_manager.py 
```python
# desktop_center/src/utils/tray_manager.py
import logging
import os
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QIcon
from pystray import MenuItem, Icon
from PIL import Image

class TrayManager:
    """
    负责管理系统托盘图标及其菜单。
    这是一个独立的组件，控制着应用的显示、隐藏和退出逻辑。
    """
    def __init__(self, app: QApplication, window: 'MainWindow', icon_path: str):
        """
        初始化托盘管理器。

        Args:
            app (QApplication): Qt应用程序实例，用于安全退出。
            window (MainWindow): 主窗口实例，用于控制其显示/隐藏。
            icon_path (str): 图标文件的路径。

        Raises:
            FileNotFoundError: 如果图标文件不存在。
        """
        self.app = app
        self.window = window

        self.window.setWindowIcon(QIcon(icon_path))
        
        try:
            image = Image.open(icon_path)
        except FileNotFoundError:
            raise FileNotFoundError(f"Icon file not found at: {icon_path}")

        menu = (
            MenuItem('显示主窗口', self.show_window, default=True),
            MenuItem('退出程序', self.quit_app)
        )
        
        # 【最终修正】修正 pystray.Icon 构造函数的参数顺序。
        # 正确的顺序是: name, icon (Image object), title (str), menu
        self.tray_icon = Icon("DesktopCenter", image, "桌面控制与监控中心", menu)
        
        logging.info("系统托盘管理器初始化完成。")

    def run(self) -> None:
        """在后台线程中启动托盘图标的事件监听。"""
        self.tray_icon.run_detached()
        logging.info("系统托盘图标已在独立线程中运行。")

    def show_window(self) -> None:
        """从托盘菜单显示并激活主窗口。"""
        logging.info("通过托盘菜单请求显示主窗口。")
        self.window.show()
        self.window.activateWindow()

    def quit_app(self) -> None:
        """安全地退出整个应用程序。"""
        logging.info("通过托盘菜单请求退出应用程序...")
        
        # 1. 停止pystray图标的事件循环。
        self.tray_icon.stop()
        logging.info("pystray图标已停止。")
        
        # 2. 使用os._exit(0)来强制结束整个Python进程。
        logging.info("正在终止应用程序进程...")
        os._exit(0)
```
## config_service.py 
```python
# desktop_center/src/services/config_service.py
import configparser
import logging
from typing import List, Tuple

class ConfigService:
    """
    健壮的配置服务，负责所有 config.ini 文件的读写逻辑。
    设计目标是即使在配置文件损坏或丢失的情况下也能让主程序安全启动。
    """
    def __init__(self, filepath: str):
        """
        初始化配置服务。

        Args:
            filepath (str): config.ini 文件的路径。
        """
        self.filepath = filepath
        self.config = configparser.ConfigParser()
        self.load_config()

    def load_config(self) -> None:
        """
        从磁盘加载配置文件。
        如果文件不存在或无法解析，将记录一个错误并使用一个空的配置对象，
        这可以防止应用程序在启动时崩溃。
        """
        try:
            # 使用utf-8-sig可以处理带有BOM头的UTF-8文件
            read_files = self.config.read(self.filepath, encoding='utf-8-sig')
            if not read_files:
                logging.warning(f"配置文件 '{self.filepath}' 未找到。将使用空配置。")
            else:
                logging.info(f"成功加载配置文件: {self.filepath}")
        except configparser.Error as e:
            logging.error(f"解析配置文件 '{self.filepath}' 失败: {e}")
            # 解析失败时重置为一个空对象，保证程序健壮性
            self.config = configparser.ConfigParser()

    def get_sections(self) -> List[str]:
        """获取所有配置区段的名称列表。"""
        return self.config.sections()

    def get_options(self, section: str) -> List[Tuple[str, str]]:
        """获取指定区段下的所有键值对。"""
        if self.config.has_section(section):
            return self.config.items(section)
        return []

    def get_value(self, section: str, option: str, fallback: str = None) -> str:
        """安全地获取一个配置值，可提供默认值。"""
        return self.config.get(section, option, fallback=fallback)

    def set_option(self, section: str, option: str, value: str) -> None:
        """设置一个配置值。如果区段不存在，则自动创建。"""
        if not self.config.has_section(section):
            self.config.add_section(section)
        self.config.set(section, option, str(value))

    def save_config(self) -> bool:
        """
        将当前配置状态写回文件。

        Returns:
            bool: 如果保存成功则返回 True，否则返回 False。
        """
        try:
            with open(self.filepath, 'w', encoding='utf-8') as configfile:
                self.config.write(configfile)
            logging.info(f"配置文件已成功保存到: {self.filepath}")
            return True
        except IOError as e:
            logging.error(f"保存配置文件到 '{self.filepath}' 失败: {e}")
            return False
```
## main_window.py
```python
# desktop_center/src/ui/main_window.py
import logging  # 【修正】添加对logging模块的导入
from PySide6.QtWidgets import (QMainWindow, QWidget, QListWidget, QListWidgetItem, 
                               QHBoxLayout, QStackedWidget)
from PySide6.QtCore import QEvent, QSize

class MainWindow(QMainWindow):
    """
    主应用程序窗口框架。
    采用“导航-内容”布局，设计为可扩展的容器。
    它自身不实现任何具体功能页面，只提供添加和切换页面的能力。
    """
    def __init__(self, parent: QWidget = None):
        """
        初始化主窗口。

        Args:
            parent (QWidget, optional): 父组件。默认为 None。
        """
        super().__init__(parent)
        self.setWindowTitle("Application Skeleton") # 初始标题，可由app.py覆盖
        self.setGeometry(100, 100, 900, 700) # 初始尺寸

        # --- 创建主布局 ---
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QHBoxLayout(main_widget)
        main_layout.setContentsMargins(0, 0, 0, 0) # 无边距，让子组件填满
        main_layout.setSpacing(0)

        # --- 左侧导航栏 ---
        self.nav_list = QListWidget()
        self.nav_list.setFixedWidth(180)
        self.nav_list.setStyleSheet("""
            QListWidget {
                background-color: #f0f0f0;
                border: none;
                font-size: 14px;
                padding-top: 10px;
            }
            QListWidget::item {
                padding: 12px 20px;
                border-bottom: 1px solid #e0e0e0;
            }
            QListWidget::item:selected {
                background-color: #0078d4;
                color: white;
                font-weight: bold;
                border-left: 5px solid #005a9e;
            }
        """)
        main_layout.addWidget(self.nav_list)
        
        # --- 右侧内容区 (使用QStackedWidget实现页面切换) ---
        self.stacked_widget = QStackedWidget()
        main_layout.addWidget(self.stacked_widget)

        # --- 连接信号与槽 ---
        # 当导航栏的当前项改变时，切换到对应的页面
        self.nav_list.currentRowChanged.connect(self.stacked_widget.setCurrentIndex)
    
    def add_page(self, title: str, widget: QWidget) -> None:
        """
        向主窗口动态添加一个功能页面。

        Args:
            title (str): 显示在导航栏中的页面标题。
            widget (QWidget): 要添加的功能页面的实例。
        """
        # 将页面实例添加到堆栈窗口中
        self.stacked_widget.addWidget(widget)
        # 将页面标题添加到导航列表
        self.nav_list.addItem(QListWidgetItem(title))
        
        # 默认选中第一个添加的页面
        if self.nav_list.count() == 1:
            self.nav_list.setCurrentRow(0)

    def closeEvent(self, event: QEvent) -> None:
        """
        重写窗口关闭事件。
        默认行为是隐藏窗口而不是退出应用，以便在系统托盘中继续运行。
        
        Args:
            event (QEvent): 关闭事件对象。
        """
        logging.info("关闭事件触发：隐藏主窗口到系统托盘。")
        event.ignore()  # 忽略默认的关闭行为（即退出）
        self.hide()     # 将窗口隐藏
```
## settings_page.py
```python
# desktop_center/src/ui/settings_page.py
import logging
from PySide6.QtWidgets import (QWidget, QLabel, QVBoxLayout, QGroupBox,
                               QLineEdit, QPushButton, QMessageBox, QFormLayout,
                               QComboBox, QSpinBox, QScrollArea, QHBoxLayout)
from PySide6.QtCore import Qt, QEvent

from src.services.config_service import ConfigService

# 【核心修改】元数据结构现在与最终的config.ini完全匹配
SETTING_METADATA = {
    "General": {
        "app_name": {"widget": "lineedit", "label": "应用程序名称"},
        "start_minimized": {"widget": "combobox", "label": "启动时最小化", "items": ["禁用", "启用"], "map": {"启用": "true", "禁用": "false"}}
    },
    "InfoService": { # 新的统一区段
        "host": {"widget": "lineedit", "label": "监听地址", "col": 0},
        "port": {"widget": "spinbox", "label": "监听端口", "min": 1024, "max": 65535, "col": 0},
        "enable_desktop_popup": {"widget": "combobox", "label": "桌面弹窗通知", "items": ["禁用", "启用"], "map": {"启用": "true", "禁用": "false"}, "col": 0},
        "popup_timeout": {"widget": "spinbox", "label": "弹窗显示时长 (秒)", "min": 1, "max": 300, "col": 1},
        "notification_level": {"widget": "combobox", "label": "通知级别阈值", "items": ["INFO", "WARNING", "CRITICAL"], "col": 1},
        "load_history_on_startup": {"widget": "combobox", "label": "启动时加载历史", "items": ["不加载", "加载最近50条", "加载最近100条", "加载最近500条"], "map": {"不加载": "0", "加载最近50条": "50", "加载最近100条": "100", "加载最近500条": "500"}, "col": 1}
    }
}

class SettingsPageWidget(QWidget):
    """
    “设置”功能页面。
    采用“元数据驱动”和“卡片式布局”进行重构，提升了可维护性和用户体验。
    """
    def __init__(self, config_service: ConfigService, parent=None):
        super().__init__(parent)
        self.config_service = config_service
        self.editors = {}

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)

        title_label = QLabel("应用程序设置")
        title_label.setStyleSheet("font-size: 22px; font-weight: bold; margin-bottom: 10px; color: #333;")
        main_layout.addWidget(title_label)
        
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet("QScrollArea { border: none; background-color: transparent; }")
        
        content_widget = QWidget()
        self.settings_layout = QVBoxLayout(content_widget)
        self.settings_layout.setSpacing(15)
        self.settings_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        scroll_area.setWidget(content_widget)
        main_layout.addWidget(scroll_area)

        self._create_setting_cards()

        self.save_button = QPushButton("保存所有设置")
        self.save_button.setMinimumHeight(35)
        self.save_button.setStyleSheet("""
            QPushButton { font-size: 14px; font-weight: bold; background-color: #0078d4; color: white; border: none; border-radius: 5px; padding: 0 20px; }
            QPushButton:hover { background-color: #005a9e; }
            QPushButton:pressed { background-color: #004578; }
        """)
        self.save_button.clicked.connect(self.save_settings)
        main_layout.addWidget(self.save_button, 0, Qt.AlignmentFlag.AlignRight)

        self.installEventFilter(self)

    # 【核心修改】UI创建逻辑大幅简化
    def _create_setting_cards(self):
        """根据元数据动态创建所有设置卡片。"""
        for section, options_meta in SETTING_METADATA.items():
            card = QGroupBox(section)
            card.setStyleSheet("""
                QGroupBox { font-size: 16px; font-weight: bold; color: #333; background-color: #fcfcfc; border: 1px solid #e0e0e0; border-radius: 8px; margin-top: 10px; }
                QGroupBox::title { subcontrol-origin: margin; subcontrol-position: top left; padding: 0 10px; left: 10px; background-color: #fcfcfc; }
            """)
            
            # 【核心修改】根据section名，选择不同的布局策略
            if section == "InfoService":
                self._populate_multi_column_layout(card, section, options_meta)
            else:
                form_layout = QFormLayout(card)
                form_layout.setSpacing(12)
                form_layout.setContentsMargins(20, 30, 20, 20)
                self._populate_form_layout(form_layout, section, options_meta)
            
            self.settings_layout.addWidget(card)

    def _populate_multi_column_layout(self, parent_group: QGroupBox, section_name: str, options_meta: dict):
        """为InfoService卡片创建多列布局。"""
        # 主水平布局
        main_hbox = QHBoxLayout(parent_group)
        main_hbox.setSpacing(40)
        main_hbox.setContentsMargins(20, 30, 20, 20)

        # 创建两个垂直的表单布局作为列
        column1_layout = QFormLayout()
        column1_layout.setSpacing(12)
        column2_layout = QFormLayout()
        column2_layout.setSpacing(12)

        # 根据元数据中的 'col' 键，将控件分配到不同的列
        for key, meta in options_meta.items():
            target_layout = column1_layout if meta.get("col", 0) == 0 else column2_layout
            self._add_widget_to_form(target_layout, section_name, key, meta)
        
        main_hbox.addLayout(column1_layout)
        main_hbox.addLayout(column2_layout)

    def _populate_form_layout(self, form_layout: QFormLayout, section_name: str, options_meta: dict):
        """将控件填充到给定的单列QFormLayout中。"""
        for key, meta in options_meta.items():
            self._add_widget_to_form(form_layout, section_name, key, meta)

    def _add_widget_to_form(self, form_layout: QFormLayout, section_name: str, key: str, meta: dict):
        """辅助方法：创建一个控件并将其添加到表单布局中。"""
        if section_name not in self.editors:
            self.editors[section_name] = {}
            
        widget_type = meta["widget"]
        label_text = meta["label"]
        editor_widget = None

        if widget_type == "lineedit":
            editor_widget = QLineEdit()
        elif widget_type == "spinbox":
            editor_widget = QSpinBox()
            editor_widget.setRange(meta.get("min", 0), meta.get("max", 99999))
        elif widget_type == "combobox":
            editor_widget = QComboBox()
            editor_widget.addItems(meta["items"])
            editor_widget.setMaximumWidth(200) # 稍微减小最大宽度

        if editor_widget:
            form_layout.addRow(QLabel(f"{label_text}:"), editor_widget)
            self.editors[section_name][key] = editor_widget

    # ... (其他方法保持不变, 逻辑上不再需要做任何特殊处理)

    def _load_settings_to_ui(self):
        logging.info("正在同步全局设置页面UI...")
        for section, options in self.editors.items():
            for key, widget in options.items():
                meta = SETTING_METADATA[section][key]
                current_value = self.config_service.get_value(section, key)

                if isinstance(widget, QLineEdit):
                    widget.setText(current_value)
                elif isinstance(widget, QSpinBox):
                    widget.setValue(int(current_value) if current_value and current_value.isdigit() else meta.get("min", 0))
                elif isinstance(widget, QComboBox):
                    if "map" in meta:
                        display_text = next((text for text, val in meta["map"].items() if val == current_value), meta["items"][0])
                        widget.setCurrentText(display_text)
                    else:
                        if current_value in meta["items"]:
                            widget.setCurrentText(current_value)

    def eventFilter(self, obj, event: QEvent) -> bool:
        if obj is self and event.type() == QEvent.Type.Show:
            self._load_settings_to_ui()
        return super().eventFilter(obj, event)

    def save_settings(self):
        logging.info("尝试保存所有设置...")
        try:
            for section, options in self.editors.items():
                for key, widget in options.items():
                    meta = SETTING_METADATA[section][key]
                    value = None
                    if isinstance(widget, QLineEdit):
                        value = widget.text()
                    elif isinstance(widget, QSpinBox):
                        value = str(widget.value())
                    elif isinstance(widget, QComboBox):
                        if "map" in meta:
                            value = meta["map"].get(widget.currentText())
                        else:
                            value = widget.currentText()
                    
                    if value is not None:
                        self.config_service.set_option(section, key, value)
            
            if self.config_service.save_config():
                QMessageBox.information(self, "成功", "所有设置已成功保存！")
            else:
                QMessageBox.warning(self, "失败", "保存设置时发生错误，请查看日志。")
        except Exception as e:
            logging.error(f"保存设置时发生未知错误: {e}", exc_info=True)
            QMessageBox.critical(self, "严重错误", f"保存设置时发生严重错误: {e}")
```
## database_service.py
```python
# desktop_center/src/services/database_service.py
import sqlite3
import logging
from typing import List, Dict, Any, Tuple
from datetime import datetime

class DatabaseService:
    """
    负责所有与SQLite数据库交互的服务。
    包括初始化、插入、查询和删除告警记录。
    """
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.conn = None
        try:
            self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
            self.conn.row_factory = sqlite3.Row
            logging.info(f"数据库连接已成功建立: {self.db_path}")
        except sqlite3.Error as e:
            logging.error(f"数据库连接失败: {e}", exc_info=True)
            raise

    def init_db(self):
        """
        初始化数据库，如果表不存在，则创建它。
        同时创建必要的索引以提高查询性能。
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS alerts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    severity TEXT NOT NULL,
                    type TEXT NOT NULL,
                    source_ip TEXT,
                    message TEXT
                )
            """)
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_alerts_timestamp ON alerts (timestamp DESC)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_alerts_severity ON alerts (severity)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_alerts_type ON alerts (type)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_alerts_source_ip ON alerts (source_ip)")
            self.conn.commit()
            logging.info("数据库表 'alerts' 初始化完成，并创建了索引。")
        except sqlite3.Error as e:
            logging.error(f"创建数据库表失败: {e}", exc_info=True)

    def add_alert(self, alert_data: Dict[str, Any]) -> None:
        """
        将一条新的告警记录插入到数据库。
        """
        sql = ''' INSERT INTO alerts(timestamp, severity, type, source_ip, message)
                  VALUES(datetime('now', 'localtime'),?,?,?,?) '''
        try:
            cursor = self.conn.cursor()
            cursor.execute(sql, (
                alert_data.get('severity', 'INFO'),
                alert_data.get('type', 'Unknown'),
                alert_data.get('source_ip', 'N/A'),
                alert_data.get('message', 'N/A')
            ))
            self.conn.commit()
        except sqlite3.Error as e:
            logging.error(f"向数据库插入告警失败: {e}", exc_info=True)

    def get_recent_alerts(self, limit: int = 100) -> List[Dict[str, Any]]:
        """
        获取最近的N条告警记录。
        """
        if limit <= 0:
            return []
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT * FROM alerts ORDER BY timestamp DESC LIMIT ?", (limit,))
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
        except sqlite3.Error as e:
            logging.error(f"从数据库查询最近告警失败: {e}", exc_info=True)
            return []

    def clear_all_alerts(self) -> bool:
        """
        删除'alerts'表中的所有记录。
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute("DELETE FROM alerts")
            cursor.execute("DELETE FROM sqlite_sequence WHERE name='alerts'")
            self.conn.commit()
            logging.info("数据库'alerts'表中的所有记录已被清除。")
            return True
        except sqlite3.Error as e:
            logging.error(f"清空数据库表失败: {e}", exc_info=True)
            return False
            
    def delete_alerts_by_ids(self, alert_ids: List[int]) -> bool:
        """
        根据提供的ID列表删除告警记录。
        """
        if not alert_ids:
            return True
        
        placeholders = ','.join('?' for _ in alert_ids)
        sql = f"DELETE FROM alerts WHERE id IN ({placeholders})"
        try:
            cursor = self.conn.cursor()
            cursor.execute(sql, alert_ids)
            self.conn.commit()
            logging.info(f"成功删除 {cursor.rowcount} 条告警记录。IDs: {alert_ids}")
            return True
        except sqlite3.Error as e:
            logging.error(f"删除告警记录失败: {e}", exc_info=True)
            return False

    def close(self):
        """关闭数据库连接。"""
        if self.conn:
            self.conn.close()
            logging.info("数据库连接已关闭。")

    def search_alerts(self, 
                      start_date: str = None, 
                      end_date: str = None, 
                      severities: List[str] = None, 
                      keyword: str = None, 
                      search_field: str = 'all', 
                      page: int = 1, 
                      page_size: int = 50,
                      order_by: str = 'timestamp',
                      order_direction: str = 'DESC'
    ) -> Tuple[List[Dict[str, Any]], int]:
        """
        根据多个条件搜索告警记录，并支持分页和排序。
        """
        sql_parts = ["SELECT id, timestamp, severity, type, source_ip, message FROM alerts WHERE 1=1"]
        count_sql_parts = ["SELECT COUNT(*) FROM alerts WHERE 1=1"]
        params = []

        if start_date:
            sql_parts.append("AND timestamp >= ?")
            count_sql_parts.append("AND timestamp >= ?")
            params.append(start_date + " 00:00:00")
        if end_date:
            sql_parts.append("AND timestamp <= ?")
            count_sql_parts.append("AND timestamp <= ?")
            params.append(end_date + " 23:59:59")

        if severities and len(severities) > 0:
            placeholders = ','.join('?' for _ in severities)
            sql_parts.append(f"AND severity IN ({placeholders})")
            count_sql_parts.append(f"AND severity IN ({placeholders})")
            params.extend(severities)

        if keyword:
            like_keyword = f"%{keyword}%"
            if search_field == 'all':
                sql_parts.append("AND (message LIKE ? OR source_ip LIKE ? OR type LIKE ?)")
                count_sql_parts.append("AND (message LIKE ? OR source_ip LIKE ? OR type LIKE ?)")
                params.extend([like_keyword, like_keyword, like_keyword])
            elif search_field == 'message':
                sql_parts.append("AND message LIKE ?")
                count_sql_parts.append("AND message LIKE ?")
                params.append(like_keyword)
            elif search_field == 'source_ip':
                sql_parts.append("AND source_ip LIKE ?")
                count_sql_parts.append("AND source_ip LIKE ?")
                params.append(like_keyword)
            elif search_field == 'type':
                sql_parts.append("AND type LIKE ?")
                count_sql_parts.append("AND type LIKE ?")
                params.append(like_keyword)

        valid_order_by_fields = ['id', 'timestamp', 'severity', 'type', 'source_ip']
        if order_by not in valid_order_by_fields:
            logging.warning(f"无效的排序字段: {order_by}，将使用默认timestamp。")
            order_by = 'timestamp'
        
        valid_order_directions = ['ASC', 'DESC']
        if order_direction.upper() not in valid_order_directions:
            logging.warning(f"无效的排序方向: {order_direction}，将使用默认DESC。")
            order_direction = 'DESC'

        sql_parts.append(f"ORDER BY {order_by} {order_direction}")

        try:
            cursor = self.conn.cursor()

            count_sql = " ".join(count_sql_parts)
            total_count_params = params[:]
            cursor.execute(count_sql, total_count_params)
            total_count = cursor.fetchone()[0]

            main_sql = " ".join(sql_parts)
            offset = (page - 1) * page_size
            main_sql += f" LIMIT ? OFFSET ?"
            
            main_params = params + [page_size, offset]
            
            cursor.execute(main_sql, main_params)
            rows = cursor.fetchall()
            results = [dict(row) for row in rows]

            return results, total_count
        except sqlite3.Error as e:
            logging.error(f"数据库搜索失败: {e}", exc_info=True)
            return [], 0

    def get_stats_by_type(self, start_date: str = None, end_date: str = None) -> List[Dict[str, Any]]:
        """
        统计指定日期范围内各告警类型的数量。
        """
        sql_parts = ["SELECT type, COUNT(*) AS count FROM alerts WHERE 1=1"]
        params = []

        if start_date:
            sql_parts.append("AND timestamp >= ?")
            params.append(start_date + " 00:00:00")
        if end_date:
            sql_parts.append("AND timestamp <= ?")
            params.append(end_date + " 23:59:59")

        sql_parts.append("GROUP BY type ORDER BY count DESC")
        full_sql = " ".join(sql_parts)

        try:
            cursor = self.conn.cursor()
            cursor.execute(full_sql, params)
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
        except sqlite3.Error as e:
            logging.error(f"按类型统计查询失败: {e}", exc_info=True)
            return []

    def get_stats_by_ip_activity(self, start_date: str = None, end_date: str = None) -> List[Dict[str, Any]]:
        """
        统计指定日期范围内各IP的告警数量。
        """
        sql_parts = ["SELECT source_ip, COUNT(*) AS count FROM alerts WHERE 1=1"]
        params = []

        if start_date:
            sql_parts.append("AND timestamp >= ?")
            params.append(start_date + " 00:00:00")
        if end_date:
            sql_parts.append("AND timestamp <= ?")
            params.append(end_date + " 23:59:59")

        sql_parts.append("GROUP BY source_ip ORDER BY count DESC")
        full_sql = " ".join(sql_parts)

        try:
            cursor = self.conn.cursor()
            cursor.execute(full_sql, params)
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
        except sqlite3.Error as e:
            logging.error(f"按IP活跃度统计查询失败: {e}", exc_info=True)
            return []
    
    # 【核心修正】恢复被误删的方法 get_stats_by_hour
    def get_stats_by_hour(self, start_date: str, end_date: str) -> List[Dict[str, Any]]:
        """
        统计指定日期范围内每小时的告警数量 (全局)。
        """
        sql = """
            SELECT
                CAST(strftime('%H', timestamp) AS INTEGER) AS hour,
                COUNT(*) AS count
            FROM
                alerts
            WHERE
                timestamp >= ? AND timestamp <= ?
            GROUP BY
                hour
            ORDER BY
                hour ASC
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute(sql, (start_date + " 00:00:00", end_date + " 23:59:59"))
            rows = cursor.fetchall()
            
            hourly_counts = {row['hour']: row['count'] for row in rows}
            full_24_hours_results = []
            for h in range(24):
                full_24_hours_results.append({'hour': h, 'count': hourly_counts.get(h, 0)})
            
            return full_24_hours_results
        except sqlite3.Error as e:
            logging.error(f"全局按小时统计查询失败: {e}", exc_info=True)
            return []
            
    # 【核心修正】恢复被误删的方法 get_stats_by_ip_and_hour
    def get_stats_by_ip_and_hour(self, ip_address: str, start_date: str, end_date: str) -> List[Dict[str, Any]]:
        """
        统计指定IP在指定日期范围内每小时的告警数量。
        """
        sql = """
            SELECT
                CAST(strftime('%H', timestamp) AS INTEGER) AS hour,
                COUNT(*) AS count
            FROM
                alerts
            WHERE
                source_ip = ? AND timestamp >= ? AND timestamp <= ?
            GROUP BY
                hour
            ORDER BY
                hour ASC
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute(sql, (ip_address, start_date + " 00:00:00", end_date + " 23:59:59"))
            rows = cursor.fetchall()
            
            hourly_counts = {row['hour']: row['count'] for row in rows}
            full_24_hours_stats = []
            for hour in range(24):
                full_24_hours_stats.append({'hour': hour, 'count': hourly_counts.get(hour, 0)})
            
            return full_24_hours_stats
        except sqlite3.Error as e:
            logging.error(f"按IP按小时统计查询失败: {e}", exc_info=True)
            return []

    # 【新增】获取详细的、按小时、级别和类型分组的统计数据
    def get_detailed_hourly_stats(self, start_date: str, end_date: str, ip_address: str = None) -> List[Dict[str, Any]]:
        """
        获取指定日期范围内按小时、严重等级和类型分组的详细告警统计。
        """
        sql_parts = [
            "SELECT",
            "    CAST(strftime('%H', timestamp) AS INTEGER) AS hour,",
            "    severity,",
            "    type,",
            "    COUNT(*) AS count",
            "FROM alerts",
            "WHERE timestamp >= ? AND timestamp <= ?"
        ]
        params = [start_date + " 00:00:00", end_date + " 23:59:59"]

        if ip_address:
            sql_parts.append("AND source_ip = ?")
            params.append(ip_address)

        sql_parts.extend([
            "GROUP BY hour, severity, type",
            "ORDER BY hour ASC, severity ASC, type ASC"
        ])
        
        full_sql = " ".join(sql_parts)

        try:
            cursor = self.conn.cursor()
            cursor.execute(full_sql, params)
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
        except sqlite3.Error as e:
            logging.error(f"获取详细按小时统计失败: {e}", exc_info=True)
            return []

    def get_distinct_source_ips(self, start_date: str = None, end_date: str = None) -> List[str]:
        """
        获取指定日期范围内所有不重复的来源IP地址列表，按活跃度降序排列。
        """
        sql_parts = ["SELECT source_ip, COUNT(*) as count FROM alerts WHERE source_ip IS NOT NULL AND source_ip != 'N/A'"]
        params = []

        if start_date:
            sql_parts.append("AND timestamp >= ?")
            params.append(start_date + " 00:00:00")
        if end_date:
            sql_parts.append("AND timestamp <= ?")
            params.append(end_date + " 23:59:59")

        sql_parts.append("GROUP BY source_ip ORDER BY count DESC")
        full_sql = " ".join(sql_parts)

        try:
            cursor = self.conn.cursor()
            cursor.execute(full_sql, params)
            rows = cursor.fetchall()
            return [row['source_ip'] for row in rows]
        except sqlite3.Error as e:
            logging.error(f"获取不重复IP列表失败: {e}", exc_info=True)
            return []
```
## history_dialog.py 
```python 
# desktop_center/src/ui/history_dialog.py
import logging
import os
import csv # 用于导出CSV
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QLabel, QTableWidget,
                               QTableWidgetItem, QHeaderView, QHBoxLayout,
                               QDateEdit, QLineEdit, QPushButton, QComboBox,
                               # 【核心修正】QCheckBox 替换为 QRadioButton
                               QRadioButton, QButtonGroup, QSpacerItem, QSizePolicy,
                               QMenu, QApplication, QMessageBox, QFileDialog)
from PySide6.QtCore import Qt, QDate, QCoreApplication, QTimer, QSize
from PySide6.QtGui import QColor, QIcon, QAction
from typing import List, Dict, Any, Tuple
from src.services.database_service import DatabaseService
from src.services.config_service import ConfigService

SEVERITY_COLORS = {
    "CRITICAL": QColor("#FFDDDD"),
    "WARNING": QColor("#FFFFCC"),
    "INFO": QColor("#FFFFFF")
}

# 【修正】移除自定义排序图标常量 (这些常量已在上一轮修正中被移除，此处保留为注释说明)
# ORDER_ASC_ICON = QIcon.fromTheme("go-up") # 上箭头
# ORDER_DESC_ICON = QIcon.fromTheme("go-down") # 下箭头
# ORDER_NONE_ICON = QIcon() # 无图标

class HistoryDialog(QDialog):
    """
    一个独立的对话框，用于浏览和查询历史告警记录。
    提供日期范围、严重等级、关键词搜索、分页、排序、导出和删除功能。
    """
    def __init__(self, db_service: DatabaseService, config_service: ConfigService, parent=None):
        super().__init__(parent)
        self.db_service = db_service
        self.config_service = config_service
        self.setWindowTitle("历史记录浏览器")
        self.setMinimumSize(950, 700)
        
        self.current_page = 1
        # 【修改】从config_service获取page_size
        self.page_size = int(self.config_service.get_value("HistoryPage", "page_size", "50"))
        self.total_records = 0
        self.total_pages = 0

        # 【新增】排序状态变量
        self.current_sort_column_db = 'timestamp' # 数据库字段名
        self.current_sort_direction = 'DESC' # 排序方向 'ASC' 或 'DESC'
        
        self._init_ui()
        self._connect_signals()
        self._load_initial_data()

    def _init_ui(self):
        """初始化对话框的UI布局和控件。"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(10)

        # 【新增】日期筛选快捷按钮布局
        date_shortcut_layout = QHBoxLayout()
        date_shortcut_layout.addWidget(QLabel("快捷日期:"))
        self.btn_today = QPushButton("今天")
        self.btn_yesterday = QPushButton("昨天")
        self.btn_last_7_days = QPushButton("近7天")
        self.btn_last_30_days = QPushButton("近30天")
        date_shortcut_layout.addWidget(self.btn_today)
        date_shortcut_layout.addWidget(self.btn_yesterday)
        date_shortcut_layout.addWidget(self.btn_last_7_days)
        date_shortcut_layout.addWidget(self.btn_last_30_days)
        date_shortcut_layout.addStretch()
        main_layout.addLayout(date_shortcut_layout)

        filter_layout = QHBoxLayout()
        
        filter_layout.addWidget(QLabel("日期范围:"))
        self.start_date_edit = QDateEdit(calendarPopup=True)
        self.start_date_edit.setDate(QDate.currentDate().addDays(-7))
        self.start_date_edit.setMinimumWidth(100)
        filter_layout.addWidget(self.start_date_edit)
        filter_layout.addWidget(QLabel("到"))
        self.end_date_edit = QDateEdit(calendarPopup=True)
        self.end_date_edit.setDate(QDate.currentDate())
        self.end_date_edit.setMinimumWidth(100)
        filter_layout.addWidget(self.end_date_edit)

        filter_layout.addWidget(QLabel("严重等级:"))
        severity_group_layout = QHBoxLayout()
        # 【核心修正】将所有严重等级选项都使用 QRadioButton，并加入到排他性的 QButtonGroup 中
        self.severity_buttons = QButtonGroup(self)
        self.severity_buttons.setExclusive(True) # 确保只有其中一个被选中
        
        self.severity_all = QRadioButton("全部")
        self.severity_info = QRadioButton("信息")
        self.severity_warning = QRadioButton("警告")
        self.severity_critical = QRadioButton("危急")

        # 默认选中“全部”
        self.severity_all.setChecked(True)

        severity_group_layout.addWidget(self.severity_all)
        severity_group_layout.addWidget(self.severity_info)
        severity_group_layout.addWidget(self.severity_warning)
        severity_group_layout.addWidget(self.severity_critical)
        
        # 将所有 RadioButton 添加到 QButtonGroup
        self.severity_buttons.addButton(self.severity_all)
        self.severity_buttons.addButton(self.severity_info)
        self.severity_buttons.addButton(self.severity_warning)
        self.severity_buttons.addButton(self.severity_critical)
        
        filter_layout.addLayout(severity_group_layout)

        filter_layout.addWidget(QLabel("关键词:"))
        self.keyword_edit = QLineEdit()
        self.keyword_edit.setPlaceholderText("请输入关键词...")
        self.keyword_edit.setMinimumWidth(150)
        filter_layout.addWidget(self.keyword_edit)

        self.search_field_combo = QComboBox()
        self.search_field_combo.addItems(["所有字段", "消息内容", "来源IP", "信息类型"])
        filter_layout.addWidget(self.search_field_combo)

        self.query_button = QPushButton("查询")
        self.query_button.setStyleSheet("background-color: #0078d4; color: white; border-radius: 4px; padding: 4px 10px;")
        filter_layout.addWidget(self.query_button)

        self.reset_button = QPushButton("重置")
        self.reset_button.setStyleSheet("background-color: #f0f0f0; border-radius: 4px; padding: 4px 10px;")
        filter_layout.addWidget(self.reset_button)
        
        filter_layout.addStretch()
        main_layout.addLayout(filter_layout)

        self.table = QTableWidget()
        self.table.setColumnCount(6)
        # 【修改】更新列标签，添加ID列
        self.table_header_labels = ["ID", "接收时间", "严重等级", "信息类型", "来源IP", "详细内容"]
        self.table.setHorizontalHeaderLabels(self.table_header_labels)
        
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents) # ID列
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents) # 接收时间
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents) # 严重等级
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents) # 信息类型
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents) # 来源IP

        # 【新增】允许点击列头进行排序
        header.setSectionsClickable(True)
        # 【新增】设置右键菜单策略
        self.table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)

        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows) # 整行选中
        self.table.setSelectionMode(QTableWidget.SelectionMode.ExtendedSelection) # 允许Ctrl/Shift多选
        main_layout.addWidget(self.table)
        
        pagination_layout = QHBoxLayout()
        self.status_label = QLabel("正在加载...")
        pagination_layout.addWidget(self.status_label)
        
        # 【新增】导出按钮
        self.export_button = QPushButton("导出当前查询")
        self.export_button.setStyleSheet("background-color: #f0f0f0; border-radius: 4px; padding: 4px 10px;")
        pagination_layout.addWidget(self.export_button)

        # 【新增】删除选中按钮
        self.delete_selected_button = QPushButton("删除选中记录")
        self.delete_selected_button.setStyleSheet("background-color: #e04a4a; color: white; border-radius: 4px; padding: 4px 10px;")
        pagination_layout.addWidget(self.delete_selected_button)

        pagination_layout.addStretch()

        self.first_page_button = QPushButton("首页")
        self.prev_page_button = QPushButton("上一页")
        self.page_number_edit = QLineEdit("1")
        self.page_number_edit.setFixedWidth(40)
        self.page_number_edit.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.next_page_button = QPushButton("下一页")
        self.last_page_button = QPushButton("末页")

        pagination_layout.addWidget(self.first_page_button)
        pagination_layout.addWidget(self.prev_page_button)
        pagination_layout.addWidget(self.page_number_edit)
        pagination_layout.addWidget(self.next_page_button)
        pagination_layout.addWidget(self.last_page_button)
        
        main_layout.addLayout(pagination_layout)

    def _connect_signals(self):
        """连接UI控件的信号到槽函数。"""
        # 【新增】日期快捷按钮
        self.btn_today.clicked.connect(lambda: self._set_date_range_shortcut("today"))
        self.btn_yesterday.clicked.connect(lambda: self._set_date_range_shortcut("yesterday"))
        self.btn_last_7_days.clicked.connect(lambda: self._set_date_range_shortcut("last7days"))
        self.btn_last_30_days.clicked.connect(lambda: self._set_date_range_shortcut("last30days"))

        self.query_button.clicked.connect(self._perform_search)
        self.reset_button.clicked.connect(self._reset_filters)
        
        self.first_page_button.clicked.connect(lambda: self._go_to_page(1))
        self.prev_page_button.clicked.connect(lambda: self._go_to_page(self.current_page - 1))
        self.next_page_button.clicked.connect(lambda: self._go_to_page(self.current_page + 1))
        self.last_page_button.clicked.connect(lambda: self._go_to_page(self.total_pages))
        
        self.page_number_edit.returnPressed.connect(lambda: self._go_to_page(int(self.page_number_edit.text())))
        
        # 【核心修正】严重等级选择现在由 QRadioButton 和排他性 QButtonGroup 自动处理
        # 当任意严重等级 RadioButton 被点击时，触发查询
        self.severity_buttons.buttonClicked.connect(lambda: self._perform_search())
        
        self.table.doubleClicked.connect(self._show_full_message)

        # 【新增】列头排序信号
        self.table.horizontalHeader().sectionClicked.connect(self._sort_table)
        # 【新增】右键菜单信号
        self.table.customContextMenuRequested.connect(self._show_context_menu)
        # 【新增】导出和删除按钮信号
        self.export_button.clicked.connect(self._export_data)
        self.delete_selected_button.clicked.connect(self._delete_selected_alerts)

    def _load_initial_data(self):
        """对话框首次打开时加载数据。"""
        self._perform_search()
        self._update_sort_indicator() # 【新增】初始化时更新排序指示器

    # 【新增】设置日期范围快捷方法
    def _set_date_range_shortcut(self, period: str):
        """
        根据预设周期设置日期范围。
        Args:
            period (str): 'today', 'yesterday', 'last7days', 'last30days'
        """
        today = QDate.currentDate()
        if period == "today":
            self.start_date_edit.setDate(today)
            self.end_date_edit.setDate(today)
        elif period == "yesterday":
            yesterday = today.addDays(-1)
            self.start_date_edit.setDate(yesterday)
            self.end_date_edit.setDate(yesterday)
        elif period == "last7days":
            self.start_date_edit.setDate(today.addDays(-6)) # 今天算在内
            self.end_date_edit.setDate(today)
        elif period == "last30days":
            self.start_date_edit.setDate(today.addDays(-29)) # 今天算在内
            self.end_date_edit.setDate(today)
        
        self.current_page = 1 # 日期范围变化后回到第一页
        self._perform_search()

    # 【新增】处理表格排序
    def _sort_table(self, logical_index: int):
        """
        处理表格列头点击事件，进行排序。
        Args:
            logical_index (int): 被点击的列的逻辑索引。
        """
        # 定义列索引到数据库字段的映射
        column_map = {
            0: 'id',
            1: 'timestamp',
            2: 'severity',
            3: 'type',
            4: 'source_ip',
            5: 'message'
        }
        
        new_sort_column_db = column_map.get(logical_index, 'timestamp')

        if self.current_sort_column_db == new_sort_column_db:
            # 如果是同一列，切换排序方向
            self.current_sort_direction = 'ASC' if self.current_sort_direction == 'DESC' else 'DESC'
        else:
            # 如果是不同列，则以新列的默认降序开始
            self.current_sort_column_db = new_sort_column_db
            self.current_sort_direction = 'DESC' # 默认降序

        self.current_page = 1 # 排序变化后回到第一页
        self._perform_search()
        self._update_sort_indicator() # 更新列头排序指示器

    # 【修正】更新列头排序指示器，使用Qt内置API
    def _update_sort_indicator(self):
        """
        根据当前排序状态更新表格列头的Qt自带排序指示器。
        """
        header = self.table.horizontalHeader()
        column_map_reverse = {
            'id': 0, 'timestamp': 1, 'severity': 2, 'type': 3,
            'source_ip': 4, 'message': 5
        }
        
        logical_index = column_map_reverse.get(self.current_sort_column_db)
        if logical_index is not None:
            header.setSortIndicatorShown(True) # 确保显示排序指示器
            # 将自定义的 'ASC'/'DESC' 映射到 Qt.AscendingOrder / Qt.DescendingOrder
            sort_order = Qt.SortOrder.AscendingOrder if self.current_sort_direction == 'ASC' else Qt.SortOrder.DescendingOrder
            header.setSortIndicator(logical_index, sort_order)
        else:
            # 如果没有有效的排序列（例如，初始加载时可能还未点击），则隐藏指示器
            header.setSortIndicatorShown(False)


    def _perform_search(self):
        """根据当前过滤条件执行数据库查询并更新UI。"""
        self.status_label.setText("正在查询...")
        QCoreApplication.processEvents() # 确保UI更新

        start_date = self.start_date_edit.date().toString(Qt.DateFormat.ISODate)
        end_date = self.end_date_edit.date().toString(Qt.DateFormat.ISODate)
        
        selected_severities = []
        # 【核心修正】根据当前选中 RadioButton 的文本来确定过滤条件
        if self.severity_all.isChecked():
            # 如果选中“全部”，则severities列表为空，数据库查询将返回所有等级
            pass 
        elif self.severity_info.isChecked():
            selected_severities.append("INFO")
        elif self.severity_warning.isChecked():
            selected_severities.append("WARNING")
        elif self.severity_critical.isChecked():
            selected_severities.append("CRITICAL")

        keyword = self.keyword_edit.text().strip()
        search_field_map = {
            "所有字段": "all",
            "消息内容": "message",
            "来源IP": "source_ip",
            "信息类型": "type"
        }
        search_field = search_field_map.get(self.search_field_combo.currentText(), "all")

        results, total_count = self.db_service.search_alerts(
            start_date=start_date,
            end_date=end_date,
            severities=selected_severities,
            keyword=keyword,
            search_field=search_field,
            page=self.current_page,
            page_size=self.page_size,
            order_by=self.current_sort_column_db,     # 【修改】传递排序字段
            order_direction=self.current_sort_direction # 【修改】传递排序方向
        )
        
        self.total_records = total_count
        self.total_pages = (total_count + self.page_size - 1) // self.page_size if self.page_size > 0 else 0
        
        self._update_table(results)
        self._update_pagination_ui()
        self.status_label.setText(f"共找到 {self.total_records} 条记录，当前显示第 {self.current_page}/{self.total_pages} 页")
        logging.info(f"历史查询完成: {self.total_records} 条记录, 当前第 {self.current_page}/{self.total_pages} 页")

    def _update_table(self, data: List[Dict[str, Any]]):
        """用查询结果更新表格。"""
        self.table.setRowCount(0)
        for row_idx, record in enumerate(data):
            self.table.insertRow(row_idx)
            
            # 【修改】ID列现在是第一列
            alert_id = str(record.get('id', ''))
            timestamp = record.get('timestamp', 'N/A')
            severity = record.get('severity', 'INFO')
            alert_type = record.get('type', 'Unknown')
            source_ip = record.get('source_ip', 'N/A')
            message = record.get('message', 'N/A')
            
            items = [
                QTableWidgetItem(alert_id),
                QTableWidgetItem(timestamp),
                QTableWidgetItem(severity),
                QTableWidgetItem(alert_type),
                QTableWidgetItem(source_ip),
                QTableWidgetItem(message)
            ]
            
            color = SEVERITY_COLORS.get(severity, SEVERITY_COLORS["INFO"])
            
            for col, item in enumerate(items):
                item.setBackground(color)
                self.table.setItem(row_idx, col, item)
        self.table.resizeColumnsToContents()
        # 确保ID和时间等列自适应内容
        for i in range(5):
             self.table.horizontalHeader().setSectionResizeMode(i, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeMode.Stretch)


    def _update_pagination_ui(self):
        """更新分页按钮和状态标签的启用/禁用状态。"""
        self.page_number_edit.setText(str(self.current_page))
        self.first_page_button.setEnabled(self.current_page > 1)
        self.prev_page_button.setEnabled(self.current_page > 1)
        self.next_page_button.setEnabled(self.current_page < self.total_pages)
        self.last_page_button.setEnabled(self.current_page < self.total_pages)
        
        if self.total_pages == 0:
            self.first_page_button.setEnabled(False)
            self.prev_page_button.setEnabled(False)
            self.next_page_button.setEnabled(False)
            self.last_page_button.setEnabled(False)
            self.page_number_edit.setEnabled(False)
            # 【新增】如果没数据，导出和删除按钮也禁用
            self.export_button.setEnabled(False)
            self.delete_selected_button.setEnabled(False)
        else:
            self.page_number_edit.setEnabled(True)
            self.export_button.setEnabled(True)
            # 只有当有选中行时才启用删除按钮（通过槽函数动态控制）
            # 这里先设置为True，具体由槽函数判断是否有选中行
            self.delete_selected_button.setEnabled(True) 

    def _go_to_page(self, page_num: int):
        """跳转到指定页码并执行查询。"""
        if self.total_pages == 0:
            if page_num == 1:
                self.current_page = 1
                self._perform_search()
            return

        if 1 <= page_num <= self.total_pages:
            self.current_page = page_num
            self._perform_search()
        else:
            logging.warning(f"尝试跳转到无效页码: {page_num}, 总页数: {self.total_pages}")
            self.page_number_edit.setText(str(self.current_page))

    def _reset_filters(self):
        """重置所有过滤条件到默认值。"""
        self.start_date_edit.setDate(QDate.currentDate().addDays(-7))
        self.end_date_edit.setDate(QDate.currentDate())
        
        # 【核心修正】重置时只设置“全部” RadioButton 为选中
        self.severity_all.setChecked(True) 
        
        self.keyword_edit.clear()
        self.search_field_combo.setCurrentIndex(0)
        self.current_page = 1
        
        # 【新增】重置排序状态
        self.current_sort_column_db = 'timestamp'
        self.current_sort_direction = 'DESC'
        self._update_sort_indicator()

        self._perform_search()

    # 【核心修正】_toggle_all_severities 和 _update_severity_all 方法不再需要，因为 QRadioButton 和排他性 QButtonGroup 自动处理了互斥逻辑。
    # 这里将它们移除，确保代码的简洁和正确性。
    # def _toggle_all_severities(self):
    #     """处理“全部”复选框的逻辑。"""
    #     is_all_checked = self.severity_all.isChecked()
    #     self.severity_info.setChecked(is_all_checked)
    #     self.severity_warning.setChecked(is_all_checked)
    #     self.severity_critical.setChecked(is_all_checked)
    #     if not is_all_checked and not (self.severity_info.isChecked() or 
    #                                    self.severity_warning.isChecked() or 
    #                                    self.severity_critical.isChecked()):
    #         self.severity_all.setChecked(True)

    # def _update_severity_all(self):
    #     """当单个严重等级被点击时，更新“全部”的状态。"""
    #     if self.sender() is not self.severity_all:
    #         if self.severity_info.isChecked() and self.severity_warning.isChecked() and self.severity_critical.isChecked():
    #             self.severity_all.setChecked(True)
    #         else:
    #             self.severity_all.setChecked(False)
                
    def _show_full_message(self):
        """双击表格行时显示完整消息内容。"""
        current_row = self.table.currentRow()
        if current_row >= 0:
            message_item = self.table.item(current_row, 5) # 详细内容在第5列（索引从0开始）
            if message_item:
                QMessageBox.information(self, "详细内容", message_item.text())

    # 【新增】表格右键菜单
    def _show_context_menu(self, pos):
        """
        显示表格右键上下文菜单。
        Args:
            pos (QPoint): 鼠标位置，用于定位菜单。
        """
        index = self.table.indexAt(pos)
        if not index.isValid():
            return

        menu = QMenu(self)

        # 复制单元格内容
        copy_cell_action = QAction("复制单元格内容", self)
        copy_cell_action.triggered.connect(lambda: QApplication.clipboard().setText(self.table.item(index.row(), index.column()).text()))
        menu.addAction(copy_cell_action)

        # 复制行所有数据
        copy_row_action = QAction("复制行所有数据", self)
        # 获取当前行所有数据并格式化
        row_data = [self.table.item(index.row(), col).text() for col in range(self.table.columnCount())]
        copy_row_action.triggered.connect(lambda: QApplication.clipboard().setText('\t'.join(row_data))) # 以制表符分隔
        menu.addAction(copy_row_action)

        menu.addSeparator()

        # 显示完整消息 (如果不是消息列，则禁用)
        show_full_message_action = QAction("显示完整消息", self)
        if index.column() == 5: # 详细内容列
            show_full_message_action.triggered.connect(self._show_full_message)
        else:
            show_full_message_action.setEnabled(False)
        menu.addAction(show_full_message_action)

        menu.exec(self.table.viewport().mapToGlobal(pos))

    # 【新增】导出数据到CSV
    def _export_data(self):
        """将当前筛选条件下的所有数据导出为CSV文件。"""
        # 获取用户选择的文件路径
        file_path, _ = QFileDialog.getSaveFileName(self, "导出历史记录", 
                                                   os.path.expanduser("~/Desktop/alerts_history.csv"), 
                                                   "CSV Files (*.csv);;All Files (*)")
        if not file_path:
            return

        # 重新获取所有符合当前筛选条件的数据，不分页
        start_date = self.start_date_edit.date().toString(Qt.DateFormat.ISODate)
        end_date = self.end_date_edit.date().toString(Qt.DateFormat.ISODate)
        selected_severities = []
        # 【核心修正】导出数据时，同样根据当前选中 RadioButton 获取过滤条件
        if self.severity_all.isChecked():
            pass # 空列表表示所有等级
        elif self.severity_info.isChecked():
            selected_severities.append("INFO")
        elif self.severity_warning.isChecked():
            selected_severities.append("WARNING")
        elif self.severity_critical.isChecked():
            selected_severities.append("CRITICAL")

        keyword = self.keyword_edit.text().strip()
        search_field_map = {
            "所有字段": "all", "消息内容": "message", "来源IP": "source_ip", "信息类型": "type"
        }
        search_field = search_field_map.get(self.search_field_combo.currentText(), "all")

        # 调用数据库服务获取所有数据 (page_size设置为一个大数，或在db_service中提供一个不分页的获取方法)
        # 这里我们直接传入一个足够大的pageSize来获取所有数据
        all_results, _ = self.db_service.search_alerts(
            start_date=start_date,
            end_date=end_date,
            severities=selected_severities,
            keyword=keyword,
            search_field=search_field,
            page=1,
            page_size=self.total_records if self.total_records > 0 else 9999999, # 确保获取所有记录
            order_by=self.current_sort_column_db,
            order_direction=self.current_sort_direction
        )

        try:
            with open(file_path, 'w', newline='', encoding='utf-8') as csvfile:
                fieldnames = ["ID", "接收时间", "严重等级", "信息类型", "来源IP", "详细内容"]
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                for row in all_results:
                    # 重新映射数据库字段到CSV表头
                    writer.writerow({
                        "ID": row.get('id', ''),
                        "接收时间": row.get('timestamp', 'N/A'),
                        "严重等级": row.get('severity', 'INFO'),
                        "信息类型": row.get('type', 'Unknown'),
                        "来源IP": row.get('source_ip', 'N/A'),
                        "详细内容": row.get('message', '无内容')
                    })
            QMessageBox.information(self, "导出成功", f"数据已成功导出到:\n{file_path}")
            logging.info(f"历史记录已导出到: {file_path}")
        except Exception as e:
            QMessageBox.critical(self, "导出失败", f"导出数据时发生错误:\n{e}")
            logging.error(f"导出历史记录失败: {e}", exc_info=True)

    # 【新增】删除选中记录
    def _delete_selected_alerts(self):
        """删除表格中选中的告警记录。"""
        selected_rows = self.table.selectionModel().selectedRows()
        if not selected_rows:
            QMessageBox.information(self, "没有选中", "请选择要删除的记录。")
            return

        # 获取所有选中行的ID
        alert_ids_to_delete = []
        for index in selected_rows:
            # ID在表格的第0列
            item = self.table.item(index.row(), 0)
            if item:
                try:
                    alert_ids_to_delete.append(int(item.text()))
                except ValueError:
                    logging.error(f"无法将ID '{item.text()}' 转换为整数，跳过。")
                    continue
        
        if not alert_ids_to_delete:
            QMessageBox.information(self, "没有有效ID", "没有找到有效的记录ID进行删除。")
            return

        reply = QMessageBox.warning(
            self,
            "确认删除",
            f"您确定要删除选中的 {len(alert_ids_to_delete)} 条历史告警记录吗？\n此操作无法撤销！",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            if self.db_service.delete_alerts_by_ids(alert_ids_to_delete):
                QMessageBox.information(self, "删除成功", "选中的记录已成功删除。")
                self._perform_search() # 刷新表格显示
            else:
                QMessageBox.critical(self, "删除失败", "删除记录时发生错误，请查看日志。")
```
## statistics_dialog.py
```python
# desktop_center/src/ui/statistics_dialog.py
import logging
from collections import defaultdict
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QLabel, QTabWidget,
                               QWidget, QHBoxLayout, QDateEdit, QPushButton,
                               QTreeWidget, QTreeWidgetItem, QHeaderView,
                               QLineEdit, QSpacerItem, QSizePolicy,
                               QComboBox, QTableWidget, QTableWidgetItem)
from PySide6.QtCore import Qt, QDate, QCoreApplication, QTimer
from PySide6.QtGui import QColor, QFont
from src.services.database_service import DatabaseService
from src.services.config_service import ConfigService
from typing import List, Dict, Any

# 定义一个常量，用于表示IP选择器中的“全部IP”选项
ALL_IPS_OPTION = "【全部IP】"

class StatisticsDialog(QDialog):
    # ... (init, _init_ui, _connect_signals, _set_date_range_shortcut, _setup_ip_activity_tab, _setup_hourly_stats_tab 等方法保持不变) ...
    """
    一个独立的对话框，用于统计和分析告警数据。
    包含四个分析选项卡，支持惰性加载和多维度钻取分析。
    """
    def __init__(self, db_service: DatabaseService, config_service: ConfigService, parent=None):
        super().__init__(parent)
        self.db_service = db_service
        self.config_service = config_service
        self.setWindowTitle("统计分析")
        self.setMinimumSize(800, 600)
        
        # 用于惰性加载的标志
        self.tab_loaded_flags = {
            "ip_activity_tab": False,
            "hourly_stats_tab": False,
            "multidim_stats_tab": False,
            "type_stats_tab": False
        }

        # 为“按小时分析”表格添加排序状态变量
        self.hourly_sort_column = 'hour'
        self.hourly_sort_direction = 'ASC'

        self._init_ui()
        self._connect_signals()

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        self.tab_widget = QTabWidget()
        main_layout.addWidget(self.tab_widget)

        # --- 1. 按IP活跃度排行榜选项卡 ---
        self.ip_activity_tab = QWidget()
        self.ip_activity_tab.setObjectName("ip_activity_tab")
        self.ip_activity_tab_layout = QVBoxLayout(self.ip_activity_tab)
        self.tab_widget.addTab(self.ip_activity_tab, "按IP活跃度排行榜")
        self._setup_ip_activity_tab()

        # --- 2. 按小时分析选项卡 ---
        self.hourly_stats_tab = QWidget()
        self.hourly_stats_tab.setObjectName("hourly_stats_tab")
        self.hourly_stats_tab_layout = QVBoxLayout(self.hourly_stats_tab)
        self.tab_widget.addTab(self.hourly_stats_tab, "按小时分析")
        self._setup_hourly_stats_tab()

        # --- 3. 多维分析选项卡 ---
        self.multidim_stats_tab = QWidget()
        self.multidim_stats_tab.setObjectName("multidim_stats_tab")
        self.multidim_stats_tab_layout = QVBoxLayout(self.multidim_stats_tab)
        self.tab_widget.addTab(self.multidim_stats_tab, "多维分析")
        self._setup_multidim_stats_tab()

        # --- 4. 告警类型排行榜选项卡 ---
        self.type_stats_tab = QWidget()
        self.type_stats_tab.setObjectName("type_stats_tab")
        self.type_stats_tab_layout = QVBoxLayout(self.type_stats_tab)
        self.tab_widget.addTab(self.type_stats_tab, "告警类型排行榜")
        self._setup_type_stats_tab()
        
    def _connect_signals(self):
        """连接所有UI控件的信号到槽函数。"""
        self.tab_widget.currentChanged.connect(self._on_tab_changed)

        # IP活跃度 Tab
        self.ip_activity_query_button.clicked.connect(self._perform_ip_activity_query)
        self.ip_activity_btn_today.clicked.connect(lambda: self._set_date_range_shortcut(self.ip_activity_start_date, self.ip_activity_end_date, "today"))
        self.ip_activity_btn_yesterday.clicked.connect(lambda: self._set_date_range_shortcut(self.ip_activity_start_date, self.ip_activity_end_date, "yesterday"))
        self.ip_activity_btn_last_7_days.clicked.connect(lambda: self._set_date_range_shortcut(self.ip_activity_start_date, self.ip_activity_end_date, "last7days"))

        # 按小时分析 Tab
        self.hourly_query_button.clicked.connect(self._perform_hourly_stats_query)
        self.hourly_btn_today.clicked.connect(lambda: self._set_date_range_shortcut(self.hourly_start_date, self.hourly_end_date, "today"))
        self.hourly_btn_yesterday.clicked.connect(lambda: self._set_date_range_shortcut(self.hourly_start_date, self.hourly_end_date, "yesterday"))
        self.hourly_btn_last_7_days.clicked.connect(lambda: self._set_date_range_shortcut(self.hourly_start_date, self.hourly_end_date, "last7days"))
        self.hourly_ip_combo.currentIndexChanged.connect(self._on_ip_combo_changed_for_hourly)
        self.hourly_stats_table.horizontalHeader().sectionClicked.connect(self._sort_hourly_table)

        # 多维分析 Tab
        self.multidim_query_button.clicked.connect(self._perform_multidim_stats_query)
        self.multidim_btn_today.clicked.connect(lambda: self._set_date_range_shortcut(self.multidim_start_date, self.multidim_end_date, "today"))
        self.multidim_btn_yesterday.clicked.connect(lambda: self._set_date_range_shortcut(self.multidim_start_date, self.multidim_end_date, "yesterday"))
        self.multidim_btn_last_7_days.clicked.connect(lambda: self._set_date_range_shortcut(self.multidim_start_date, self.multidim_end_date, "last7days"))
        self.multidim_ip_combo.currentIndexChanged.connect(self._on_ip_combo_changed_for_multidim)
        # 【核心修正】连接新按钮的信号到槽函数
        self.multidim_expand_button.clicked.connect(self.multidim_stats_tree.expandAll)
        self.multidim_collapse_button.clicked.connect(self.multidim_stats_tree.collapseAll)
        self.type_query_button.clicked.connect(self._perform_type_stats_query)
        self.type_btn_today.clicked.connect(lambda: self._set_date_range_shortcut(self.type_start_date, self.type_end_date, "today"))
        self.type_btn_yesterday.clicked.connect(lambda: self._set_date_range_shortcut(self.type_start_date, self.type_end_date, "yesterday"))
        self.type_btn_last_7_days.clicked.connect(lambda: self._set_date_range_shortcut(self.type_start_date, self.type_end_date, "last7days"))
        QTimer.singleShot(0, lambda: self._on_tab_changed(self.tab_widget.currentIndex()))

    def _set_date_range_shortcut(self, start_date_edit: QDateEdit, end_date_edit: QDateEdit, period: str):
        today = QDate.currentDate()
        if period == "today":
            start_date_edit.setDate(today)
            end_date_edit.setDate(today)
        elif period == "yesterday":
            yesterday = today.addDays(-1)
            start_date_edit.setDate(yesterday)
            end_date_edit.setDate(yesterday)
        elif period == "last7days":
            start_date_edit.setDate(today.addDays(-6))
            end_date_edit.setDate(today)
        if start_date_edit is self.ip_activity_start_date:
            self._perform_ip_activity_query()
        elif start_date_edit is self.hourly_start_date:
            self._perform_hourly_stats_query()
        elif start_date_edit is self.multidim_start_date:
            self._perform_multidim_stats_query()
        elif start_date_edit is self.type_start_date:
            self._perform_type_stats_query()

    # --- UI 设置方法 ---

    def _setup_ip_activity_tab(self):
        date_shortcut_layout = QHBoxLayout()
        date_shortcut_layout.addWidget(QLabel("快捷日期:"))
        self.ip_activity_btn_today = QPushButton("今天")
        self.ip_activity_btn_yesterday = QPushButton("昨天")
        self.ip_activity_btn_last_7_days = QPushButton("近7天")
        date_shortcut_layout.addWidget(self.ip_activity_btn_today)
        date_shortcut_layout.addWidget(self.ip_activity_btn_yesterday)
        date_shortcut_layout.addWidget(self.ip_activity_btn_last_7_days)
        date_shortcut_layout.addStretch()
        self.ip_activity_tab_layout.addLayout(date_shortcut_layout)
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("日期范围:"))
        self.ip_activity_start_date = QDateEdit(calendarPopup=True)
        self.ip_activity_start_date.setDate(QDate.currentDate().addDays(-7))
        filter_layout.addWidget(self.ip_activity_start_date)
        filter_layout.addWidget(QLabel("到"))
        self.ip_activity_end_date = QDateEdit(calendarPopup=True)
        self.ip_activity_end_date.setDate(QDate.currentDate())
        filter_layout.addWidget(self.ip_activity_end_date)
        self.ip_activity_query_button = QPushButton("查询")
        self.ip_activity_query_button.setStyleSheet("background-color: #0078d4; color: white; border-radius: 4px; padding: 4px 10px;")
        filter_layout.addWidget(self.ip_activity_query_button)
        filter_layout.addStretch()
        self.ip_activity_tab_layout.addLayout(filter_layout)
        self.ip_activity_table = QTableWidget()
        self.ip_activity_table.setColumnCount(2)
        self.ip_activity_table.setHorizontalHeaderLabels(["来源IP", "数量"])
        self.ip_activity_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.ip_activity_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.ip_activity_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.ip_activity_tab_layout.addWidget(self.ip_activity_table)

    def _setup_hourly_stats_tab(self):
        date_shortcut_layout = QHBoxLayout()
        date_shortcut_layout.addWidget(QLabel("快捷日期:"))
        self.hourly_btn_today = QPushButton("今天")
        self.hourly_btn_yesterday = QPushButton("昨天")
        self.hourly_btn_last_7_days = QPushButton("近7天")
        date_shortcut_layout.addWidget(self.hourly_btn_today)
        date_shortcut_layout.addWidget(self.hourly_btn_yesterday)
        date_shortcut_layout.addWidget(self.hourly_btn_last_7_days)
        date_shortcut_layout.addStretch()
        self.hourly_stats_tab_layout.addLayout(date_shortcut_layout)
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("IP地址:"))
        self.hourly_ip_combo = QComboBox()
        self.hourly_ip_combo.setEditable(True)
        self.hourly_ip_combo.setPlaceholderText("请选择或输入IP地址")
        self.hourly_ip_combo.setMinimumWidth(150)
        filter_layout.addWidget(self.hourly_ip_combo)
        filter_layout.addWidget(QLabel("日期范围:"))
        self.hourly_start_date = QDateEdit(calendarPopup=True)
        self.hourly_start_date.setDate(QDate.currentDate())
        filter_layout.addWidget(self.hourly_start_date)
        filter_layout.addWidget(QLabel("到"))
        self.hourly_end_date = QDateEdit(calendarPopup=True)
        self.hourly_end_date.setDate(QDate.currentDate())
        filter_layout.addWidget(self.hourly_end_date)
        self.hourly_query_button = QPushButton("查询")
        self.hourly_query_button.setStyleSheet("background-color: #0078d4; color: white; border-radius: 4px; padding: 4px 10px;")
        filter_layout.addWidget(self.hourly_query_button)
        filter_layout.addStretch()
        self.hourly_stats_tab_layout.addLayout(filter_layout)
        self.hourly_stats_table = QTableWidget()
        self.hourly_stats_table.setColumnCount(2)
        self.hourly_stats_table.setHorizontalHeaderLabels(["小时", "数量"])
        self.hourly_stats_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.hourly_stats_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.hourly_stats_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.hourly_stats_table.setSortingEnabled(False)
        self.hourly_stats_table.horizontalHeader().setSectionsClickable(True)
        self.hourly_stats_tab_layout.addWidget(self.hourly_stats_table)
    
    def _setup_multidim_stats_tab(self):
        """【核心修正】为“多维分析”选项卡添加“展开/折叠”按钮。"""
        date_shortcut_layout = QHBoxLayout()
        date_shortcut_layout.addWidget(QLabel("快捷日期:"))
        self.multidim_btn_today = QPushButton("今天")
        self.multidim_btn_yesterday = QPushButton("昨天")
        self.multidim_btn_last_7_days = QPushButton("近7天")
        date_shortcut_layout.addWidget(self.multidim_btn_today)
        date_shortcut_layout.addWidget(self.multidim_btn_yesterday)
        date_shortcut_layout.addWidget(self.multidim_btn_last_7_days)
        date_shortcut_layout.addStretch()
        self.multidim_stats_tab_layout.addLayout(date_shortcut_layout)

        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("IP地址:"))
        self.multidim_ip_combo = QComboBox()
        self.multidim_ip_combo.setEditable(True)
        self.multidim_ip_combo.setPlaceholderText("请选择或输入IP地址")
        self.multidim_ip_combo.setMinimumWidth(150)
        filter_layout.addWidget(self.multidim_ip_combo)
        filter_layout.addWidget(QLabel("日期范围:"))
        self.multidim_start_date = QDateEdit(calendarPopup=True)
        self.multidim_start_date.setDate(QDate.currentDate())
        filter_layout.addWidget(self.multidim_start_date)
        filter_layout.addWidget(QLabel("到"))
        self.multidim_end_date = QDateEdit(calendarPopup=True)
        self.multidim_end_date.setDate(QDate.currentDate())
        filter_layout.addWidget(self.multidim_end_date)
        self.multidim_query_button = QPushButton("查询")
        self.multidim_query_button.setStyleSheet("background-color: #0078d4; color: white; border-radius: 4px; padding: 4px 10px;")
        filter_layout.addWidget(self.multidim_query_button)
        
        # 【新增】添加展开和折叠按钮
        filter_layout.addStretch()
        self.multidim_expand_button = QPushButton("展开全部")
        self.multidim_collapse_button = QPushButton("折叠全部")
        filter_layout.addWidget(self.multidim_expand_button)
        filter_layout.addWidget(self.multidim_collapse_button)
        
        self.multidim_stats_tab_layout.addLayout(filter_layout)

        self.multidim_stats_tree = QTreeWidget()
        self.multidim_stats_tree.setColumnCount(2)
        self.multidim_stats_tree.setHeaderLabels(["分析维度", "告警数量"])
        self.multidim_stats_tree.header().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.multidim_stats_tree.header().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.multidim_stats_tree.setSortingEnabled(True)
        self.multidim_stats_tree.sortByColumn(0, Qt.SortOrder.AscendingOrder)
        
        # 【核心修正】为树状视图应用样式表以突出显示选中行
        self.multidim_stats_tree.setStyleSheet("""
            QTreeView::item:selected {
                background-color: #cce8ff; /* 一个更柔和的蓝色 */
                color: black; /* 确保文本颜色为黑色，而不是系统默认的白色 */
            }
        """)
        self.multidim_stats_tab_layout.addWidget(self.multidim_stats_tree)

    def _setup_type_stats_tab(self):
        # (代码无变化)
        date_shortcut_layout = QHBoxLayout()
        date_shortcut_layout.addWidget(QLabel("快捷日期:"))
        self.type_btn_today = QPushButton("今天")
        self.type_btn_yesterday = QPushButton("昨天")
        self.type_btn_last_7_days = QPushButton("近7天")
        date_shortcut_layout.addWidget(self.type_btn_today)
        date_shortcut_layout.addWidget(self.type_btn_yesterday)
        date_shortcut_layout.addWidget(self.type_btn_last_7_days)
        date_shortcut_layout.addStretch()
        self.type_stats_tab_layout.addLayout(date_shortcut_layout)
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("日期范围:"))
        self.type_start_date = QDateEdit(calendarPopup=True)
        self.type_start_date.setDate(QDate.currentDate().addDays(-7))
        filter_layout.addWidget(self.type_start_date)
        filter_layout.addWidget(QLabel("到"))
        self.type_end_date = QDateEdit(calendarPopup=True)
        self.type_end_date.setDate(QDate.currentDate())
        filter_layout.addWidget(self.type_end_date)
        self.type_query_button = QPushButton("查询")
        self.type_query_button.setStyleSheet("background-color: #0078d4; color: white; border-radius: 4px; padding: 4px 10px;")
        filter_layout.addWidget(self.type_query_button)
        filter_layout.addStretch()
        self.type_stats_tab_layout.addLayout(filter_layout)
        self.type_stats_table = QTableWidget()
        self.type_stats_table.setColumnCount(2)
        self.type_stats_table.setHorizontalHeaderLabels(["告警类型", "数量"])
        self.type_stats_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.type_stats_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.type_stats_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.type_stats_tab_layout.addWidget(self.type_stats_table)

    # --- 数据加载和查询方法 ---

    def _on_tab_changed(self, index: int):
        # (代码无变化)
        current_widget = self.tab_widget.widget(index)
        if not current_widget: return
        current_tab_name = current_widget.objectName()
        if not self.tab_loaded_flags.get(current_tab_name, False):
            logging.info(f"第一次加载选项卡: {current_tab_name}")
            if current_tab_name == "ip_activity_tab":
                self._perform_ip_activity_query()
            elif current_tab_name == "hourly_stats_tab":
                self._populate_ip_combo_box(self.hourly_ip_combo, self.hourly_start_date, self.hourly_end_date)
                self._perform_hourly_stats_query()
            elif current_tab_name == "multidim_stats_tab":
                self._populate_ip_combo_box(self.multidim_ip_combo, self.multidim_start_date, self.multidim_end_date)
                self._perform_multidim_stats_query()
            elif current_tab_name == "type_stats_tab":
                self._perform_type_stats_query()
            self.tab_loaded_flags[current_tab_name] = True
        if current_tab_name == "hourly_stats_tab":
            self._populate_ip_combo_box(self.hourly_ip_combo, self.hourly_start_date, self.hourly_end_date)
            self._update_hourly_sort_indicator()
        elif current_tab_name == "multidim_stats_tab":
            self._populate_ip_combo_box(self.multidim_ip_combo, self.multidim_start_date, self.multidim_end_date)

    def _perform_ip_activity_query(self):
        # (代码无变化)
        start_date = self.ip_activity_start_date.date().toString(Qt.DateFormat.ISODate)
        end_date = self.ip_activity_end_date.date().toString(Qt.DateFormat.ISODate)
        self._set_loading_state(self.ip_activity_table, "来源IP", "数量")
        logging.info(f"正在查询按IP活跃度排行榜 (日期: {start_date} - {end_date})...")
        results = self.db_service.get_stats_by_ip_activity(start_date, end_date)
        self._update_stats_table(self.ip_activity_table, results, ["source_ip", "count"])
        logging.info(f"按IP活跃度排行榜查询完成，共 {len(results)} 个活跃IP。")

    def _perform_hourly_stats_query(self):
        # (代码无变化)
        ip_address = self.hourly_ip_combo.currentText().strip()
        start_date = self.hourly_start_date.date().toString(Qt.DateFormat.ISODate)
        end_date = self.hourly_end_date.date().toString(Qt.DateFormat.ISODate)
        self._set_loading_state(self.hourly_stats_table, "小时", "数量")
        if not ip_address:
            logging.warning("按小时分析：IP地址为空。")
            self._update_stats_table(self.hourly_stats_table, [], ["hour", "count"])
            return
        if ip_address == ALL_IPS_OPTION:
            logging.info(f"正在查询全局按小时统计 (日期: {start_date} - {end_date})...")
            results = self.db_service.get_stats_by_hour(start_date, end_date)
        else:
            logging.info(f"正在查询IP {ip_address} 的按小时统计 (日期: {start_date} - {end_date})...")
            results = self.db_service.get_stats_by_ip_and_hour(ip_address, start_date, end_date)
        if results:
            reverse_order = (self.hourly_sort_direction == 'DESC')
            results.sort(key=lambda x: x[self.hourly_sort_column], reverse=reverse_order)
        self._update_stats_table(self.hourly_stats_table, results, ["hour", "count"])
        self._update_hourly_sort_indicator()
        logging.info(f"按小时统计查询完成，共 {len(results)} 小时数据。")

    def _perform_multidim_stats_query(self):
        # (代码无变化)
        ip_address = self.multidim_ip_combo.currentText().strip()
        start_date = self.multidim_start_date.date().toString(Qt.DateFormat.ISODate)
        end_date = self.multidim_end_date.date().toString(Qt.DateFormat.ISODate)
        self.multidim_stats_tree.clear()
        self.multidim_stats_tree.setHeaderLabels(["分析维度 (加载中...)", "告警数量"])
        QCoreApplication.processEvents()
        if not ip_address:
            logging.warning("多维分析：IP地址为空。")
            self.multidim_stats_tree.setHeaderLabels(["分析维度 (无数据)", "告警数量"])
            return
        query_ip = None if ip_address == ALL_IPS_OPTION else ip_address
        logging.info(f"正在查询多维按小时统计 (IP: {ip_address}, 日期: {start_date} - {end_date})...")
        results = self.db_service.get_detailed_hourly_stats(start_date, end_date, query_ip)
        self._populate_multidim_tree(results)
        self.multidim_stats_tree.setHeaderLabels(["分析维度", "告警数量"])
        logging.info(f"多维按小时统计查询完成。")

    def _perform_type_stats_query(self):
        # (代码无变化)
        start_date = self.type_start_date.date().toString(Qt.DateFormat.ISODate)
        end_date = self.type_end_date.date().toString(Qt.DateFormat.ISODate)
        self._set_loading_state(self.type_stats_table, "告警类型", "数量")
        logging.info(f"正在查询告警类型排行榜 (日期: {start_date} - {end_date})...")
        results = self.db_service.get_stats_by_type(start_date, end_date)
        self._update_stats_table(self.type_stats_table, results, ["type", "count"])
        logging.info(f"告警类型排行榜查询完成，共 {len(results)} 种类型。")

    # --- 辅助方法 ---
    
    def _sort_hourly_table(self, logical_index: int):
        # (代码无变化)
        column_map = {0: 'hour', 1: 'count'}
        new_sort_column = column_map.get(logical_index, 'hour')
        if self.hourly_sort_column == new_sort_column:
            self.hourly_sort_direction = 'ASC' if self.hourly_sort_direction == 'DESC' else 'DESC'
        else:
            self.hourly_sort_column = new_sort_column
            self.hourly_sort_direction = 'DESC' if new_sort_column == 'count' else 'ASC'
        self._perform_hourly_stats_query()

    def _update_hourly_sort_indicator(self):
        # (代码无变化)
        header = self.hourly_stats_table.horizontalHeader()
        column_map_reverse = {'hour': 0, 'count': 1}
        logical_index = column_map_reverse.get(self.hourly_sort_column)
        if logical_index is not None:
            header.setSortIndicatorShown(True)
            sort_order = Qt.SortOrder.AscendingOrder if self.hourly_sort_direction == 'ASC' else Qt.SortOrder.DescendingOrder
            header.setSortIndicator(logical_index, sort_order)
        else:
            header.setSortIndicatorShown(False)

    def _populate_multidim_tree(self, data: List[Dict[str, Any]]):
        """将详细统计数据填充到多维分析的 QTreeWidget 中，并应用颜色和默认折叠。"""
        self.multidim_stats_tree.clear()
        if not data:
            return
        tree_data = defaultdict(lambda: defaultdict(lambda: defaultdict(int)))
        for row in data:
            tree_data[row['hour']][row['severity']][row['type']] = row['count']
        bold_font = QFont()
        bold_font.setBold(True)
        
        # 【新增】定义不同层级的颜色
        hour_color = QColor("#003366")      # 深蓝色
        severity_color = QColor("#8B4513")  # 棕褐色/深橙色
        
        self.multidim_stats_tree.setSortingEnabled(False)
        for hour, severities in sorted(tree_data.items()):
            hour_total = sum(sum(types.values()) for types in severities.values())
            hour_text = f"{hour:02d}:00 - {hour:02d}:59"
            hour_item = QTreeWidgetItem(self.multidim_stats_tree)
            hour_item.setFont(0, bold_font)
            hour_item.setFont(1, bold_font)
            hour_item.setText(0, hour_text)
            hour_item.setText(1, str(hour_total))
            # 【新增】为小时节点设置颜色
            hour_item.setForeground(0, hour_color)
            hour_item.setForeground(1, hour_color)
            hour_item.setData(0, Qt.ItemDataRole.UserRole, hour)
            hour_item.setData(1, Qt.ItemDataRole.UserRole, hour_total)
            for severity, types in sorted(severities.items()):
                severity_total = sum(types.values())
                severity_item = QTreeWidgetItem(hour_item)
                severity_item.setText(0, f"  - {severity}")
                severity_item.setText(1, str(severity_total))
                # 【新增】为严重等级节点设置颜色
                severity_item.setForeground(0, severity_color)
                severity_item.setData(1, Qt.ItemDataRole.UserRole, severity_total)
                for type_name, count in sorted(types.items()):
                    type_item = QTreeWidgetItem(severity_item)
                    type_item.setText(0, f"    - {type_name}")
                    type_item.setText(1, str(count))
                    type_item.setData(1, Qt.ItemDataRole.UserRole, count)
        self.multidim_stats_tree.setSortingEnabled(True)

    def _populate_ip_combo_box(self, combo_box: QComboBox, start_date_edit: QDateEdit, end_date_edit: QDateEdit):
        # (代码无变化)
        start_date = start_date_edit.date().toString(Qt.DateFormat.ISODate)
        end_date = end_date_edit.date().toString(Qt.DateFormat.ISODate)
        distinct_ips = self.db_service.get_distinct_source_ips(start_date, end_date)
        current_text = combo_box.currentText()
        combo_box.clear()
        combo_box.addItem(ALL_IPS_OPTION)
        if distinct_ips:
            combo_box.addItems(distinct_ips)
            logging.info(f"IP地址下拉框 ({combo_box.objectName()}) 已更新，共 {len(distinct_ips)} 个不重复IP。")
        if current_text in [ALL_IPS_OPTION] + distinct_ips:
            combo_box.setCurrentText(current_text)
        elif current_text:
            combo_box.setEditText(current_text)
        else:
            combo_box.setCurrentIndex(0)

    def _on_ip_combo_changed_for_hourly(self, index: int):
        # (代码无变化)
        if self.tab_loaded_flags.get("hourly_stats_tab", False):
            self._perform_hourly_stats_query()

    def _on_ip_combo_changed_for_multidim(self, index: int):
        # (代码无变化)
        if self.tab_loaded_flags.get("multidim_stats_tab", False):
            self._perform_multidim_stats_query()

    def _set_loading_state(self, table: QTableWidget, col1_text: str, col2_text: str):
        # (代码无变化)
        table.setRowCount(0)
        table.setHorizontalHeaderLabels([col1_text, f"{col2_text} (加载中...)"])
        QCoreApplication.processEvents()

    def _update_stats_table(self, table: QTableWidget, data: List[Dict[str, Any]], column_keys: List[str]):
        # (代码无变化)
        table.setRowCount(0)
        col1_text = column_keys[0].capitalize().replace('_', ' ')
        col2_text = column_keys[1].capitalize().replace('_', ' ')
        if not data:
            table.setHorizontalHeaderLabels([f"{col1_text} (无数据)", col2_text])
            return
        table.setHorizontalHeaderLabels([col1_text, col2_text])
        table.setColumnCount(len(column_keys))
        for row_idx, record in enumerate(data):
            table.insertRow(row_idx)
            for col_idx, key in enumerate(column_keys):
                item_text = str(record.get(key, 'N/A'))
                item = QTableWidgetItem(item_text)
                if isinstance(record.get(key), (int, float)):
                    item.setData(Qt.ItemDataRole.UserRole, record.get(key))
                table.setItem(row_idx, col_idx, item)
        table.resizeColumnsToContents()
```
## alerts_page.py
```python
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
        # 【修改】将主窗口作为父窗口传递，确保对话框居中显示且生命周期受主窗口管理
        dialog = HistoryDialog(self.db_service, self.config_service, self.window())
        dialog.exec() # exec()使其成为模态对话框

    def show_statistics_dialog(self):
        """创建并显示统计分析对话框。"""
        # 【修改】将主窗口作为父窗口传递
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
            # 【修改】从InfoService部分读取load_history_on_startup配置
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
        if not timestamp or not is_history: # 只有非历史记录才自动获取当前时间
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
```