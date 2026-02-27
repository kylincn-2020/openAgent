"""
项目分析 Agent

集成 ProjectAnalyzer 到 LangGraph 工作流，提供项目分析功能。
"""

from pathlib import Path
from typing import Optional

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from devops_agent.agent.base import Agent, AgentRegistry
from devops_agent.agent.state import AgentState
from devops_agent.analyzer import ProjectAnalyzer, print_project_table, print_error
from devops_agent.analyzer.analyzer import SUPPORTED_LANGUAGES
from devops_agent.cfg.models import ProjectAnalysisError
from devops_agent.cfg.output import format_error


# 支持的语言列表
SUPPORTED_LANGUAGES = ["Python", "Node.js", "Go", "Java"]


@AgentRegistry.register("analyze_project")
class ProjectAgent(Agent):
    """项目分析 Agent

    使用 ProjectAnalyzer 分析项目结构、依赖和构建命令。
    不使用 LLM，纯文件系统分析。
    """

    async def execute(self) -> AgentState:
        """执行项目分析

        分析当前目录的项目结构，返回分析结果。
        不使用 LLM，直接调用 ProjectAnalyzer。

        Returns:
            更新后的 AgentState
        """
        # 获取项目路径
        project_path = Path(self.get_context("project_path", Path.cwd()))

        try:
            # 创建分析器
            analyzer = ProjectAnalyzer(project_path)

            # 执行分析
            result = analyzer.analyze()

            # 分析成功，格式化响应
            self.state["response"] = self._format_success_message(result)
            # 更新上下文
            self.update_context("project_info", result.model_dump())

        except ProjectAnalysisError as e:
            # 项目分析错误（使用格式化的错误消息）
            print_error(e)
            error_message = f"{e}\n\n{e.fix_suggestions}" if hasattr(e, 'fix_suggestions') and e.fix_suggestions else str(e)
            self.add_error(error_message)
            self.state["response"] = error_message
            self.state["status"] = "error"
            self.state["error"] = {
                "type": "ProjectAnalysisError",
                "message": str(e),
            }

        except Exception as e:
            # 其他异常
            print_error(e, context="项目分析")
            error_message = f"项目分析失败: {type(e).__name__}"
            self.add_error(error_message)
            self.state["response"] = error_message
            self.state["status"] = "error"
            self.state["error"] = {
                "type": type(e).__name__,
                "message": "未预期的分析错误",
            }

        return self.state

    def _format_success_message(self, result) -> str:
        """格式化成功的分析结果

        Args:
            result: ProjectAnalysisResult

        Returns:
            格式化的文本消息（用于 LLM 上下文）
        """
        lines = [
            f"项目路径: {result.project_path}",
            f"主语言: {result.primary_language}",
            f"检测到 {len(result.languages)} 种语言",
        ]

        # 添加语言详情
        for lang_info in result.languages:
            lines.append(
                f"\n- {lang_info.language} ({lang_info.framework})"
                f"\n  依赖文件: {lang_info.dependency_file}"
                f"\n  构建: {lang_info.build_command}"
                f"\n  测试: {lang_info.test_command}"
            )

        # 添加子项目信息
        if result.subprojects:
            lines.append(f"\n检测到 {len(result.subprojects)} 个子项目:")
            for sub in result.subprojects:
                lines.append(f"  - {sub.project_path} ({sub.primary_language})")

        return "\n".join(lines)
