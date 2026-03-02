"""
测试模块 - 测试多 Agent 系统核心功能
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

from core.registry import registry, AgentRegistry
from core.session_manager import SessionManager, Session
from agents.coding_agent import CodingAgent
from agents.writing_agent import WritingAgent
from agents.analysis_agent import AnalysisAgent


class TestAgentRegistry:
    """测试 Agent 注册系统"""

    def test_singleton(self):
        """测试单例模式"""
        reg1 = AgentRegistry()
        reg2 = AgentRegistry()
        assert reg1 is reg2

    def test_get_all_agents(self):
        """测试获取所有 agents"""
        agents = registry.get_all_agents()
        assert len(agents) >= 3  # 至少有 3 个示例子 agent
        assert "coding_assistant" in agents
        assert "writing_assistant" in agents
        assert "analysis_agent" in agents

    def test_get_agent_by_name(self):
        """测试按名称获取 agent"""
        agent = registry.get_agent("coding_assistant")
        assert agent is not None
        assert agent.name == "coding_assistant"
        assert agent.category == "coding"

    def test_get_agents_by_category(self):
        """测试按分类获取 agents"""
        agents = registry.get_agents_by_category("coding")
        assert len(agents) >= 1
        assert all(a.category == "coding" for a in agents)

    def test_find_best_match(self):
        """测试关键词匹配"""
        # 测试代码相关关键词
        match = registry.find_best_match("帮我写个 Python 函数")
        assert match == "coding_assistant"

        # 测试写作相关关键词
        match = registry.find_best_match("帮我写一篇文章")
        assert match == "writing_assistant"

        # 测试数据分析相关关键词
        match = registry.find_best_match("分析这个数据")
        assert match == "analysis_agent"

    def test_get_intent_prompt(self):
        """测试生成意图提示"""
        prompt = registry.get_intent_prompt()
        assert "可用的专业助手：" in prompt
        assert "coding_assistant" in prompt
        assert "writing_assistant" in prompt


class TestSessionManager:
    """测试会话管理器"""

    @pytest.fixture
    def session_manager(self):
        """创建测试用的会话管理器"""
        return SessionManager(timeout_minutes=1)  # 1 分钟超时用于测试

    def test_get_or_create_session(self, session_manager):
        """测试获取或创建会话"""
        session = session_manager.get_or_create_session("user123")
        assert session is not None
        assert session.user_id == "user123"
        assert session.session_id is not None

    def test_session_reuse(self, session_manager):
        """测试会话复用"""
        session1 = session_manager.get_or_create_session("user123")
        session2 = session_manager.get_or_create_session("user123")
        assert session1.session_id == session2.session_id

    def test_session_expiration(self, session_manager):
        """测试会话过期"""
        session = session_manager.get_or_create_session("user123")
        assert not session.is_expired(1)  # 刚创建，未过期

        # 模拟过期
        from datetime import datetime, timedelta

        session.last_active_at = datetime.now() - timedelta(minutes=2)
        assert session.is_expired(1)  # 已过期

    def test_delete_session(self, session_manager):
        """测试删除会话"""
        session = session_manager.get_or_create_session("user123")
        session_id = session.session_id

        # 删除会话
        asyncio.run(session_manager.delete_session(session_id))

        # 验证已删除
        retrieved = session_manager.get_session(session_id)
        assert retrieved is None

    def test_add_message(self, session_manager):
        """测试添加消息"""
        session = session_manager.get_or_create_session("user123")
        session.add_message("user", "你好")
        session.add_message("assistant", "你好！有什么可以帮助你的？")

        assert len(session.message_history) == 2
        assert session.message_history[0].content == "你好"

    def test_get_recent_messages(self, session_manager):
        """测试获取最近消息"""
        session = session_manager.get_or_create_session("user123")

        # 添加 15 条消息
        for i in range(15):
            session.add_message("user", f"消息{i}")

        # 获取最近 10 条
        recent = session.get_recent_messages(limit=10)
        assert len(recent) == 10
        assert recent[-1].content == "消息 14"


class TestSubAgents:
    """测试子 Agent"""

    def test_coding_agent_metadata(self):
        """测试编程助手元数据"""
        agent = CodingAgent()
        assert agent.name == "coding_assistant"
        assert "代码" in agent.agent_metadata.keywords

    def test_writing_agent_metadata(self):
        """测试写作助手元数据"""
        agent = WritingAgent()
        assert agent.name == "writing_assistant"
        assert "写作" in agent.agent_metadata.keywords

    def test_analysis_agent_metadata(self):
        """测试数据分析助手元数据"""
        agent = AnalysisAgent()
        assert agent.name == "analysis_agent"
        assert "数据" in agent.agent_metadata.keywords

    @pytest.mark.asyncio
    async def test_coding_agent_act(self):
        """测试编程助手执行"""
        agent = CodingAgent()

        # Mock LLM
        mock_llm = AsyncMock()
        mock_llm.ainvoke = AsyncMock(
            return_value=MagicMock(content="这是一个 Python 函数示例")
        )
        agent.llm = mock_llm

        # 执行
        response = await agent.act("帮我写个函数")
        assert response is not None
        assert mock_llm.ainvoke.called


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
