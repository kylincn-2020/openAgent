"""
会话管理器 - 管理用户会话，30 分钟无活动自动释放
"""

import asyncio
from typing import Dict, Optional, Any, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from loguru import logger
from contextlib import asynccontextmanager
import uuid

from langgraph.graph import StateGraph
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage


@dataclass
class Session:
    """用户会话"""

    session_id: str
    user_id: str
    created_at: datetime = field(default_factory=datetime.now)
    last_active_at: datetime = field(default_factory=datetime.now)
    message_history: list = field(default_factory=list)
    agent_graph: Optional[StateGraph] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def update_activity(self):
        """更新活动时间"""
        self.last_active_at = datetime.now()

    def is_expired(self, timeout_minutes: int) -> bool:
        """检查是否已过期"""
        timeout = timedelta(minutes=timeout_minutes)
        return datetime.now() - self.last_active_at > timeout

    def add_message(self, role: str, content: str):
        """添加消息到历史记录"""
        if role == "user":
            self.message_history.append(HumanMessage(content=content))
        elif role == "assistant":
            self.message_history.append(AIMessage(content=content))
        self.update_activity()

    def get_recent_messages(self, limit: int = 10) -> list:
        """获取最近的对话历史"""
        return self.message_history[-limit:]

    def clear_history(self):
        """清除对话历史"""
        self.message_history.clear()


class SessionManager:
    """
    会话管理器

    功能：
    - 为用户创建/获取会话
    - 自动清理过期会话（默认 30 分钟）
    - 支持按用户 ID 索引
    """

    def __init__(self, timeout_minutes: int = 30):
        """
        初始化会话管理器

        Args:
            timeout_minutes: 会话超时时间（分钟）
        """
        self.timeout_minutes = timeout_minutes
        self._sessions: Dict[str, Session] = {}  # session_id -> Session
        self._user_sessions: Dict[str, str] = {}  # user_id -> session_id
        self._cleanup_task: Optional[asyncio.Task] = None
        self._running = False

        logger.info(f"SessionManager 已初始化，超时时间：{timeout_minutes}分钟")

    async def start_cleanup_loop(self, check_interval: int = 60):
        """启动定期清理任务"""
        self._running = True
        self._cleanup_task = asyncio.create_task(self._cleanup_loop(check_interval))
        logger.info("会话清理任务已启动")

    async def stop_cleanup_loop(self):
        """停止定期清理任务"""
        self._running = False
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
        logger.info("会话清理任务已停止")

    async def _cleanup_loop(self, check_interval: int):
        """定期清理过期会话"""
        while self._running:
            await asyncio.sleep(check_interval)
            await self._cleanup_expired_sessions()

    async def _cleanup_expired_sessions(self):
        """清理所有过期会话"""
        expired_ids = []

        for session_id, session in self._sessions.items():
            if session.is_expired(self.timeout_minutes):
                expired_ids.append(session_id)

        for session_id in expired_ids:
            await self._remove_session(session_id)

        if expired_ids:
            logger.info(f"已清理 {len(expired_ids)} 个过期会话")

    async def _remove_session(self, session_id: str):
        """移除会话"""
        if session_id in self._sessions:
            session = self._sessions[session_id]
            # 从用户索引中移除
            if session.user_id in self._user_sessions:
                del self._user_sessions[session.user_id]
            # 移除会话
            del self._sessions[session_id]
            logger.info(f"会话已移除：{session_id} (用户：{session.user_id})")

    def get_or_create_session(self, user_id: str) -> Session:
        """
        获取或创建用户会话

        Args:
            user_id: 用户 ID

        Returns:
            Session 对象
        """
        # 检查用户是否已有会话
        if user_id in self._user_sessions:
            session_id = self._user_sessions[user_id]
            if session_id in self._sessions:
                session = self._sessions[session_id]
                # 检查是否过期
                if not session.is_expired(self.timeout_minutes):
                    session.update_activity()
                    logger.debug(f"会话已复用：{session_id}")
                    return session
                else:
                    # 会话已过期，清理
                    logger.debug(f"会话已过期，将创建新会话：{session_id}")
                    asyncio.create_task(self._remove_session(session_id))

        # 创建新会话
        session_id = str(uuid.uuid4())
        session = Session(session_id=session_id, user_id=user_id)

        self._sessions[session_id] = session
        self._user_sessions[user_id] = session_id

        logger.info(f"新会话已创建：{session_id} (用户：{user_id})")
        return session

    def get_session(self, session_id: str) -> Optional[Session]:
        """根据 session_id 获取会话"""
        session = self._sessions.get(session_id)
        if session and not session.is_expired(self.timeout_minutes):
            session.update_activity()
            return session
        return None

    def get_session_by_user(self, user_id: str) -> Optional[Session]:
        """根据 user_id 获取会话"""
        if user_id in self._user_sessions:
            session_id = self._user_sessions[user_id]
            return self.get_session(session_id)
        return None

    async def delete_session(self, session_id: str) -> bool:
        """
        删除会话

        Args:
            session_id: 会话 ID

        Returns:
            是否删除成功
        """
        if session_id in self._sessions:
            await self._remove_session(session_id)
            return True
        return False

    def get_stats(self) -> Dict[str, Any]:
        """获取会话统计信息"""
        active_count = sum(
            1 for s in self._sessions.values() if not s.is_expired(self.timeout_minutes)
        )
        return {
            "total_sessions": len(self._sessions),
            "active_sessions": active_count,
            "unique_users": len(self._user_sessions),
            "timeout_minutes": self.timeout_minutes,
        }


# 全局会话管理器实例
session_manager = SessionManager()
