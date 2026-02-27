"""
Client 管理
整合 Client 缓存和意图识别 Agent
"""

import os
from typing import Any, Dict, Optional
from dotenv import load_dotenv
from pydantic import BaseModel

from ..cache.client_cache import get_global_cache
from .intent_agent import IntentRecognitionAgent


# 加载环境变量
load_dotenv()


class AgentClient:
    """
    Agent 客户端
    为每个用户和入口提供独立的 client 实例
    """

    def __init__(
        self,
        user_id: str,
        entry_point: str,
        model_name: Optional[str] = None,
        temperature: float = 0.0,
    ):
        """
        初始化 Client

        Args:
            user_id: 用户ID
            entry_point: 入口标识
            model_name: 使用的模型名称
            temperature: 温度参数
        """
        self.user_id = user_id
        self.entry_point = entry_point
        self.model_name = model_name or os.getenv("DEFAULT_MODEL", "gpt-4o-mini")
        self.temperature = temperature

        # 初始化意图识别 Agent
        self.intent_agent = IntentRecognitionAgent(
            model_name=self.model_name, temperature=self.temperature
        )

    async def process(
        self, user_input: str, input_data: Any = None, context: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        处理用户请求

        Args:
            user_input: 用户输入
            input_data: 传递给 Agent 的输入数据（默认为 user_input）
            context: 上下文信息

        Returns:
            处理结果
        """
        # 如果没有指定 input_data，使用 user_input
        if input_data is None:
            input_data = user_input

        # 意图识别
        intent_result = await self.intent_agent.recognize_intent(user_input, context)

        # 执行 Agent
        execution_results = await self.intent_agent.execute_agents(
            intent_result, input_data, context
        )

        return execution_results


class ClientManager:
    """
    Client 管理器
    管理 Client 的创建和缓存
    """

    def __init__(self):
        """初始化 Client 管理器"""
        self.cache = get_global_cache()

    def get_client(
        self,
        user_id: str,
        entry_point: str,
        model_name: Optional[str] = None,
        temperature: float = 0.0,
    ) -> AgentClient:
        """
        获取或创建 Client

        Args:
            user_id: 用户ID
            entry_point: 入口标识
            model_name: 使用的模型名称
            temperature: 温度参数

        Returns:
            AgentClient 实例
        """
        # 尝试从缓存获取
        client = self.cache.get(user_id, entry_point)

        if client is None:
            # 创建新的 Client
            client = AgentClient(
                user_id=user_id,
                entry_point=entry_point,
                model_name=model_name,
                temperature=temperature,
            )
            # 存入缓存
            self.cache.set(user_id, entry_point, client)

        return client

    def remove_client(self, user_id: str, entry_point: str) -> bool:
        """
        移除指定的 Client

        Args:
            user_id: 用户ID
            entry_point: 入口标识

        Returns:
            是否成功移除
        """
        return self.cache.delete(user_id, entry_point)

    def clear_expired_clients(self) -> int:
        """
        清理过期的 Client

        Returns:
            清理的 Client 数量
        """
        return self.cache.clear_expired()

    def get_stats(self) -> Dict[str, Any]:
        """
        获取统计信息

        Returns:
            统计信息字典
        """
        return self.cache.stats()


# 全局 Client 管理器实例
_global_client_manager: Optional[ClientManager] = None


def get_client_manager() -> ClientManager:
    """
    获取全局 Client 管理器实例（单例模式）

    Returns:
        ClientManager 实例
    """
    global _global_client_manager

    if _global_client_manager is None:
        _global_client_manager = ClientManager()

    return _global_client_manager
