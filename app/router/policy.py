"""
路由策略
根据意图识别结果决定路由到哪个 Agent
"""
from app.core.models import IntentResult, RouteDecision


def select_agent_by_intent(intent: str) -> str:
    """
    根据意图类型选择对应的 Agent
    :param intent: 意图类型
    :return: Agent ID
    """
    mapping = {
        "code_gen": "CodeAgent",
        "doc_qa": "DocAgent",
        "task_query": "TaskAgent",
        "unknown": "DocAgent",  # 未知意图时降级到 DocAgent
    }
    return mapping.get(intent, "DocAgent")


def decide_route(intent_result: IntentResult) -> RouteDecision:
    """
    根据意图识别结果决定路由策略
    策略：
    - 置信度 >= 0.75: 直接路由
    - 置信度 0.5-0.75: 需要用户澄清
    - 置信度 < 0.5: 降级到 DocAgent

    :param intent_result: 意图识别结果
    :return: 路由决策
    """
    c = intent_result.confidence

    # 高置信度：直接路由
    if c >= 0.75:
        return RouteDecision(
            selected_agent=select_agent_by_intent(intent_result.intent),
            intent=intent_result.intent,
            confidence=c,
            is_fallback=(intent_result.intent == "unknown")
        )

    # 中等置信度：需要澄清
    if 0.5 <= c < 0.75:
        return RouteDecision(
            selected_agent="",
            intent=intent_result.intent,
            confidence=c,
            need_clarification=True,
            clarification_question=intent_result.clarification_question or "你是要代码生成、文档问答，还是任务查询？"
        )

    # 低置信度：降级
    return RouteDecision(
        selected_agent="DocAgent",
        intent="unknown",
        confidence=c,
        is_fallback=True
    )
