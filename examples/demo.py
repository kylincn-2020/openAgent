"""
使用示例 - 演示如何使用多 Agent 系统
"""

import asyncio
from agents import IntentAgent
from core.session_manager import SessionManager


async def demo_chat():
    """演示聊天流程"""
    print("=" * 60)
    print("多 Agent 系统演示")
    print("=" * 60)

    # 创建 intent agent
    intent_agent = IntentAgent()

    # 创建会话管理器
    session_manager = SessionManager(timeout_minutes=30)

    # 模拟用户对话
    test_cases = [
        "帮我写一个 Python 函数，计算斐波那契数列",
        "帮我写一封感谢邮件给客户",
        "分析一下这个销售数据的增长趋势",
        "你好啊",  # 测试模糊意图
    ]

    user_id = "demo_user"

    for i, message in enumerate(test_cases, 1):
        print(f"\n[用户] 问题 {i}: {message}")

        # 获取或创建会话
        session = session_manager.get_or_create_session(user_id)

        # 准备上下文
        context = {"messages": session.get_recent_messages(limit=10)}

        # 调用 intent agent
        response = await intent_agent.act(message, context)

        print(f"[助手] 响应：{response}")

        # 更新会话历史
        session.add_message("user", message)
        session.add_message("assistant", response)

        # 显示会话信息
        print(
            f"[会话] ID: {session.session_id}, 消息数：{len(session.message_history)}"
        )

    # 显示统计
    print("\n" + "=" * 60)
    print("会话统计:")
    stats = session_manager.get_stats()
    print(f"  总会话数：{stats['total_sessions']}")
    print(f"  活跃会话：{stats['active_sessions']}")
    print(f"  唯一用户：{stats['unique_users']}")

    # 显示注册的 agents
    from core.registry import registry

    print("\n已注册的 Agents:")
    for name, metadata in registry.get_all_agents().items():
        print(f"  - {name} ({metadata.category})")
        print(f"    描述：{metadata.description}")
        print(f"    关键词：{', '.join(metadata.keywords[:5])}...")


async def demo_api_usage():
    """演示 API 调用方式"""
    import httpx

    print("\n" + "=" * 60)
    print("API 调用示例")
    print("=" * 60)

    base_url = "http://localhost:8000"

    # 1. 发送聊天请求
    print("\n[1] 发送聊天请求...")
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{base_url}/chat",
            json={"message": "帮我写个 hello world 函数", "user_id": "api_user"},
        )
        result = response.json()
        print(f"响应：{result['response'][:100]}...")
        print(f"会话 ID: {result['session_id']}")

        # 2. 查看会话信息
        print("\n[2] 查看会话信息...")
        response = await client.get(f"{base_url}/session/{result['session_id']}")
        session_info = response.json()
        print(f"会话信息：{session_info}")

        # 3. 查看所有 agents
        print("\n[3] 查看所有 agents...")
        response = await client.get(f"{base_url}/agents")
        agents = response.json()
        print(f"可用 agents: {[a['name'] for a in agents['agents']]}")

        # 4. 查看统计
        print("\n[4] 查看统计信息...")
        response = await client.get(f"{base_url}/sessions")
        stats = response.json()
        print(f"统计：{stats['sessions']}")


if __name__ == "__main__":
    # 运行演示
    print("选择演示模式:")
    print("1. 直接调用演示 (不需要启动服务)")
    print("2. API 调用演示 (需要先启动服务)")
    print()

    choice = input("请输入选择 (1/2): ").strip()

    if choice == "1":
        asyncio.run(demo_chat())
    elif choice == "2":
        asyncio.run(demo_api_usage())
    else:
        print("无效选择，运行直接调用演示...")
        asyncio.run(demo_chat())
