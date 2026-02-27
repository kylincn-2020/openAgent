"""
子 Agent 注册装饰器
提供快速注册子 Agent 的装饰器
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional, Type


@dataclass
class AgentMetadata:
    """Agent 元数据"""

    name: str  # Agent 名称（唯一标识）
    description: str  # Agent 描述
    intent_keywords: List[str]  # 意图关键词列表
    priority: int = 0  # 优先级（数字越大优先级越高）
    parallel_allowed: bool = True  # 是否允许并行执行
    category: Optional[str] = None  # Agent 类别


class BaseSubAgent(ABC):
    """
    子 Agent 基类
    所有子 Agent 都需要继承此类并实现 execute 方法
    """

    def __init__(self):
        """初始化子 Agent"""
        self.metadata: Optional[AgentMetadata] = None

    @abstractmethod
    async def execute(self, input_data: Any, context: Optional[Dict] = None) -> Any:
        """
        执行 Agent 任务

        Args:
            input_data: 输入数据
            context: 上下文信息

        Returns:
            执行结果
        """
        pass

    @classmethod
    def get_metadata(cls) -> AgentMetadata:
        """
        获取 Agent 元数据

        Returns:
            AgentMetadata 实例
        """
        raise NotImplementedError("Subclasses must implement get_metadata method")


class AgentRegistry:
    """
    Agent 注册表
    管理所有已注册的子 Agent
    """

    def __init__(self):
        """初始化注册表"""
        self._agents: Dict[str, Type[BaseSubAgent]] = {}
        self._metadata: Dict[str, AgentMetadata] = {}

    def register(self, metadata: AgentMetadata) -> Callable:
        """
        注册 Agent 的装饰器

        Args:
            metadata: Agent 元数据

        Returns:
            装饰器函数

        Example:
            @registry.register(AgentMetadata(
                name="weather_agent",
                description="查询天气信息",
                intent_keywords=["天气", "气温"],
                priority=10
            ))
            class WeatherAgent(BaseSubAgent):
                async def execute(self, input_data, context):
                    # 实现逻辑
                    pass
        """

        def decorator(agent_class: Type[BaseSubAgent]) -> Type[BaseSubAgent]:
            # 验证 agent_class 是否继承自 BaseSubAgent
            if not issubclass(agent_class, BaseSubAgent):
                raise TypeError(
                    f"{agent_class.__name__} must inherit from BaseSubAgent"
                )

            # 检查名称是否已注册
            if metadata.name in self._agents:
                raise ValueError(f"Agent '{metadata.name}' is already registered")

            # 注册 Agent
            self._agents[metadata.name] = agent_class
            self._metadata[metadata.name] = metadata

            # 将元数据附加到类上
            agent_class._metadata = metadata

            return agent_class

        return decorator

    def get_agent(self, name: str) -> Optional[Type[BaseSubAgent]]:
        """
        获取已注册的 Agent 类

        Args:
            name: Agent 名称

        Returns:
            Agent 类，如果未注册则返回 None
        """
        return self._agents.get(name)

    def get_metadata(self, name: str) -> Optional[AgentMetadata]:
        """
        获取 Agent 元数据

        Args:
            name: Agent 名称

        Returns:
            Agent 元数据，如果未注册则返回 None
        """
        return self._metadata.get(name)

    def get_all_metadata(self) -> List[AgentMetadata]:
        """
        获取所有已注册 Agent 的元数据

        Returns:
            Agent 元数据列表，按优先级降序排列
        """
        return sorted(self._metadata.values(), key=lambda x: x.priority, reverse=True)

    def get_all_agents(self) -> Dict[str, Type[BaseSubAgent]]:
        """
        获取所有已注册的 Agent

        Returns:
            字典：{name: agent_class}
        """
        return self._agents.copy()

    def find_by_keywords(self, keywords: List[str]) -> List[AgentMetadata]:
        """
        根据关键词查找匹配的 Agent

        Args:
            keywords: 关键词列表

        Returns:
            匹配的 Agent 元数据列表，按优先级降序排列
        """
        matched = []

        for metadata in self._metadata.values():
            # 检查是否有任何关键词匹配
            for keyword in keywords:
                if any(
                    keyword in kw or kw in keyword for kw in metadata.intent_keywords
                ):
                    matched.append(metadata)
                    break

        return sorted(matched, key=lambda x: x.priority, reverse=True)

    def find_by_category(self, category: str) -> List[AgentMetadata]:
        """
        根据类别查找 Agent

        Args:
            category: Agent 类别

        Returns:
            匹配的 Agent 元数据列表
        """
        return [
            metadata
            for metadata in self._metadata.values()
            if metadata.category == category
        ]

    def unregister(self, name: str) -> bool:
        """
        注销 Agent

        Args:
            name: Agent 名称

        Returns:
            是否成功注销
        """
        if name in self._agents:
            del self._agents[name]
            del self._metadata[name]
            return True
        return False

    def clear(self) -> None:
        """清空所有注册的 Agent"""
        self._agents.clear()
        self._metadata.clear()

    def count(self) -> int:
        """获取已注册 Agent 的数量"""
        return len(self._agents)


# 全局注册表实例
_global_registry: Optional[AgentRegistry] = None


def get_global_registry() -> AgentRegistry:
    """
    获取全局注册表实例（单例模式）

    Returns:
        AgentRegistry 实例
    """
    global _global_registry

    if _global_registry is None:
        _global_registry = AgentRegistry()

    return _global_registry


def register_agent(metadata: AgentMetadata) -> Callable:
    """
    便捷的 Agent 注册装饰器

    Args:
        metadata: Agent 元数据

    Returns:
        装饰器函数

    Example:
        @register_agent(AgentMetadata(
            name="weather_agent",
            description="查询天气信息",
            intent_keywords=["天气", "气温"],
            priority=10
        ))
        class WeatherAgent(BaseSubAgent):
            async def execute(self, input_data, context):
                return {"weather": "晴"}
    """
    # 获取全局注册表
    registry = get_global_registry()
    return registry.register(metadata)
