# src/features/multidim_table/views/statistics_tab_view.py
from PySide6.QtWidgets import QVBoxLayout, QWidget, QTableView, QHeaderView, QPushButton, QHBoxLayout
from PySide6.QtCore import QAbstractTableModel, Qt, QModelIndex
import pandas as pd

class PandasTableModel(QAbstractTableModel):
    """
    一个用于将 Pandas DataFrame 显示在 QTableView 中的模型。
    """
    def __init__(self, dataframe: pd.DataFrame = pd.DataFrame(), parent=None):
        super().__init__(parent)
        self._dataframe = dataframe

    def rowCount(self, parent=QModelIndex()):
        return self._dataframe.shape[0]

    def columnCount(self, parent=QModelIndex()):
        return self._dataframe.shape[1]

    def data(self, index: QModelIndex, role: int):
        if not index.isValid():
            return None
        if role == Qt.DisplayRole:
            return str(self._dataframe.iloc[index.row(), index.column()])
        return None

    def headerData(self, section: int, orientation: Qt.Orientation, role: int):
        if role == Qt.DisplayRole:
            if orientation == Qt.Horizontal:
                return str(self._dataframe.columns[section])
            elif orientation == Qt.Vertical:
                # 如果有行索引，可以显示行索引
                # return str(self._dataframe.index[section])
                return str(section + 1) # 默认显示行号
        return None

    def set_dataframe(self, dataframe: pd.DataFrame):
        self.beginResetModel()
        self._dataframe = dataframe
        self.endResetModel()

class StatisticsTabView(QWidget):
    """
    用于显示统计结果的标签页。
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        # 创建按钮
        self.calculate_button = QPushButton("执行计算")
        
        self.config_button = QPushButton("配置统计")

        # 按钮布局
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        button_layout.addWidget(self.config_button)
        button_layout.addWidget(self.calculate_button)
        button_layout.addStretch()

        self.table_view = QTableView()
        self.table_model = PandasTableModel()
        self.table_view.setModel(self.table_model)

        # 调整列宽以适应内容
        self.table_view.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table_view.verticalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)

        layout.addLayout(button_layout)
        layout.addWidget(self.table_view)

    def display_statistics_data(self, dataframe: pd.DataFrame):
        """
        设置并显示统计数据。
        """
        self.table_model.set_dataframe(dataframe)