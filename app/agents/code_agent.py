"""
代码生成 Agent
处理代码生成、重构、调试等请求
"""
from app.agents.base import BaseAgent


class CodeAgent(BaseAgent):
    """
    代码生成 Agent
    负责处理代码相关的请求，如生成代码、重构、调试等
    """

    agent_id = "CodeAgent"

    def invoke(self, text: str, context: dict) -> str:
        """
        处理代码生成请求
        :param text: 用户请求文本
        :param context: 上下文信息
        :return: 响应文本
        """
        return f"[CodeAgent] 已收到代码请求：{text}\n示例建议：可先定义接口、加单元测试、再补文档。"
