import sys
from pathlib import Path

# 添加父目录到 Python 路径
current_dir = Path(__file__).parent
parent_dir = current_dir.parent.parent
sys.path.insert(0, str(parent_dir))

# 测试导入
try:
    from langchain_agent.agents.agent_registry import (
        AgentMetadata,
        register_agent,
        BaseSubAgent,
    )

    print("导入成功!")

    # 测试装饰器
    @register_agent(
        AgentMetadata(
            name="test_agent",
            description="测试Agent",
            intent_keywords=["test"],
            priority=1,
        )
    )
    class TestAgent(BaseSubAgent):
        async def execute(self, input_data, context):
            return {"result": "test"}

    print("装饰器应用成功!")
    print("TestAgent._metadata:", TestAgent._metadata)

except Exception as e:
    print(f"错误: {e}")
    import traceback

    traceback.print_exc()
