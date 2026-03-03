"""
任务查询 Agent
处理任务进度、工单、项目状态查询等请求
"""
from app.agents.base import BaseAgent


class TaskAgent(BaseAgent):
    """
    任务查询 Agent
    负责处理任务进度、工单、项目状态查询等请求
    """

    agent_id = "TaskAgent"

    def invoke(self, text: str, context: dict) -> str:
        """
        处理任务查询请求
        :param text: 用户请求文本
        :param context: 上下文信息
        :return: 响应文本
        """
        return f"[TaskAgent] 任务查询（MVP mock）：未发现阻塞任务，建议检查 Jira 过滤条件。"
