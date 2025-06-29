# desktop_center/src/features/alert_center/models/history_model.py
from dataclasses import dataclass, field
from typing import List

@dataclass
class HistoryModel:
    """
    历史记录页面的数据模型。
    主要用于存储和管理UI的状态，如分页和排序信息，而不是直接的数据库交互。
    """
    current_page: int = 1
    page_size: int = 50
    total_records: int = 0
    total_pages: int = 0
    sort_column: str = 'timestamp'
    sort_direction: str = 'DESC'
    
    start_date: str = ""
    end_date: str = ""
    severities: List[str] = field(default_factory=list)
    keyword: str = ""
    search_field: str = "all"

    def update_pagination(self, total_records: int):
        """根据总记录数更新分页信息。"""
        self.total_records = total_records
        if self.page_size > 0:
            self.total_pages = (total_records + self.page_size - 1) // self.page_size
        else:
            self.total_pages = 0
        
        # 修正当前页码，防止超出范围
        if self.current_page > self.total_pages and self.total_pages > 0:
            self.current_page = self.total_pages
        elif self.total_pages == 0:
            self.current_page = 1