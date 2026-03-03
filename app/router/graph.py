"""
路由图构建
使用 LangGraph 构建状态机流程
"""
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
    """
    构建路由图
    流程：preprocess -> rule_route -> llm_intent -> policy -> invoke_agent -> END

    1. preprocess: 预处理输入
    2. rule_route: 基于规则的快速路由（命令前缀匹配）
    3. llm_intent: LLM 意图识别（当规则未命中时）
    4. policy: 根据意图和置信度决定路由策略
    5. invoke_agent: 调用对应的 Agent 处理请求
    """
    # 创建状态图
    g = StateGraph(RouterState)

    # 添加节点
    g.add_node("preprocess", preprocess_node)
    g.add_node("rule_route", rule_route_node)
    g.add_node("llm_intent", llm_intent_node)
    g.add_node("policy", policy_node)
    g.add_node("invoke_agent", invoke_agent_node)

    # 设置入口点
    g.set_entry_point("preprocess")

    # 添加边，定义执行顺序
    g.add_edge("preprocess", "rule_route")      # 预处理后进入规则路由
    g.add_edge("rule_route", "llm_intent")      # 规则路由后进入 LLM 意图识别
    g.add_edge("llm_intent", "policy")          # 意图识别后进入策略决策
    g.add_edge("policy", "invoke_agent")        # 策略决策后调用 Agent
    g.add_edge("invoke_agent", END)             # Agent 处理后结束

    # 编译图
    return g.compile()
