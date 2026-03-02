"""
编程助手 Agent - 示例子 agent
"""

from typing import Optional, Dict, Any
from core.base_agent import BaseAgent
from core.registry import registry


@registry.register(
    name="coding_assistant",
    description="编程助手，帮助编写、调试、解释代码，支持多种编程语言",
    category="coding",
    keywords=[
        "代码",
        "编程",
        "debug",
        "python",
        "函数",
        "类",
        "算法",
        "javascript",
        "java",
        "c++",
        "web",
        "api",
        "bug",
        "错误",
    ],
)
class CodingAgent(BaseAgent):
    """编程助手 Agent"""

    def get_system_prompt(self) -> str:
        return """你是一位经验丰富的编程助手。你的职责：

1. **代码编写**: 根据需求编写清晰、高效、有注释的代码
2. **代码解释**: 解释代码的功能、原理和最佳实践
3. **调试帮助**: 帮助定位和修复 bug，解释错误原因
4. **代码审查**: 提供代码改进建议，指出潜在问题
5. **技术方案**: 提供技术选型和架构建议

回答风格：
- 代码示例要完整、可运行
- 解释要清晰、简洁
- 指出关键点和注意事项
- 如有多种方案，说明各自的优缺点
"""

    async def act(
        self, user_input: str, context: Optional[Dict[str, Any]] = None
    ) -> str:
        """处理编程相关问题"""
        system_prompt = self.get_system_prompt()

        messages = context.get("messages", []) if context else []

        response = await self._invoke_llm(
            messages=messages, system_prompt=system_prompt
        )

        return response
