# desktop_center/src/features/window_arranger/sorting_strategies/sort_strategy_interface.py
from abc import ABC, abstractmethod
from typing import List
from src.features.window_arranger.models.window_info import WindowInfo

class ISortStrategy(ABC):
    """
    排序策略的接口。所有排序方案都必须实现这个接口。
    """
    
    @property
    @abstractmethod
    def name(self) -> str:
        """
        返回策略的显示名称，将用于UI下拉框中。
        例如："默认排序 (按标题)"
        """
        pass

    @abstractmethod
    def sort(self, windows: List[WindowInfo]) -> List[WindowInfo]:
        """
        对窗口信息列表进行排序。
        
        Args:
            windows (List[WindowInfo]): 未排序的窗口信息列表。

        Returns:
            List[WindowInfo]: 已排序的窗口信息列表。
        """
        pass