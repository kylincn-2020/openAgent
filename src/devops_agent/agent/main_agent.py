"""主 Agent 和意图识别系统"""

import re
from typing import Optional
from .base import Agent
from .state import AgentState
from ..llm import LLMClient
from ..llm.prompts import INTENT_RECOGNITION_PROMPT, format_prompt


class IntentRouter:
    """意图识别:规则预筛选 + LLM 确认

    使用混合模式进行意图识别:
    1. 第一阶段:规则快速匹配(关键词正则)
    2. 第二阶段:LLM 确认(当规则无法确定时)

    这种方式既保证了响应速度,又保持了 LLM 的灵活性。
    """

    # 规则预筛选:关键词匹配(按优先级顺序)
    RULES = {
        "generate_ci": [
            r"generate.*ci",
            r"create.*workflow",
            r"github actions?",
            r"gitlab ci",
            r"ci/cd",
            r"continuous integration",
            r"continuous deployment",
            r"ci config",
            r"pipeline",
            r"build.*config"
        ],
        "analyze_project": [
            r"analyze.*project",
            r"what.*language",
            r"check.*project",
            r"project.*type",
            r"detect.*framework",
            r"what.*framework",
            r"project.*structure"
        ],
        "update_config": [
            r"update.*config",
            r"change.*setting",
            r"modify.*configuration",
            r"edit.*config"
        ]
    }

    def __init__(self, llm_client: LLMClient):
        """初始化意图路由器

        Args:
            llm_client: LLM 客户端
        """
        self.llm = llm_client

    def route_by_rules(self, user_input: str) -> Optional[str]:
        """第一阶段:规则快速匹配

        使用正则表达式匹配关键词,快速识别常见意图。

        Args:
            user_input: 用户输入

        Returns:
            匹配的意图,如果未匹配则返回 None
        """
        input_lower = user_input.lower()
        for intent, patterns in self.RULES.items():
            for pattern in patterns:
                if re.search(pattern, input_lower):
                    return intent
        return None

    async def route_by_llm(self, user_input: str) -> str:
        """第二阶段:LLM 确认(当规则无法确定时)

        使用 LLM 进行更智能的意图识别。

        Args:
            user_input: 用户输入

        Returns:
            识别的意图
        """
        prompt = format_prompt(
            INTENT_RECOGNITION_PROMPT,
            user_input=user_input
        )
        response = await self.llm.complete(prompt)
        intent = response.strip().lower()

        # 验证返回的意图是否有效
        valid_intents = ["generate_ci", "analyze_project", "update_config", "unknown"]
        return intent if intent in valid_intents else "unknown"

    async def route(self, user_input: str) -> str:
        """混合路由:先规则,后 LLM

        Args:
            user_input: 用户输入

        Returns:
            识别的意图
        """
        # 第一阶段:规则预筛选
        rule_intent = self.route_by_rules(user_input)
        if rule_intent:
            return rule_intent

        # 第二阶段:LLM 确认
        return await self.route_by_llm(user_input)


class MainAgent(Agent):
    """主 Agent:接收用户输入,识别意图,分发任务,聚合响应

    作为系统的唯一入口,负责:
    1. 接收用户输入
    2. 识别用户意图
    3. 分发任务到相应的子 Agent
    4. 聚合子 Agent 的输出并格式化响应

    在当前阶段,子 Agent 尚未实现,因此只处理意图识别和占位响应。
    """

    def __init__(self, state: AgentState, llm_client: LLMClient):
        """初始化主 Agent

        Args:
            state: Agent 状态
            llm_client: LLM 客户端
        """
        super().__init__(state, llm_client)
        self.intent_router = IntentRouter(llm_client)

    async def execute(self) -> AgentState:
        """执行主 Agent 逻辑

        Returns:
            更新后的 AgentState
        """
        user_input = self.state['user_input']

        # 步骤 1: 意图识别
        self.state['intent'] = await self.intent_router.route(user_input)

        # 步骤 2: 根据意图分发任务(暂时只处理 unknown)
        if self.state['intent'] == 'unknown':
            self.state['response'] = self._format_unknown_response(user_input)
        else:
            # 其他意图暂时占位,等待子 Agent 实现
            self.state['response'] = self._format_placeholder_response(
                self.state['intent']
            )

        return self.state

    def _format_unknown_response(self, user_input: str) -> str:
        """格式化未知意图的响应

        Args:
            user_input: 用户输入

        Returns:
            友好的帮助消息
        """
        return f"I couldn't understand your request: '{user_input}'.\n\n" \
               f"I can help you with:\n" \
               f"- Generating CI/CD configurations (GitHub Actions, GitLab CI)\n" \
               f"- Analyzing your project structure\n" \
               f"- Updating configurations\n\n" \
               f"Please rephrase your request."

    def _format_placeholder_response(self, intent: str) -> str:
        """格式化占位响应(等待子 Agent 实现)

        Args:
            intent: 识别的意图

        Returns:
            占位消息
        """
        descriptions = {
            "generate_ci": "generate CI/CD configuration",
            "analyze_project": "analyze project structure",
            "update_config": "update configuration"
        }
        return f"I understood you want to {descriptions.get(intent, intent)}. " \
               f"This feature will be implemented in the next phase."
