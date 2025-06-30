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
        【变更】支持IP、按天、按小时作为维度。
        """
        if not dimensions:
            return []

        # 维度白名单和到SQL表达式的映射
        dim_to_sql_expr = {
            'severity': 'severity',
            'type': 'type',
            'source_ip': 'source_ip',
            'dim_date': "strftime('%Y-%m-%d', timestamp)",
            'dim_hour': "strftime('%H', timestamp)",
        }

        # 过滤并转换用户选择的维度
        safe_dims = [dim for dim in dimensions if dim in dim_to_sql_expr]
        if not safe_dims:
            logging.warning("自定义分析收到了无效的维度，查询已中止。")
            return []

        # 构建SELECT和GROUP BY子句
        select_clauses = [f"{dim_to_sql_expr[dim]} AS {dim}" for dim in safe_dims]
        select_str = ", ".join(select_clauses)
        group_by_str = ", ".join([dim_to_sql_expr[dim] for dim in safe_dims])

        sql_parts = [f"SELECT {select_str}, COUNT(*) as count FROM alerts WHERE 1=1"]
        params = []

        if start_date:
            sql_parts.append("AND timestamp >= ?")
            params.append(start_date + " 00:00:00")
        if end_date:
            sql_parts.append("AND timestamp <= ?")
            params.append(end_date + " 23:59:59")

        sql_parts.append(f"GROUP BY {group_by_str}")
        sql_parts.append(f"ORDER BY {group_by_str}")
        
        full_sql = " ".join(sql_parts)
        logging.info(f"执行自定义分析查询: {full_sql} with params {params}")

        try:
            cursor = self.conn.cursor()
            cursor.execute(full_sql, params)
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
        except sqlite3.Error as e:
            logging.error(f"自定义分析数据库查询失败: {e}", exc_info=True)
            return []