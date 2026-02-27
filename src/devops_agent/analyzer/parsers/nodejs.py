"""
Node.js 项目解析器

解析 package.json 等依赖文件。
"""

import json
from pathlib import Path

from devops_agent.analyzer.models import ProjectInfo
from devops_agent.analyzer.parsers.python import BaseParser


class NodeJSParser(BaseParser):
    """Node.js 项目解析器"""

    MARKER_FILES = ["package.json"]

    def can_parse(self, marker_file: Path) -> bool:
        """判断是否能解析该文件"""
        return marker_file.name == "package.json"

    def parse(self, project_root: Path, marker_file: Path) -> ProjectInfo:
        """解析 Node.js 项目"""
        try:
            with open(marker_file, "r", encoding="utf-8") as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            print(f"[red]错误: {marker_file} JSON 格式无效[/red]")
            print(f"[red]位置: 第 {e.lineno} 行, 第 {e.colno} 列[/red]")
            print(f"[yellow]建议: 使用在线 JSON 验证工具检查语法[/yellow]")
            return ProjectInfo(
                language="Node.js",
                dependency_file=str(marker_file.name),
            )
        except FileNotFoundError:
            return ProjectInfo(
                language="Node.js",
                dependency_file=str(marker_file.name),
            )
        except Exception as e:
            print(f"[yellow]警告: 无法解析 {marker_file}: {e}[/yellow]")
            return ProjectInfo(
                language="Node.js",
                dependency_file=str(marker_file.name),
            )

        # 提取依赖
        dependencies = list(data.get("dependencies", {}).keys())
        dev_dependencies = list(data.get("devDependencies", {}).keys())
        all_deps = dependencies + dev_dependencies

        # 提取脚本
        scripts = data.get("scripts", {})

        # 推断构建命令
        build_cmd = "未检测到"
        if "build" in scripts:
            # 检测使用的是 npm 还是 yarn
            if (project_root / "yarn.lock").exists():
                build_cmd = f"yarn build"
            else:
                build_cmd = f"npm run build"
        elif "compile" in scripts:
            build_cmd = f"npm run compile"

        # 推断测试命令
        test_cmd = "未检测到"
        if "test" in scripts:
            if (project_root / "yarn.lock").exists():
                test_cmd = f"yarn test"
            else:
                test_cmd = f"npm test"

        # 检测框架
        framework = self._detect_framework(all_deps)

        return ProjectInfo(
            language="Node.js",
            framework=framework,
            dependency_file=str(marker_file.name),
            dependencies=all_deps,
            build_command=f"{build_cmd} - 构建项目" if build_cmd != "未检测到" else "未检测到",
            test_command=f"{test_cmd} - 运行测试" if test_cmd != "未检测到" else "未检测到",
            metadata={
                "name": data.get("name", ""),
                "version": data.get("version", ""),
            },
        )

    def _detect_framework(self, deps: list) -> str:
        """检测 Node.js 框架"""
        deps_str = " ".join(deps).lower()

        if "react" in deps_str:
            return "React"
        elif "vue" in deps_str:
            return "Vue"
        elif "next" in deps_str:
            return "Next.js"
        elif "nuxt" in deps_str:
            return "Nuxt"
        elif "express" in deps_str:
            return "Express"
        elif "koa" in deps_str:
            return "Koa"
        elif "nestjs" in deps_str:
            return "NestJS"
        elif "astro" in deps_str:
            return "Astro"
        elif "svelte" in deps_str:
            return "Svelte"
        elif "angular" in deps_str:
            return "Angular"
        elif "webpack" in deps_str:
            return "Webpack"
        elif "vite" in deps_str:
            return "Vite"
        else:
            return "unknown"
