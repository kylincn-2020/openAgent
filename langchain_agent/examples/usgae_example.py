"""
USGA 示例
展示如何自定义 USGA 相关的子 Agent
"""

import asyncio
from typing import Any, Dict, Optional
from datetime import datetime
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
from langchain_agent.agents.agent_registry import (
    BaseSubAgent,
    AgentMetadata,
    register_agent,
)
from langchain_agent.agents.client_manager import get_client_manager


@register_agent(
    AgentMetadata(
        name="usgae_agent",
        description="查询 USGA 相关信息",
        intent_keywords=["usga", "GCP", "云存储", "Blob", "存储"],
        priority=9,
        parallel_allowed=False,
        category="cloud",
    )
)
class USGAAgent(BaseSubAgent):
    """USGA 查询 Agent"""

    async def execute(
        self, input_data: Any, context: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """执行 USGA 查询"""
        await asyncio.sleep(0.3)

        input_str = str(input_data).lower()

        if "存储" in input_str or "bucket" in input_str:
            return {
                "service": "usgae_storage",
                "operation": "list_buckets",
                "message": "列出所有存储桶",
            }
        elif "数据" in input_str or "数据上传" in input_str:
            return {
                "service": "usgae_datastore",
                "operation": "query",
                "message": "查询数据",
            }
        else:
            return {
                "service": "usgae_taskqueue",
                "operation": "queue_task",
                "message": "队列任务",
            }


async def main():
    """主函数"""
    print("USGA Agent 测试")

    # 获取 Client
    client_manager = get_client_manager()
    client = client_manager.get_client(user_id="test_user", entry_point="usgae_app")

    # 测试 USGA 查询
    result = await client.process("列出所有存储桶")
    print("结果:", result)

    # 测试数据查询
    result2 = await client.process("查询用户数据")
    print("结果2:", result2)

    # 测试队列任务
    result3 = await client.process("创建队列任务")
    print("结果3:", result3)


if __name__ == "__main__":
    asyncio.run(main())
