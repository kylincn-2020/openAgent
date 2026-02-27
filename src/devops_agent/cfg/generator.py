"""
GitHub Actions 配置生成器

根据项目分析结果生成定制的 GitHub Actions 工作流配置。
"""

from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple
from functools import lru_cache

from devops_agent.analyzer.models import ProjectInfo, ProjectAnalysisResult
from devops_agent.cfg.models import WorkflowConfig, CIConfig
from devops_agent.cfg.templates import get_template
from devops_agent.cfg.validator import WorkflowValidator, WorkflowValidationError


class ConfigGenerator:
    """GitHub Actions 配置生成器

    根据项目分析结果生成定制的 GitHub Actions 工作流配置。
    支持多语言项目和缓存优化。
    """

    def __init__(
        self, analysis_result: ProjectAnalysisResult, config: Optional[WorkflowConfig] = None
    ):
        """初始化配置生成器

        Args:
            analysis_result: 项目分析结果
            config: 工作流配置（可选，使用默认配置）
        """
        self.analysis = analysis_result
        self.config = config or WorkflowConfig()
        self.validator = WorkflowValidator()

    def generate(self, language: Optional[str] = None) -> str:
        """生成 GitHub Actions 配置

        Args:
            language: 指定语言（None = 使用主语言）

        Returns:
            生成的 YAML 配置字符串
        """
        # 选择语言
        if language is None:
            language = self.analysis.primary_language

        # 查找对应的项目信息
        project_info = self._find_project_info(language)
        if project_info is None:
            raise ValueError(f"未找到 {language} 项目信息")

        # 规范化语言名称（例如 Node.js -> nodejs）
        template_language = self._normalize_language_name(language)

        # 获取模板（使用缓存）
        template = self._get_cached_template(template_language)

        # 构建模板变量
        variables = self._build_variables(project_info)

        # 渲染模板
        try:
            return template.format(**variables)
        except KeyError as e:
            raise ValueError(f"模板变量缺失: {e}") from e

    def generate_and_validate(
        self, language: Optional[str] = None
    ) -> Tuple[str, List[WorkflowValidationError]]:
        """生成并验证配置

        Args:
            language: 指定语言（None = 使用主语言）

        Returns:
            (生成的配置, 错误列表)
        """
        config = self.generate(language)
        errors = self.validator.validate(config)
        return config, errors

    def _find_project_info(self, language: str) -> Optional[ProjectInfo]:
        """查找指定语言的项目信息

        Args:
            language: 编程语言名称

        Returns:
            项目信息，如果未找到返回 None
        """
        language_lower = language.lower()

        for proj_info in self.analysis.languages:
            if proj_info.language.lower() == language_lower:
                return proj_info

        return None

    def _normalize_language_name(self, language: str) -> str:
        """规范化语言名称为模板目录名

        Args:
            language: 编程语言名称

        Returns:
            规范化后的语言名称
        """
        language_lower = language.lower()
        # 处理特殊语言名称映射
        language_map = {
            "node.js": "nodejs",
            "javascript": "nodejs",
        }
        return language_map.get(language_lower, language_lower)

    def _build_variables(self, project_info: ProjectInfo) -> Dict[str, Any]:
        """构建模板变量

        从 ProjectInfo 提取模板所需的变量。
        支持四种语言：Python, Node.js, Go, Java

        Args:
            project_info: 项目信息

        Returns:
            模板变量字典
        """
        variables = {
            # CI 配置
            "ci_name": self.config.ci.ci_name,
            # 依赖文件
            "cache_dependency_path": project_info.dependency_file,
            # 命令
            "install_command": self._format_install_command(project_info),
            "test_command": self._format_test_command(project_info),
        }

        # 语言特定变量
        if project_info.language == "Python":
            variables.update(
                {
                    "python_version": self._extract_python_version(project_info),
                    "build_step": self._format_build_step(project_info),
                }
            )
        elif project_info.language == "Node.js":
            variables.update(
                {
                    "node_version": self._extract_node_version(project_info),
                    "package_manager": self._detect_package_manager(project_info),
                    "build_step": self._format_build_step(project_info),
                }
            )
        elif project_info.language == "Go":
            variables.update(
                {
                    "go_version": self._extract_go_version(project_info),
                    "build_command": self._format_build_command(project_info),
                }
            )
        elif project_info.language == "Java":
            variables.update(
                {
                    "setup_step": self._format_java_setup(project_info),
                    "test_command": self._format_test_command(project_info),
                    "build_command": self._format_build_command(project_info),
                }
            )

        return variables

    def _extract_python_version(self, project_info: ProjectInfo) -> str:
        """提取 Python 版本

        Args:
            project_info: 项目信息

        Returns:
            Python 版本字符串
        """
        if project_info.metadata and "python_version" in project_info.metadata:
            return str(project_info.metadata["python_version"])
        return self.config.python_version

    def _extract_node_version(self, project_info: ProjectInfo) -> str:
        """提取 Node.js 版本

        Args:
            project_info: 项目信息

        Returns:
            Node.js 版本字符串
        """
        if project_info.metadata and "node_version" in project_info.metadata:
            return str(project_info.metadata["node_version"])
        return self.config.node_version

    def _extract_go_version(self, project_info: ProjectInfo) -> str:
        """提取 Go 版本

        Args:
            project_info: 项目信息

        Returns:
            Go 版本字符串
        """
        if project_info.metadata and "go_version" in project_info.metadata:
            return str(project_info.metadata["go_version"])
        return self.config.go_version

    def _detect_package_manager(self, project_info: ProjectInfo) -> str:
        """检测 Node.js 包管理器

        Args:
            project_info: 项目信息

        Returns:
            包管理器名称（npm, yarn, pnpm）
        """
        if project_info.metadata and "package_manager" in project_info.metadata:
            return str(project_info.metadata["package_manager"])

        # 根据锁文件检测
        dep_file = project_info.dependency_file or ""
        if "yarn.lock" in dep_file or "package-lock.json" not in dep_file:
            return "yarn"
        return "npm"

    def _format_install_command(self, project_info: ProjectInfo) -> str:
        """格式化安装命令

        Args:
            project_info: 项目信息

        Returns:
            安装命令字符串
        """
        # 使用检测到的安装命令，如果没有则使用默认值
        if project_info.build_command:
            return project_info.build_command

        # 根据语言提供默认值
        if project_info.language == "Python":
            return "pip install -r requirements.txt"
        elif project_info.language == "Node.js":
            return "npm install"
        elif project_info.language == "Go":
            return "go mod download"
        elif project_info.language == "Java":
            return "# 依赖由构建工具自动处理"
        return "# 未检测到安装命令"

    def _format_test_command(self, project_info: ProjectInfo) -> str:
        """格式化测试命令

        Args:
            project_info: 项目信息

        Returns:
            测试命令字符串
        """
        if project_info.test_command:
            return project_info.test_command

        # 根据语言提供默认值
        if project_info.language == "Python":
            return "pytest"
        elif project_info.language == "Node.js":
            return "npm test"
        elif project_info.language == "Go":
            return "go test ./..."
        elif project_info.language == "Java":
            return "# 未检测到测试命令"
        return "# 未检测到测试命令"

    def _format_build_command(self, project_info: ProjectInfo) -> str:
        """格式化构建命令

        对于 Go 和 Java，返回实际的构建命令（不使用 build_command 字段）。

        Args:
            project_info: 项目信息

        Returns:
            构建命令字符串
        """
        # 根据语言提供默认值
        if project_info.language == "Go":
            # Go 的构建命令总是 go build，不使用 build_command 字段
            return "go build ./..."
        elif project_info.language == "Java":
            # 对于 Java，尝试从 metadata 获取构建命令
            if project_info.metadata and "build_command" in project_info.metadata:
                return str(project_info.metadata["build_command"])
            # 根据构建工具提供默认值
            if project_info.metadata and "build_tool" in project_info.metadata:
                build_tool = project_info.metadata["build_tool"]
                if build_tool == "gradle":
                    return "./gradlew build"
                else:  # maven
                    return "mvn package"
            return "# 未检测到构建命令"
        return "# 未检测到构建命令"

    def _format_build_step(self, project_info: ProjectInfo) -> str:
        """格式化构建步骤（Python 和 Node.js）

        Args:
            project_info: 项目信息

        Returns:
            构建步骤 YAML 字符串
        """
        # 对于 Python 和 Node.js，构建步骤是可选的
        if project_info.build_command and project_info.language in ["Python", "Node.js"]:
            return f"""      # 构建项目
      - name: Build
        run: |
          {project_info.build_command}"""
        return ""

    def _format_java_setup(self, project_info: ProjectInfo) -> str:
        """格式化 Java 设置步骤

        Args:
            project_info: 项目信息

        Returns:
            设置步骤 YAML 字符串
        """
        # 检测构建工具类型（Maven 或 Gradle）
        build_tool = "maven"  # 默认
        if project_info.metadata and "build_tool" in project_info.metadata:
            build_tool = project_info.metadata["build_tool"]
        elif project_info.dependency_file:
            if "pom.xml" in project_info.dependency_file:
                build_tool = "maven"
            elif "build.gradle" in project_info.dependency_file:
                build_tool = "gradle"

        java_version = self.config.java_version

        if build_tool == "gradle":
            return f"""      # 设置 Java 环境（Gradle）
      - name: Set up Java
        uses: actions/setup-java@v4
        with:
          java-version: "{java_version}"
          distribution: "temurin"

      # 设置 Gradle 缓存
      - name: Setup Gradle
        uses: gradle/actions/setup-gradle@v3"""
        else:
            return f"""      # 设置 Java 环境（Maven）
      - name: Set up Java
        uses: actions/setup-java@v4
        with:
          java-version: "{java_version}"
          distribution: "temurin"
          cache: "maven" """

    @lru_cache(maxsize=32)
    def _get_cached_template(self, language: str) -> str:
        """获取缓存的模板（减少文件读取）

        Args:
            language: 编程语言

        Returns:
            模板内容字符串
        """
        return get_template(language)


def generate_workflow(
    analysis_result: ProjectAnalysisResult, language: Optional[str] = None
) -> str:
    """便捷函数：生成 GitHub Actions 工作流配置

    Args:
        analysis_result: 项目分析结果
        language: 指定语言（None = 使用主语言）

    Returns:
        生成的 YAML 配置字符串
    """
    generator = ConfigGenerator(analysis_result)
    return generator.generate(language)
