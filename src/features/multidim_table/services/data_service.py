# src/features/multidim_table/services/data_service.py
import pandas as pd
import json
import os
from src.features.multidim_table.models.multidim_table_model import MultidimTableModel

class DataService:
    """
    服务层，封装了多维表格的核心业务逻辑。
    """
    def __init__(self, model: MultidimTableModel):
        self._model = model

    def generate_column_analysis_report(self, series: pd.Series) -> str:
        """
        为单个数据列（Series）生成描述性统计或频率分布的分析报告。
        """
        column_name = series.name
        result_text = f"--- 对字段 '{column_name}' 的分析 ---\n\n"
        if pd.api.types.is_numeric_dtype(series):
            stats = series.describe()
            result_text += "基本描述性统计:\n"
            result_text += "---------------------\n"
            result_text += f"总数 (Count):    {stats.get('count', 'N/A')}\n"
            result_text += f"平均值 (Mean):     {stats.get('mean', 'N/A'):.2f}\n"
            result_text += f"标准差 (Std):    {stats.get('std', 'N/A'):.2f}\n"
            result_text += f"最小值 (Min):      {stats.get('min', 'N/A')}\n"
            result_text += f"25% (Q1):        {stats.get('25%', 'N/A')}\n"
            result_text += f"50% (Median):    {stats.get('50%', 'N/A')}\n"
            result_text += f"75% (Q3):        {stats.get('75%', 'N/A')}\n"
            result_text += f"最大值 (Max):      {stats.get('max', 'N/A')}\n"
        else:
            counts = series.value_counts()
            result_text += "值的频率分布:\n"
            result_text += "---------------------\n"
            result_text += counts.to_string()
        return result_text

    def create_pivot_table(self, df: pd.DataFrame, pivot_config: dict) -> tuple[bool, pd.DataFrame | None, str | None]:
        """
        根据配置从给定的DataFrame创建数据透视表。
        """
        return self._model.create_pivot_table_from_df(df, pivot_config)

    def save_table_data(self, table_name: str, dataframe: pd.DataFrame) -> tuple[bool, str | None]:
        """
        以安全的方式保存整个DataFrame到指定的表中（清空后插入）。
        """
        return self._model.replace_table_data_transaction(table_name, dataframe)

    def execute_custom_analysis(self, df: pd.DataFrame, query: str) -> tuple[bool, pd.DataFrame | None, str | None]:
        """
        使用 df.query() 执行自定义分析语句。
        为了安全，我们使用 pandas 自带的 query 功能，它比 eval 更受限。
        """
        try:
            # 为了让 query 更直观，允许用户直接使用 df
            # 但实际执行时 df.query() 的上下文就是 df 本身，所以我们替换掉它
            if 'df.' in query:
                query = query.replace('df.', '')

            result_df = df.query(query, engine='python')
            return True, result_df, None
        except Exception as e:
            return False, None, str(e)

    def get_custom_statistics(self, table_name: str, config_path: str) -> tuple[bool, pd.DataFrame | None, str | None]:
        """
        根据指定的外部配置文件动态生成并执行查询。
        支持 'statistics' 和 'filter' 两种查询类型。
        """
        if not os.path.exists(config_path):
            return False, None, f"配置文件 '{os.path.basename(config_path)}' 未找到。"

        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
        except Exception as e:
            return False, None, f"读取或解析配置文件失败: {e}"

        query_type = config.get("query_type", "statistics") # 默认为旧的统计模式

        if query_type == "statistics":
            return self._execute_statistics_query(table_name, config)
        elif query_type == "filter":
            return self._execute_filter_query(table_name, config)
        elif query_type == "group_by_aggregate":
            return self._execute_group_by_aggregate_query(table_name, config)
        else:
            return False, None, f"不支持的查询类型: '{query_type}'"

    def _execute_statistics_query(self, table_name: str, config: dict) -> tuple[bool, pd.DataFrame | None, str | None]:
        """执行 'statistics' 类型的查询。"""
        schema, err = self._model.get_table_schema(table_name)
        if err: return False, None, f"无法获取表结构: {err}"
        
        table_columns = {col['name'] for col in schema}
        required_cols = set(config.get("required_columns", []))

        if not required_cols.issubset(table_columns):
            missing_cols = ", ".join(required_cols - table_columns)
            return False, None, f"当前表缺少必要的列: {missing_cols}。"

        base_cols_str = ", ".join([f'"{col}"' for col in required_cols])
        calc_cols_str = ", ".join([f'{col["formula"]} AS "{col["name"]}"' for col in config.get("calculated_columns", [])])
        all_cols_str = f"{base_cols_str}, {calc_cols_str}" if calc_cols_str else base_cols_str
        where_clause = " AND ".join([f'"{col}" IS NOT NULL' for col in required_cols])
        summary_row_name = config.get("summary_row_name", "总计")
        group_by_col = config.get("group_by_column", "id")
        null_cols_count = len(required_cols) - 1 + len(config.get("calculated_columns", [])) - len(config.get("aggregation_columns", []))
        null_placeholders = ", ".join(["NULL"] * null_cols_count)
        agg_cols_str = ", ".join([f'{col["formula"]}' for col in config.get("aggregation_columns", [])])

        sql_query = f"""
        SELECT {all_cols_str}, 1 AS sort_order FROM "{table_name}" WHERE {where_clause}
        UNION ALL
        SELECT '{summary_row_name}', {null_placeholders}, {agg_cols_str}, 2 FROM "{table_name}" WHERE {where_clause}
        ORDER BY sort_order, "{group_by_col}";
        """
        try:
            stats_df = pd.read_sql(sql_query, self._model.conn)
            if 'sort_order' in stats_df.columns:
                stats_df = stats_df.drop(columns=['sort_order'])
            return True, stats_df, None
        except Exception as e:
            return False, None, f"执行统计查询失败: {e}"

    def _execute_filter_query(self, table_name: str, config: dict) -> tuple[bool, pd.DataFrame | None, str | None]:
        """执行 'filter' 类型的查询。"""
        display_cols = config.get("display_columns", ["*"])
        filters = config.get("filters", [])

        if not filters:
            return False, None, "筛选查询需要至少一个筛选条件。"

        display_cols_str = ", ".join([f'"{col}"' for col in display_cols])
        
        where_conditions = []
        for f in filters:
            col, op, val = f.get("column"), f.get("operator"), f.get("value")
            if not all([col, op, val is not None]):
                return False, None, f"筛选器格式错误: {f}"
            
            # 对字符串值进行转义处理
            if isinstance(val, str):
                # 正确处理SQL字符串中的单引号转义
                val_str = "'" + val.replace("'", "''") + "'"
            else:
                val_str = str(val)
            where_conditions.append(f'"{col}" {op} {val_str}')
        
        where_clause = " AND ".join(where_conditions)

        sql_query = f"SELECT {display_cols_str} FROM \"{table_name}\" WHERE {where_clause};"

        try:
            result_df = pd.read_sql(sql_query, self._model.conn)
            return True, result_df, None
        except Exception as e:
            return False, None, f"执行筛选查询失败: {e}"


    def _execute_group_by_aggregate_query(self, table_name: str, config: dict) -> tuple[bool, pd.DataFrame | None, str | None]:
        """执行 'group_by_aggregate' 类型的查询。"""
        group_by_columns = config.get("group_by_columns", [])
        aggregations = config.get("aggregations", [])

        if not group_by_columns and not aggregations:
            return False, None, "分组聚合查询需要指定分组列或聚合函数。"

        group_by_cols_str = ", ".join([f'"{col}"' for col in group_by_columns])
        
        select_parts = []
        if group_by_columns:
            select_parts.append(group_by_cols_str)
        
        agg_parts = []
        for agg in aggregations:
            name = agg.get("name")
            func = agg.get("function")
            col = agg.get("column")
            if not all([name, func, col]):
                return False, None, f"聚合函数格式错误: {agg}"
            agg_parts.append(f'{func.upper()}("{col}") AS "{name}"')
        
        if agg_parts:
            select_parts.append(", ".join(agg_parts))
        
        select_clause = ", ".join(select_parts)
        
        group_by_clause = ""
        if group_by_columns:
            group_by_clause = f"GROUP BY {group_by_cols_str}"

        sql_query = f"SELECT {select_clause} FROM \"{table_name}\" {group_by_clause};"

        try:
            result_df = pd.read_sql(sql_query, self._model.conn)
            return True, result_df, None
        except Exception as e:
            return False, None, f"执行分组聚合查询失败: {e}"
