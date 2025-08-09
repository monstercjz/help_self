from PySide6.QtCore import QObject, Signal
import logging

class CalculatorModel(QObject):
    """
    计算器模型，处理计算逻辑和历史记录。
    """
    history_updated = Signal(list) # 当历史记录更新时发出信号

    def __init__(self):
        super().__init__()
        self._current_expression = ""
        self._current_result = "0"
        self._history = [] # 存储历史记录，每个条目是 (expression, result)
        logging.info("CalculatorModel: 初始化完成。")

    def get_current_expression(self) -> str:
        return self._current_expression

    def get_current_result(self) -> str:
        return self._current_result

    def get_history(self) -> list:
        return list(self._history) # 返回副本以防止外部直接修改

    def append_input(self, value: str):
        """向当前表达式追加输入。"""
        if self._current_result != "0" and self._current_expression == "":
            # 如果有上次计算结果且没有新输入，则清空结果开始新计算
            self._current_expression = self._current_result
            self._current_result = "0"

        if value in "+-*/" and not self._current_expression:
            # 如果是运算符且表达式为空，则使用当前结果作为第一个操作数
            self._current_expression = self._current_result + value
        elif value == "=":
            self.calculate_result()
        elif value == "C":
            self.clear_all()
        elif value == "DEL":
            self.delete_last_char()
        else:
            self._current_expression += value
        logging.debug(f"CalculatorModel: 追加输入 '{value}', 当前表达式: '{self._current_expression}'")

    def calculate_result(self):
        """计算当前表达式的结果并更新历史记录。"""
        if not self._current_expression:
            return

        try:
            # 替换特殊字符，例如 '×' 为 '*'，'÷' 为 '/'
            expression_to_eval = self._current_expression.replace('×', '*').replace('÷', '/')
            
            # 处理百分比符号 '%'
            # 简单的处理方式：将 'X%' 转换为 'X/100'
            # 注意：这不处理 'A + B%' 这种复杂情况，只处理独立数字的百分比
            if '%' in expression_to_eval:
                # 使用正则表达式查找数字后紧跟的百分号
                import re
                # 匹配数字（整数或浮点数）后紧跟的百分号
                expression_to_eval = re.sub(r'(\d+\.?\d*)%', r'(\1/100)', expression_to_eval)

            # 确保表达式是安全的，只包含数字和基本运算符
            # 这是一个简化的安全检查，实际应用中可能需要更健壮的解析器
            # 允许的字符包括数字、运算符、小数点和括号
            allowed_chars = "0123456789+-*/.()"
            if not all(c in allowed_chars for c in expression_to_eval):
                raise ValueError("包含非法字符")

            result = str(eval(expression_to_eval))
            self._current_result = result
            self._history.append((self._current_expression, result))
            self.history_updated.emit(self._history)
            self._current_expression = "" # 计算后清空表达式
            logging.info(f"CalculatorModel: 计算 '{expression_to_eval}' = '{result}'")
        except Exception as e:
            self._current_result = "Error"
            logging.error(f"CalculatorModel: 计算表达式 '{self._current_expression}' 失败: {e}")
            self._current_expression = "" # 错误后也清空表达式

    def clear_all(self):
        """清空当前表达式和结果。"""
        self._current_expression = ""
        self._current_result = "0"
        logging.info("CalculatorModel: 已清空所有。")

    def delete_last_char(self):
        """删除当前表达式的最后一个字符。"""
        self._current_expression = self._current_expression[:-1]
        if not self._current_expression:
            self._current_result = "0" # 如果表达式为空，结果显示0
        logging.debug(f"CalculatorModel: 删除最后一个字符，当前表达式: '{self._current_expression}'")

    def clear_history(self):
        """清空历史记录。"""
        self._history = []
        self.history_updated.emit(self._history)
        logging.info("CalculatorModel: 已清空历史记录。")