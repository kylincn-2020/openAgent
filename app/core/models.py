"""
核心数据模型定义
包含请求、响应、意图等结构化模型
"""
from __future__ import annotations
from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, Field

# 意图类型：code_gen(代码生成), doc_qa(文档问答), task_query(任务查询), unknown(未知)
IntentType = Literal["code_gen", "doc_qa", "task_query", "unknown"]


class InboundMessage(BaseModel):
    """
    入站消息模型
    表示从客户端接收到的请求消息
    """
    tenant_id: str           # 租户 ID，用于多租户隔离
    channel: str             # 渠道来源：web/slack/etc
    user_id: str             # 用户 ID
    session_id: str          # 会话 ID，与 tenant_id+channel+user_id 共同确定唯一会话
    text: str                # 用户输入文本
    request_id: Optional[str] = None    # 请求 ID，用于追踪
    message_id: Optional[str] = None    # 消息 ID
    metadata: Dict[str, Any] = Field(default_factory=dict)  # 额外元数据


class IntentResult(BaseModel):
    """
    意图识别结果
    由意图分类器输出的结构化结果
    """
    intent: IntentType                          # 识别出的意图类型
    confidence: float = Field(ge=0.0, le=1.0)  # 置信度，0-1 之间
    candidate_agents: List[str] = Field(default_factory=list)  # 候选 Agent 列表
    slots: Dict[str, Any] = Field(default_factory=dict)       # 槽位信息，用于参数提取
    need_clarification: bool = False          # 是否需要用户澄清
    clarification_question: str = ""          # 澄清问题


class ChatResponse(BaseModel):
    """
    聊天响应模型
    返回给客户端的最终响应
    """
    request_id: str              # 请求 ID
    conversation_key: str        # 会话键
    route: Dict[str, Any]        # 路由决策信息
    answer: str                  # Agent 回答


class RouteDecision(BaseModel):
    """
    路由决策模型
    决定将请求路由到哪个 Agent
    """
    selected_agent: str          # 选中的 Agent ID
    intent: IntentType           # 意图类型
    confidence: float            # 置信度
    is_fallback: bool = False    # 是否为降级处理
    need_clarification: bool = False  # 是否需要澄清
    clarification_question: str = ""  # 澄清问题
