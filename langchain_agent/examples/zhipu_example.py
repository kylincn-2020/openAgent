"""
智谱 GLM-4.7 使用示例

本示例演示如何使用智谱 GLM-4.7 模型进行意图识别和 Agent 执行
使用 OpenAI 兼容协议
"""

import asyncio
import os
from dotenv import load_dotenv

# 导入示例子 Agent
from langchain_agent.agents.example_agents import (
    WeatherAgent,
    TimeAgent,
    CalculationAgent,
    NewsAgent,
    TranslationAgent,
)

# 导入核心组件
from langchain_agent.agents.client_manager import get_client_manager
from langchain_agent.agents.intent_agent import IntentRecognitionAgent


async def main():
    # 加载环境变量
    load_dotenv()

    # 获取配置
    api_key = os.getenv("ZHIPU_API_KEY")
    base_url = os.getenv("ZHIPU_BASE_URL", "https://open.bigmodel.cn/api/paas/v4/")
    model_name = os.getenv("DEFAULT_MODEL", "glm-4-plus")

    # 检查 API Key
    if not api_key:
        print("=" * 60)
        print("错误: 未设置 ZHIPU_API_KEY 环境变量")
        print("=" * 60)
        print("\n请按照以下步骤配置：")
        print("1. 复制 .env.example 为 .env")
        print("   cp .env.example .env")
        print("\n2. 编辑 .env 文件，填入你的智谱 API Key")
        print("   ZHIPU_API_KEY=your_api_key_here")
        print("\n3. 获取 API Key: https://open.bigmodel.cn/usercenter/apikeys")
        print("=" * 60)
        return

    print("=" * 60)
    print("智谱 GLM-4.7 意图识别 Agent 示例")
    print("=" * 60)
    print(f"模型: {model_name}")
    print(f"API 端点: {base_url}")
    print("=" * 60)
    print()

    # 示例 1: 直接使用 IntentRecognitionAgent
    print("示例 1: 直接使用 IntentRecognitionAgent")
    print("-" * 60)

    agent = IntentRecognitionAgent(
        model_name=model_name, api_key=api_key, base_url=base_url, temperature=0.0
    )

    # 测试意图识别
    test_inputs = [
        "北京今天的天气怎么样？",
        "现在几点了？",
        "帮我计算 234 * 567",
        "今天的新闻有哪些？",
        "把这句话翻译成英语",
    ]

    for i, user_input in enumerate(test_inputs, 1):
        print(f"\n测试 {i}: {user_input}")
        try:
            # 意图识别
            intent_result = await agent.recognize_intent(user_input)
            print(f"  主要意图: {intent_result.primary_intent}")
            print(f"  次要意图: {intent_result.secondary_intents}")
            print(f"  置信度: {intent_result.confidence:.2f}")
            print(f"  推理: {intent_result.reasoning}")
        except Exception as e:
            print(f"  错误: {str(e)}")

    print("\n" + "=" * 60)
    print("示例 2: 使用 Client 管理器")
    print("-" * 60)

    # 使用 Client 管理器（支持缓存）
    client_manager = get_client_manager()

    # 获取或创建 Client（会自动缓存）
    client = client_manager.get_client(
        user_id="user_001",
        entry_point="demo",
        model_name=model_name,
        api_key=api_key,
        base_url=base_url,
    )

    print("\n处理用户请求:")
    print("-" * 60)

    # 测试完整流程
    request = "帮我计算 123 + 456，同时告诉我现在几点了"
    print(f"用户输入: {request}")

    result = await client.process(request)

    print("\n执行结果:")
    print("-" * 60)
    for key, value in result.items():
        if key.startswith("_"):
            continue
        print(f"  {key}: {value}")

    if "_metadata" in result:
        print("\n元数据:")
        print("-" * 60)
        for key, value in result["_metadata"].items():
            print(f"  {key}: {value}")

    # 查看缓存统计
    print("\n" + "=" * 60)
    print("缓存统计:")
    print("-" * 60)
    stats = client_manager.get_stats()
    print(f"  缓存 Client 数量: {stats['total_clients']}")
    print(f"  过期 Client 数量: {stats['expired_clients']}")
    print(f"  活跃 Client 数量: {stats['active_clients']}")

    print("\n" + "=" * 60)
    print("示例完成！")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
