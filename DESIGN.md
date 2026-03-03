太好了。下面我给你一套 可运行的 MVP 代码实现（LangChain 1.0 + LangGraph + FastAPI + Redis，会话隔离 + 意图识别 + Agent路由）。

我会按文件给出，你可以直接复制。

0) 安装依赖
pyproject.toml（简化版）

<TOML>
[project]
name = "devagent-mvp"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = [
  "fastapi>=0.115.0",
  "uvicorn>=0.30.0",
  "pydantic>=2.7.0",
  "langchain>=1.0.0",
  "langgraph>=0.2.0",
  "langchain-openai>=0.2.0",
  "redis>=5.0.0",
  "python-dotenv>=1.0.1"
]
.env

<ENV>
OPENAI_API_KEY=your_key
OPENAI_MODEL=gpt-4o-mini
REDIS_URL=redis://localhost:6379/0
1) 目录结构
<BASH>
app/
  main.py
  core/
    models.py
    context.py
    registry.py
  infra/
    llm.py
  memory/
    session_store.py
  agents/
    base.py
    code_agent.py
    doc_agent.py
    task_agent.py
  router/
    prompts.py
    policy.py
    nodes.py
    graph.py
2) 核心模型
app/core/models.py
<PYTHON>
from __future__ import annotations
from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, Field
IntentType = Literal["code_gen", "doc_qa", "task_query", "unknown"]
class InboundMessage(BaseModel):
    tenant_id: str
    channel: str
    user_id: str
    session_id: str
    text: str
    request_id: Optional[str] = None
    message_id: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
class IntentResult(BaseModel):
    intent: IntentType
    confidence: float = Field(ge=0.0, le=1.0)
    candidate_agents: List[str] = Field(default_factory=list)
    slots: Dict[str, Any] = Field(default_factory=dict)
    need_clarification: bool = False
    clarification_question: str = ""
class ChatResponse(BaseModel):
    request_id: str
    conversation_key: str
    route: Dict[str, Any]
    answer: str
class RouteDecision(BaseModel):
    selected_agent: str
    intent: IntentType
    confidence: float
    is_fallback: bool = False
    need_clarification: bool = False
    clarification_question: str = ""
3) 上下文与会话key
app/core/context.py
<PYTHON>
from dataclasses import dataclass
from app.core.models import InboundMessage
def build_conversation_key(msg: InboundMessage) -> str:
    return f"{msg.tenant_id}:{msg.channel}:{msg.user_id}:{msg.session_id}"
@dataclass
class RequestContext:
    request_id: str
    conversation_key: str
4) LLM 初始化
app/infra/llm.py
<PYTHON>
import os
from langchain_openai import ChatOpenAI
def get_llm():
    model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    return ChatOpenAI(model=model, temperature=0)
5) Session Store（Redis，会话隔离）
app/memory/session_store.py
<PYTHON>
import json
import os
from typing import Any, Dict, List
import redis
class SessionStore:
    def __init__(self):
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        self.client = redis.Redis.from_url(redis_url, decode_responses=True)
    def _history_key(self, conversation_key: str) -> str:
        return f"sess:{conversation_key}:history"
    def _state_key(self, conversation_key: str) -> str:
        return f"sess:{conversation_key}:state"
    def append_history(self, conversation_key: str, role: str, content: str, ttl_sec: int = 7 * 24 * 3600):
        key = self._history_key(conversation_key)
        self.client.rpush(key, json.dumps({"role": role, "content": content}))
        self.client.ltrim(key, -20, -1)
        self.client.expire(key, ttl_sec)
    def get_history(self, conversation_key: str) -> List[Dict[str, Any]]:
        key = self._history_key(conversation_key)
        items = self.client.lrange(key, 0, -1)
        return [json.loads(x) for x in items]
    def set_state(self, conversation_key: str, state: Dict[str, Any], ttl_sec: int = 7 * 24 * 3600):
        key = self._state_key(conversation_key)
        self.client.set(key, json.dumps(state), ex=ttl_sec)
    def get_state(self, conversation_key: str) -> Dict[str, Any]:
        key = self._state_key(conversation_key)
        raw = self.client.get(key)
        return json.loads(raw) if raw else {}
6) Agent 抽象与实现
app/agents/base.py
<PYTHON>
from abc import ABC, abstractmethod
from typing import Dict, Any
class BaseAgent(ABC):
    agent_id: str
    @abstractmethod
    def invoke(self, text: str, context: Dict[str, Any]) -> str:
        ...
app/agents/code_agent.py
<PYTHON>
from app.agents.base import BaseAgent
class CodeAgent(BaseAgent):
    agent_id = "CodeAgent"
    def invoke(self, text: str, context: dict) -> str:
        return f"[CodeAgent] 已收到代码请求：{text}\n示例建议：可先定义接口、加单元测试、再补文档。"
app/agents/doc_agent.py
<PYTHON>
from app.agents.base import BaseAgent
class DocAgent(BaseAgent):
    agent_id = "DocAgent"
    def invoke(self, text: str, context: dict) -> str:
        return f"[DocAgent] 文档问答结果（MVP示例）：你问的是：{text}"
app/agents/task_agent.py
<PYTHON>
from app.agents.base import BaseAgent
class TaskAgent(BaseAgent):
    agent_id = "TaskAgent"
    def invoke(self, text: str, context: dict) -> str:
        return f"[TaskAgent] 任务查询（MVP mock）：未发现阻塞任务，建议检查Jira过滤条件。"
7) Agent 注册中心
app/core/registry.py
<PYTHON>
from app.agents.code_agent import CodeAgent
from app.agents.doc_agent import DocAgent
from app.agents.task_agent import TaskAgent
class AgentRegistry:
    def __init__(self):
        self._agents = {
            "CodeAgent": CodeAgent(),
            "DocAgent": DocAgent(),
            "TaskAgent": TaskAgent(),
        }
    def get(self, agent_id: str):
        if agent_id not in self._agents:
            raise ValueError(f"Agent not found: {agent_id}")
        return self._agents[agent_id]
8) Prompt 与 Policy
app/router/prompts.py
<PYTHON>
INTENT_CLASSIFIER_SYSTEM = """
你是一个意图分类器。只做分类，不做回答。
可选intent:
- code_gen: 代码生成、重构、调试、接口实现
- doc_qa: 文档解释、知识问答、报错说明
- task_query: 任务进度、工单、项目状态查询
- unknown: 无法判断
输出必须严格遵循结构化schema。
"""
app/router/policy.py
<PYTHON>
from app.core.models import IntentResult, RouteDecision
def select_agent_by_intent(intent: str) -> str:
    mapping = {
        "code_gen": "CodeAgent",
        "doc_qa": "DocAgent",
        "task_query": "TaskAgent",
        "unknown": "DocAgent",  # fallback
    }
    return mapping.get(intent, "DocAgent")
def decide_route(intent_result: IntentResult) -> RouteDecision:
    c = intent_result.confidence
    if c >= 0.75:
        return RouteDecision(
            selected_agent=select_agent_by_intent(intent_result.intent),
            intent=intent_result.intent,
            confidence=c,
            is_fallback=(intent_result.intent == "unknown")
        )
    if 0.5 <= c < 0.75:
        return RouteDecision(
            selected_agent="",
            intent=intent_result.intent,
            confidence=c,
            need_clarification=True,
            clarification_question=intent_result.clarification_question or "你是要代码生成、文档问答，还是任务查询？"
        )
    return RouteDecision(
        selected_agent="DocAgent",
        intent="unknown",
        confidence=c,
        is_fallback=True
    )
9) LangGraph 节点与图
app/router/nodes.py
<PYTHON>
from __future__ import annotations
from typing import Any, Dict, TypedDict
from pydantic import BaseModel, Field
from app.core.models import InboundMessage, IntentResult
from app.router.prompts import INTENT_CLASSIFIER_SYSTEM
from app.router.policy import decide_route
from app.infra.llm import get_llm
from app.core.registry import AgentRegistry
class RouterState(TypedDict, total=False):
    msg: InboundMessage
    history: list
    intent_result: IntentResult
    route: dict
    answer: str
class IntentSchema(BaseModel):
    intent: str = Field(description="code_gen/doc_qa/task_query/unknown")
    confidence: float = Field(ge=0, le=1)
    candidate_agents: list[str] = Field(default_factory=list)
    slots: dict[str, Any] = Field(default_factory=dict)
    need_clarification: bool = False
    clarification_question: str = ""
def preprocess_node(state: RouterState) -> RouterState:
    msg = state["msg"]
    msg.text = msg.text.strip()
    return {"msg": msg}
def rule_route_node(state: RouterState) -> RouterState:
    text = state["msg"].text.lower()
    if text.startswith("/code"):
        ir = IntentResult(intent="code_gen", confidence=0.99, candidate_agents=["CodeAgent"])
        return {"intent_result": ir}
    if text.startswith("/doc"):
        ir = IntentResult(intent="doc_qa", confidence=0.99, candidate_agents=["DocAgent"])
        return {"intent_result": ir}
    if text.startswith("/task"):
        ir = IntentResult(intent="task_query", confidence=0.99, candidate_agents=["TaskAgent"])
        return {"intent_result": ir}
    return {}
def llm_intent_node(state: RouterState) -> RouterState:
    if state.get("intent_result"):  # 规则已命中
        return {}
    llm = get_llm().with_structured_output(IntentSchema)
    msg = state["msg"]
    result: IntentSchema = llm.invoke([
        ("system", INTENT_CLASSIFIER_SYSTEM),
        ("human", f"用户输入: {msg.text}")
    ])
    intent = result.intent if result.intent in {"code_gen", "doc_qa", "task_query", "unknown"} else "unknown"
    ir = IntentResult(
        intent=intent, confidence=result.confidence,
        candidate_agents=result.candidate_agents,
        slots=result.slots,
        need_clarification=result.need_clarification,
        clarification_question=result.clarification_question
    )
    return {"intent_result": ir}
def policy_node(state: RouterState) -> RouterState:
    decision = decide_route(state["intent_result"])
    return {"route": decision.model_dump()}
def invoke_agent_node(state: RouterState) -> RouterState:
    route = state["route"]
    if route.get("need_clarification"):
        return {"answer": route["clarification_question"]}
    registry = AgentRegistry()
    agent = registry.get(route["selected_agent"])
    answer = agent.invoke(state["msg"].text, context={})
    return {"answer": answer}
app/router/graph.py
<PYTHON>
from langgraph.graph import StateGraph, END
from app.router.nodes import (
    RouterState,
    preprocess_node,
    rule_route_node,
    llm_intent_node,
    policy_node,
    invoke_agent_node
)
def build_router_graph():
    g = StateGraph(RouterState)
    g.add_node("preprocess", preprocess_node)
    g.add_node("rule_route", rule_route_node)
    g.add_node("llm_intent", llm_intent_node)
    g.add_node("policy", policy_node)
    g.add_node("invoke_agent", invoke_agent_node)
    g.set_entry_point("preprocess")
    g.add_edge("preprocess", "rule_route")
    g.add_edge("rule_route", "llm_intent")
    g.add_edge("llm_intent", "policy")
    g.add_edge("policy", "invoke_agent")
    g.add_edge("invoke_agent", END)
    return g.compile()
10) FastAPI 入口
app/main.py
<PYTHON>
import uuid
from fastapi import FastAPI, HTTPException
from dotenv import load_dotenv
from app.core.models import InboundMessage, ChatResponse
from app.core.context import build_conversation_key
from app.memory.session_store import SessionStore
from app.router.graph import build_router_graph
load_dotenv()
app = FastAPI(title="DevAgent MVP")
session_store = SessionStore()
router_graph = build_router_graph()
@app.get("/healthz")
def healthz():
    return {"ok": True}
@app.post("/v1/chat", response_model=ChatResponse)
def chat(req: InboundMessage):
    try:
        request_id = req.request_id or str(uuid.uuid4())
        conversation_key = build_conversation_key(req)
        # 读取历史
        history = session_store.get_history(conversation_key)
        # 图执行
        state = {"msg": req, "history": history}
        result = router_graph.invoke(state)
        answer = result.get("answer", "")
        route = result.get("route", {"intent": "unknown", "selected_agent": "DocAgent", "confidence": 0.0})
        # 持久化
        session_store.append_history(conversation_key, "user", req.text)
        session_store.append_history(conversation_key, "assistant", answer)
        session_store.set_state(conversation_key, {"last_route": route, "request_id": request_id})
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
        raise HTTPException(status_code=500, detail=str(e))
11) 启动方式
<BASH>
# 1) 启redis
docker run -d --name redis -p 6379:6379 redis:7
# 2) 启服务
uvicorn app.main:app --reload --port 8000
测试：

<BASH>
curl -X POST "http://127.0.0.1:8000/v1/chat" \
-H "Content-Type: application/json" \
-d '{
  "tenant_id":"t1",
  "channel":"web",
  "user_id":"u1",
  "session_id":"s1",
  "text":"/code 帮我写一个fastapi健康检查接口"
}'
12) 下一步增强（你确认后我再给代码）
流式输出（SSE）
LangGraph checkpointer（替代手写部分状态）
Agent Manifest 动态注册（从yaml加载）
机器人签名验签中间件
路由评测脚本（准确率统计）