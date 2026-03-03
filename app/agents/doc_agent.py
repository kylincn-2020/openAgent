"""
文档问答 Agent
处理文档解释、知识问答等请求
"""
from app.agents.base import BaseAgent


class DocAgent(BaseAgent):
    """
    文档问答 Agent
    负责处理文档解释、知识问答、报错说明等请求
    """

    agent_id = "DocAgent"

    def invoke(self, text: str, context: dict) -> str:
        """
        处理文档问答请求
        :param text: 用户请求文本
        :param context: 上下文信息
        :return: 响应文本
        """
        return f"[DocAgent] 文档问答结果（MVP 示例）：你问的是：{text}"
