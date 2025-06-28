# desktop_center/src/ui/alerts_page.py
from PySide6.QtWidgets import (QWidget, QTableWidget, QTableWidgetItem,
                               QHeaderView, QVBoxLayout, QLabel, QPushButton,
                               QMessageBox, QHBoxLayout)
from PySide6.QtCore import Slot, Qt
from PySide6.QtGui import QColor # 【新增】导入QColor用于设置背景色
from datetime import datetime

# 【新增】定义与严重等级对应的颜色
SEVERITY_COLORS = {
    "CRITICAL": QColor("#FFDDDD"),  # 淡红色
    "WARNING": QColor("#FFFFCC"),   # 淡黄色
    "INFO": QColor("#FFFFFF")       # 默认白色
}

class AlertsPageWidget(QWidget):
    """
    “信息接收中心”功能页面。
    负责以表格形式展示从后台服务接收到的实时告警信息。
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(15, 15, 15, 15)
        
        title_label = QLabel("实时信息接收中心")
        title_label.setStyleSheet("font-size: 20px; font-weight: bold; margin-bottom: 10px;")
        main_layout.addWidget(title_label)
        
        self.table = QTableWidget()
        # 【修改】表格列数增加到5列，以容纳“严重等级”
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["接收时间", "严重等级", "信息类型", "来源IP", "详细内容"])
        
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        # 【修改】调整列宽策略
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents) # 时间
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents) # 等级
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents) # 类型
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents) # IP
        
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        
        main_layout.addWidget(self.table)

        # 【新增】添加底部按钮区域
        button_layout = QHBoxLayout()
        button_layout.addStretch() # 添加一个伸缩项，将按钮推到右侧
        
        self.clear_button = QPushButton("清空所有信息")
        self.clear_button.setFixedWidth(120)
        self.clear_button.clicked.connect(self.clear_table)
        button_layout.addWidget(self.clear_button)
        
        main_layout.addLayout(button_layout)
        
    @Slot(dict)
    def add_alert(self, alert_data: dict) -> None:
        """
        一个公开的槽函数，用于安全地向表格添加新行。
        可被任何发出信号的组件（尤其是跨线程的）调用。

        Args:
            alert_data (dict): 包含告警信息的字典。
        """
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        self.table.insertRow(0)
        
        # 【修改】填充单元格数据，包括新的“严重等级”列
        severity = alert_data.get('severity', 'INFO')
        
        time_item = QTableWidgetItem(now)
        severity_item = QTableWidgetItem(severity)
        type_item = QTableWidgetItem(alert_data.get('type', '未知'))
        ip_item = QTableWidgetItem(alert_data.get('ip', 'N/A'))
        message_item = QTableWidgetItem(alert_data.get('message', '无内容'))
        
        self.table.setItem(0, 0, time_item)
        self.table.setItem(0, 1, severity_item)
        self.table.setItem(0, 2, type_item)
        self.table.setItem(0, 3, ip_item)
        self.table.setItem(0, 4, message_item)
        
        # 【新增】根据严重等级设置行背景色
        color = SEVERITY_COLORS.get(severity, SEVERITY_COLORS["INFO"])
        for col in range(self.table.columnCount()):
            self.table.item(0, col).setBackground(color)
            
    # 【新增】清空表格的方法
    def clear_table(self):
        """清空表格中的所有行，并有确认提示。"""
        if self.table.rowCount() == 0:
            return # 如果表格已空，则不执行任何操作

        reply = QMessageBox.question(
            self,
            "确认操作",
            "您确定要清空所有信息吗？此操作不可撤销。",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No  # 默认焦点在“否”
        )

        if reply == QMessageBox.StandardButton.Yes:
            self.table.setRowCount(0) # 将行数设为0，即清空表格
            logging.info("UI表格信息已被用户清空。")