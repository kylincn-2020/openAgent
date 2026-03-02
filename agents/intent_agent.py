"""
意图识别主 Agent - 使用 LangGraph StateGraph 实现
"""
from typing import TypedDict, Literal, Optional, Dict, Any, List
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage, AIMessage
from langchain_core.language_models import BaseChatModel
from langgraph.graph import StateGraph, START, END
from loguru import logger

from core.base_agent import BaseAgent
from core.registry import registry, AgentMetadata

from core.base_agent import BaseAgent
from core.registry import registry, AgentMetadata


class AgentState(TypedDict):
    """Agent 状态"""

    user_input: str
    intent: Optional[str]
    selected_agent: Optional[str]
    response: Optional[str]
    messages: List[BaseMessage]
    metadata: Dict[str, Any]


class IntentAgent(BaseAgent):
    """
    意图识别主 Agent

    工作流程：
    1. 接收用户输入
    2. 分析意图，选择最合适的子 agent
    3. 调用子 agent 处理
    4. 返回响应
    """

    def __init__(self, llm: Optional[BaseChatModel] = None):
        super().__init__(llm)
        self.graph = self._build_graph()
        logger.info("IntentAgent 已初始化")

    def _build_graph(self) -> StateGraph:
        """构建 LangGraph 状态图"""
        graph = StateGraph(AgentState)

        # 添加节点
        graph.add_node("analyze_intent", self._analyze_intent)
        graph.add_node("route_to_agent", self._route_to_agent)
        graph.add_node("execute_agent", self._execute_agent)
        graph.add_node("fallback", self._fallback)

        # 添加边
        graph.add_edge(START, "analyze_intent")
        graph.add_conditional_edges(
            "analyze_intent",
            self._check_intent,
            {
                "identified": "route_to_agent",
                "unclear": "fallback",
            },
        )
        graph.add_edge("route_to_agent", "execute_agent")
        graph.add_edge("execute_agent", END)
        graph.add_edge("fallback", END)

        return graph.compile()

    def _get_intent_system_prompt(self) -> str:
        """获取意图识别的系统提示"""
        agents_info = registry.get_intent_prompt()

        return f"""你是一个意图识别助手。你的任务是分析用户输入，识别用户需要使用哪个专业助手。

{agents_info}

规则：
1. 根据用户输入的关键词和语义，选择最匹配的助手
2. 如果无法确定，返回 null
3. 只返回助手的 name 字段，不要其他内容

示例：
用户："帮我写一个 Python 函数"
你：coding_assistant

用户："分析这个数据集"
你：analysis_agent

用户："你好"
你：null
"""

    async def _analyze_intent(self, state: AgentState) -> AgentState:
        """分析用户意图"""
        user_input = state["user_input"]

        # 尝试关键词快速匹配
        quick_match = registry.find_best_match(user_input)
        if quick_match:
            logger.debug(f"关键词快速匹配：{quick_match}")
            return {
                **state,
                "intent": quick_match,
                "messages": state["messages"]
                + [AIMessage(content=f"快速匹配到 agent: {quick_match}")],
            }

        # 使用 LLM 进行意图识别
        if self.llm is None:
            from config import settings
            from langchain_openai import ChatOpenAI

            self.llm = ChatOpenAI(model=settings.DEFAULT_MODEL, temperature=0)

        messages = [
            SystemMessage(content=self._get_intent_system_prompt()),
            HumanMessage(content=f"用户输入：{user_input}"),
        ]

        response = await self.llm.ainvoke(messages)
        intent = response.content.strip()

        # 处理 null 情况
        if intent.lower() in ["null", "none", "无", "不知道"]:
            intent = None

        logger.info(f"意图识别结果：{intent}")

        return {
            **state,
            "intent": intent,
            "messages": state["messages"] + [AIMessage(content=f"意图识别：{intent}")],
        }

    def _check_intent(self, state: AgentState) -> Literal["identified", "unclear"]:
        """检查意图是否清晰"""
        intent = state["intent"]

        if intent and registry.get_agent(intent):
            return "identified"
        return "unclear"

    async def _route_to_agent(self, state: AgentState) -> AgentState:
        """路由到选定的 agent"""
        selected_agent = state["intent"]
        logger.info(f"路由到 agent: {selected_agent}")

        return {
            **state,
            "selected_agent": selected_agent,
        }

    async def _execute_agent(self, state: AgentState) -> AgentState:
        """执行选定的 agent"""
        selected_agent_name = state["selected_agent"]
        user_input = state["user_input"]

        # 获取 agent 类并实例化
        agent_cls = registry.get_agent_class(selected_agent_name)
        if not agent_cls:
            logger.error(f"未找到 agent 类：{selected_agent_name}")
            return {
                **state,
                "response": f"错误：未找到助手 {selected_agent_name}",
            }

        try:
            agent_instance = agent_cls(self.llm)
            response = await agent_instance.act(
                user_input=user_input, context={"messages": state["messages"]}
            )

            logger.info(f"Agent {selected_agent_name} 执行完成")

            return {
                **state,
                "response": response,
            }
        except Exception as e:
            logger.error(f"Agent 执行失败：{e}")
            return {
                **state,
                "response": f"错误：{selected_agent_name} 处理失败 - {str(e)}",
            }

    async def _fallback(self, state: AgentState) -> AgentState:
        """Fallback 处理"""
        logger.warning("意图不清晰，使用 fallback")

        return {
            **state,
            "response": "抱歉，我不太确定您需要哪个助手。能请您更具体地描述一下您的需求吗？\n\n例如：\n- 编程相关问题 → 编程助手\n- 写作/编辑相关 → 写作助手\n- 数据分析相关 → 分析助手",
        }

    async def act(
        self, user_input: str, context: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        处理用户输入

        Args:
            user_input: 用户输入
            context: 上下文（包含消息历史等）

        Returns:
            响应文本
        """
        initial_state: AgentState = {
            "user_input": user_input,
            "intent": None,
            "selected_agent": None,
            "response": None,
            "messages": context.get("messages", []) if context else [],
            "metadata": context.get("metadata", {}) if context else {},
        }

        # 执行状态图
        result = await self.graph.ainvoke(initial_state)

        return result["response"]
