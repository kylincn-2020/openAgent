"""
快速测试示例（不需要 API Key）
"""

import asyncio
import sys
from pathlib import Path

# 添加父目录到 Python 路径
current_dir = Path(__file__).parent
parent_dir = current_dir.parent.parent
sys.path.insert(0, str(parent_dir))

from langchain_agent.agents.agent_registry import (
    BaseSubAgent,
    AgentMetadata,
    register_agent,
    get_global_registry,
)


# 添加一个简单的测试 Agent
@register_agent(
    AgentMetadata(
        name="test_agent",
        description="测试 Agent",
        intent_keywords=["测试", "test"],
        priority=1,
        parallel_allowed=False,
    )
)
class TestAgent(BaseSubAgent):
    """测试 Agent"""

    async def execute(self, input_data, context=None):
        return {"status": "success", "data": str(input_data)}


async def test_basic_functionality():
    """测试基本功能"""
    print("=" * 50)
    print("测试 1: Agent 注册")
    print("=" * 50)

    # 获取注册表
    registry = get_global_registry()

    # 检查注册的 Agent
    print(f"\n已注册的 Agent 数量: {registry.count()}")

    all_metadata = registry.get_all_metadata()
    print("\n已注册的 Agent:")
    for metadata in all_metadata:
        print(f"  - {metadata.name}: {metadata.description}")
        print(f"    关键词: {', '.join(metadata.intent_keywords)}")
        print(f"    优先级: {metadata.priority}")

    # 测试关键词查找
    print("\n测试关键词查找:")
    matched = registry.find_by_keywords(["测试", "天气"])
    for metadata in matched:
        print(f"  匹配: {metadata.name}")

    print("\n" + "=" * 50)
    print("测试 2: Agent 执行")
    print("=" * 50)

    # 测试执行 Agent
    test_agent = registry.get_agent("test_agent")
    if test_agent:
        agent_instance = test_agent()
        result = await agent_instance.execute("测试数据", {"key": "value"})
        print(f"\n执行结果: {result}")

    print("\n" + "=" * 50)
    print("测试完成！")
    print("=" * 50)


if __name__ == "__main__":
    asyncio.run(test_basic_functionality())
