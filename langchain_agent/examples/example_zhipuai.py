# 智谱 GLM-4.7 集成示例
"""
本示例展示如何使用智谱 GLM-4.7 模型替代 OpenAI 进行意图识别
"""

import asyncio
from typing import Any, Dict, Optional

from langchain_agent.agents.client_manager import get_client_manager
from langchain_agent.agents.example_agents import (
    WeatherAgent,
    TimeAgent,
    CalculationAgent,
)


async def example_with_zhipuai():
    """使用智谱模型的示例"""
    print("=" * 60)
    print("智谱 GLM-4.7 集成示例")
    print("=" * 60)

    # 获取 Client 管理器
    client_manager = get_client_manager()

    # 创建使用智谱的 Client（指定模型名称）
    client = client_manager.get_client(
        user_id="zhipuai_user",
        entry_point="zhipuai_app",
        model_name="glm-4-plus",  # 使用智谱 GLM-4.7
        temperature=0.3,
    )

    # 测试意图识别
    user_inputs = [
        "今天天气怎么样？",
        "现在几点了？",
        "帮我计算 100 + 200",
        "把这句话翻译成英文：你好世界",
    ]

    for user_input in user_inputs:
        print(f"\n用户输入: {user_input}")
        result = await client.process(user_input)
        print(f"主要意图: {result.get('_metadata', {}).get('primary_intent')}")
        print(f"置信度: {result.get('_metadata', {}).get('confidence')}")
        print("-" * 40)

    print("\n" + "=" * 60)


async def main():
    """主函数"""
    try:
        await example_with_zhipuai()
    except Exception as e:
        print(f"错误: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
