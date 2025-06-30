# desktop_center/src/features/window_arranger/sorting_strategies/numeric_sort_strategy.py
import re
from typing import List, Tuple
from .sort_strategy_interface import ISortStrategy
from src.features.window_arranger.models.window_info import WindowInfo

class NumericSortStrategy(ISortStrategy):
    """
    按窗口标题中提取的数字进行排序的策略。
    例如，从 "1-41704 - 完全控制" 中提取 141704。
    """
    @property
    def name(self) -> str:
        return "按标题数字排序"

    def _extract_numeric_key(self, title: str) -> Tuple[int, str]:
        """
        辅助方法，从标题中提取数字作为排序键。
        
        Returns:
            A tuple (numeric_key, original_title).
            numeric_key is the extracted number, or float('inf') if no number is found.
            original_title is for stable secondary sorting.
        """
        # 使用正则表达式找到所有数字字符
        digits = re.findall(r'\d', title)
        
        if digits:
            try:
                # 将找到的数字字符拼接起来并转换为整数
                numeric_value = int("".join(digits))
                return (numeric_value, title)
            except (ValueError, TypeError):
                # 如果转换失败（不太可能发生，但作为保障），则视为无数字
                return (float('inf'), title)
        else:
            # 如果标题中没有数字，则将其排在最后
            return (float('inf'), title)

    def sort(self, windows: List[WindowInfo]) -> List[WindowInfo]:
        """
        使用提取的数字作为主键，对窗口列表进行排序。
        """
        return sorted(windows, key=lambda w: self._extract_numeric_key(w.title))