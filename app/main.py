"""
FastAPI 应用入口
提供 HTTP API 接口
"""
import uuid
from fastapi import FastAPI, HTTPException
from dotenv import load_dotenv

from app.core.models import InboundMessage, ChatResponse
from app.core.context import build_conversation_key
from app.memory.session_store import SessionStore
from app.router.graph import build_router_graph

# 加载环境变量
load_dotenv()

# 创建 FastAPI 应用
app = FastAPI(title="DevAgent MVP")

# 初始化组件
session_store = SessionStore()
router_graph = build_router_graph()


@app.get("/healthz")
def healthz():
    """
    健康检查接口
    用于 Kubernetes 或其他监控系统的健康检查
    """
    return {"ok": True}


@app.post("/v1/chat", response_model=ChatResponse)
def chat(req: InboundMessage):
    """
    聊天接口
    处理用户请求，通过 Agent 路由系统返回响应

    流程：
    1. 生成请求 ID
    2. 构建会话键
    3. 读取会话历史
    4. 执行路由图
    5. 持久化历史记录
    6. 返回响应
    """
    try:
        # 生成或使用现有请求 ID
        request_id = req.request_id or str(uuid.uuid4())

        # 构建会话键（用于会话隔离）
        conversation_key = build_conversation_key(req)

        # 读取会话历史
        history = session_store.get_history(conversation_key)

        # 执行路由图
        state = {"msg": req, "history": history}
        result = router_graph.invoke(state)

        # 提取结果
        answer = result.get("answer", "")
        route = result.get(
            "route",
            {"intent": "unknown", "selected_agent": "DocAgent", "confidence": 0.0}
        )

        # 持久化历史记录
        session_store.append_history(conversation_key, "user", req.text)
        session_store.append_history(conversation_key, "assistant", answer)
        session_store.set_state(
            conversation_key,
            {"last_route": route, "request_id": request_id}
        )

        # 返回响应
        return ChatResponse(
            request_id=request_id,
            conversation_key=conversation_key,
            route={
                "intent": route.get("intent"),
                "agent": route.get("selected_agent"),
                "confidence": route.get("confidence"),
                "need_clarification": route.get("need_clarification", False),
            },
            answer=answer
        )

    except Exception as e:
        # 错误处理
        raise HTTPException(status_code=500, detail=str(e))
