# desktop_center/src/features/alert_center/database_extensions.py
import logging
import sqlite3
from typing import List, Dict, Any

class AlertCenterDatabaseExtensions:
    """
    一个混入类(Mixin)，为DatabaseService提供alert_center插件专属的查询功能。
    """
    def get_custom_stats(self, dimensions: List[str], start_date: str = None, end_date: str = None) -> List[Dict[str, Any]]:
        """
        根据用户选择的动态维度进行分组统计。

        Args:
            dimensions (List[str]): 用户选择的维度字段列表, e.g., ['severity', 'type']
            start_date (str, optional): 起始日期.
            end_date (str, optional): 结束日期.

        Returns:
            List[Dict[str, Any]]: 查询结果列表.
        """
        if not dimensions:
            return []

        # 安全性检查：确保所有维度都在允许的字段列表中
        allowed_dimensions = {'severity', 'type', 'source_ip'}
        safe_dimensions = [dim for dim in dimensions if dim in allowed_dimensions]
        if not safe_dimensions:
            logging.warning("自定义分析收到了无效的维度，查询已中止。")
            return []

        dim_str = ", ".join(safe_dimensions)
        
        sql_parts = [f"SELECT {dim_str}, COUNT(*) as count FROM alerts WHERE 1=1"]
        params = []

        if start_date:
            sql_parts.append("AND timestamp >= ?")
            params.append(start_date + " 00:00:00")
        if end_date:
            sql_parts.append("AND timestamp <= ?")
            params.append(end_date + " 23:59:59")

        sql_parts.append(f"GROUP BY {dim_str}")
        sql_parts.append(f"ORDER BY {dim_str}")
        
        full_sql = " ".join(sql_parts)
        logging.info(f"执行自定义分析查询: {full_sql} with params {params}")

        try:
            # self.conn 会由继承了此Mixin的DatabaseService提供
            cursor = self.conn.cursor()
            cursor.execute(full_sql, params)
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
        except sqlite3.Error as e:
            logging.error(f"自定义分析数据库查询失败: {e}", exc_info=True)
            return []