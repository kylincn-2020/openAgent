"""Agent 基类和注册系统"""

from typing import Dict, Type, Callable, Any, Optional
from functools import wraps
from abc import ABC, abstractmethod
from .state import AgentState


class AgentRegistry:
    """全局 Agent 注册表,使用装饰器模式

    允许通过装饰器注册 Agent 类,便于扩展和管理。
    添加新 Agent 只需创建类并使用 @AgentRegistry.register() 装饰器。

    Example:
        @AgentRegistry.register('my_agent')
        class MyAgent(Agent):
            async def execute(self) -> AgentState:
                # Agent 逻辑
                return self.state
    """
    _agents: Dict[str, Type['Agent']] = {}

    @classmethod
    def register(cls, name: str) -> Callable:
        """装饰器:注册 Agent 到全局注册表

        Args:
            name: Agent 名称(用于路由和查找)

        Returns:
            装饰器函数

        Example:
            @AgentRegistry.register('ci_generator')
            class CIGeneratorAgent(Agent):
                pass
        """
        def decorator(agent_class: Type['Agent']) -> Type['Agent']:
            cls._agents[name] = agent_class
            return agent_class
        return decorator

    @classmethod
    def get(cls, name: str) -> Optional[Type['Agent']]:
        """获取注册的 Agent 类

        Args:
            name: Agent 名称

        Returns:
            Agent 类,如果不存在则返回 None
        """
        return cls._agents.get(name)

    @classmethod
    def list_agents(cls) -> Dict[str, Type['Agent']]:
        """列出所有已注册的 Agent

        Returns:
            Agent 名称到类的字典
        """
        return cls._agents.copy()


class Agent(ABC):
    """Agent 基类,所有子 Agent 必须继承

    提供统一的接口和工具方法,所有 Agent 都需要实现 execute() 方法。

    Attributes:
        state: Agent 状态字典
        llm: LLM 客户端实例
    """

    def __init__(self, state: AgentState, llm_client: 'LLMClient'):
        """初始化 Agent

        Args:
            state: Agent 状态
            llm_client: LLM 客户端
        """
        self.state = state
        self.llm = llm_client

    @abstractmethod
    async def execute(self) -> AgentState:
        """执行 Agent 逻辑,必须由子类实现

        Returns:
            更新后的 AgentState
        """
        pass

    def update_context(self, key: str, value: Any) -> None:
        """更新会话上下文

        Args:
            key: 上下文键
            value: 上下文值
        """
        self.state['context'][key] = value

    def get_context(self, key: str, default: Any = None) -> Any:
        """获取会话上下文

        Args:
            key: 上下文键
            default: 默认值(如果键不存在)

        Returns:
            上下文值或默认值
        """
        return self.state['context'].get(key, default)

    def add_error(self, error: str) -> None:
        """添加错误信息到状态

        Args:
            error: 错误消息
        """
        self.state['errors'].append(error)

    def add_result(self, agent_name: str, result: Any) -> None:
        """添加子 Agent 执行结果

        Args:
            agent_name: Agent 名称
            result: 执行结果
        """
        self.state['agent_results'].append({
            'agent': agent_name,
            'result': result
        })
