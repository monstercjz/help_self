# src/features/memo_pad/models/memo_model.py

from dataclasses import dataclass
from datetime import datetime

@dataclass
class Memo:
    """
    代表一条备忘录的数据模型。
    """
    id: int
    title: str
    content: str
    created_at: datetime
    updated_at: datetime
