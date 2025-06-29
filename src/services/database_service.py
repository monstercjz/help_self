# desktop_center/src/services/database_service.py
import sqlite3
import logging
from typing import List, Dict, Any, Tuple
from datetime import datetime

class DatabaseService:
    """
    负责所有与SQLite数据库交互的服务。
    包括初始化、插入、查询和删除告警记录。
    """
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.conn = None
        try:
            self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
            self.conn.row_factory = sqlite3.Row
            logging.info(f"数据库连接已成功建立: {self.db_path}")
        except sqlite3.Error as e:
            logging.error(f"数据库连接失败: {e}", exc_info=True)
            raise

    def init_db(self):
        """
        初始化数据库，如果表不存在，则创建它。
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
            self.conn.commit()
            logging.info("数据库表 'alerts' 初始化完成。")
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
                      page_size: int = 50
    ) -> Tuple[List[Dict[str, Any]], int]:
        """
        根据多个条件搜索告警记录，并支持分页。
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

        sql_parts.append("ORDER BY timestamp DESC")

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
        """
        统计指定日期范围内各告警类型的数量。
        """
        sql_parts = ["SELECT type, COUNT(*) AS count FROM alerts WHERE 1=1"]
        params = []

        if start_date:
            sql_parts.append("AND timestamp >= ?")
            params.append(start_date + " 00:00:00")
        if end_date:
            sql_parts.append("AND timestamp <= ?")
            params.append(end_date + " 23:59:59")

        sql_parts.append("GROUP BY type ORDER BY count DESC")
        full_sql = " ".join(sql_parts)

        try:
            cursor = self.conn.cursor()
            cursor.execute(full_sql, params)
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
        except sqlite3.Error as e:
            logging.error(f"按类型统计查询失败: {e}", exc_info=True)
            return []

    # 【核心修改】全局按小时统计，支持日期范围
    def get_stats_by_hour(self, start_date: str, end_date: str) -> List[Dict[str, Any]]:
        """
        统计指定日期范围内每小时的告警数量 (全局)。
        """
        sql = """
            SELECT
                CAST(strftime('%H', timestamp) AS INTEGER) AS hour,
                COUNT(*) AS count
            FROM
                alerts
            WHERE
                timestamp >= ? AND timestamp <= ?
            GROUP BY
                hour
            ORDER BY
                hour ASC
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute(sql, (start_date + " 00:00:00", end_date + " 23:59:59"))
            rows = cursor.fetchall()
            
            hourly_counts = {row['hour']: row['count'] for row in rows}
            full_day_stats = []
            # 如果是单日查询，可以填充24小时
            # 如果是多日查询，通常不填充，因为会产生大量0值，图表和表格不易读
            # 这里选择不填充完整的24小时，只显示有数据的
            
            # 改进：始终返回24小时的数据，无论是否多日查询，便于统一图表绘制
            # for multi-day range, this still gives aggregate for that hour across all days
            full_24_hours_results = []
            for h in range(24):
                full_24_hours_results.append({'hour': h, 'count': hourly_counts.get(h, 0)})
            
            return full_24_hours_results
        except sqlite3.Error as e:
            logging.error(f"全局按小时统计查询失败: {e}", exc_info=True)
            return []

    # 【核心修改】按IP活跃度统计，支持日期范围
    def get_stats_by_ip_activity(self, start_date: str = None, end_date: str = None) -> List[Dict[str, Any]]:
        """
        统计指定日期范围内各IP的告警数量。
        """
        sql_parts = ["SELECT source_ip, COUNT(*) AS count FROM alerts WHERE 1=1"]
        params = []

        if start_date:
            sql_parts.append("AND timestamp >= ?")
            params.append(start_date + " 00:00:00")
        if end_date:
            sql_parts.append("AND timestamp <= ?")
            params.append(end_date + " 23:59:59")

        sql_parts.append("GROUP BY source_ip ORDER BY count DESC")
        full_sql = " ".join(sql_parts)

        try:
            cursor = self.conn.cursor()
            cursor.execute(full_sql, params)
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
        except sqlite3.Error as e:
            logging.error(f"按IP活跃度统计查询失败: {e}", exc_info=True)
            return []

    # 【核心修改】按IP按小时统计，支持日期范围
    def get_stats_by_ip_and_hour(self, ip_address: str, start_date: str, end_date: str) -> List[Dict[str, Any]]:
        """
        统计指定IP在指定日期范围内每小时的告警数量。
        """
        sql = """
            SELECT
                CAST(strftime('%H', timestamp) AS INTEGER) AS hour,
                COUNT(*) AS count
            FROM
                alerts
            WHERE
                source_ip = ? AND timestamp >= ? AND timestamp <= ?
            GROUP BY
                hour
            ORDER BY
                hour ASC
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute(sql, (ip_address, start_date + " 00:00:00", end_date + " 23:59:59"))
            rows = cursor.fetchall()
            
            # 填充缺失的小时数据为0
            hourly_counts = {row['hour']: row['count'] for row in rows}
            full_24_hours_stats = []
            for hour in range(24):
                full_24_hours_stats.append({'hour': hour, 'count': hourly_counts.get(hour, 0)})
            
            return full_24_hours_stats
        except sqlite3.Error as e:
            logging.error(f"按IP按小时统计查询失败: {e}", exc_info=True)
            return []