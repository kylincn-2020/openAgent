"""
LangGraph 节点定义
实现路由流程的各个处理节点
"""
from __future__ import annotations
from typing import Any, Dict, TypedDict
from pydantic import BaseModel, Field

from app.core.models import InboundMessage, IntentResult
from app.router.prompts import INTENT_CLASSIFIER_SYSTEM
from app.router.policy import decide_route
from app.infra.llm import get_llm
from app.core.registry import AgentRegistry


class RouterState(TypedDict, total=False):
    """
    路由状态
    LangGraph 中传递的状态对象
    """
    msg: InboundMessage           # 入站消息
    history: list                 # 会话历史
    intent_result: IntentResult   # 意图识别结果
    route: dict                   # 路由决策
    answer: str                   # 最终回答


class IntentSchema(BaseModel):
    """
    意图识别的结构化输出 Schema
    用于 LangChain 的 structured output 功能
    """
    intent: str = Field(description="意图类型：code_gen/doc_qa/task_query/unknown")
    confidence: float = Field(ge=0, le=1, description="置信度")
    candidate_agents: list[str] = Field(default_factory=list, description="候选 Agent 列表")
    slots: dict[str, Any] = Field(default_factory=dict, description="参数槽位")
    need_clarification: bool = Field(default=False, description="是否需要澄清")
    clarification_question: str = Field(default="", description="澄清问题")


def preprocess_node(state: RouterState) -> RouterState:
    """
    预处理节点
    对输入消息进行预处理，如去除空白字符
    """
    msg = state["msg"]
    msg.text = msg.text.strip()
    return {"msg": msg}


def rule_route_node(state: RouterState) -> RouterState:
    """
    规则路由节点
    基于命令前缀（/code, /doc, /task）进行快速路由
    这是一种确定性路由，优先级高于 LLM 意图识别
    """
    text = state["msg"].text.lower()

    # 检查命令前缀
    if text.startswith("/code"):
        ir = IntentResult(
            intent="code_gen",
            confidence=0.99,
            candidate_agents=["CodeAgent"]
        )
        return {"intent_result": ir}

    if text.startswith("/doc"):
        ir = IntentResult(
            intent="doc_qa",
            confidence=0.99,
            candidate_agents=["DocAgent"]
        )
        return {"intent_result": ir}

    if text.startswith("/task"):
        ir = IntentResult(
            intent="task_query",
            confidence=0.99,
            candidate_agents=["TaskAgent"]
        )
        return {"intent_result": ir}

    # 没有匹配规则时返回空字典，让后续 LLM 节点处理
    return {}


def llm_intent_node(state: RouterState) -> RouterState:
    """
    LLM 意图识别节点
    使用 LLM 进行意图分类（当规则路由未命中时）
    """
    # 如果规则路由已经命中，跳过 LLM 识别
    if state.get("intent_result"):
        return {}

    # 使用结构化输出的 LLM
    llm = get_llm().with_structured_output(IntentSchema)
    msg = state["msg"]

    # 调用 LLM 进行意图分类
    result: IntentSchema = llm.invoke([
        ("system", INTENT_CLASSIFIER_SYSTEM),
        ("human", f"用户输入：{msg.text}")
    ])

    # 验证意图类型
    valid_intents = {"code_gen", "doc_qa", "task_query", "unknown"}
    intent = result.intent if result.intent in valid_intents else "unknown"

    # 构建意图识别结果
    ir = IntentResult(
        intent=intent,
        confidence=result.confidence,
        candidate_agents=result.candidate_agents,
        slots=result.slots,
        need_clarification=result.need_clarification,
        clarification_question=result.clarification_question
    )

    return {"intent_result": ir}


def policy_node(state: RouterState) -> RouterState:
    """
    策略节点
    根据意图识别结果决定路由策略
    """
    decision = decide_route(state["intent_result"])
    return {"route": decision.model_dump()}


def invoke_agent_node(state: RouterState) -> RouterState:
    """
    Agent 调用节点
    根据路由决策调用相应的 Agent
    """
    route = state["route"]

    # 如果需要澄清，直接返回澄清问题
    if route.get("need_clarification"):
        return {"answer": route["clarification_question"]}

    # 获取并调用对应的 Agent
    registry = AgentRegistry()
    agent = registry.get(route["selected_agent"])
    answer = agent.invoke(state["msg"].text, context={})

    return {"answer": answer}
