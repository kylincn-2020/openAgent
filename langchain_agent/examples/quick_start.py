"""
快速开始示例
最简单的使用方式
"""

import asyncio
from langchain_agent.agents.example_agents import (
    WeatherAgent,
    TimeAgent,
    CalculationAgent,
)
from langchain_agent.agents.client_manager import get_client_manager


async def quick_start():
    """快速开始"""
    # 1. 导入示例子 Agent（自动注册）
    # from langchain_agent.agents.example_agents import *

    # 2. 获取 Client 管理器
    client_manager = get_client_manager()

    # 3. 获取或创建 Client（会自动缓存）
    client = client_manager.get_client(user_id="my_user", entry_point="my_app")

    # 4. 处理用户请求
    result = await client.process("北京今天的天气怎么样？")
    print("结果:", result)

    # 再次调用同一用户同一入口，会使用缓存的 Client
    result2 = await client.process("现在几点了？")
    print("结果2:", result2)


if __name__ == "__main__":
    asyncio.run(quick_start())
