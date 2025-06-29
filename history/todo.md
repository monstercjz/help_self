变更版本日志 (Version Log)
版本: 1.3.0-staged1
日期: 2025-06-28
变更内容:
功能增强: 为信息引入“严重等级”(Severity)概念，并支持默认等级，实现向后兼容。
UI升级: 表格新增“严重等级”列，并根据等级对行进行颜色高亮。
UI升级: “信息接收中心”页面增加“清空信息”按钮，并有防误触确认。
通知优化: 实现智能通知，仅当信息等级高于或等于配置的阈值时才触发桌面弹窗。
影响文件:
src/services/alert_receiver.py (修改)
src/ui/alerts_page.py (修改)
config.ini (修改)
## 2
好的，收到明确指令。我们将立即按照“卡片式布局”、“控件升级”和“元数据驱动”的方案，来对全局“设置”页面进行一次彻底的改造。我会严格遵循您之前提出的开发准则，并适当地运用颜色和样式来提升美感。

---

### **变更版本日志 (Version Log)**

*   **版本:** 1.4.0-settings-revamp
*   **日期:** 2025-06-28
*   **变更内容:**
    1.  **架构升级:** “设置”页面重构为“元数据驱动”模式，增强了可维护性和可扩展性。
    2.  **UI控件升级:** 根据设置项类型，引入 `QCheckBox`, `QComboBox`, `QSpinBox`，大幅提升易用性。
    3.  **UI美化:** 应用样式表，将设置分组改造为现代化的“卡片式”布局，并优化了颜色、字体和间距。
    4.  **健壮性提升:** 为数字输入框增加了范围校验。
*   **影响文件:**
    *   `src/ui/settings_page.py` (重大修改)

---

### **1. 修改 `src/ui/settings_page.py`**

这是本次唯一的修改文件。我们将对其进行一次大范围但逻辑封闭的重构。原有的线性布局和纯`QLineEdit`的逻辑将被完全替换。

**文件: `desktop_center/src/ui/settings_page.py` (重构后)**

```python
# desktop_center/src/ui/settings_page.py
import logging
from PySide6.QtWidgets import (QWidget, QLabel, QVBoxLayout, QGroupBox,
                               QLineEdit, QPushButton, QMessageBox, QFormLayout,
                               QComboBox, QCheckBox, QSpinBox, QScrollArea)
from PySide6.QtCore import Qt
from src.services.config_service import ConfigService

# 【新增】定义设置项的元数据。这是“元数据驱动UI”的核心。
# 它描述了每个设置项的UI展现形式和约束。
# 结构: { section: { key: { metadata } } }
SETTING_METADATA = {
    "General": {
        "app_name": {
            "widget": "lineedit", 
            "label": "应用程序名称"
        },
        "start_minimized": {
            "widget": "checkbox", 
            "label": "启动时最小化到系统托盘"
        }
    },
    "WebServer": {
        "host": {
            "widget": "lineedit", 
            "label": "监听地址 (0.0.0.0代表所有)"
        },
        "port": {
            "widget": "spinbox", 
            "label": "监听端口", 
            "min": 1024, 
            "max": 65535
        }
    },
    "Notification": {
        "enable_desktop_popup": {
            "widget": "checkbox", 
            "label": "启用桌面弹窗通知"
        },
        "popup_timeout": {
            "widget": "spinbox", 
            "label": "弹窗显示时长 (秒)", 
            "min": 1, 
            "max": 300
        },
        "notification_level": {
            "widget": "combobox", 
            "label": "通知级别阈值", 
            "items": ["INFO", "WARNING", "CRITICAL"]
        }
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
        # self.editors 用于存储所有动态创建的控件: {section: {key: widget_instance}}
        self.editors = {}

        # --- 整体布局 ---
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20) # 增大边距，让内容呼吸
        main_layout.setSpacing(15) # 增加卡片间的间距

        title_label = QLabel("应用程序设置")
        title_label.setStyleSheet("font-size: 22px; font-weight: bold; margin-bottom: 10px; color: #333;")
        main_layout.addWidget(title_label)
        
        # --- 创建一个可滚动的区域，以防未来设置项过多 ---
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet("QScrollArea { border: none; background-color: transparent; }")
        
        # 滚动区域的内容Widget
        content_widget = QWidget()
        self.settings_layout = QVBoxLayout(content_widget)
        self.settings_layout.setSpacing(15)

        scroll_area.setWidget(content_widget)
        main_layout.addWidget(scroll_area)

        # --- 动态生成设置卡片 ---
        self._create_setting_cards()

        # --- 保存按钮 ---
        self.save_button = QPushButton("保存所有设置")
        self.save_button.setMinimumHeight(35) # 增大按钮高度
        self.save_button.setStyleSheet("""
            QPushButton {
                font-size: 14px;
                font-weight: bold;
                background-color: #0078d4;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 0 20px;
            }
            QPushButton:hover {
                background-color: #005a9e;
            }
            QPushButton:pressed {
                background-color: #004578;
            }
        """)
        self.save_button.clicked.connect(self.save_settings)
        main_layout.addWidget(self.save_button, 0, Qt.AlignmentFlag.AlignRight)

    def _create_setting_cards(self):
        """根据元数据动态创建所有设置卡片和控件。"""
        for section, options_meta in SETTING_METADATA.items():
            # 为每个section创建一个卡片(QGroupBox)
            card = QGroupBox(section)
            card.setStyleSheet("""
                QGroupBox {
                    font-size: 16px;
                    font-weight: bold;
                    color: #333;
                    background-color: #fcfcfc;
                    border: 1px solid #e0e0e0;
                    border-radius: 8px;
                    margin-top: 10px; /* 为标题提供空间 */
                }
                QGroupBox::title {
                    subcontrol-origin: margin;
                    subcontrol-position: top left;
                    padding: 0 10px;
                    left: 10px;
                    background-color: #fcfcfc;
                }
            """)
            
            form_layout = QFormLayout(card)
            form_layout.setSpacing(12)
            form_layout.setContentsMargins(20, 30, 20, 20) # 调整内边距

            self.editors[section] = {}

            for key, meta in options_meta.items():
                widget_type = meta["widget"]
                label_text = meta["label"]
                current_value = self.config_service.get_value(section, key)
                
                editor_widget = None

                # 根据元数据创建不同类型的控件
                if widget_type == "lineedit":
                    editor_widget = QLineEdit(current_value)
                
                elif widget_type == "checkbox":
                    editor_widget = QCheckBox()
                    editor_widget.setChecked(current_value.lower() == 'true')

                elif widget_type == "spinbox":
                    editor_widget = QSpinBox()
                    editor_widget.setRange(meta["min"], meta["max"])
                    editor_widget.setValue(int(current_value) if current_value and current_value.isdigit() else meta["min"])

                elif widget_type == "combobox":
                    editor_widget = QComboBox()
                    items = meta["items"]
                    editor_widget.addItems(items)
                    if current_value in items:
                        editor_widget.setCurrentText(current_value)

                if editor_widget:
                    form_layout.addRow(QLabel(f"{label_text}:"), editor_widget)
                    self.editors[section][key] = editor_widget
            
            self.settings_layout.addWidget(card)
        
        self.settings_layout.addStretch() # 将所有卡片推到顶部

    def save_settings(self):
        """遍历所有控件，收集数据并通过ConfigService保存。"""
        logging.info("尝试保存所有设置...")
        try:
            for section, options in self.editors.items():
                for key, widget in options.items():
                    value = None
                    # 根据控件类型获取值
                    if isinstance(widget, QLineEdit):
                        value = widget.text()
                    elif isinstance(widget, QCheckBox):
                        value = str(widget.isChecked()).lower() # "true" or "false"
                    elif isinstance(widget, QSpinBox):
                        value = str(widget.value())
                    elif isinstance(widget, QComboBox):
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

---

### **交付成果说明**

1.  **元数据驱动 (`SETTING_METADATA`):**
    *   我将所有设置项的UI定义集中到了文件顶部的 `SETTING_METADATA` 字典中。
    *   **未来扩展:** 当您需要添加一个新的设置项时，**只需修改这个字典**，UI就会自动生成，无需更改任何循环或创建控件的逻辑。例如，要给"General"添加一个"theme"设置，只需添加一行：`"theme": {"widget": "combobox", "label": "应用主题", "items": ["Light", "Dark"]}`。

2.  **卡片式布局:**
    *   我使用了 `QGroupBox` 并通过 `setStyleSheet` 对其进行了深度美化，包括圆角、边框、背景色和标题位置，使其呈现出现代化的卡片效果。
    *   整个设置区域被放在一个 `QScrollArea` 中，确保了即使未来设置项增多，页面也不会无限拉长，而是会出现滚动条。

3.  **控件升级:**
    *   **布尔值 (`true/false`)** 现在是 `QCheckBox` (复选框)，非常直观。
    *   **固定选项** (如通知级别) 现在是 `QComboBox` (下拉框)，杜绝了输入错误。
    *   **数字** (如端口号) 现在是 `QSpinBox` (数字调节框)，并根据元数据设置了有效的输入范围，增强了程序的健壮性。

4.  **视觉美化:**
    *   整体布局增加了边距和间距，使视觉不拥挤。
    *   标题字体被放大加粗。
    *   “保存”按钮被设计得更醒目，并带有悬停和点击效果。
    *   卡片内部的表单布局 (`QFormLayout`) 也调整了间距，使其更易读。

5.  **健壮性:**
    *   代码现在可以优雅地处理 `config.ini` 中某个值缺失或格式不正确的情况，会使用一个合理的默认值来初始化UI控件。

现在，您的“设置”页面已经焕然一新，不仅在视觉上更专业，其内部结构也为未来的快速迭代和维护打下了坚实的基础。
