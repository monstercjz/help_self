# desktop_center/src/features/alert_center/models/custom_analysis_model.py
from collections import defaultdict
from typing import List, Dict, Any

class CustomAnalysisModel:
    """
    为自定义分析功能提供数据处理能力。
    """
    def build_tree_from_data(self, data: List[Dict[str, Any]], dimensions: List[str]) -> Dict:
        """
        【变更】将扁平的数据库查询结果，根据动态维度列表，通过递归方式构建成嵌套字典。

        Args:
            data: 从数据库获取的行列表。
            dimensions: 用户选择的维度顺序，例如 ['severity', 'type']。

        Returns:
            一个代表层级树的嵌套字典。
        """
        if not data or not dimensions:
            return {}

        def recursive_builder(sub_data: List[Dict[str, Any]], dims: List[str]) -> Dict:
            """
            递归函数，处理当前维度层级的数据。

            Args:
                sub_data: 属于当前递归分支的数据子集。
                dims: 剩余待处理的维度列表。

            Returns:
                当前层级的树状字典。
            """
            # 基本情况：没有更多维度需要处理
            if not dims:
                return {}

            current_dim = dims[0]
            remaining_dims = dims[1:]
            
            # 使用defaultdict简化节点的创建
            tree_level = defaultdict(lambda: {'_count': 0, '_children': {}})
            
            # 第一次遍历：计算当前层级每个键的总数
            for row in sub_data:
                key = row[current_dim]
                tree_level[key]['_count'] += row.get('count', 0)
            
            # 如果还有剩余维度，则为每个键递归构建子树
            if remaining_dims:
                # 首先按当前维度对数据进行分组，以优化递归调用
                grouped_data = defaultdict(list)
                for row in sub_data:
                    grouped_data[row[current_dim]].append(row)
                
                # 为每个分组的数据递归调用
                for key, node in tree_level.items():
                    node['_children'] = recursive_builder(grouped_data[key], remaining_dims)
            
            # 返回排序后的字典，以保证UI显示顺序稳定
            return dict(sorted(tree_level.items()))

        # 从顶层维度开始递归
        return recursive_builder(data, dimensions)