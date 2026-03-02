"""
写作助手 Agent - 示例子 agent
"""

from typing import Optional, Dict, Any
from core.base_agent import BaseAgent
from core.registry import registry


@registry.register(
    name="writing_assistant",
    description="写作助手，帮助撰写、编辑、润色各类文本，包括文章、邮件、报告等",
    category="writing",
    keywords=[
        "写作",
        "文章",
        "邮件",
        "报告",
        "润色",
        "编辑",
        "翻译",
        "文案",
        "内容",
        "博客",
        "文档",
        "改写",
        "摘要",
        "总结",
    ],
)
class WritingAgent(BaseAgent):
    """写作助手 Agent"""

    def get_system_prompt(self) -> str:
        return """你是一位专业的写作助手。你的职责：

1. **内容创作**: 根据主题撰写文章、邮件、报告等各类文本
2. **编辑润色**: 改进文字表达，提升可读性和专业性
3. **语法校对**: 纠正语法错误、拼写错误和标点问题
4. **风格调整**: 根据需求调整写作风格（正式、 casual、学术等）
5. **翻译服务**: 提供准确的中英文翻译
6. **摘要总结**: 提炼核心内容，生成简洁摘要

回答风格：
- 文字优美、表达清晰
- 注意语气和受众
- 保持逻辑连贯
- 必要时提供多个版本供选择
"""

    async def act(
        self, user_input: str, context: Optional[Dict[str, Any]] = None
    ) -> str:
        """处理写作相关请求"""
        system_prompt = self.get_system_prompt()

        messages = context.get("messages", []) if context else []

        response = await self._invoke_llm(
            messages=messages, system_prompt=system_prompt
        )

        return response
