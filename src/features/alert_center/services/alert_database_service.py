# desktop_center/src/features/alert_center/services/alert_database_service.py
import sqlite3
import logging
import os
from typing import List, Dict, Any, Tuple
from datetime import datetime
# 【变更】导入插件的数据库扩展
from ..database_extensions import AlertCenterDatabaseExtensions
from src.core.context import ApplicationContext
from src.services.base_database_service import BaseDatabaseService

# 【变更】让DatabaseService继承扩展类和新的基类
class AlertDatabaseService(AlertCenterDatabaseExtensions, BaseDatabaseService):
    """
    负责所有与SQLite数据库交互的服务。
    继承自 BaseDatabaseService，只关注业务逻辑。
    """
    TABLE_NAME = "alerts"
    EXPECTED_COLUMNS = {'id', 'timestamp', 'severity', 'type', 'source_ip', 'message'}

    def __init__(self, db_path: str):
        # 调用父类的构造函数来处理连接和通用验证
        BaseDatabaseService.__init__(self, db_path)

    def _create_table(self):
        """实现父类的抽象方法，定义 'alerts' 表的创建SQL。"""
        self.init_db() # 复用原有的init_db逻辑

    def init_db(self):
        """
        初始化数据库，如果表不存在，则创建它。
        同时创建必要的索引以提高查询性能。
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS alerts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    severity TEXT NOT NULL,
                    type TEXT NOT NULL,
                    source_ip TEXT,
                    message TEXT
                )
            """)
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_alerts_timestamp ON alerts (timestamp DESC)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_alerts_severity ON alerts (severity)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_alerts_type ON alerts (type)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_alerts_source_ip ON alerts (source_ip)")
            self.conn.commit()
            logging.info("数据库表 'alerts' 初始化完成，并创建了索引。")
        except sqlite3.Error as e:
            logging.error(f"创建数据库表失败: {e}", exc_info=True)

    def add_alert(self, alert_data: Dict[str, Any]) -> None:
        """
        将一条新的告警记录插入到数据库。
        """
        sql = ''' INSERT INTO alerts(timestamp, severity, type, source_ip, message)
                  VALUES(datetime('now', 'localtime'),?,?,?,?) '''
        try:
            cursor = self.conn.cursor()
            cursor.execute(sql, (
                alert_data.get('severity', 'INFO'),
                alert_data.get('type', 'Unknown'),
                alert_data.get('source_ip', 'N/A'),
                alert_data.get('message', 'N/A')
            ))
            self.conn.commit()
        except sqlite3.Error as e:
            logging.error(f"向数据库插入告警失败: {e}", exc_info=True)

    def get_recent_alerts(self, limit: int = 100) -> List[Dict[str, Any]]:
        """
        获取最近的N条告警记录。
        """
        if limit <= 0:
            return []
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT * FROM alerts ORDER BY timestamp DESC LIMIT ?", (limit,))
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
        except sqlite3.Error as e:
            logging.error(f"从数据库查询最近告警失败: {e}", exc_info=True)
            return []

    def clear_all_alerts(self) -> bool:
        """
        删除'alerts'表中的所有记录。
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute("DELETE FROM alerts")
            cursor.execute("DELETE FROM sqlite_sequence WHERE name='alerts'")
            self.conn.commit()
            logging.info("数据库'alerts'表中的所有记录已被清除。")
            return True
        except sqlite3.Error as e:
            logging.error(f"清空数据库表失败: {e}", exc_info=True)
            return False
            
    def delete_alerts_by_ids(self, alert_ids: List[int]) -> bool:
        """
        根据提供的ID列表删除告警记录。
        """
        if not alert_ids:
            return True
        
        placeholders = ','.join('?' for _ in alert_ids)
        sql = f"DELETE FROM alerts WHERE id IN ({placeholders})"
        try:
            cursor = self.conn.cursor()
            cursor.execute(sql, alert_ids)
            self.conn.commit()
            logging.info(f"成功删除 {cursor.rowcount} 条告警记录。IDs: {alert_ids}")
            return True
        except sqlite3.Error as e:
            logging.error(f"删除告警记录失败: {e}", exc_info=True)
            return False

    def close(self):
        """关闭数据库连接。"""
        if self.conn:
            self.conn.close()
            logging.info("数据库连接已关闭。")

    def search_alerts(self, 
                      start_date: str = None, 
                      end_date: str = None, 
                      severities: List[str] = None, 
                      keyword: str = None, 
                      search_field: str = 'all', 
                      page: int = 1, 
                      page_size: int = 50,
                      order_by: str = 'timestamp',
                      order_direction: str = 'DESC'
    ) -> Tuple[List[Dict[str, Any]], int]:
        """
        根据多个条件搜索告警记录，并支持分页和排序。
        """
        sql_parts = ["SELECT id, timestamp, severity, type, source_ip, message FROM alerts WHERE 1=1"]
        count_sql_parts = ["SELECT COUNT(*) FROM alerts WHERE 1=1"]
        params = []

        if start_date:
            sql_parts.append("AND timestamp >= ?")
            count_sql_parts.append("AND timestamp >= ?")
            params.append(start_date + " 00:00:00")
        if end_date:
            sql_parts.append("AND timestamp <= ?")
            count_sql_parts.append("AND timestamp <= ?")
            params.append(end_date + " 23:59:59")

        if severities and len(severities) > 0:
            placeholders = ','.join('?' for _ in severities)
            sql_parts.append(f"AND severity IN ({placeholders})")
            count_sql_parts.append(f"AND severity IN ({placeholders})")
            params.extend(severities)

        if keyword:
            like_keyword = f"%{keyword}%"
            if search_field == 'all':
                sql_parts.append("AND (message LIKE ? OR source_ip LIKE ? OR type LIKE ?)")
                count_sql_parts.append("AND (message LIKE ? OR source_ip LIKE ? OR type LIKE ?)")
                params.extend([like_keyword, like_keyword, like_keyword])
            elif search_field == 'message':
                sql_parts.append("AND message LIKE ?")
                count_sql_parts.append("AND message LIKE ?")
                params.append(like_keyword)
            elif search_field == 'source_ip':
                sql_parts.append("AND source_ip LIKE ?")
                count_sql_parts.append("AND source_ip LIKE ?")
                params.append(like_keyword)
            elif search_field == 'type':
                sql_parts.append("AND type LIKE ?")
                count_sql_parts.append("AND type LIKE ?")
                params.append(like_keyword)

        valid_order_by_fields = ['id', 'timestamp', 'severity', 'type', 'source_ip']
        if order_by not in valid_order_by_fields:
            order_by = 'timestamp'
        
        valid_order_directions = ['ASC', 'DESC']
        if order_direction.upper() not in valid_order_directions:
            order_direction = 'DESC'

        sql_parts.append(f"ORDER BY {order_by} {order_direction}")

        try:
            cursor = self.conn.cursor()

            count_sql = " ".join(count_sql_parts)
            total_count_params = params[:]
            cursor.execute(count_sql, total_count_params)
            total_count = cursor.fetchone()[0]

            main_sql = " ".join(sql_parts)
            offset = (page - 1) * page_size
            main_sql += f" LIMIT ? OFFSET ?"
            
            main_params = params + [page_size, offset]
            
            cursor.execute(main_sql, main_params)
            rows = cursor.fetchall()
            results = [dict(row) for row in rows]

            return results, total_count
        except sqlite3.Error as e:
            logging.error(f"数据库搜索失败: {e}", exc_info=True)
            return [], 0

    def get_stats_by_type(self, start_date: str = None, end_date: str = None) -> List[Dict[str, Any]]:
        sql_parts = ["SELECT type, COUNT(*) AS count FROM alerts WHERE 1=1"]
        params = []
        if start_date:
            sql_parts.append("AND timestamp >= ?"); params.append(start_date + " 00:00:00")
        if end_date:
            sql_parts.append("AND timestamp <= ?"); params.append(end_date + " 23:59:59")
        sql_parts.append("GROUP BY type ORDER BY count DESC")
        try:
            cursor = self.conn.cursor(); cursor.execute(" ".join(sql_parts), params)
            return [dict(row) for row in cursor.fetchall()]
        except sqlite3.Error as e:
            logging.error(f"按类型统计查询失败: {e}", exc_info=True); return []

    def get_stats_by_ip_activity(self, start_date: str = None, end_date: str = None) -> List[Dict[str, Any]]:
        sql_parts = ["SELECT source_ip, COUNT(*) AS count FROM alerts WHERE 1=1"]
        params = []
        if start_date:
            sql_parts.append("AND timestamp >= ?"); params.append(start_date + " 00:00:00")
        if end_date:
            sql_parts.append("AND timestamp <= ?"); params.append(end_date + " 23:59:59")
        sql_parts.append("GROUP BY source_ip ORDER BY count DESC")
        try:
            cursor = self.conn.cursor(); cursor.execute(" ".join(sql_parts), params)
            return [dict(row) for row in cursor.fetchall()]
        except sqlite3.Error as e:
            logging.error(f"按IP活跃度统计查询失败: {e}", exc_info=True); return []
    
    def get_stats_by_hour(self, start_date: str, end_date: str) -> List[Dict[str, Any]]:
        sql = "SELECT CAST(strftime('%H', timestamp) AS INTEGER) AS hour, COUNT(*) AS count FROM alerts WHERE timestamp >= ? AND timestamp <= ? GROUP BY hour ORDER BY hour ASC"
        try:
            cursor = self.conn.cursor(); cursor.execute(sql, (start_date + " 00:00:00", end_date + " 23:59:59"))
            hourly_counts = {row['hour']: row['count'] for row in cursor.fetchall()}
            return [{'hour': h, 'count': hourly_counts.get(h, 0)} for h in range(24)]
        except sqlite3.Error as e:
            logging.error(f"全局按小时统计查询失败: {e}", exc_info=True); return []
            
    def get_stats_by_ip_and_hour(self, ip_address: str, start_date: str, end_date: str) -> List[Dict[str, Any]]:
        sql = "SELECT CAST(strftime('%H', timestamp) AS INTEGER) AS hour, COUNT(*) AS count FROM alerts WHERE source_ip = ? AND timestamp >= ? AND timestamp <= ? GROUP BY hour ORDER BY hour ASC"
        try:
            cursor = self.conn.cursor(); cursor.execute(sql, (ip_address, start_date + " 00:00:00", end_date + " 23:59:59"))
            hourly_counts = {row['hour']: row['count'] for row in cursor.fetchall()}
            return [{'hour': h, 'count': hourly_counts.get(hour, 0)} for hour in range(24)]
        except sqlite3.Error as e:
            logging.error(f"按IP按小时统计查询失败: {e}", exc_info=True); return []

    def get_detailed_hourly_stats(self, start_date: str, end_date: str, ip_address: str = None) -> List[Dict[str, Any]]:
        sql_parts = ["SELECT CAST(strftime('%H', timestamp) AS INTEGER) AS hour, severity, type, COUNT(*) AS count FROM alerts WHERE timestamp >= ? AND timestamp <= ?"]
        params = [start_date + " 00:00:00", end_date + " 23:59:59"]
        if ip_address:
            sql_parts.append("AND source_ip = ?"); params.append(ip_address)
        sql_parts.extend(["GROUP BY hour, severity, type", "ORDER BY hour ASC, severity ASC, type ASC"])
        try:
            cursor = self.conn.cursor(); cursor.execute(" ".join(sql_parts), params)
            return [dict(row) for row in cursor.fetchall()]
        except sqlite3.Error as e:
            logging.error(f"获取详细按小时统计失败: {e}", exc_info=True); return []

    def get_distinct_source_ips(self, start_date: str = None, end_date: str = None) -> List[str]:
        sql_parts = ["SELECT source_ip, COUNT(*) as count FROM alerts WHERE source_ip IS NOT NULL AND source_ip != 'N/A'"]
        params = []
        if start_date:
            sql_parts.append("AND timestamp >= ?"); params.append(start_date + " 00:00:00")
        if end_date:
            sql_parts.append("AND timestamp <= ?"); params.append(end_date + " 23:59:59")
        sql_parts.append("GROUP BY source_ip ORDER BY count DESC")
        try:
            cursor = self.conn.cursor(); cursor.execute(" ".join(sql_parts), params)
            return [row['source_ip'] for row in cursor.fetchall()]
        except sqlite3.Error as e:
            logging.error(f"获取不重复IP列表失败: {e}", exc_info=True); return []