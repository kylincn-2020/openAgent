"""
FastAPI 服务层
"""

from fastapi import FastAPI, HTTPException, Header
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from contextlib import asynccontextmanager
import uvicorn

from config import settings
from loguru import logger
from core.session_manager import session_manager
from core.registry import registry
from agents.intent_agent import IntentAgent


class ChatRequest(BaseModel):
    """聊天请求"""

    message: str = Field(..., description="用户消息")
    user_id: Optional[str] = Field(None, description="用户 ID，不传则自动生成")
    session_id: Optional[str] = Field(None, description="会话 ID，不传则创建新会话")


class ChatResponse(BaseModel):
    """聊天响应"""

    response: str
    session_id: str
    agent_used: Optional[str] = None
    message_count: int = 0


class SessionInfo(BaseModel):
    """会话信息"""

    session_id: str
    user_id: str
    created_at: str
    last_active_at: str
    message_count: int


class StatsResponse(BaseModel):
    """统计信息响应"""

    sessions: Dict[str, Any]
    agents: List[str]


# 全局 intent agent 实例
intent_agent: Optional[IntentAgent] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    global intent_agent

    # 启动时初始化
    logger.info("正在初始化多 Agent 系统...")

    # 创建 intent agent
    intent_agent = IntentAgent()

    # 启动会话清理任务
    await session_manager.start_cleanup_loop(settings.SESSION_CHECK_INTERVAL)

    logger.info("多 Agent 系统初始化完成")

    yield

    # 关闭时清理
    logger.info("正在关闭多 Agent 系统...")
    await session_manager.stop_cleanup_loop()
    logger.info("多 Agent 系统已关闭")


app = FastAPI(
    title="Multi-Agent System",
    description="基于 LangGraph 的多 Agent 系统，支持意图识别和自动路由",
    version="1.0.0",
    lifespan=lifespan,
)


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    聊天接口

    - 自动创建/复用用户会话
    - 自动识别意图并路由到合适的子 agent
    - 保持对话历史上下文
    """
    try:
        # 获取或创建会话
        user_id = request.user_id or "anonymous"
        session = session_manager.get_or_create_session(user_id)

        # 添加用户消息到历史
        session.add_message("user", request.message)

        # 使用 intent agent 处理
        global intent_agent
        context = {"messages": session.get_recent_messages(limit=20)}
        response_text = await intent_agent.act(request.message, context)

        # 添加助手响应到历史
        session.add_message("assistant", response_text)

        # 确定使用的 agent
        # 注意：这里简化处理，实际可以从 context 中获取
        agent_used = "intent_router"

        return ChatResponse(
            response=response_text,
            session_id=session.session_id,
            agent_used=agent_used,
            message_count=len(session.message_history),
        )

    except Exception as e:
        logger.error(f"聊天处理失败：{e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/session/{session_id}", response_model=SessionInfo)
async def get_session(session_id: str):
    """获取会话信息"""
    session = session_manager.get_session(session_id)

    if not session:
        raise HTTPException(status_code=404, detail="会话不存在或已过期")

    return SessionInfo(
        session_id=session.session_id,
        user_id=session.user_id,
        created_at=session.created_at.isoformat(),
        last_active_at=session.last_active_at.isoformat(),
        message_count=len(session.message_history),
    )


@app.delete("/session/{session_id}")
async def delete_session(session_id: str):
    """删除会话"""
    success = await session_manager.delete_session(session_id)

    if not success:
        raise HTTPException(status_code=404, detail="会话不存在")

    return {"message": "会话已删除"}


@app.get("/sessions", response_model=StatsResponse)
async def get_sessions():
    """获取所有会话统计和注册的 agent 列表"""
    stats = session_manager.get_stats()
    agents = list(registry.get_all_agents().keys())

    return StatsResponse(sessions=stats, agents=agents)


@app.get("/agents")
async def list_agents():
    """获取所有已注册的 agent 列表"""
    agents = []
    for name, metadata in registry.get_all_agents().items():
        agents.append(
            {
                "name": name,
                "description": metadata.description,
                "category": metadata.category,
                "keywords": metadata.keywords,
            }
        )

    return {"agents": agents}


@app.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "healthy", "sessions": session_manager.get_stats()}


if __name__ == "__main__":
    uvicorn.run(
        "api.server:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=True,
    )
