# src/features/calculator/models/calculator_model.py

class CalculatorModel:
    """
    管理计算器的状态。
    """
    def __init__(self):
        self._expression = ""
        self._display_text = "0"
        self.result_is_displayed = False
        self.history = []

    @property
    def expression(self) -> str:
        """获取内部计算表达式。"""
        return self._expression

    @expression.setter
    def expression(self, value: str):
        """设置内部计算表达式。"""
        self._expression = value

    @property
    def display_text(self) -> str:
        """获取用于UI显示的文本。"""
        return self._display_text

    @display_text.setter
    def display_text(self, value: str):
        """设置用于UI显示的文本。"""
        self._display_text = value
