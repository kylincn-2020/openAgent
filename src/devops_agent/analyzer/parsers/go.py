"""
Go 项目解析器

解析 go.mod 等依赖文件。
"""

import re
from pathlib import Path

from devops_agent.analyzer.models import ProjectInfo
from devops_agent.analyzer.parsers.python import BaseParser


class GoParser(BaseParser):
    """Go 项目解析器"""

    MARKER_FILES = ["go.mod"]

    def can_parse(self, marker_file: Path) -> bool:
        """判断是否能解析该文件"""
        return marker_file.name == "go.mod"

    def parse(self, project_root: Path, marker_file: Path) -> ProjectInfo:
        """解析 Go 项目"""
        try:
            with open(marker_file, "r", encoding="utf-8") as f:
                content = f.read()
        except FileNotFoundError:
            return ProjectInfo(
                language="Go",
                dependency_file=str(marker_file.name),
            )
        except Exception as e:
            print(f"[yellow]警告: 无法解析 {marker_file}: {e}[/yellow]")
            return ProjectInfo(
                language="Go",
                dependency_file=str(marker_file.name),
            )

        # 提取 module 名称
        module_match = re.search(r"^module\s+([^\s]+)", content, re.MULTILINE)
        module_name = module_match.group(1) if module_match else ""

        # 提取 require 依赖（忽略 indirect 依赖）
        deps = []
        # 匹配单行 require: require github.com/pkg/errors v0.9.1
        for match in re.finditer(r"^require\s+([^\s]+)\s+\S+", content, re.MULTILINE):
            dep = match.group(1)
            deps.append(dep)

        # 匹配多行 require 块
        require_block = re.search(
            r"require\s+\((.*?)\)", content, re.DOTALL
        )
        if require_block:
            block_content = require_block.group(1)
            for match in re.finditer(r"\s+([^\s]+)\s+\S+", block_content):
                dep = match.group(1)
                # 跳过 indirect 依赖
                if "// indirect" not in match.group(0):
                    deps.append(dep)

        return ProjectInfo(
            language="Go",
            framework="unknown",
            dependency_file=str(marker_file.name),
            dependencies=deps,
            build_command="go build - 构建项目",
            test_command="go test ./... - 运行测试",
            metadata={"name": module_name},
        )
