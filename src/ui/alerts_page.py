# src/ui/alerts_page.py
from PySide6.QtWidgets import (QWidget, QTableWidget, QTableWidgetItem, 
                               QHeaderView, QVBoxLayout)
from PySide6.QtCore import Slot

class AlertsPageWidget(QWidget):
    """告警中心功能页面"""
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["时间", "来源IP", "详情"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        
        layout.addWidget(self.table)
        
    @Slot(dict)
    def add_alert_to_table(self, alert_data):
        from datetime import datetime
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self.table.insertRow(0)
        self.table.setItem(0, 0, QTableWidgetItem(now))
        self.table.setItem(0, 1, QTableWidgetItem(alert_data.get('ip')))
        self.table.setItem(0, 2, QTableWidgetItem(alert_data.get('message')))