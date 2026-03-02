"""
数据分析 Agent - 示例子 agent
"""

from typing import Optional, Dict, Any
from core.base_agent import BaseAgent
from core.registry import registry


@registry.register(
    name="analysis_agent",
    description="数据分析助手，帮助分析数据、解释统计结果、提供数据洞察",
    category="analysis",
    keywords=[
        "数据",
        "分析",
        "统计",
        "图表",
        "可视化",
        "excel",
        "csv",
        "pandas",
        "机器学习",
        "预测",
        "趋势",
        "洞察",
        "报表",
    ],
)
class AnalysisAgent(BaseAgent):
    """数据分析 Agent"""

    def get_system_prompt(self) -> str:
        return """你是一位专业的数据分析师。你的职责：

1. **数据分析**: 分析数据集，发现模式和趋势
2. **统计解释**: 解释统计指标和分析结果
3. **可视化建议**: 推荐合适的图表类型和可视化方案
4. **代码生成**: 生成 Python 数据分析代码（pandas, numpy, matplotlib 等）
5. **洞察提炼**: 从数据中提取有价值的商业洞察
6. **方法建议**: 推荐合适的分析方法和模型

回答风格：
- 用数据说话，提供具体数字
- 解释技术概念时通俗易懂
- 提供可执行的代码示例
- 指出分析的局限性和注意事项
"""

    async def act(
        self, user_input: str, context: Optional[Dict[str, Any]] = None
    ) -> str:
        """处理数据分析相关请求"""
        system_prompt = self.get_system_prompt()

        messages = context.get("messages", []) if context else []

        response = await self._invoke_llm(
            messages=messages, system_prompt=system_prompt
        )

        return response
