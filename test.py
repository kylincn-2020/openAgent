"""
功能测试脚本
直接测试 Agent 路由系统，无需启动 FastAPI 服务
"""
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent))

from app.core.models import InboundMessage
from app.core.context import build_conversation_key
from app.memory.session_store import SessionStore
from app.router.graph import build_router_graph


def test_code_agent():
    """测试代码生成 Agent"""
    print("\n=== 测试代码生成 Agent ===")

    # 创建测试消息
    msg = InboundMessage(
        tenant_id="test_tenant",
        channel="test",
        user_id="user1",
        session_id="session1",
        text="/code 帮我写一个快速排序算法"
    )

    # 构建会话键
    conversation_key = build_conversation_key(msg)

    # 执行路由图
    graph = build_router_graph()
    state = {"msg": msg, "history": []}
    result = graph.invoke(state)

    print(f"输入：{msg.text}")
    print(f"路由：{result.get('route')}")
    print(f"回答：{result.get('answer')}")

    return result


def test_doc_agent():
    """测试文档问答 Agent"""
    print("\n=== 测试文档问答 Agent ===")

    msg = InboundMessage(
        tenant_id="test_tenant",
        channel="test",
        user_id="user1",
        session_id="session1",
        text="/doc 什么是 RESTful API"
    )

    graph = build_router_graph()
    state = {"msg": msg, "history": []}
    result = graph.invoke(state)

    print(f"输入：{msg.text}")
    print(f"路由：{result.get('route')}")
    print(f"回答：{result.get('answer')}")

    return result


def test_task_agent():
    """测试任务查询 Agent"""
    print("\n=== 测试任务查询 Agent ===")

    msg = InboundMessage(
        tenant_id="test_tenant",
        channel="test",
        user_id="user1",
        session_id="session1",
        text="/task 查看当前任务进度"
    )

    graph = build_router_graph()
    state = {"msg": msg, "history": []}
    result = graph.invoke(state)

    print(f"输入：{msg.text}")
    print(f"路由：{result.get('route')}")
    print(f"回答：{result.get('answer')}")

    return result


def test_session_history():
    """测试会话历史功能"""
    print("\n=== 测试会话历史功能 ===")

    session_store = SessionStore()
    conversation_key = "tenant1:channel1:user1:session1"

    # 添加历史记录
    session_store.append_history(conversation_key, "user", "你好")
    session_store.append_history(conversation_key, "assistant", "有什么可以帮你？")
    session_store.append_history(conversation_key, "user", "帮我写代码")

    # 获取历史记录
    history = session_store.get_history(conversation_key)
    print(f"历史记录数量：{len(history)}")
    for h in history:
        print(f"  - {h['role']}: {h['content']}")

    return history


def test_session_isolation():
    """测试会话隔离功能"""
    print("\n=== 测试会话隔离功能 ===")

    session_store = SessionStore()

    # 会话 A
    key_a = "tenant1:channel1:userA:sessionA"
    session_store.append_history(key_a, "user", "用户 A 的消息")

    # 会话 B
    key_b = "tenant1:channel1:userB:sessionB"
    session_store.append_history(key_b, "user", "用户 B 的消息")

    # 验证隔离
    history_a = session_store.get_history(key_a)
    history_b = session_store.get_history(key_b)

    print(f"会话 A 历史：{history_a}")
    print(f"会话 B 历史：{history_b}")
    print(f"隔离正常：{len(history_a) == 1 and len(history_b) == 1}")

    return history_a, history_b


def test_natural_language():
    """测试自然语言输入（无命令前缀）"""
    print("\n=== 测试自然语言输入 ===")
    print("(需要 OPENAI_API_KEY 才能测试 LLM 意图识别)")


    test_cases = [
        "帮我写一个 Python 函数计算斐波那契数列",
        "解释一下什么是依赖注入",
        "我的任务完成得怎么样了",
    ]

    for text in test_cases:
        print(f"\n输入：{text}")
        msg = InboundMessage(
            tenant_id="test_tenant",
            channel="test",
            user_id="user1",
            session_id="session1",
            text=text
        )

        graph = build_router_graph()
        state = {"msg": msg, "history": []}
        result = graph.invoke(state)

        print(f"路由意图：{result.get('route', {}).get('intent')}")
        print(f"回答：{result.get('answer', 'N/A')[:100]}...")


def run_all_tests():
    """运行所有测试"""
    print("=" * 50)
    print("DevAgent MVP 功能测试")
    print("=" * 50)

    try:
        test_code_agent()
        test_doc_agent()
        test_task_agent()
        test_session_history()
        test_session_isolation()
        test_natural_language()

        print("\n" + "=" * 50)
        print("所有测试完成!")
        print("=" * 50)
    except Exception as e:
        print(f"\n测试失败：{e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    run_all_tests()
