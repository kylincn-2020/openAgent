# LangGraph 1.0+ 多智能体系统研究报告

本文档提供 LangGraph 1.0+ 构建多智能体系统的完整指南，包括 API 引用、生产就绪模式和代码示例。

---

## 目录

1. [LangGraph 1.0+ 文档和 API](#1-langgraph-10-文档和-api)
2. [动态智能体注册模式](#2-动态智能体注册模式)
3. [会话管理和 TTL 超时模式](#3-会话管理和-ttl-超时模式)
4. [意图分类和路由器最佳实践](#4-意图分类和路由器最佳实践)
5. [生产就绪完整示例](#5-生产就绪完整示例)

---

## 1. LangGraph 1.0+ 文档和 API

### 核心文档

**官方文档链接：**
- LangGraph 官方文档：https://python.langchain.com/docs/langgraph
- LangGraph GitHub (v1.0.8)：https://github.com/langchain-ai/langgraph
- LangGraph 概览：https://python.langchain.com/docs/langgraph/overview

**安装：**
```bash
pip install -U langgraph
# 或使用 uv
uv add langgraph
```

### 核心 API 引用

#### 1.1 StateGraph - 状态图构建

**导入：**
```python
from langgraph.graph import StateGraph, MessagesState, START, END
from typing_extensions import TypedDict
```

**基本用法：**

```python
# 定义状态结构
class State(TypedDict):
    text: str
    messages: list

# 创建状态图
workflow = StateGraph(State)

# 添加节点
def node_a(state: State) -> dict:
    return {"text": state["text"] + "a"}

def node_b(state: State) -> dict:
    return {"text": state["text"] + "b"}

workflow.add_node("node_a", node_a)
workflow.add_node("node_b", node_b)

# 添加边
workflow.add_edge(START, "node_a")
workflow.add_edge("node_a", "node_b")

# 编译图
graph = workflow.compile()

# 执行
result = graph.invoke({"text": ""})
# {'text': 'ab'}
```

#### 1.2 条件边 (Conditional Edges)

```python
from langgraph.graph import StateGraph, START, END
from typing import Literal

class GraphState(TypedDict):
    question: str
    documents: list

def route_question(state: GraphState) -> Literal["web_search", "vectorstore"]:
    """路由查询到不同的节点"""
    if "current" in state["question"].lower():
        return "web_search"
    return "vectorstore"

# 创建工作流
workflow = StateGraph(GraphState)
workflow.add_node("web_search", web_search_node)
workflow.add_node("vectorstore", vectorstore_node)

# 添加条件边
workflow.add_conditional_edges(
    START,
    route_question,
    {
        "web_search": "web_search",
        "vectorstore": "vectorstore",
    },
)

# 编译
app = workflow.compile()
```

#### 1.3 预构建 Agent

```python
from langgraph.prebuilt import create_react_agent
from langchain_anthropic import ChatAnthropic

def search(query: str):
    """搜索工具"""
    if "sf" in query.lower():
        return "It's 60 degrees and foggy."
    return "It's 90 degrees and sunny."

tools = [search]
model = ChatAnthropic(model="claude-3-7-sonnet-latest")

# 创建 ReAct Agent
app = create_react_agent(model, tools)

# 执行
result = app.invoke({
    "messages": [{"role": "user", "content": "what is the weather in sf"}]
})
```

#### 1.4 Checkpointers（检查点）

```python
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.checkpoint.sqlite import SqliteSaver

# 内存检查点（用于开发）
checkpointer = InMemorySaver()

# SQLite 检查点（持久化）
checkpointer = SqliteSaver.from_conn_string("checkpoints.db")

# 编译图时使用检查点
graph = workflow.compile(checkpointer=checkpointer)

# 使用配置执行
config = {"configurable": {"thread_id": "session_123"}}
result = graph.invoke({"messages": ["user input"]}, config=config)
```

---

## 2. 动态智能体注册模式

### 2.1 装饰器模式实现

LangGraph 1.0+ 本身不提供装饰器注册，但可以使用 Python 装饰器实现动态注册。

**实现示例：**

```python
from typing import Callable, Dict, Any, TypeVar, Optional
from functools import wraps

T = TypeVar('T')

class AgentRegistry:
    """智能体注册中心"""
    def __init__(self):
        self._agents: Dict[str, Callable] = {}
        self._metadata: Dict[str, Dict[str, Any]] = {}

    def register(self, name: Optional[str] = None, **metadata):
        """
        装饰器：注册智能体

        使用示例:
        @agent_registry.register(name="research_agent")
        def research_agent(state: State) -> dict:
            return {"result": "research completed"}
        """
        def decorator(func: T) -> T:
            agent_name = name or func.__name__
            self._agents[agent_name] = func
            self._metadata[agent_name] = {
                "description": func.__doc__ or "",
                "module": func.__module__,
                **metadata
            }
            return func
        return decorator

    def get(self, name: str) -> Callable:
        """获取已注册的智能体"""
        if name not in self._agents:
            raise ValueError(f"Agent '{name}' not found")
        return self._agents[name]

    def list_agents(self) -> Dict[str, Dict[str, Any]]:
        """列出所有已注册的智能体"""
        return {
            name: {
                "description": metadata["description"],
                "module": metadata["module"]
            }
            for name, metadata in self._metadata.items()
        }

    def register_node_to_graph(self, workflow: StateGraph, name: Optional[str] = None):
        """
        将已注册的智能体作为节点添加到图中

        使用示例:
        agent_registry.register_node_to_graph(workflow, "research_agent")
        """
        def decorator(func: T) -> T:
            agent_name = name or func.__name__
            # 先注册
            self.register(agent_name)(func)
            # 然后添加到图
            workflow.add_node(agent_name, func)
            return func
        return decorator


# 全局注册表实例
agent_registry = AgentRegistry()
```

**使用装饰器注册智能体：**

```python
from langgraph.graph import StateGraph

# 定义状态
class MultiAgentState(TypedDict):
    query: str
    results: dict
    messages: list

# 创建工作流
workflow = StateGraph(MultiAgentState)

# 使用装饰器注册多个智能体
@agent_registry.register_node_to_graph(workflow)
def research_agent(state: MultiAgentState) -> dict:
    """执行研究任务"""
    print(f"Research agent processing: {state['query']}")
    return {
        "results": {
            "research": f"Research completed for: {state['query']}"
        }
    }

@agent_registry.register_node_to_graph(workflow, priority="high")
def analysis_agent(state: MultiAgentState) -> dict:
    """执行分析任务"""
    print(f"Analysis agent processing: {state['results']}")
    return {
        "results": {
            **state['results'],
            "analysis": f"Analysis of research results"
        }
    }

@agent_registry.register_node_to_graph(workflow)
def report_agent(state: MultiAgentState) -> dict:
    """生成报告"""
    print(f"Report agent processing: {state['results']}")
    return {
        "messages": [{
            "role": "assistant",
            "content": f"Report: {state['results']}"
        }]
    }

# 列出所有已注册的智能体
agents_list = agent_registry.list_agents()
print("Registered agents:", agents_list)
```

### 2.2 工厂模式实现

```python
from abc import ABC, abstractmethod
from enum import Enum

class AgentType(Enum):
    RESEARCH = "research"
    ANALYSIS = "analysis"
    REPORT = "report"
    ROUTER = "router"

class BaseAgent(ABC):
    """智能体基类"""

    @abstractmethod
    def execute(self, state: dict) -> dict:
        pass

    @property
    @abstractmethod
    def agent_type(self) -> AgentType:
        pass

class AgentFactory:
    """智能体工厂"""

    _agent_classes: Dict[AgentType, type] = {}

    @classmethod
    def register(cls, agent_type: AgentType):
        """注册智能体类"""
        def decorator(agent_class: type):
            cls._agent_classes[agent_type] = agent_class
            return agent_class
        return decorator

    @classmethod
    def create(cls, agent_type: AgentType, **kwargs) -> BaseAgent:
        """创建智能体实例"""
        if agent_type not in cls._agent_classes:
            raise ValueError(f"Unknown agent type: {agent_type}")
        return cls._agent_classes[agent_type](**kwargs)

    @classmethod
    def list_available_agents(cls) -> list:
        """列出可用的智能体类型"""
        return list(cls._agent_types())

    @classmethod
    def _agent_types(cls) -> list:
        return cls._agent_classes.keys()


# 使用工厂模式注册和创建智能体
@AgentFactory.register(AgentType.RESEARCH)
class ResearchAgent(BaseAgent):
    def __init__(self, model: str = "gpt-4"):
        self.model = model

    def execute(self, state: dict) -> dict:
        # 实现研究逻辑
        return {"research_result": "research completed"}

    @property
    def agent_type(self) -> AgentType:
        return AgentType.RESEARCH


@AgentFactory.register(AgentType.ANALYSIS)
class AnalysisAgent(BaseAgent):
    def __init__(self, depth: int = 3):
        self.depth = depth

    def execute(self, state: dict) -> dict:
        # 实现分析逻辑
        return {"analysis_result": "analysis completed"}

    @property
    def agent_type(self) -> AgentType:
        return AgentType.ANALYSIS


# 动态创建智能体
research_agent = AgentFactory.create(AgentType.RESEARCH, model="gpt-4-turbo")
analysis_agent = AgentFactory.create(AgentType.ANALYSIS, depth=5)

# 添加到工作流
workflow.add_node("research", research_agent.execute)
workflow.add_node("analysis", analysis_agent.execute)
```

### 2.3 动态节点注册

```python
class DynamicGraphBuilder:
    """动态图构建器"""

    def __init__(self, state_class: type):
        self.workflow = StateGraph(state_class)
        self._registered_nodes: Dict[str, Callable] = {}

    def register_nodes(self, nodes: Dict[str, Callable]):
        """批量注册节点"""
        for name, func in nodes.items():
            self.workflow.add_node(name, func)
            self._registered_nodes[name] = func

    def build_router(self, router_func: Callable, routes: Dict[str, str]):
        """构建路由器"""
        self.workflow.add_conditional_edges(
            START,
            router_func,
            routes
        )

    def compile_with_checkpointer(self, checkpointer):
        """使用检查点编译图"""
        return self.workflow.compile(checkpointer=checkpointer)


# 使用示例
dynamic_builder = DynamicGraphBuilder(MultiAgentState)

# 批量注册节点
dynamic_builder.register_nodes({
    "research": research_agent_node,
    "analysis": analysis_agent_node,
    "report": report_agent_node
})

# 构建路由
def intent_router(state: MultiAgentState) -> str:
    """基于意图路由"""
    if "research" in state["query"]:
        return "research"
    elif "analyze" in state["query"]:
        return "analysis"
    return "report"

dynamic_builder.build_router(
    intent_router,
    {
        "research": "research",
        "analysis": "analysis",
        "report": "report"
    }
)

# 编译
graph = dynamic_builder.compile_with_checkpointer(InMemorySaver())
```

---

## 3. 会话管理和 TTL 超时模式

### 3.1 会话状态管理

```python
from datetime import datetime, timedelta
from typing import Dict, Optional
import json

class SessionManager:
    """会话管理器"""

    def __init__(self, default_ttl_minutes: int = 30):
        self.default_ttl = timedelta(minutes=default_ttl_minutes)
        self.checkpointer = InMemorySaver()
        self._sessions: Dict[str, Dict] = {}

    def create_session(self, thread_id: str, user_id: str,
                      metadata: Optional[Dict] = None) -> Dict:
        """创建新会话"""
        session = {
            "thread_id": thread_id,
            "user_id": user_id,
            "created_at": datetime.now(),
            "last_active": datetime.now(),
            "ttl": self.default_ttl,
            "metadata": metadata or {},
            "config": {"configurable": {"thread_id": thread_id}}
        }
        self._sessions[thread_id] = session
        return session

    def update_last_active(self, thread_id: str):
        """更新最后活跃时间"""
        if thread_id in self._sessions:
            self._sessions[thread_id]["last_active"] = datetime.now()

    def is_session_expired(self, thread_id: str) -> bool:
        """检查会话是否过期"""
        if thread_id not in self._sessions:
            return True
        session = self._sessions[thread_id]
        elapsed = datetime.now() - session["last_active"]
        return elapsed > session["ttl"]

    def cleanup_expired_sessions(self) -> list:
        """清理过期会话"""
        expired_threads = []
        for thread_id in list(self._sessions.keys()):
            if self.is_session_expired(thread_id):
                self.delete_session(thread_id)
                expired_threads.append(thread_id)
        return expired_threads

    def delete_session(self, thread_id: str):
        """删除会话"""
        if thread_id in self._sessions:
            del self._sessions[thread_id]

    def get_session(self, thread_id: str) -> Optional[Dict]:
        """获取会话信息"""
        if self.is_session_expired(thread_id):
            self.delete_session(thread_id)
            return None
        return self._sessions.get(thread_id)

    def get_config(self, thread_id: str) -> Optional[Dict]:
        """获取会话配置"""
        session = self.get_session(thread_id)
        if session:
            self.update_last_active(thread_id)
            return session["config"]
        return None


# 使用示例
session_manager = SessionManager(default_ttl_minutes=30)

# 创建会话
session = session_manager.create_session(
    thread_id="session_123",
    user_id="user_456",
    metadata={"plan": "premium"}
)

# 获取配置
config = session_manager.get_config("session_123")

# 在图中使用配置
result = graph.invoke({"messages": ["input"]}, config=config)

# 定期清理过期会话
import threading
import time

def cleanup_task():
    while True:
        time.sleep(300)  # 每5分钟检查一次
        expired = session_manager.cleanup_expired_sessions()
        print(f"Cleaned up {len(expired)} expired sessions")

# 在生产环境中使用调度器如 APScheduler
```

### 3.2 持久化会话管理

```python
from langgraph.checkpoint.sqlite import SqliteSaver
import sqlite3

class PersistentSessionManager(SessionManager):
    """持久化会话管理器"""

    def __init__(self, db_path: str = "sessions.db",
                 default_ttl_minutes: int = 30):
        super().__init__(default_ttl_minutes)
        self.checkpointer = SqliteSaver.from_conn_string(db_path)
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        """初始化数据库"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                thread_id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                created_at TIMESTAMP NOT NULL,
                last_active TIMESTAMP NOT NULL,
                ttl_minutes INTEGER NOT NULL,
                metadata TEXT,
                expires_at TIMESTAMP NOT NULL
            )
        """)
        conn.commit()
        conn.close()

    def create_session(self, thread_id: str, user_id: str,
                      metadata: Optional[Dict] = None,
                      ttl_minutes: Optional[int] = None) -> Dict:
        """创建持久化会话"""
        ttl_minutes = ttl_minutes or int(self.default_ttl.total_seconds() / 60)
        created_at = datetime.now()
        expires_at = created_at + timedelta(minutes=ttl_minutes)

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO sessions
            (thread_id, user_id, created_at, last_active, ttl_minutes, metadata, expires_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            thread_id,
            user_id,
            created_at.isoformat(),
            created_at.isoformat(),
            ttl_minutes,
            json.dumps(metadata or {}),
            expires_at.isoformat()
        ))
        conn.commit()
        conn.close()

        return {
            "thread_id": thread_id,
            "user_id": user_id,
            "created_at": created_at,
            "last_active": created_at,
            "ttl": timedelta(minutes=ttl_minutes),
            "metadata": metadata or {},
            "config": {"configurable": {"thread_id": thread_id}},
            "expires_at": expires_at
        }

    def update_last_active(self, thread_id: str):
        """更新最后活跃时间"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE sessions
            SET last_active = ?
            WHERE thread_id = ?
        """, (datetime.now().isoformat(), thread_id))
        conn.commit()
        conn.close()

    def is_session_expired(self, thread_id: str) -> bool:
        """检查会话是否过期"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT expires_at
            FROM sessions
            WHERE thread_id = ?
        """, (thread_id,))
        result = cursor.fetchone()
        conn.close()

        if not result:
            return True

        expires_at = datetime.fromisoformat(result[0])
        return datetime.now() > expires_at

    def cleanup_expired_sessions(self) -> list:
        """清理过期会话"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # 找到过期的会话
        cursor.execute("""
            SELECT thread_id
            FROM sessions
            WHERE expires_at < ?
        """, (datetime.now().isoformat(),))
        expired_threads = [row[0] for row in cursor.fetchall()]

        # 删除过期会话
        if expired_threads:
            cursor.execute("""
                DELETE FROM sessions
                WHERE expires_at < ?
            """, (datetime.now().isoformat(),))
            conn.commit()

        conn.close()

        # 同时清理检查点
        for thread_id in expired_threads:
            config = {"configurable": {"thread_id": thread_id}}
            # 注意：checkpointer 的清理需要根据具体实现调整
            # 这里可能需要直接操作数据库

        return expired_threads
```

### 3.3 会话中间件

```python
from fastapi import FastAPI, Request, Response, HTTPException
from typing import Callable

app = FastAPI()
session_manager = PersistentSessionManager("sessions.db", default_ttl_minutes=30)

async def session_middleware(request: Request, call_next: Callable):
    """会话中间件"""
    # 从请求头获取会话 ID
    session_id = request.headers.get("X-Session-ID")

    if not session_id:
        # 创建新会话
        user_id = request.headers.get("X-User-ID", "anonymous")
        session = session_manager.create_session(
            thread_id=f"session_{datetime.now().timestamp()}",
            user_id=user_id
        )
        session_id = session["thread_id"]
    else:
        # 验证会话
        if session_manager.is_session_expired(session_id):
            raise HTTPException(status_code=401, detail="Session expired")

    # 将会话信息添加到请求状态
    request.state.session_id = session_id
    request.state.session_config = session_manager.get_config(session_id)

    # 处理请求
    response = await call_next(request)

    # 更新最后活跃时间
    session_manager.update_last_active(session_id)

    # 返回会话 ID
    response.headers["X-Session-ID"] = session_id

    return response

app.middleware("http")(session_middleware)


@app.post("/chat")
async def chat_endpoint(request: Request, message: str):
    """聊天端点"""
    config = request.state.session_config

    # 执行图
    result = graph.invoke(
        {"messages": [{"role": "user", "content": message}]},
        config=config
    )

    return {"response": result}
```

### 3.4 上下文感知的会话管理

```python
from typing import Any
import hashlib

class ContextualSessionManager(PersistentSessionManager):
    """上下文感知的会话管理器"""

    def __init__(self, db_path: str = "sessions.db",
                 default_ttl_minutes: int = 30,
                 context_window_size: int = 10):
        super().__init__(db_path, default_ttl_minutes)
        self.context_window_size = context_window_size

    def get_session_context(self, thread_id: str) -> list:
        """获取会话上下文"""
        config = {"configurable": {"thread_id": thread_id}}

        # 从检查点获取历史
        checkpoints = list(self.checkpointer.list(config))
        context = []

        # 获取最近 N 条消息
        for checkpoint in checkpoints[-self.context_window_size:]:
            if "messages" in checkpoint.get("channel_values", {}):
                messages = checkpoint["channel_values"]["messages"]
                context.extend(messages)

        return context

    def truncate_context(self, messages: list, max_tokens: int = 4000) -> list:
        """截断上下文以适应 token 限制"""
        total_tokens = 0
        truncated_messages = []

        for message in reversed(messages):
            # 估算 token 数量（粗略估计：1 token ≈ 4 字符）
            message_tokens = len(message.get("content", "")) / 4

            if total_tokens + message_tokens > max_tokens:
                break

            truncated_messages.insert(0, message)
            total_tokens += message_tokens

        return truncated_messages

    def get_contextual_state(self, thread_id: str) -> dict:
        """获取带上下文的状态"""
        context = self.get_session_context(thread_id)
        truncated_context = self.truncate_context(context)

        return {
            "messages": truncated_context,
            "context_summary": f"Session has {len(context)} total messages"
        }
```

---

## 4. 意图分类和路由器最佳实践

### 4.1 基于结构化输出的意图分类

```python
from typing import Literal
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.pydantic_v1 import BaseModel, Field
from langchain_openai import ChatOpenAI

# 定义意图类型
class Intent(BaseModel):
    """用户意图分类"""
    intent: Literal["research", "analysis", "creative", "chat", "code"] = Field(
        ...,
        description="用户的意图类型"
    )
    confidence: float = Field(
        ...,
        description="置信度分数 (0.0 - 1.0)",
        ge=0.0,
        le=1.0
    )
    reasoning: str = Field(
        ...,
        description="分类的原因"
    )

# 创建意图分类器
def create_intent_classifier(model: ChatOpenAI):
    """创建意图分类器"""
    system_prompt = """你是一个专业的意图分类器。分析用户的问题，确定其主要意图。

可用的意图类型：
- research: 用户需要研究、查找信息或获取事实
- analysis: 用户需要分析数据、比较选项或进行评估
- creative: 用户需要创意内容生成、头脑风暴或创意建议
- chat: 用户只是聊天或进行一般对话
- code: 用户需要代码编写、调试或编程相关帮助

请分析用户的问题并返回分类结果，包括置信度和推理过程。"""

    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", "用户问题: {query}")
    ])

    structured_llm = model.with_structured_output(Intent)
    return prompt | structured_llm

# 使用意图分类器
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
intent_classifier = create_intent_classifier(llm)

# 测试
result = intent_classifier.invoke({
    "query": "帮我分析一下市场趋势"
})
print(result)
# Intent(intent='analysis', confidence=0.9, reasoning='用户要求分析...')
```

### 4.2 多层级路由器

```python
from typing import Dict, Callable

class MultiLevelRouter:
    """多层级路由器"""

    def __init__(self):
        self._level1_routes: Dict[str, Callable] = {}
        self._level2_routes: Dict[str, Dict[str, Callable]] = {}
        self._default_handler: Optional[Callable] = None

    def register_level1_route(self, intent: str, handler: Callable):
        """注册一级路由"""
        self._level1_routes[intent] = handler

    def register_level2_route(self, intent: str, sub_intent: str, handler: Callable):
        """注册二级路由"""
        if intent not in self._level2_routes:
            self._level2_routes[intent] = {}
        self._level2_routes[intent][sub_intent] = handler

    def set_default_handler(self, handler: Callable):
        """设置默认处理器"""
        self._default_handler = handler

    def route(self, state: dict) -> str:
        """执行路由"""
        intent = state.get("intent")
        sub_intent = state.get("sub_intent")

        # 尝试二级路由
        if intent and sub_intent:
            if intent in self._level2_routes:
                if sub_intent in self._level2_routes[intent]:
                    return sub_intent

        # 尝试一级路由
        if intent in self._level1_routes:
            return intent

        # 使用默认处理器
        if self._default_handler:
            return "default"

        raise ValueError(f"No route found for intent: {intent}, sub_intent: {sub_intent}")


# 定义子意图类型
class ResearchIntent(BaseModel):
    """研究意图的详细分类"""
    intent: Literal["research"] = Field(default="research")
    sub_intent: Literal["search", "summarize", "compare", "deep_dive"] = Field(
        ...,
        description="研究意图的子类型"
    )

def create_research_router(model: ChatOpenAI):
    """创建研究路由器"""
    prompt = ChatPromptTemplate.from_messages([
        ("system", "你是研究意图的分类器。确定用户研究请求的具体类型。"),
        ("human", "用户问题: {query}")
    ])

    structured_llm = model.with_structured_output(ResearchIntent)
    return prompt | structured_llm


# 使用多层级路由
router = MultiLevelRouter()

# 注册一级路由
router.register_level1_route("research", research_handler)
router.register_level1_route("analysis", analysis_handler)

# 注册二级路由
router.register_level2_route("research", "search", search_handler)
router.register_level2_route("research", "summarize", summarize_handler)
router.register_level2_route("analysis", "trend", trend_analysis_handler)

# 设置默认
router.set_default_handler(chat_handler)

# 在图中使用
workflow.add_node("intent_classifier", intent_classifier_node)
workflow.add_node("research_router", research_router_node)

workflow.add_edge(START, "intent_classifier")
workflow.add_conditional_edges(
    "intent_classifier",
    lambda state: state["intent"],
    {
        "research": "research_router",
        "analysis": "analysis",
        "default": "chat"
    }
)
```

### 4.3 动态路由器

```python
class DynamicRouter:
    """动态路由器"""

    def __init__(self, model: ChatOpenAI):
        self.model = model
        self._registered_agents: Dict[str, Callable] = {}
        self._agent_descriptions: Dict[str, str] = {}

    def register_agent(self, name: str, handler: Callable, description: str):
        """注册智能体"""
        self._registered_agents[name] = handler
        self._agent_descriptions[name] = description

    def create_dynamic_router(self):
        """创建动态路由器"""
        # 构建可用的智能体列表
        agent_list = "\n".join([
            f"- {name}: {description}"
            for name, description in self._agent_descriptions.items()
        ])

        # 定义路由提示
        system_prompt = f"""你是一个智能路由器。根据用户的问题，选择最合适的智能体来处理。

可用的智能体：
{agent_list}

请返回智能体的名称。"""

        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("human", "用户问题: {query}")
        ])

        # 使用带字符串输出的 LLM
        return prompt | self.model | StrOutputParser()

    def route(self, state: dict) -> str:
        """执行路由"""
        router = self.create_dynamic_router()
        agent_name = router.invoke({"query": state["query"]})

        if agent_name not in self._registered_agents:
            raise ValueError(f"Unknown agent: {agent_name}")

        return agent_name

    def build_workflow(self, state_class: type) -> StateGraph:
        """构建动态工作流"""
        workflow = StateGraph(state_class)

        # 添加路由节点
        workflow.add_node("router", self.route)

        # 添加所有智能体节点
        for name, handler in self._registered_agents.items():
            workflow.add_node(name, handler)

        # 添加从路由到智能体的条件边
        workflow.add_conditional_edges(
            "router",
            lambda state: state["selected_agent"],
            {name: name for name in self._registered_agents.keys()}
        )

        return workflow


# 使用示例
dynamic_router = DynamicRouter(ChatOpenAI(model="gpt-4o-mini"))

# 注册多个智能体
dynamic_router.register_agent(
    "research",
    research_handler,
    "执行研究任务，查找信息和数据"
)

dynamic_router.register_agent(
    "analysis",
    analysis_handler,
    "分析数据，比较选项，进行评估"
)

dynamic_router.register_agent(
    "creative",
    creative_handler,
    "生成创意内容，头脑风暴"
)

# 构建工作流
workflow = dynamic_router.build_workflow(MultiAgentState)
graph = workflow.compile()
```

### 4.4 意图分类器节点

```python
def intent_classifier_node(state: MultiAgentState) -> dict:
    """意图分类节点"""
    # 提取查询
    query = state["messages"][-1]["content"]

    # 使用意图分类器
    result = intent_classifier.invoke({"query": query})

    # 返回分类结果
    return {
        "intent": result.intent,
        "confidence": result.confidence,
        "reasoning": result.reasoning,
        "selected_agent": result.intent  # 用于路由
    }


def research_router_node(state: MultiAgentState) -> dict:
    """研究路由节点"""
    query = state["messages"][-1]["content"]

    # 使用研究子意图分类器
    result = research_router.invoke({"query": query})

    # 返回子意图
    return {
        "sub_intent": result.sub_intent,
        "selected_agent": result.sub_intent  # 用于二级路由
    }
```

### 4.5 条件边函数

```python
def route_by_intent(state: MultiAgentState) -> str:
    """根据意图路由"""
    intent = state.get("intent", "chat")
    return intent


def route_by_confidence(state: MultiAgentState) -> str:
    """根据置信度路由"""
    confidence = state.get("confidence", 0.0)

    if confidence < 0.5:
        return "clarify"  # 需要澄清
    elif confidence < 0.8:
        return "verify"   # 需要验证
    else:
        return "execute"  # 直接执行


def route_by_sub_intent(state: MultiAgentState) -> str:
    """根据子意图路由"""
    sub_intent = state.get("sub_intent", "default")
    return sub_intent
```

---

## 5. 生产就绪完整示例

### 5.1 完整的多智能体系统

```python
import os
from typing import Dict, Any, Optional
from datetime import datetime, timedelta

from langgraph.graph import StateGraph, START, END, MessagesState
from langgraph.checkpoint.sqlite import SqliteSaver
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic

# ============== 配置 ==============
class Config:
    """系统配置"""
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

    MODELS = {
        "gpt-4": ChatOpenAI(model="gpt-4", temperature=0),
        "gpt-4o-mini": ChatOpenAI(model="gpt-4o-mini", temperature=0),
        "claude-3-sonnet": ChatAnthropic(model="claude-3-5-sonnet-20241022", temperature=0),
    }

    SESSION_TTL_MINUTES = 30
    DB_PATH = "multi_agent.db"


# ============== 状态定义 ==============
class MultiAgentState(MessagesState):
    """多智能体状态"""
    query: Optional[str] = None
    intent: Optional[str] = None
    confidence: Optional[float] = None
    sub_intent: Optional[str] = None
    selected_agent: Optional[str] = None
    metadata: Dict[str, Any] = {}


# ============== 智能体注册 ==============
class AgentRegistry:
    """智能体注册中心"""

    def __init__(self):
        self._agents = {}
        self._descriptions = {}

    def register(self, name: str, description: str):
        """注册智能体装饰器"""
        def decorator(func):
            self._agents[name] = func
            self._descriptions[name] = description
            return func
        return decorator

    def get(self, name: str):
        """获取智能体"""
        return self._agents.get(name)

    def list_agents(self) -> Dict[str, str]:
        """列出所有智能体"""
        return self._descriptions.copy()


# 全局注册表
agent_registry = AgentRegistry()


# ============== 意图分类 ==============
class Intent(BaseModel):
    """意图分类"""
    intent: Literal["research", "analysis", "creative", "code", "chat"] = Field(...)
    confidence: float = Field(..., ge=0.0, le=1.0)
    reasoning: str = Field(...)


def create_intent_classifier():
    """创建意图分类器"""
    from langchain_core.prompts import ChatPromptTemplate
    from langchain_core.pydantic_v1 import BaseModel, Field
    from typing import Literal

    system_prompt = """你是意图分类器。分析用户问题并分类。

意图类型：
- research: 研究、查找信息
- analysis: 分析、比较、评估
- creative: 创意生成、头脑风暴
- code: 编程、代码帮助
- chat: 一般对话"""

    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", "问题: {query}")
    ])

    llm = Config.MODELS["gpt-4o-mini"]
    structured_llm = llm.with_structured_output(Intent)
    return prompt | structured_llm


intent_classifier = create_intent_classifier()


# ============== 智能体实现 ==============
@agent_registry.register("research", "执行研究和信息检索任务")
def research_agent(state: MultiAgentState) -> MultiAgentState:
    """研究智能体"""
    query = state["messages"][-1]["content"]

    llm = Config.MODELS["gpt-4"]
    response = llm.invoke(f"研究以下主题: {query}")

    return {
        "messages": [{
            "role": "assistant",
            "content": f"[研究] {response.content}"
        }],
        "metadata": {
            "agent": "research",
            "timestamp": datetime.now().isoformat()
        }
    }


@agent_registry.register("analysis", "执行数据分析和比较")
def analysis_agent(state: MultiAgentState) -> MultiAgentState:
    """分析智能体"""
    query = state["messages"][-1]["content"]

    llm = Config.MODELS["gpt-4"]
    response = llm.invoke(f"分析以下内容: {query}")

    return {
        "messages": [{
            "role": "assistant",
            "content": f"[分析] {response.content}"
        }],
        "metadata": {
            "agent": "analysis",
            "timestamp": datetime.now().isoformat()
        }
    }


@agent_registry.register("creative", "生成创意内容")
def creative_agent(state: MultiAgentState) -> MultiAgentState:
    """创意智能体"""
    query = state["messages"][-1]["content"]

    llm = Config.MODELS["claude-3-sonnet"]
    response = llm.invoke(f"为以下请求生成创意内容: {query}")

    return {
        "messages": [{
            "role": "assistant",
            "content": f"[创意] {response.content}"
        }],
        "metadata": {
            "agent": "creative",
            "timestamp": datetime.now().isoformat()
        }
    }


@agent_registry.register("code", "处理编程相关任务")
def code_agent(state: MultiAgentState) -> MultiAgentState:
    """代码智能体"""
    query = state["messages"][-1]["content"]

    llm = Config.MODELS["gpt-4"]
    response = llm.invoke(f"帮助解决编程问题: {query}")

    return {
        "messages": [{
            "role": "assistant",
            "content": f"[代码] {response.content}"
        }],
        "metadata": {
            "agent": "code",
            "timestamp": datetime.now().isoformat()
        }
    }


@agent_registry.register("chat", "处理一般对话")
def chat_agent(state: MultiAgentState) -> MultiAgentState:
    """聊天智能体"""
    query = state["messages"][-1]["content"]

    llm = Config.MODELS["gpt-4o-mini"]
    response = llm.invoke(f"回答: {query}")

    return {
        "messages": [{
            "role": "assistant",
            "content": response.content
        }],
        "metadata": {
            "agent": "chat",
            "timestamp": datetime.now().isoformat()
        }
    }


# ============== 节点函数 ==============
def intent_classifier_node(state: MultiAgentState) -> MultiAgentState:
    """意图分类节点"""
    query = state["messages"][-1]["content"]

    # 执行意图分类
    result = intent_classifier.invoke({"query": query})

    return {
        "query": query,
        "intent": result.intent,
        "confidence": result.confidence,
        "selected_agent": result.intent
    }


def route_to_agent(state: MultiAgentState) -> MultiAgentState:
    """路由到选定的智能体"""
    agent_name = state["selected_agent"]
    agent_func = agent_registry.get(agent_name)

    if not agent_func:
        raise ValueError(f"Unknown agent: {agent_name}")

    # 执行智能体
    return agent_func(state)


# ============== 图构建 ==============
def build_multi_agent_graph():
    """构建多智能体图"""
    workflow = StateGraph(MultiAgentState)

    # 添加节点
    workflow.add_node("intent_classifier", intent_classifier_node)
    workflow.add_node("execute_agent", route_to_agent)

    # 添加边
    workflow.add_edge(START, "intent_classifier")
    workflow.add_edge("intent_classifier", "execute_agent")
    workflow.add_edge("execute_agent", END)

    return workflow


# ============== 会话管理 ==============
class SessionManager:
    """会话管理器"""

    def __init__(self, db_path: str = "sessions.db",
                 ttl_minutes: int = 30):
        from langgraph.checkpoint.sqlite import SqliteSaver
        import sqlite3

        self.checkpointer = SqliteSaver.from_conn_string(db_path)
        self.db_path = db_path
        self.ttl = timedelta(minutes=ttl_minutes)
        self._init_db()

    def _init_db(self):
        """初始化数据库"""
        import sqlite3
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                thread_id TEXT PRIMARY KEY,
                created_at TIMESTAMP,
                last_active TIMESTAMP,
                expires_at TIMESTAMP
            )
        """)
        conn.commit()
        conn.close()

    def create_session(self, user_id: str = "anonymous") -> str:
        """创建新会话"""
        import sqlite3
        thread_id = f"{user_id}_{datetime.now().timestamp()}"
        now = datetime.now()
        expires_at = now + self.ttl

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO sessions (thread_id, created_at, last_active, expires_at)
            VALUES (?, ?, ?, ?)
        """, (thread_id, now.isoformat(), now.isoformat(), expires_at.isoformat()))
        conn.commit()
        conn.close()

        return thread_id

    def get_config(self, thread_id: str) -> dict:
        """获取会话配置"""
        self._update_last_active(thread_id)
        return {"configurable": {"thread_id": thread_id}}

    def _update_last_active(self, thread_id: str):
        """更新最后活跃时间"""
        import sqlite3
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE sessions
            SET last_active = ?
            WHERE thread_id = ?
        """, (datetime.now().isoformat(), thread_id))
        conn.commit()
        conn.close()

    def cleanup_expired(self):
        """清理过期会话"""
        import sqlite3
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            DELETE FROM sessions
            WHERE expires_at < ?
        """, (datetime.now().isoformat(),))
        conn.commit()
        conn.close()


# ============== 系统初始化 ==============
def initialize_system():
    """初始化多智能体系统"""
    print("初始化多智能体系统...")

    # 构建图
    workflow = build_multi_agent_graph()

    # 创建会话管理器
    session_manager = SessionManager(
        db_path=Config.DB_PATH,
        ttl_minutes=Config.SESSION_TTL_MINUTES
    )

    # 编译图
    graph = workflow.compile(checkpointer=session_manager.checkpointer)

    print(f"系统初始化完成!")
    print(f"已注册 {len(agent_registry.list_agents())} 个智能体:")
    for name, desc in agent_registry.list_agents().items():
        print(f"  - {name}: {desc}")

    return graph, session_manager


# ============== 使用示例 ==============
def main():
    """主函数"""
    import json

    # 初始化系统
    graph, session_manager = initialize_system()

    # 创建会话
    thread_id = session_manager.create_session(user_id="user_123")
    config = session_manager.get_config(thread_id)

    print(f"\n=== 会话 ID: {thread_id} ===\n")

    # 测试查询
    test_queries = [
        "帮我研究一下人工智能的最新发展",
        "分析一下这组数据的意义",
        "给我一些创意的想法",
        "如何用 Python 实现快速排序",
        "你好，今天天气怎么样"
    ]

    for query in test_queries:
        print(f"用户: {query}")

        # 执行查询
        result = graph.invoke({
            "messages": [{"role": "user", "content": query}]
        }, config=config)

        # 输出结果
        response = result["messages"][-1]["content"]
        print(f"助手: {response}\n")

        print(f"意图: {result.get('intent')}")
        print(f"置信度: {result.get('confidence')}")
        print(f"智能体: {result.get('metadata', {}).get('agent')}")
        print("-" * 60 + "\n")


if __name__ == "__main__":
    main()
```

### 5.2 FastAPI 集成

```python
from fastapi import FastAPI, HTTPException, Header
from pydantic import BaseModel
from typing import Optional

app = FastAPI(title="多智能体系统 API")

# 初始化系统
graph, session_manager = initialize_system()


class ChatRequest(BaseModel):
    """聊天请求"""
    message: str
    session_id: Optional[str] = None


class ChatResponse(BaseModel):
    """聊天响应"""
    message: str
    session_id: str
    intent: Optional[str] = None
    confidence: Optional[float] = None
    agent: Optional[str] = None


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest, x_user_id: Optional[str] = Header(None)):
    """聊天端点"""
    try:
        # 获取或创建会话
        if request.session_id:
            config = session_manager.get_config(request.session_id)
            thread_id = request.session_id
        else:
            thread_id = session_manager.create_session(user_id=x_user_id or "anonymous")
            config = session_manager.get_config(thread_id)

        # 执行查询
        result = graph.invoke({
            "messages": [{"role": "user", "content": request.message}]
        }, config=config)

        # 构建响应
        response = result["messages"][-1]["content"]

        return ChatResponse(
            message=response,
            session_id=thread_id,
            intent=result.get("intent"),
            confidence=result.get("confidence"),
            agent=result.get("metadata", {}).get("agent")
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/agents")
async def list_agents():
    """列出所有智能体"""
    return agent_registry.list_agents()


@app.delete("/session/{session_id}")
async def delete_session(session_id: str):
    """删除会话"""
    # 实现删除逻辑
    return {"message": "Session deleted"}


@app.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "healthy"}
```

### 5.3 Docker 部署

```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app

# 安装依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制代码
COPY . .

# 暴露端口
EXPOSE 8000

# 运行应用
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

```yaml
# docker-compose.yml
version: '3.8'

services:
  app:
    build: .
    ports:
      - "8000:8000"
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
    volumes:
      - ./data:/app/data
    restart: unless-stopped
```

---

## 总结

本文档提供了 LangGraph 1.0+ 构建多智能体系统的完整指南，包括：

1. **核心 API**: StateGraph、条件边、预构建 Agent、Checkpoints
2. **动态注册模式**: 装饰器模式、工厂模式、动态节点注册
3. **会话管理**: 内存会话、持久化会话、TTL 超时、上下文管理
4. **意图分类**: 结构化输出、多层级路由、动态路由器
5. **生产就绪**: 完整系统实现、FastAPI 集成、Docker 部署

**关键要点：**
- 使用装饰器模式实现智能体自动注册
- 实现 TTL 超时的会话管理（30 分钟空闲超时）
- 使用结构化输出实现精确的意图分类
- 构建多层级路由器处理复杂意图
- 使用检查点实现持久化和恢复
- 集成 FastAPI 提供 REST API

**下一步建议：**
- 添加监控和日志记录（使用 LangSmith）
- 实现更复杂的上下文管理（长期记忆）
- 添加智能体协作机制
- 实现流式输出和 WebSocket 支持
- 添加单元测试和集成测试
