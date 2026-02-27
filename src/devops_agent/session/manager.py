"""会话上下文管理"""

import uuid
from typing import Dict, Any, Optional
from datetime import datetime


class SessionManager:
    """会话上下文管理(内存存储,不持久化)

    管理用户会话的上下文信息,包括项目路径、会话变量、对话历史等。
    会话数据仅在内存中存储,退出时自动清理,不持久化到磁盘。

    Attributes:
        sessions: 所有活跃会话
        current_session_id: 当前活跃会话 ID
    """

    def __init__(self):
        """初始化会话管理器"""
        self.sessions: Dict[str, Dict[str, Any]] = {}
        self.current_session_id: Optional[str] = None

    def create_session(self, project_path: str = ".") -> str:
        """创建新会话

        Args:
            project_path: 项目路径

        Returns:
            会话 ID
        """
        session_id = str(uuid.uuid4())
        self.sessions[session_id] = {
            'id': session_id,
            'created_at': datetime.now(),
            'project_path': project_path,
            'context': {},  # 会话级上下文
            'history': []   # 对话历史(暂不持久化)
        }
        self.current_session_id = session_id
        return session_id

    def get_current_session(self) -> Optional[Dict[str, Any]]:
        """获取当前会话

        Returns:
            当前会话字典,如果不存在则返回 None
        """
        if self.current_session_id:
            return self.sessions.get(self.current_session_id)
        return None

    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """获取指定会话

        Args:
            session_id: 会话 ID

        Returns:
            会话字典,如果不存在则返回 None
        """
        return self.sessions.get(session_id)

    def update_context(self, key: str, value: Any, session_id: Optional[str] = None) -> None:
        """更新会话上下文

        Args:
            key: 上下文键
            value: 上下文值
            session_id: 会话 ID(如果为 None 则使用当前会话)
        """
        sid = session_id or self.current_session_id
        if sid and sid in self.sessions:
            self.sessions[sid]['context'][key] = value

    def get_context(self, key: str, session_id: Optional[str] = None) -> Any:
        """获取会话上下文

        Args:
            key: 上下文键
            session_id: 会话 ID(如果为 None 则使用当前会话)

        Returns:
            上下文值,如果不存在则返回 None
        """
        sid = session_id or self.current_session_id
        if sid and sid in self.sessions:
            return self.sessions[sid]['context'].get(key)
        return None

    def add_to_history(self, user_input: str, response: str, session_id: Optional[str] = None) -> None:
        """添加到对话历史

        Args:
            user_input: 用户输入
            response: 响应
            session_id: 会话 ID(如果为 None 则使用当前会话)
        """
        sid = session_id or self.current_session_id
        if sid and sid in self.sessions:
            self.sessions[sid]['history'].append({
                'timestamp': datetime.now(),
                'user_input': user_input,
                'response': response
            })

    def cleanup_session(self, session_id: Optional[str] = None) -> None:
        """清理会话数据

        Args:
            session_id: 会话 ID(如果为 None 则清理当前会话)
        """
        sid = session_id or self.current_session_id
        if sid and sid in self.sessions:
            del self.sessions[sid]
            if self.current_session_id == sid:
                self.current_session_id = None

    def cleanup_all(self) -> None:
        """清理所有会话数据"""
        self.sessions.clear()
        self.current_session_id = None
