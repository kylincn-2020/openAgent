"""
会话存储（基于内存）
使用字典实现会话隔离，每个会话的历史和状态独立存储

注意：内存存储在进程重启后会丢失，适用于开发和测试环境
"""
import threading
from collections import defaultdict
from typing import Any, Dict, List


class SessionStore:
    """
    内存会话存储
    使用线程锁保证并发安全
    负责管理会话历史和状态
    """

    def __init__(self):
        """初始化内存存储"""
        self._lock = threading.Lock()  # 线程锁，保证并发安全
        # 会话历史：{conversation_key: [{"role": "...", "content": "..."}, ...]}
        self._history: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        # 会话状态：{conversation_key: {...}}
        self._state: Dict[str, Dict[str, Any]] = {}

    def append_history(
        self,
        conversation_key: str,
        role: str,
        content: str,
        max_history: int = 20
    ):
        """
        添加历史记录到会话
        :param conversation_key: 会话键
        :param role: 角色 (user/assistant)
        :param content: 消息内容
        :param max_history: 最大保留历史条数，默认 20 条
        """
        with self._lock:
            key = self._history_key(conversation_key)
            # 追加消息
            self._history[key].append({"role": role, "content": content})
            # 只保留最近 max_history 条消息
            if len(self._history[key]) > max_history:
                self._history[key] = self._history[key][-max_history:]

    def get_history(self, conversation_key: str) -> List[Dict[str, Any]]:
        """
        获取会话历史
        :param conversation_key: 会话键
        :return: 历史记录列表
        """
        with self._lock:
            key = self._history_key(conversation_key)
            return list(self._history.get(key, []))

    def set_state(
        self,
        conversation_key: str,
        state: Dict[str, Any]
    ):
        """
        设置会话状态
        :param conversation_key: 会话键
        :param state: 状态字典
        """
        with self._lock:
            key = self._state_key(conversation_key)
            self._state[key] = state

    def get_state(self, conversation_key: str) -> Dict[str, Any]:
        """
        获取会话状态
        :param conversation_key: 会话键
        :return: 状态字典
        """
        with self._lock:
            key = self._state_key(conversation_key)
            return self._state.get(key, {})

    def _history_key(self, conversation_key: str) -> str:
        """获取历史存储的键（内存版本不需要实际键名，保持接口一致）"""
        return f"sess:{conversation_key}:history"

    def _state_key(self, conversation_key: str) -> str:
        """获取状态存储的键（内存版本不需要实际键名，保持接口一致）"""
        return f"sess:{conversation_key}:state"

    def clear(self, conversation_key: str = None):
        """
        清除会话数据
        :param conversation_key: 可选，指定清除某个会话；不传则清除所有
        """
        with self._lock:
            if conversation_key:
                hist_key = self._history_key(conversation_key)
                state_key = self._state_key(conversation_key)
                self._history.pop(hist_key, None)
                self._state.pop(state_key, None)
            else:
                # 清除所有会话数据
                self._history.clear()
                self._state.clear()
