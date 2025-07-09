# src/features/multidim_table/widgets/custom_delegate.py
from PySide6.QtWidgets import (
    QStyledItemDelegate, QLineEdit, QComboBox, QDateTimeEdit
)
from PySide6.QtCore import QDateTime

class CustomItemDelegate(QStyledItemDelegate):
    """
    一个自定义的委托，用于根据数据类型为QTableView提供不同的编辑器。
    """
    def __init__(self, schema, parent=None):
        super().__init__(parent)
        self.schema = schema
        # 创建一个从列索引到类型的快速查找字典
        self.column_types = {i: field['type'].upper() for i, field in enumerate(self.schema)}

    def createEditor(self, parent, option, index):
        """当用户开始编辑一个单元格时，创建相应的编辑器。"""
        col = index.column()
        col_type = self.column_types.get(col)

        if col_type == 'DATETIME':
            editor = QDateTimeEdit(parent)
            editor.setCalendarPopup(True)
            editor.setDisplayFormat("yyyy-MM-dd HH:mm:ss")
            return editor
        elif col_type == 'BOOLEAN':
            editor = QComboBox(parent)
            editor.addItems(["True", "False"])
            return editor
        
        # 对于所有其他类型，使用默认的编辑器
        return super().createEditor(parent, option, index)

    def setEditorData(self, editor, index):
        """将模型中的数据设置到编辑器中。"""
        value = index.model().data(index, 0) # Qt.EditRole is 0
        if isinstance(editor, QDateTimeEdit):
            # 尝试将字符串转换为QDateTime
            dt = QDateTime.fromString(value, "yyyy-MM-dd HH:mm:ss")
            editor.setDateTime(dt)
        elif isinstance(editor, QComboBox):
            editor.setCurrentText(value)
        else:
            super().setEditorData(editor, index)

    def setModelData(self, editor, model, index):
        """将编辑器中的数据写回到模型中。"""
        if isinstance(editor, QDateTimeEdit):
            model.setData(index, editor.text())
        elif isinstance(editor, QComboBox):
            model.setData(index, editor.currentText())
        else:
            super().setModelData(editor, model, index)