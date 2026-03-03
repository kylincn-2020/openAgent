"""
Agent 注册中心
管理所有可用的 Agent 实例
"""
from app.agents.code_agent import CodeAgent
from app.agents.doc_agent import DocAgent
from app.agents.task_agent import TaskAgent


class AgentRegistry:
    """
    Agent 注册中心
    单例模式，管理所有 Agent 实例
    """

    def __init__(self):
        """初始化注册中心，注册所有内置 Agent"""
        self._agents = {
            "CodeAgent": CodeAgent(),
            "DocAgent": DocAgent(),
            "TaskAgent": TaskAgent(),
        }

    def get(self, agent_id: str):
        """
        获取指定 Agent 实例
        :param agent_id: Agent ID
        :raises ValueError: 如果 Agent 不存在
        :return: Agent 实例
        """
        if agent_id not in self._agents:
            raise ValueError(f"Agent not found: {agent_id}")
        return self._agents[agent_id]
