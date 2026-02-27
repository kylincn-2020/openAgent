"""
项目分析结果输出模块

提供 Rich 表格和 JSON 双格式输出功能。
"""

from rich.console import Console
from rich.table import Table

from devops_agent.analyzer.models import ProjectAnalysisResult


# 支持的语言列表（用于错误提示）
SUPPORTED_LANGUAGES = ["Python", "Node.js", "Go", "Java"]


def print_project_table(result: ProjectAnalysisResult, console: Console) -> None:
    """打印项目分析结果的 Rich 表格

    Args:
        result: 项目分析结果
        console: Rich Console 实例
    """
    # 检查是否有分析结果
    if not result.languages and not result.subprojects:
        print_error("未检测到任何项目信息", SUPPORTED_LANGUAGES, console)
        return

    # 创建表格
    table = Table(title="项目分析结果", show_header=True, header_style="bold magenta")
    table.add_column("语言", style="cyan", width=12)
    table.add_column("框架", style="magenta", width=12)
    table.add_column("依赖文件", style="green", width=15)
    table.add_column("构建命令", style="yellow", width=30)
    table.add_column("测试命令", style="blue", width=25)

    # 添加主项目信息
    for lang_info in result.languages:
        table.add_row(
            lang_info.language,
            lang_info.framework,
            lang_info.dependency_file,
            lang_info.build_command,
            lang_info.test_command,
        )

    # 显示表格
    console.print(table)

    # 显示 Monorepo 子项目信息
    if result.subprojects:
        console.print(f"\n[bold cyan]检测到 Monorepo 结构 ({len(result.subprojects)} 个子项目):[/bold cyan]")
        for i, subproject in enumerate(result.subprojects, 1):
            console.print(f"\n  [dim]子项目 {i}:[/dim] {subproject.project_path}")
            console.print(f"  主语言: [cyan]{subproject.primary_language}[/cyan]")
            for lang_info in subproject.languages:
                console.print(f"    - {lang_info.language}: {lang_info.dependency_file}")


def print_compact_view(result: ProjectAnalysisResult, console: Console) -> None:
    """打印精简模式的项目分析结果

    只显示关键信息（语言、构建命令、测试命令）。

    Args:
        result: 项目分析结果
        console: Rich Console 实例
    """
    # 检查是否有分析结果
    if not result.languages and not result.subprojects:
        print_error("未检测到任何项目信息", SUPPORTED_LANGUAGES, console)
        return

    for lang_info in result.languages:
        console.print(f"\n[bold cyan]{lang_info.language}[/bold cyan]")
        console.print(f"  构建: {lang_info.build_command}")
        console.print(f"  测试: {lang_info.test_command}")

    # 显示 Monorepo 子项目信息
    if result.subprojects:
        console.print(f"\n[dim]({len(result.subprojects)} 个子项目)[/dim]")
        for subproject in result.subprojects:
            console.print(f"  - {subproject.project_path} ({subproject.primary_language})")


def print_json_output(result: ProjectAnalysisResult) -> None:
    """打印 JSON 格式的项目分析结果

    使用 Pydantic 的 model_dump_json() 确保类型一致。
    适合 CI/CD 集成和脚本处理。

    Args:
        result: 项目分析结果
    """
    # 使用 Pydantic 的 model_dump_json() 输出
    json_output = result.model_dump_json(indent=2)
    print(json_output)


def print_analysis_result(
    result: ProjectAnalysisResult, console: Console, json_mode: bool = False
) -> None:
    """打印项目分析结果（主入口函数）

    根据 json_mode 选择输出格式。

    Args:
        result: 项目分析结果
        console: Rich Console 实例
        json_mode: 是否使用 JSON 输出模式
    """
    if json_mode:
        print_json_output(result)
    else:
        print_project_table(result, console)


def print_error(message: str, supported_languages: list[str], console: Console) -> None:
    """打印错误消息和支持的语言列表

    Args:
        message: 错误消息
        supported_languages: 支持的语言列表
        console: Rich Console 实例
    """
    console.print(f"\n[bold red]错误: {message}[/bold red]")
    console.print(f"\n[yellow]支持的语言: {', '.join(supported_languages)}[/yellow]")
    console.print(
        "[dim]请确保项目根目录包含对应的依赖文件（如 requirements.txt、package.json 等）。[/dim]"
    )
