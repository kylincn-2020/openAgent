"""
装饰器注册系统 - 自动发现和注册所有子 agent
"""

from typing import Dict, Type, List, Optional
from dataclasses import dataclass, field
from loguru import logger
import inspect


@dataclass
class AgentMetadata:
    """Agent 元数据"""

    name: str  # agent 唯一标识
    description: str  # agent 描述，用于意图识别
    category: str  # 分类，如 "coding", "writing", "analysis"
    keywords: List[str] = field(default_factory=list)  # 关键词，用于快速匹配
    cls: Type = None  # agent 类

    def to_intent_prompt(self) -> str:
        """生成用于意图识别的提示文本"""
        return f"- {self.name}: {self.description} (关键词：{', '.join(self.keywords)})"


class AgentRegistry:
    """
    Agent 注册中心 - 单例模式

    使用装饰器自动注册所有子 agent，支持：
    - 自动发现通过装饰器标记的 agent 类
    - 按名称、分类、关键词查找 agent
    - 生成意图识别所需的 agent 列表
    """

    _instance: Optional["AgentRegistry"] = None
    _agents: Dict[str, AgentMetadata]
    _categories: Dict[str, List[str]]

    def __new__(cls) -> "AgentRegistry":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._agents = {}
            cls._instance._categories = {}
        return cls._instance

    def register(
        self,
        name: str,
        description: str,
        category: str,
        keywords: Optional[List[str]] = None,
    ):
        """
        装饰器：注册一个 agent 类

        Args:
            name: agent 唯一标识
            description: agent 描述，用于意图识别
            category: 分类
            keywords: 关键词列表，用于快速匹配

        Returns:
            装饰器函数

        Example:
            @registry.register(
                name="coding_assistant",
                description="编程助手，帮助编写、调试、解释代码",
                category="coding",
                keywords=["代码", "编程", "debug", "python", "函数"]
            )
            class CodingAgent(BaseAgent):
                ...
        """

        def decorator(cls: Type) -> Type:
            # 创建元数据
            metadata = AgentMetadata(
                name=name,
                description=description,
                category=category,
                keywords=keywords or [],
                cls=cls,
            )

            # 注册到全局注册表
            self._agents[name] = metadata

            # 注册到分类索引
            if category not in self._categories:
                self._categories[category] = []
            self._categories[category].append(name)

            # 为类添加元数据属性
            cls.agent_metadata = metadata

            logger.info(f"Agent 已注册：{name} (分类：{category})")
            return cls

        return decorator

    def get_agent(self, name: str) -> Optional[AgentMetadata]:
        """根据名称获取 agent 元数据"""
        return self._agents.get(name)

    def get_agent_class(self, name: str) -> Optional[Type]:
        """根据名称获取 agent 类"""
        metadata = self._agents.get(name)
        return metadata.cls if metadata else None

    def get_all_agents(self) -> Dict[str, AgentMetadata]:
        """获取所有已注册的 agent"""
        return self._agents.copy()

    def get_agents_by_category(self, category: str) -> List[AgentMetadata]:
        """根据分类获取 agents"""
        names = self._categories.get(category, [])
        return [self._agents[name] for name in names if name in self._agents]

    def get_categories(self) -> List[str]:
        """获取所有分类"""
        return list(self._categories.keys())

    def get_intent_prompt(self) -> str:
        """
        生成用于意图识别的提示文本

        Returns:
            包含所有 agent 描述的提示文本
        """
        lines = ["可用的专业助手：", ""]
        for metadata in self._agents.values():
            lines.append(f"  {metadata.to_intent_prompt()}")
        return "\n".join(lines)

    def find_best_match(self, query: str) -> Optional[str]:
        """
        基于关键词快速匹配最相关的 agent

        Args:
            query: 用户输入

        Returns:
            最佳匹配的 agent 名称，如果没有匹配则返回 None
        """
        query_lower = query.lower()
        scores: Dict[str, int] = {}

        for name, metadata in self._agents.items():
            score = 0
            # 检查关键词匹配
            for keyword in metadata.keywords:
                if keyword.lower() in query_lower:
                    score += 1
            # 检查分类匹配
            if metadata.category.lower() in query_lower:
                score += 2
            # 检查名称匹配
            if metadata.name.lower() in query_lower:
                score += 3

            if score > 0:
                scores[name] = score

        if not scores:
            return None

        return max(scores, key=scores.get)


# 全局注册实例
registry = AgentRegistry()
