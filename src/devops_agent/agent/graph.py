"""LangGraph 工作流构建"""

from langgraph.graph import StateGraph, END
from .state import AgentState
from .main_agent import MainAgent
from .project_agent import ProjectAgent
from .build_agent import BuildAgent


def main_agent_node(state: AgentState, config: dict) -> AgentState:
    """主 Agent 节点(LangGraph 节点函数)

    LangGraph 节点函数签名:接收 state 和 config,返回更新后的 state。

    Args:
        state: Agent 状态
        config: 配置字典(包含 llm_client)

    Returns:
        更新后的 AgentState
    """
    # config 中包含 llm_client(通过可调用对象配置)
    llm_client = config.get('configurable', {}).get('llm_client')
    agent = MainAgent(state, llm_client)

    # 执行 Agent(同步调用,LangGraph 节点函数)
    import asyncio
    return asyncio.run(agent.execute())


def project_agent_node(state: AgentState, config: dict) -> AgentState:
    """项目分析 Agent 节点

    执行项目分析，不使用 LLM。

    Args:
        state: Agent 状态
        config: 配置字典（包含 llm_client，虽然 ProjectAgent 不使用）

    Returns:
        更新后的 AgentState
    """
    # ProjectAgent 不使用 LLM，但为了保持一致性，仍传递 llm_client
    llm_client = config.get('configurable', {}).get('llm_client')
    agent = ProjectAgent(state, llm_client)

    # 执行 Agent
    import asyncio
    return asyncio.run(agent.execute())


def build_agent_node(state: AgentState, config: dict) -> AgentState:
    """Build Agent 节点

    处理 generate_ci 意图，生成 GitHub Actions 配置。

    Args:
        state: Agent 状态
        config: 配置字典（包含 llm_client，虽然 BuildAgent 不使用）

    Returns:
        更新后的 AgentState
    """
    # BuildAgent 不使用 LLM，但为了保持一致性，仍传递 llm_client
    llm_client = config.get('configurable', {}).get('llm_client')
    agent = BuildAgent(state, llm_client)

    # 执行 Agent
    import asyncio
    return asyncio.run(agent.execute())


def route_by_intent(state: AgentState) -> str:
    """根据意图路由到不同的 Agent

    Args:
        state: Agent 状态

    Returns:
        下一个节点名称
    """
    intent = state.get("intent", "unknown")

    if intent == "analyze_project":
        return "project_agent"
    elif intent == "generate_ci":
        return "build_agent"
    else:
        return END


def create_agent_graph() -> StateGraph:
    """构建 LangGraph 工作流

    创建一个简单的 StateGraph,目前只包含主 Agent 节点。
    后续可以添加子 Agent 节点和条件边。

    Returns:
        编译后的 StateGraph
    """
    graph = StateGraph(AgentState)

    # 添加节点
    graph.add_node("main_agent", main_agent_node)
    graph.add_node("project_agent", project_agent_node)
    graph.add_node("build_agent", build_agent_node)

    # 设置入口点
    graph.set_entry_point("main_agent")

    # 添加条件边:根据 intent 路由
    graph.add_conditional_edges(
        "main_agent",
        route_by_intent,
        {
            "project_agent": "project_agent",
            "build_agent": "build_agent",
            END: END,
        },
    )

    # 添加边:project_agent 结束
    graph.add_edge("project_agent", END)
    # 添加边:build_agent 结束
    graph.add_edge("build_agent", END)

    return graph.compile()
