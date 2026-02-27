"""
Python 项目解析器

解析 requirements.txt、pyproject.toml、setup.py 等依赖文件。
"""

import re
from abc import ABC, abstractmethod
from pathlib import Path
from typing import List

from devops_agent.analyzer.models import ProjectInfo


class BaseParser(ABC):
    """解析器基类（策略模式）"""

    @abstractmethod
    def can_parse(self, marker_file: Path) -> bool:
        """判断是否能解析该文件"""
        pass

    @abstractmethod
    def parse(self, project_root: Path, marker_file: Path) -> ProjectInfo:
        """解析项目信息"""
        pass


class PythonParser(BaseParser):
    """Python 项目解析器"""

    MARKER_FILES = ["requirements.txt", "pyproject.toml", "setup.py", "Pipfile"]

    def can_parse(self, marker_file: Path) -> bool:
        """判断是否能解析该文件"""
        return marker_file.name in self.MARKER_FILES

    def parse(self, project_root: Path, marker_file: Path) -> ProjectInfo:
        """解析 Python 项目"""
        if marker_file.name == "requirements.txt":
            return self._parse_requirements(project_root, marker_file)
        elif marker_file.name == "pyproject.toml":
            return self._parse_pyproject(project_root, marker_file)
        elif marker_file.name == "setup.py":
            return self._parse_setup(project_root, marker_file)
        elif marker_file.name == "Pipfile":
            return self._parse_pipfile(project_root, marker_file)
        else:
            return ProjectInfo(
                language="Python",
                dependency_file=str(marker_file.name),
            )

    def _parse_requirements(
        self, project_root: Path, file: Path
    ) -> ProjectInfo:
        """解析 requirements.txt"""
        deps = []
        try:
            with open(file, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    # 跳过注释和空行
                    if not line or line.startswith("#"):
                        continue
                    # 提取包名（忽略版本说明：>=, ==, <=, ~=, <, >）
                    pkg_name = (
                        line.split(">=")[0]
                        .split("==")[0]
                        .split("<=")[0]
                        .split("~=")[0]
                        .split("<")[0]
                        .split(">")[0]
                        .strip()
                    )
                    if pkg_name:
                        deps.append(pkg_name)
        except FileNotFoundError:
            return ProjectInfo(
                language="Python",
                dependency_file=str(file.name),
            )
        except Exception as e:
            print(f"[yellow]警告: 无法解析 {file}: {e}[/yellow]")
            return ProjectInfo(
                language="Python",
                dependency_file=str(file.name),
            )

        # 推断构建命令
        build_cmd = "pip install -r requirements.txt"

        # 推断测试命令
        test_cmd = "未检测到"
        if (project_root / "pytest.ini").exists():
            test_cmd = "pytest"
        elif (project_root / "tests").exists():
            test_cmd = "pytest"
        elif any("pytest" in dep for dep in deps):
            test_cmd = "pytest"

        return ProjectInfo(
            language="Python",
            framework=self._detect_framework(deps),
            dependency_file=str(file.name),
            dependencies=deps,
            build_command=f"{build_cmd} - 安装依赖",
            test_command=f"{test_cmd} - 运行测试" if test_cmd != "未检测到" else "未检测到",
            metadata={},
        )

    def _parse_pyproject(
        self, project_root: Path, file: Path
    ) -> ProjectInfo:
        """解析 pyproject.toml"""
        try:
            # 优先使用标准库 tomllib (Python 3.11+)
            try:
                import tomllib
            except ImportError:
                import tomli as tomllib

            with open(file, "rb") as f:
                data = tomllib.load(f)

            # 提取项目元数据
            project = data.get("project", {})
            deps = project.get("dependencies", [])

            # 检测构建系统
            build_system = data.get("build-system", {})
            backend = build_system.get("build-backend", "")

            # 推断构建命令
            if "poetry" in backend.lower():
                build_cmd = "poetry install"
            elif "pip" in backend.lower() or "setuptools" in backend.lower():
                build_cmd = "pip install -e ."
            else:
                build_cmd = "pip install -e ."

            # 推断测试命令
            test_cmd = "未检测到"
            if any("pytest" in str(d) for d in deps):
                test_cmd = "pytest"
            elif (project_root / "tests").exists():
                test_cmd = "pytest"

            return ProjectInfo(
                language="Python",
                framework=self._detect_framework(deps),
                dependency_file=str(file.name),
                dependencies=deps,
                build_command=f"{build_cmd} - 安装依赖",
                test_command=f"{test_cmd} - 运行测试" if test_cmd != "未检测到" else "未检测到",
                metadata={
                    "name": project.get("name", ""),
                    "version": project.get("version", ""),
                },
            )
        except ImportError as e:
            print(f"[yellow]警告: 无法导入 TOML 解析库: {e}[/yellow]")
            print("[yellow]建议: pip install tomli[/yellow]")
            return ProjectInfo(
                language="Python",
                dependency_file=str(file.name),
            )
        except Exception as e:
            print(f"[yellow]警告: 无法解析 {file}: {e}[/yellow]")
            return ProjectInfo(
                language="Python",
                dependency_file=str(file.name),
            )

    def _parse_setup(self, project_root: Path, file: Path) -> ProjectInfo:
        """解析 setup.py（简化版）"""
        return ProjectInfo(
            language="Python",
            framework="unknown",
            dependency_file=str(file.name),
            build_command="pip install -e . - 安装依赖",
            test_command="未检测到",
        )

    def _parse_pipfile(self, project_root: Path, file: Path) -> ProjectInfo:
        """解析 Pipfile（简化版）"""
        return ProjectInfo(
            language="Python",
            framework="unknown",
            dependency_file=str(file.name),
            build_command="pipenv install - 安装依赖",
            test_command="未检测到",
        )

    def _detect_framework(self, deps: List[str]) -> str:
        """检测 Python 框架"""
        deps_str = " ".join(deps).lower()

        if "flask" in deps_str:
            return "Flask"
        elif "django" in deps_str:
            return "Django"
        elif "fastapi" in deps_str:
            return "FastAPI"
        elif "pytest" in deps_str:
            return "pytest"
        elif "unittest" in deps_str:
            return "unittest"
        else:
            return "unknown"
