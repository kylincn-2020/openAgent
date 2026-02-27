"""
快速开始示例
最简单的使用方式
"""

import asyncio
import sys
from pathlib import Path

# 添加父目录到 Python 路径
current_dir = Path(__file__).parent
parent_dir = current_dir.parent.parent
sys.path.insert(0, str(parent_dir))

from langchain_agent.agents.example_agents import (
    WeatherAgent,
    TimeAgent,
    CalculationAgent,
)
from langchain_agent.agents.client_manager import get_client_manager


async def quick_start():
    """快速开始"""
    print("测试：导入模块成功！")
    print(
        f"注册的 Agent: {WeatherAgent._metadata.name}, {TimeAgent._metadata.name}, {CalculationAgent._metadata.name}"
    )


if __name__ == "__main__":
    asyncio.run(quick_start())
