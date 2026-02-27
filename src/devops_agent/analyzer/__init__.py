"""
项目分析器模块

提供项目类型检测、语言识别和依赖文件解析功能。
支持多语言项目和 Monorepo 结构的自动分析。
"""

from devops_agent.analyzer.models import ProjectInfo, ProjectAnalysisResult
from devops_agent.analyzer.detector import (
    find_project_root,
    detect_languages,
    determine_primary_language,
    is_valid_project,
    detect_monorepo,
)
from devops_agent.analyzer.parsers.python import PythonParser
from devops_agent.analyzer.parsers.nodejs import NodeJSParser
from devops_agent.analyzer.parsers.go import GoParser
from devops_agent.analyzer.parsers.java import JavaParser
from devops_agent.analyzer.analyzer import ProjectAnalyzer
from devops_agent.analyzer.output import (
    print_project_table,
    print_compact_view,
    print_json_output,
    print_analysis_result,
    print_error,
)

__all__ = [
    # Models
    "ProjectInfo",
    "ProjectAnalysisResult",
    # Detector functions
    "find_project_root",
    "detect_languages",
    "determine_primary_language",
    "is_valid_project",
    "detect_monorepo",
    # Parsers
    "PythonParser",
    "NodeJSParser",
    "GoParser",
    "JavaParser",
    # Analyzer
    "ProjectAnalyzer",
    # Output
    "print_project_table",
    "print_compact_view",
    "print_json_output",
    "print_analysis_result",
    "print_error",
]
