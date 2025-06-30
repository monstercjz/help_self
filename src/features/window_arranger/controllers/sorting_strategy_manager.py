# desktop_center/src/features/window_arranger/controllers/sorting_strategy_manager.py
import importlib
import pkgutil
import logging
from typing import Dict, List, Type
from src.features.window_arranger.sorting_strategies.sort_strategy_interface import ISortStrategy

class SortingStrategyManager:
    """
    负责发现、加载和管理所有排序策略。
    """
    def __init__(self):
        self.strategies: Dict[str, Type[ISortStrategy]] = {}
        self._load_strategies()

    def _load_strategies(self):
        """
        动态扫描 sorting_strategies 包，加载所有实现了 ISortStrategy 接口的类。
        """
        import src.features.window_arranger.sorting_strategies as strategies_package
        
        for module_info in pkgutil.walk_packages(path=strategies_package.__path__, prefix=strategies_package.__name__ + '.'):
            try:
                module = importlib.import_module(module_info.name)
                for item_name in dir(module):
                    item = getattr(module, item_name)
                    if isinstance(item, type) and issubclass(item, ISortStrategy) and item is not ISortStrategy:
                        # 使用策略的 name 属性作为键
                        strategy_instance = item()
                        if strategy_instance.name in self.strategies:
                            logging.warning(f"排序策略名称冲突: '{strategy_instance.name}' 已存在。将覆盖。")
                        self.strategies[strategy_instance.name] = item
                        logging.info(f"[WindowArranger] 已加载排序策略: '{strategy_instance.name}'")
            except Exception as e:
                logging.error(f"加载排序策略模块 {module_info.name} 时失败: {e}", exc_info=True)

    def get_strategy_names(self) -> List[str]:
        """获取所有已加载策略的名称列表。"""
        return sorted(list(self.strategies.keys()))

    def get_strategy(self, name: str) -> ISortStrategy | None:
        """
        根据名称获取一个排序策略的实例。
        
        Args:
            name (str): 策略的显示名称。

        Returns:
            ISortStrategy | None: 策略的实例，如果未找到则返回 None。
        """
        strategy_class = self.strategies.get(name)
        if strategy_class:
            return strategy_class()
        return None