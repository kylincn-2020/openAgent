"""会话清理钩子

使用 atexit 钩子在程序退出时自动清理会话数据。
"""

import atexit
from typing import Callable, List, Optional
from .manager import SessionManager


_cleanup_hooks: List[Callable] = []
_session_manager: Optional[SessionManager] = None


def set_session_manager(manager: SessionManager) -> None:
    """设置全局 SessionManager

    Args:
        manager: 会话管理器实例
    """
    global _session_manager
    _session_manager = manager


def register_cleanup_hook(hook: Callable) -> None:
    """注册清理钩子

    Args:
        hook: 清理函数(无参数,无返回值)
    """
    _cleanup_hooks.append(hook)


def cleanup_session() -> None:
    """清理会话(退出时自动调用)

    由 atexit 自动调用,清理所有会话数据并执行注册的清理钩子。
    """
    global _session_manager
    if _session_manager:
        _session_manager.cleanup_all()

    # 执行所有注册的钩子
    for hook in _cleanup_hooks:
        try:
            hook()
        except Exception as e:
            print(f"Cleanup hook error: {e}")


def register_atexit_handler() -> None:
    """注册 atexit 处理器

    在模块导入时自动注册,确保程序退出时清理会话数据。
    """
    atexit.register(cleanup_session)


# 自动注册
register_atexit_handler()
