"""LangGraph State 定义,显式传递给所有 Agent"""

from typing import TypedDict, List, Optional, Dict, Any


class AgentState(TypedDict):
    """LangGraph 状态定义,显式传递给所有 Agent

    用于在多个 Agent 之间传递状态,包含用户输入、意图识别结果、
    项目路径、会话上下文、Agent 执行结果和错误信息。
    """
    user_input: str                    # 用户原始输入
    intent: Optional[str]              # 识别的意图(generate_ci, analyze_project, update_config, unknown)
    project_path: str                  # 当前工作目录
    context: Dict[str, Any]            # 会话上下文(变量、配置等)
    agent_results: List[Dict[str, Any]]  # 子 Agent 执行结果列表
    errors: List[str]                  # 错误信息列表
    response: Optional[str]            # 最终响应文本
