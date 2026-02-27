"""
使用示例
展示如何使用 LangChain 意图识别 Agent 系统
"""

import asyncio
import sys
from langchain_agent.agents.client_manager import get_client_manager
from langchain_agent.agents.example_agents import (
    WeatherAgent,
    TimeAgent,
    CalculationAgent,
    NewsAgent,
    TranslationAgent,
)


async def example_basic_usage():
    """基础使用示例"""
    print("=" * 50)
    print("示例 1: 基础使用")
    print("=" * 50)

    # 获取 Client 管理器
    client_manager = get_client_manager()

    # 获取或创建 Client
    client = client_manager.get_client(user_id="user_001", entry_point="web_chat")

    # 处理用户请求
    user_input = "北京今天的天气怎么样？"
    print(f"\n用户输入: {user_input}")

    result = await client.process(user_input)

    print("\n处理结果:")
    print(result)

    # 查看缓存统计
    stats = client_manager.get_stats()
    print(f"\n缓存统计: {stats}")


async def example_parallel_execution():
    """并行执行示例"""
    print("\n" + "=" * 50)
    print("示例 2: 并行执行")
    print("=" * 50)

    client_manager = get_client_manager()
    client = client_manager.get_client(user_id="user_002", entry_point="mobile_app")

    # 涉及多个独立任务的请求
    user_input = "今天天气怎么样，现在几点了？"
    print(f"\n用户输入: {user_input}")

    result = await client.process(user_input)

    print("\n处理结果:")
    print(result)


async def example_multi_user():
    """多用户示例"""
    print("\n" + "=" * 50)
    print("示例 3: 多用户独立缓存")
    print("=" * 50)

    client_manager = get_client_manager()

    # 用户 A
    client_a = client_manager.get_client(user_id="user_a", entry_point="web")
    result_a = await client_a.process("上海天气如何？")
    print(f"\n用户 A (web) 结果: {result_a}")

    # 用户 B
    client_b = client_manager.get_client(user_id="user_b", entry_point="web")
    result_b = await client_b.process("现在几点了？")
    print(f"\n用户 B (web) 结果: {result_b}")

    # 同一用户，不同入口
    client_c = client_manager.get_client(user_id="user_a", entry_point="mobile")
    result_c = await client_c.process("计算 100 + 200")
    print(f"\n用户 A (mobile) 结果: {result_c}")

    stats = client_manager.get_stats()
    print(f"\n缓存统计: {stats}")


async def example_different_intents():
    """不同意图示例"""
    print("\n" + "=" * 50)
    print("示例 4: 不同意图测试")
    print("=" * 50)

    client_manager = get_client_manager()
    client = client_manager.get_client(user_id="test_user", entry_point="test")

    test_inputs = [
        "北京天气怎么样？",
        "现在几点了？",
        "帮我计算 100 + 50",
        "今天有什么新闻？",
        "把这句话翻译成英文：你好世界",
        "今天的天气和新闻",
    ]

    for user_input in test_inputs:
        print(f"\n用户输入: {user_input}")
        result = await client.process(user_input)
        print(f"主要意图: {result.get('_metadata', {}).get('primary_intent')}")
        print(f"置信度: {result.get('_metadata', {}).get('confidence')}")


async def example_cache_expiration():
    """缓存过期示例"""
    print("\n" + "=" * 50)
    print("示例 5: 缓存管理")
    print("=" * 50)

    client_manager = get_client_manager()

    # 创建多个 Client
    for i in range(3):
        client_manager.get_client(user_id=f"user_{i}", entry_point="test")

    print(f"\n当前缓存数量: {client_manager.get_stats()['total']}")

    # 清理过期缓存
    cleared = client_manager.clear_expired_clients()
    print(f"清理的缓存数量: {cleared}")

    # 移除特定 Client
    removed = client_manager.remove_client("user_0", "test")
    print(f"移除 user_0: {removed}")

    print(f"\n当前缓存统计: {client_manager.get_stats()}")


async def main():
    """主函数"""
    print("\n" + "=" * 50)
    print("LangChain 意图识别 Agent 系统示例")
    print("=" * 50)

    try:
        # 导入示例子 Agent（会自动注册）
        from langchain_agent.agents.example_agents import *

        # 运行示例
        await example_basic_usage()
        await example_parallel_execution()
        await example_multi_user()
        await example_different_intents()
        await example_cache_expiration()

        print("\n" + "=" * 50)
        print("所有示例运行完成！")
        print("=" * 50)

    except Exception as e:
        print(f"\n错误: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
