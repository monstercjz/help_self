# desktop_center/src/ui/alerts_page.py
from PySide6.QtWidgets import (QWidget, QTableWidget, QTableWidgetItem,
                               QHeaderView, QVBoxLayout, QLabel)
from PySide6.QtCore import Slot, Qt
from datetime import datetime

class AlertsPageWidget(QWidget):
    """
    “信息接收中心”功能页面。
    负责以表格形式展示从后台服务接收到的实时告警信息。
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(15, 15, 15, 15) # 设置内边距
        
        title_label = QLabel("实时信息接收中心")
        title_label.setStyleSheet("font-size: 20px; font-weight: bold; margin-bottom: 10px;")
        main_layout.addWidget(title_label)
        
        # --- 创建信息展示表格 ---
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["接收时间", "信息类型", "来源IP", "详细内容"])
        
        # --- 设置表头样式和尺寸策略 ---
        header = self.table.horizontalHeader()
        # 内容列自动拉伸以填满空间
        header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        # 其他列根据内容自适应宽度
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers) # 禁止编辑
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows) # 整行选择
        
        main_layout.addWidget(self.table)
        
    @Slot(dict)
    def add_alert(self, alert_data: dict) -> None:
        """
        一个公开的槽函数，用于安全地向表格添加新行。
        可被任何发出信号的组件（尤其是跨线程的）调用。

        Args:
            alert_data (dict): 包含告警信息的字典，
                               应包含 'ip', 'type', 'message' 等键。
        """
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # 在表格顶部插入新行
        self.table.insertRow(0)
        
        # 填充单元格数据
        self.table.setItem(0, 0, QTableWidgetItem(now))
        self.table.setItem(0, 1, QTableWidgetItem(alert_data.get('type', '未知')))
        self.table.setItem(0, 2, QTableWidgetItem(alert_data.get('ip', 'N/A')))
        self.table.setItem(0, 3, QTableWidgetItem(alert_data.get('message', '无内容')))