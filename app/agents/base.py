"""
Agent 抽象基类
定义所有 Agent 必须实现的接口
"""
from abc import ABC, abstractmethod
from typing import Dict, Any


class BaseAgent(ABC):
    """
    Agent 抽象基类
    所有具体 Agent 必须继承此类并实现 invoke 方法
    """

    agent_id: str  # Agent 唯一标识

    @abstractmethod
    def invoke(self, text: str, context: Dict[str, Any]) -> str:
        """
        调用 Agent 处理请求
        :param text: 用户输入文本
        :param context: 上下文信息（如会话历史、状态等）
        :return: Agent 响应文本
        """
        pass
