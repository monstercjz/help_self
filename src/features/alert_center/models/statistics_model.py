# desktop_center/src/features/alert_center/models/statistics_model.py
import logging
from collections import defaultdict
from typing import List, Dict, Any, Tuple

class StatisticsModel:
    """
    统计分析的数据模型。
    负责将从数据库获取的扁平数据，处理成UI（如QTreeWidget）所需的层级结构。
    """

    def process_detailed_stats_for_tree(self, data: List[Dict[str, Any]]) -> Dict:
        """
        将详细的、按小时/级别/类型分组的统计数据处理成嵌套字典，
        以方便在QTreeWidget中展示。

        Args:
            data (List[Dict[str, Any]]): 从 `db_service.get_detailed_hourly_stats` 返回的列表。

        Returns:
            Dict: 一个嵌套字典，结构为 {hour: {severity: {type: count}}}。
        """
        if not data:
            return {}
            
        tree_data = defaultdict(lambda: defaultdict(lambda: defaultdict(int)))
        try:
            for row in data:
                hour = row.get('hour')
                severity = row.get('severity')
                type_name = row.get('type')
                count = row.get('count')
                if all(v is not None for v in [hour, severity, type_name, count]):
                    tree_data[hour][severity][type_name] = count
            
            # 返回排序后的结果以保证UI显示一致性
            sorted_tree_data = {
                h: {s: dict(sorted(t.items())) for s, t in sorted(severities.items())}
                for h, severities in sorted(tree_data.items())
            }
            return sorted_tree_data
        except Exception as e:
            logging.error(f"处理多维统计数据时出错: {e}", exc_info=True)
            return {}