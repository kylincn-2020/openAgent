"""
项目分析器协调器

整合检测器和解析器，提供完整的项目分析功能。
支持多语言项目、Monorepo 结构检测和友好的错误处理。
"""

from pathlib import Path
from typing import List, Optional, Dict, Any

from devops_agent.analyzer.detector import (
    find_project_root,
    detect_languages,
    determine_primary_language,
    detect_monorepo,
)
from devops_agent.analyzer.models import ProjectInfo, ProjectAnalysisResult
from devops_agent.analyzer.parsers import (
    PythonParser,
    NodeJSParser,
    GoParser,
    JavaParser,
)
from devops_agent.cfg.models import ProjectAnalysisError


# 支持的语言列表
SUPPORTED_LANGUAGES = ["Python", "Node.js", "Go", "Java"]

# 语言名称映射（detector.py 使用小写，这里需要映射）
LANGUAGE_NAME_MAP = {
    "python": "Python",
    "nodejs": "Node.js",
    "go": "Go",
    "java": "Java",
}


# 错误消息字典
_ANALYSIS_ERROR_MESSAGES: Dict[str, Dict[str, Any]] = {
    "no_git_dir": {
        "description": "未找到项目根目录",
        "suggestions": [
            "请在包含 .git 目录的项目根目录中运行此工具",
            "使用 `git init` 初始化 Git 仓库",
            "切换到项目根目录后重试",
        ],
    },
    "unrecognized_language": {
        "description": "无法识别项目类型",
        "suggestions": [
            f"支持的语言: {', '.join(SUPPORTED_LANGUAGES)}",
            "请确保项目根目录包含对应的依赖文件（如 requirements.txt、package.json 等）",
            "检查文件名是否正确",
        ],
    },
    "parse_error": {
        "description": "解析依赖文件失败",
        "suggestions": [
            "检查文件格式是否正确",
            "确保文件没有损坏",
            "尝试恢复备份文件",
            "检查文件编码是否为 UTF-8",
        ],
    },
}


# 支持的语言列表
SUPPORTED_LANGUAGES = ["Python", "Node.js", "Go", "Java"]

# 语言名称映射（detector.py 使用小写，这里需要映射）
LANGUAGE_NAME_MAP = {
    "python": "Python",
    "nodejs": "Node.js",
    "go": "Go",
    "java": "Java",
}


class ProjectAnalyzer:
    """项目分析器协调器

    整合检测器和解析器，提供完整的项目分析功能。
    支持多语言项目、Monorepo 结构检测和友好的错误处理。
    """

    def __init__(self, project_root: Path):
        """初始化项目分析器

        Args:
            project_root: 项目根目录路径
        """
        self.project_root = project_root
        # 初始化所有解析器
        self.parsers = {
            "Python": PythonParser(),
            "Node.js": NodeJSParser(),
            "Go": GoParser(),
            "Java": JavaParser(),
        }

    def analyze(self) -> ProjectAnalysisResult:
        """分析项目

        检测项目类型、解析依赖文件、推断构建命令。
        支持多语言项目和 Monorepo 结构。

        Returns:
            项目分析结果

        Raises:
            ProjectAnalysisError: 当项目分析失败时
        """
        # 查找项目根目录
        root = find_project_root(self.project_root)
        if root is None:
            error_info = _ANALYSIS_ERROR_MESSAGES["no_git_dir"]
            raise ProjectAnalysisError(
                error_info["description"],
                fix_suggestions="\n".join(error_info["suggestions"])
            )

        # 检测语言
        detected = detect_languages(root)
        if not detected:
            error_info = _ANALYSIS_ERROR_MESSAGES["unrecognized_language"]
            raise ProjectAnalysisError(
                error_info["description"],
                fix_suggestions="\n".join(error_info["suggestions"])
            )

        # 检测 Monorepo 子项目
        subproject_paths = detect_monorepo(root)

        # 解析每种语言的项目信息
        languages: List[ProjectInfo] = []
        for lang_key, marker_files in detected.items():
            # 获取解析器
            parser = self._get_parser(lang_key)
            if parser is None:
                continue

            # 解析每个标记文件
            for marker_file in marker_files:
                marker_path = root / marker_file
                if not marker_path.exists():
                    continue

                try:
                    # 解析项目信息
                    project_info = parser.parse(root, marker_path)
                    languages.append(project_info)
                except Exception as e:
                    # 解析失败时，创建基本的项目信息
                    error_info = _ANALYSIS_ERROR_MESSAGES["parse_error"]
                    print(f"[yellow]警告: 无法解析 {marker_file}: {e}[/yellow]")
                    print(f"[dim]  建议: {error_info['suggestions'][0]}[/dim]")
                    languages.append(
                        ProjectInfo(
                            language=LANGUAGE_NAME_MAP.get(lang_key, lang_key.title()),
                            dependency_file=marker_file,
                        )
                    )

        # 分析子项目（Monorepo）
        subprojects: List[ProjectAnalysisResult] = []
        for subproject_path in subproject_paths:
            try:
                # 递归分析子项目
                sub_analyzer = ProjectAnalyzer(subproject_path)
                sub_result = sub_analyzer.analyze()

                # 只添加成功解析的子项目
                if sub_result.languages:
                    subprojects.append(sub_result)
            except Exception as e:
                print(f"[yellow]警告: 无法分析子项目 {subproject_path}: {e}[/yellow]")
                continue

        # 确定主语言
        primary_language = determine_primary_language(detected)
        primary_language = LANGUAGE_NAME_MAP.get(
            primary_language, primary_language.title()
        )

        # 创建分析结果
        return ProjectAnalysisResult(
            project_path=str(root),
            primary_language=primary_language,
            languages=languages,
            subprojects=subprojects,
        )

    def _get_parser(self, language_key: str):
        """根据语言键获取解析器

        Args:
            language_key: 语言键（python, nodejs, go, java）

        Returns:
            对应的解析器实例，如果语言不支持则返回 None
        """
        language_name = LANGUAGE_NAME_MAP.get(language_key)
        if language_name is None:
            return None
        return self.parsers.get(language_name)
