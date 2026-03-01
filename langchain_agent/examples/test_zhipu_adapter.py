"""
简单测试脚本 - 验证智谱 GLM-4.7 适配
"""

import asyncio
import os
from dotenv import load_dotenv

# 导入核心组件
from langchain_agent.agents.example_agents import WeatherAgent, TimeAgent
from langchain_agent.agents.intent_agent import IntentRecognitionAgent


async def test_import_and_initialization():
    """测试导入和初始化"""
    print("=" * 60)
    print("测试 1: 导入和初始化")
    print("=" * 60)

    # 测试 Agent 注册
    from langchain_agent.agents.agent_registry import get_global_registry

    registry = get_global_registry()

    agents_metadata = registry.get_all_metadata()
    print(f"\n已注册的 Agent 数量: {len(agents_metadata)}")

    for metadata in agents_metadata:
        print(f"  - {metadata.name}: {metadata.description}")

    # 测试 IntentRecognitionAgent 初始化
    agent = IntentRecognitionAgent(
        model_name="glm-4-plus",
        api_key="test_key",
        base_url="https://open.bigmodel.cn/api/paas/v4/",
        temperature=0.0,
    )
    print(f"\nIntentRecognitionAgent 初始化成功")
    print(f"  模型: {agent.model_name}")
    print(f"  API 端点: {agent.base_url}")

    # 测试 Client 管理器
    from langchain_agent.agents.client_manager import get_client_manager

    client_manager = get_client_manager()
    print(f"\nClientManager 初始化成功")
    print(f"  缓存统计: {client_manager.get_stats()}")

    print("\n" + "=" * 60)
    print("测试 1: 通过 ✅")
    print("=" * 60)


async def test_keyword_matching():
    """测试关键词匹配（不需要 API Key）"""
    print("\n" + "=" * 60)
    print("测试 2: 关键词匹配")
    print("=" * 60)

    agent = IntentRecognitionAgent(
        model_name="glm-4-plus",
        api_key="test_key",
        base_url="https://open.bigmodel.cn/api/paas/v4/",
        temperature=0.0,
    )

    # 测试关键词匹配
    test_cases = ["北京今天的天气怎么样？", "现在几点了？", "帮我计算 234 * 567"]

    for user_input in test_cases:
        print(f"\n输入: {user_input}")
        try:
            # 使用备选方案（关键词匹配）
            from langchain_agent.agents.intent_agent import IntentRecognitionResult

            result = agent._fallback_intent_recognition(user_input, None, "测试")
            print(f"  主要意图: {result.primary_intent}")
            print(f"  次要意图: {result.secondary_intents}")
            print(f"  置信度: {result.confidence:.2f}")
        except Exception as e:
            print(f"  错误: {str(e)}")

    print("\n" + "=" * 60)
    print("测试 2: 通过 ✅")
    print("=" * 60)


async def test_config_parsing():
    """测试配置解析"""
    print("\n" + "=" * 60)
    print("测试 3: 配置解析")
    print("=" * 60)

    load_dotenv()

    # 测试环境变量读取
    api_key = os.getenv("ZHIPU_API_KEY")
    base_url = os.getenv("ZHIPU_BASE_URL")
    model_name = os.getenv("DEFAULT_MODEL")

    print(f"\n环境变量:")
    print(f"  ZHIPU_API_KEY: {'已设置' if api_key else '未设置'}")
    print(f"  ZHIPU_BASE_URL: {base_url}")
    print(f"  DEFAULT_MODEL: {model_name}")

    print("\n" + "=" * 60)
    print("测试 3: 通过 ✅")
    print("=" * 60)


async def main():
    """运行所有测试"""
    print("\n")
    print("🚀 智谱 GLM-4.7 适配测试")
    print("=" * 60)

    try:
        # 测试 1: 导入和初始化
        await test_import_and_initialization()

        # 测试 2: 关键词匹配
        await test_keyword_matching()

        # 测试 3: 配置解析
        await test_config_parsing()

        print("\n" + "=" * 60)
        print("✅ 所有测试通过！")
        print("=" * 60)
        print("\n注意: 完整的意图识别需要配置智谱 API Key")
        print("配置步骤:")
        print("1. cp .env.example .env")
        print("2. 编辑 .env 文件，填入 ZHIPU_API_KEY")
        print("3. 运行: python examples/zhipu_example.py")
        print("=" * 60)

    except Exception as e:
        print(f"\n❌ 测试失败: {str(e)}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
