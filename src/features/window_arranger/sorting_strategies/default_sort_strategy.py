# desktop_center/src/features/window_arranger/sorting_strategies/default_sort_strategy.py
from typing import List
from .sort_strategy_interface import ISortStrategy
from src.features.window_arranger.models.window_info import WindowInfo

class DefaultSortStrategy(ISortStrategy):
    """
    默认的排序策略：按窗口标题升序，然后按进程名升序。
    """
    @property
    def name(self) -> str:
        return "默认排序 (按标题)"

    def sort(self, windows: List[WindowInfo]) -> List[WindowInfo]:
        return sorted(windows, key=lambda w: (w.title.lower(), w.process_name.lower()))