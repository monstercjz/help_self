# src/features/multidim_table/services/data_service.py
import pandas as pd
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
