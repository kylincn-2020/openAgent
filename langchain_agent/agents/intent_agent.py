"""
意图识别 Agent（基于智谱 GLM-4.7 + LangChain OpenAI 兼容协议）
负责识别用户意图并路由到相应的子 Agent
"""

import asyncio
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
    使用智谱 GLM-4.7 和 LangChain OpenAI 兼容协议进行意图识别和路由
    """

    def __init__(
        self,
        model_name: str = "glm-4-plus",
        temperature: float = 0.0,
        registry=None,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
    ):
        """
        初始化意图识别 Agent

        Args:
            model_name: 使用的模型名称（智谱支持的模型：glm-4-flash, glm-4-plus, glm-4-air, glm-4-airx）
            temperature: 温度参数
            registry: Agent 注册表，默认使用全局注册表
            api_key: 智谱 API Key（可选，如果不提供则从环境变量读取）
            base_url: API 基础 URL（可选，默认使用智谱 OpenAI 兼容端点）
        """
        self.model_name = model_name
        self.temperature = temperature
        self.registry = registry or get_global_registry()

        # 智谱 OpenAI 兼容 API 配置
        self.base_url = base_url or "https://open.bigmodel.cn/api/paas/v4/"
        self.api_key = api_key

        # 初始化 LangChain ChatOpenAI（使用智谱的 OpenAI 兼容端点）
        self.llm = ChatOpenAI(
            model=self.model_name,
            api_key=self.api_key,
            base_url=self.base_url,
            temperature=self.temperature,
        )

        # 使用 with_structured_output 进行结构化输出
        self.structured_llm = self.llm.with_structured_output(IntentRecognitionResult)

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
        try:
            # 构建消息
            messages = [("system", self._build_system_prompt()), ("user", user_input)]

            # 使用 LangChain 的结构化输出进行意图识别
            result = await self.structured_llm.ainvoke(messages)

            return result

        except Exception as e:
            # 如果智谱 API 调用失败，使用关键词匹配作为备选方案
            return self._fallback_intent_recognition(user_input, context, str(e))

    def _fallback_intent_recognition(
        self, user_input: str, context: Optional[Dict], error: str
    ) -> IntentRecognitionResult:
        """
        备选的意图识别方案（关键词匹配）

        Args:
            user_input: 用户输入
            context: 上下文信息
            error: 原始错误信息

        Returns:
            意图识别结果
        """
        # 简单的关键词匹配
        user_text = (user_input + " " + str(context or "")).lower()
        words = user_text.split()

        # 获取所有 Agent 元数据
        agents_metadata = self.registry.get_all_metadata()

        # 匹配关键词
        matched = self._match_agents_by_keywords(words, agents_metadata)

        # 确定主要意图
        primary_intent = matched[0].name if matched else "unknown"

        # 确定次要意图（并行任务）
        secondary_intents = [
            agent.name for agent in matched[1:3] if agent.name != primary_intent
        ]

        # 置信度
        confidence = 0.8 if len(matched) > 0 else 0.3

        reasoning = f"基于关键词匹配，识别到 {len(matched)} 个相关 Agent：{', '.join([a.name for a in matched])}。API 调用失败，使用备选方案。"

        return IntentRecognitionResult(
            primary_intent=primary_intent,
            secondary_intents=secondary_intents,
            confidence=confidence,
            reasoning=reasoning,
        )

    def _match_agents_by_keywords(
        self, keywords: List[str], agents_metadata: List
    ) -> List:
        """
        根据关键词匹配相关的 Agent

        Args:
            keywords: 用户输入的关键词列表
            agents_metadata: 所有 Agent 元数据

        Returns:
            匹配的 Agent 列表
        """
        matched = []
        used_keywords = set()

        # 统一关键词（小写、去除空格）
        for kw in keywords:
            if kw.strip():
                used_keywords.add(kw.lower())

        # 为每个 Agent 匹配关键词
        for metadata in agents_metadata:
            score = 0
            for kw in metadata.intent_keywords:
                if kw.lower() in used_keywords:
                    score += 1

            if score > 0:
                matched.append((metadata, score))

        # 按分数和优先级降序排列
        matched.sort(key=lambda x: (x[1], x[0].priority), reverse=True)

        # 返回按优先级排序的 Agent 列表
        return [metadata for metadata, score in matched]

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
                "error": "No valid agents found for intent",
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
                import copy

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
