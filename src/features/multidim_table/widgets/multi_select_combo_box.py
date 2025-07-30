# src/features/multidim_table/widgets/multi_select_combo_box.py
from PySide6.QtWidgets import QComboBox, QListView, QCheckBox, QStyledItemDelegate
from PySide6.QtGui import QStandardItemModel, QStandardItem
from PySide6.QtCore import Qt, Signal

class MultiSelectComboBox(QComboBox):
    itemsSelected = Signal(list)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setEditable(True)
        self.lineEdit().setReadOnly(True)
        
        list_view = QListView(self)
        self.setView(list_view)
        
        self.model = QStandardItemModel(self)
        self.setModel(self.model)

        self.view().setItemDelegate(QStyledItemDelegate(self.view()))

    def addItem(self, text, data=None):
        item = QStandardItem(text)
        item.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled)
        item.setData(Qt.Unchecked, Qt.CheckStateRole)
        self.model.appendRow(item)

    def addItems(self, texts):
        for text in texts:
            self.addItem(text)

    def hidePopup(self):
        self._emit_selected_items()
        super().hidePopup()

    def _emit_selected_items(self):
        selected_items = []
        for i in range(self.model.rowCount()):
            item = self.model.item(i)
            if item.checkState() == Qt.Checked:
                selected_items.append(item.text())
        self.itemsSelected.emit(selected_items)
        self.lineEdit().setText(", ".join(selected_items))

    def setSelectedItems(self, texts):
        for i in range(self.model.rowCount()):
            item = self.model.item(i)
            if item.text() in texts:
                item.setCheckState(Qt.Checked)
            else:
                item.setCheckState(Qt.Unchecked)
        self._emit_selected_items()
