"""
项目分析器数据模型

定义项目信息和分析结果的 Pydantic 模型，用于类型验证和序列化。
"""

from typing import Dict, List
from pydantic import BaseModel, Field


class ProjectInfo(BaseModel):
    """单个语言的项目信息

    包含项目的语言类型、框架、依赖文件、依赖列表、构建命令等信息。
    """
    language: str = Field(..., description="编程语言名称，如 Python, Node.js, Go, Java")
    framework: str = Field(default="unknown", description="框架名称，如 React, Flask, Express")
    dependency_file: str = Field(..., description="依赖文件名，如 requirements.txt, package.json")
    dependencies: List[str] = Field(default_factory=list, description="依赖包列表（直接依赖）")
    build_command: str = Field(default="未检测到", description="构建命令及说明")
    test_command: str = Field(default="未检测到", description="测试命令及说明")
    metadata: Dict[str, str] = Field(default_factory=dict, description="项目元数据（名称、版本等）")

    def __str__(self) -> str:
        """返回项目的简短描述"""
        return f"{self.language} 项目 ({self.dependency_file})"


class ProjectAnalysisResult(BaseModel):
    """完整的项目分析结果

    包含项目路径、主语言、所有检测到的语言信息以及 Monorepo 子项目。
    """
    project_path: str = Field(..., description="项目根目录的绝对路径")
    primary_language: str = Field(..., description="主语言（按标记文件数量判断）")
    languages: List[ProjectInfo] = Field(..., description="所有检测到的语言信息列表")
    subprojects: List["ProjectAnalysisResult"] = Field(
        default_factory=list,
        description="Monorepo 子项目列表"
    )

    def __str__(self) -> str:
        """返回分析结果的简短描述"""
        if self.subprojects:
            return f"{self.project_path} (主语言: {self.primary_language}, {len(self.languages)} 种语言, {len(self.subprojects)} 个子项目)"
        return f"{self.project_path} (主语言: {self.primary_language}, {len(self.languages)} 种语言)"


# 更新前向引用
ProjectAnalysisResult.model_rebuild()
