"""
配置生成数据模型

定义 CI 配置和工作流配置的数据结构。
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List


class ConfigGenerationError(Exception):
    """配置生成失败异常

    当配置生成过程中发生错误时抛出。
    """

    def __init__(self, message: str, fix_suggestions: str | None = None) -> None:
        """
        Initialize ConfigGenerationError.

        Args:
            message: Error message
            fix_suggestions: Optional suggestions for fixing the error
        """
        self.fix_suggestions = fix_suggestions
        super().__init__(message)

    def __str__(self) -> str:
        """Return formatted error message with fix suggestions."""
        msg = super().__str__()
        if self.fix_suggestions:
            msg += f"\n\n{self.fix_suggestions}"
        return msg


class ProjectAnalysisError(Exception):
    """项目分析失败异常

    当项目分析过程中发生错误时抛出。
    """

    def __init__(self, message: str, fix_suggestions: str | None = None) -> None:
        """
        Initialize ProjectAnalysisError.

        Args:
            message: Error message
            fix_suggestions: Optional suggestions for fixing the error
        """
        self.fix_suggestions = fix_suggestions
        super().__init__(message)

    def __str__(self) -> str:
        """Return formatted error message with fix suggestions."""
        msg = super().__str__()
        if self.fix_suggestions:
            msg += f"\n\n{self.fix_suggestions}"
        return msg


class CIConfig(BaseModel):
    """CI 配置参数

    定义 GitHub Actions 工作流的基本配置。
    """

    ci_name: str = Field(default="CI", description="CI 工作流名称")
    on_push: bool = Field(default=True, description="是否在 push 时触发")
    on_pull_request: bool = Field(default=True, description="是否在 PR 时触发")
    branches: list[str] = Field(
        default_factory=lambda: ["main", "develop"], description="触发分支"
    )


class WorkflowConfig(BaseModel):
    """工作流配置

    包含所有语言和通用配置的工作流参数。
    """

    # CI 配置
    ci: CIConfig = Field(default_factory=CIConfig)

    # 语言版本
    python_version: str = Field(default="3.11", description="Python 版本")
    node_version: str = Field(default="20", description="Node.js 版本")
    go_version: str = Field(default="1.21", description="Go 版本")
    java_version: str = Field(default="17", description="Java 版本（Maven/Gradle）")

    # 缓存配置
    cache_enabled: bool = Field(default=True, description="是否启用缓存")
