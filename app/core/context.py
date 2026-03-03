"""
上下文工具函数
用于构建会话键和管理请求上下文
"""
from dataclasses import dataclass
from app.core.models import InboundMessage


def build_conversation_key(msg: InboundMessage) -> str:
    """
    构建会话键
    格式：tenant_id:channel:user_id:session_id
    用于在 Redis 中唯一标识一个会话
    """
    return f"{msg.tenant_id}:{msg.channel}:{msg.user_id}:{msg.session_id}"


@dataclass
class RequestContext:
    """
    请求上下文
    包含请求 ID 和会话键
    """
    request_id: str
    conversation_key: str
