"""
意图识别 Agent（基于 LangChain）
负责识别用户意图并路由到相应的子 Agent
"""

import asyncio
import json
from typing import Any, Dict, List, Optional

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field

from .agent_registry import get_global_registry


class IntentRecognitionResult(BaseModel):
    """意图识别结果"""

    primary_intent: str = Field(description="主要意图的 Agent 名称")
    secondary_intents: List[str] = Field(
        default_factory=list, description="次要意图的 Agent 名称列表（用于并行执行）"
    )
    confidence: float = Field(description="置信度 0-1")
    reasoning: str = Field(description="识别推理过程")


class IntentRecognitionAgent:
    """
    意图识别 Agent
    使用 LangChain v1.0+ API 进行意图识别和路由
    """

    def __init__(
        self, model_name: str = "gpt-4o-mini", temperature: float = 0.0, registry=None
    ):
        """
        初始化意图识别 Agent

        Args:
            model_name: 使用的模型名称
            temperature: 温度参数
            registry: Agent 注册表，默认使用全局注册表
        """
        self.llm = ChatOpenAI(model=model_name, temperature=temperature)
        self.registry = registry or get_global_registry()

    def _build_system_prompt(self) -> str:
        """
        构建系统提示词

        Returns:
            系统提示词字符串
        """
        # 获取所有已注册的 Agent 元数据
        agents_metadata = self.registry.get_all_metadata()

        if not agents_metadata:
            return "你是一个意图识别助手，但目前没有可用的子 Agent。"

        # 构建 Agent 列表描述
        agents_desc = []
        for metadata in agents_metadata:
            parallel_info = "（可并行）" if metadata.parallel_allowed else "（串行）"
            agents_desc.append(
                f"- {metadata.name}: {metadata.description} "
                f"[关键词: {', '.join(metadata.intent_keywords)}] "
                f"[优先级: {metadata.priority}]{parallel_info}"
            )

        return f"""你是一个智能意图识别助手。你的任务是分析用户的输入，识别出最合适的子 Agent 来处理用户请求。

可用的子 Agent：
{chr(10).join(agents_desc)}

识别规则：
1. 根据用户输入中的关键词和上下文，识别最匹配的主 Agent（primary_intent）
2. 如果用户请求涉及多个独立任务，可以识别多个次要 Agent（secondary_intents）进行并行处理
3. 置信度应该基于关键词匹配程度和上下文的清晰度
4. 推理过程要说明识别的主要依据

注意事项：
- 优先选择优先级更高的 Agent
- 只有当不同 Agent 处理的任务完全独立时，才添加到 secondary_intents
- 如果没有匹配的 Agent，返回 "unknown" 作为 primary_intent
"""

    async def recognize_intent(
        self, user_input: str, context: Optional[Dict] = None
    ) -> IntentRecognitionResult:
        """
        识别用户意图

        Args:
            user_input: 用户输入
            context: 上下文信息

        Returns:
            意图识别结果
        """
        # 使用 with_structured_output 创建结构化输出模型
        structured_llm = self.llm.with_structured_output(IntentRecognitionResult)

        # 构建消息
        messages = [
            ("system", self._build_system_prompt()),
        ]

        # 构建用户消息
        user_message = user_input
        if context:
            context_str = json.dumps(context, ensure_ascii=False)
            user_message = f"{user_input}\n\n上下文: {context_str}"

        messages.append(("human", user_message))

        try:
            # 调用 LLM
            result = await structured_llm.ainvoke(messages)
            return result
        except Exception as e:
            # 如果解析失败，返回默认结果
            return IntentRecognitionResult(
                primary_intent="unknown",
                secondary_intents=[],
                confidence=0.0,
                reasoning=f"识别失败: {str(e)}",
            )

    async def execute_agents(
        self,
        intent_result: IntentRecognitionResult,
        input_data: Any,
        context: Optional[Dict] = None,
    ) -> Dict[str, Any]:
        """
        执行识别出的 Agent

        Args:
            intent_result: 意图识别结果
            input_data: 输入数据
            context: 上下文信息

        Returns:
            执行结果字典 {agent_name: result}
        """
        results = {}

        # 收集需要执行的 Agent
        agents_to_execute = [intent_result.primary_intent]
        agents_to_execute.extend(intent_result.secondary_intents)

        # 过滤掉 "unknown"
        agents_to_execute = [name for name in agents_to_execute if name != "unknown"]

        if not agents_to_execute:
            return {
                "error": "No valid agents found for the intent",
                "intent": intent_result.model_dump(),
            }

        # 执行主要 Agent
        if intent_result.primary_intent != "unknown":
            primary_agent = self.registry.get_agent(intent_result.primary_intent)
            if primary_agent:
                try:
                    agent_instance = primary_agent()
                    results[
                        intent_result.primary_intent
                    ] = await agent_instance.execute(input_data, context)
                except Exception as e:
                    results[intent_result.primary_intent] = {"error": str(e)}

        # 并行执行次要 Agent
        if intent_result.secondary_intents:
            secondary_tasks = []
            for agent_name in intent_result.secondary_intents:
                if agent_name == "unknown":
                    continue

                agent = self.registry.get_agent(agent_name)
                if agent:
                    secondary_tasks.append(
                        self._execute_agent_task(agent_name, agent, input_data, context)
                    )

            # 并行执行
            if secondary_tasks:
                secondary_results = await asyncio.gather(
                    *secondary_tasks, return_exceptions=True
                )

                # 收集结果
                for agent_name, result in zip(
                    [n for n in intent_result.secondary_intents if n != "unknown"],
                    secondary_results,
                ):
                    if isinstance(result, Exception):
                        results[agent_name] = {"error": str(result)}
                    else:
                        results[agent_name] = result

        # 添加元数据
        results["_metadata"] = {
            "primary_intent": intent_result.primary_intent,
            "secondary_intents": intent_result.secondary_intents,
            "confidence": intent_result.confidence,
            "reasoning": intent_result.reasoning,
        }

        return results

    async def _execute_agent_task(
        self,
        agent_name: str,
        agent_class: type,
        input_data: Any,
        context: Optional[Dict],
    ) -> tuple:
        """
        执行单个 Agent 的辅助方法

        Args:
            agent_name: Agent 名称
            agent_class: Agent 类
            input_data: 输入数据
            context: 上下文信息

        Returns:
            (agent_name, result) 元组
        """
        try:
            agent_instance = agent_class()
            result = await agent_instance.execute(input_data, context)
            return (agent_name, result)
        except Exception as e:
            return (agent_name, {"error": str(e)})

    async def process(
        self,
        user_input: str,
        input_data: Any = None,
        context: Optional[Dict] = None,
    ) -> Dict[str, Any]:
        """
        完整的处理流程：意图识别 + Agent 执行

        Args:
            user_input: 用户输入
            input_data: 传递给 Agent 的输入数据（默认为 user_input）
            context: 上下文信息

        Returns:
            处理结果
        """
        # 如果没有指定 input_data，使用 user_input
        if input_data is None:
            input_data = user_input

        # 意图识别
        intent_result = await self.recognize_intent(user_input, context)

        # 执行 Agent
        execution_results = await self.execute_agents(
            intent_result, input_data, context
        )

        return execution_results
