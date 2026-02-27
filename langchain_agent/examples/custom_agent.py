"""
添加自定义子 Agent 示例
展示如何快速注册新的子 Agent
"""

from langchain_agent.agents.agent_registry import (
    BaseSubAgent,
    AgentMetadata,
    register_agent,
    get_global_registry,
)
from typing import Any, Dict, Optional
import asyncio


@register_agent(
    AgentMetadata(
        name="joke_agent",
        description="讲笑话、幽默内容",
        intent_keywords=["笑话", "幽默", "逗", "搞笑", "开心"],
        priority=5,
        parallel_allowed=True,
        category="entertainment",
    )
)
class JokeAgent(BaseSubAgent):
    """笑话 Agent"""

    async def execute(
        self, input_data: Any, context: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """执行笑话任务"""
        jokes = [
            "为什么程序员总是分不清万圣节和圣诞节？因为 Oct 31 == Dec 25！",
            "有一个程序员去买包子，老板说：'你要几个包子？' 程序员说：'我要一个包子。' 老板：'还要别的吗？' 程序员：'一个包子，end。'",
            "为什么 Java 程序员戴眼镜？因为他们看不清 C#！",
        ]

        return {
            "joke": jokes[hash(str(input_data)) % len(jokes)],
            "agent": "joke_agent",
        }


@register_agent(
    AgentMetadata(
        name="quote_agent",
        description="提供励志名言、哲学语录",
        intent_keywords=["名言", "语录", "名言警句", "格言"],
        priority=6,
        parallel_allowed=True,
        category="entertainment",
    )
)
class QuoteAgent(BaseSubAgent):
    """名言 Agent"""

    async def execute(
        self, input_data: Any, context: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """执行名言任务"""
        quotes = [
            "生活不是等待风暴过去，而是学会在雨中跳舞。",
            "成功的秘诀在于坚持自己的目标和信念。",
            "每一个不曾起舞的日子，都是对生命的辜负。",
            "知之者不如好之者，好之者不如乐之者。",
        ]

        return {
            "quote": quotes[hash(str(input_data)) % len(quotes)],
            "agent": "quote_agent",
        }


# 测试自定义 Agent
async def test_custom_agents():
    """测试自定义 Agent"""
    from langchain_agent.agents.client_manager import get_client_manager

    client_manager = get_client_manager()
    client = client_manager.get_client(user_id="test_user", entry_point="test")

    # 测试笑话
    result1 = await client.process("给我讲个笑话")
    print("笑话结果:", result1)

    # 测试名言
    result2 = await client.process("给我一句名言")
    print("名言结果:", result2)

    # 查看注册的所有 Agent
    registry = get_global_registry()
    print(f"\n已注册的 Agent 数量: {registry.count()}")
    print("\n所有 Agent:")
    for metadata in registry.get_all_metadata():
        print(f"  - {metadata.name}: {metadata.description}")


if __name__ == "__main__":
    asyncio.run(test_custom_agents())
