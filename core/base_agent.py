"""
子 Agent 基类
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, List
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from loguru import logger


class BaseAgent(ABC):
    """
    所有子 agent 的基类

    每个子 agent 必须：
    1. 使用 @registry.register 装饰器注册
    2. 实现 act 方法处理用户输入
    3. 可选实现 get_system_prompt 方法定制系统提示
    """

    # 类变量，由装饰器设置
    agent_metadata = None

    def __init__(self, llm: Optional[BaseChatModel] = None):
        """
        初始化 agent

        Args:
            llm: 语言模型，如果为 None 则使用默认模型
        """
        self.llm = llm
        self._state: Dict[str, Any] = {}
        logger.debug(f"Agent 已初始化：{self.name}")

    @property
    def name(self) -> str:
        """获取 agent 名称"""
        return (
            self.agent_metadata.name if self.agent_metadata else self.__class__.__name__
        )

    @property
    def description(self) -> str:
        """获取 agent 描述"""
        return self.agent_metadata.description if self.agent_metadata else ""

    def get_system_prompt(self) -> str:
        """
        获取系统提示

        子类可以重写此方法定制系统提示
        """
        return f"""你是{self.name}助手。
{self.description}

请专业、友好地回答用户的问题。
"""

    @abstractmethod
    async def act(
        self, user_input: str, context: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        处理用户输入并生成响应

        Args:
            user_input: 用户输入
            context: 上下文信息（可选）

        Returns:
            agent 的响应文本
        """
        pass

    async def _invoke_llm(
        self, messages: List, system_prompt: Optional[str] = None
    ) -> str:
        """
        调用 LLM 生成响应

        Args:
            messages: 消息列表
            system_prompt: 系统提示（可选）

        Returns:
            LLM 生成的响应
        """
        if self.llm is None:
            from config import settings
            from langchain_openai import ChatOpenAI

            self.llm = ChatOpenAI(model=settings.DEFAULT_MODEL)

        # 构建消息
        full_messages = []
        if system_prompt:
            full_messages.append(SystemMessage(content=system_prompt))
        full_messages.extend(messages)

        # 调用 LLM
        response = await self.llm.ainvoke(full_messages)
        return response.content

    def update_state(self, key: str, value: Any):
        """更新内部状态"""
        self._state[key] = value

    def get_state(self, key: Optional[str] = None) -> Any:
        """获取内部状态"""
        if key:
            return self._state.get(key)
        return self._state.copy()

    def clear_state(self):
        """清除内部状态"""
        self._state.clear()
