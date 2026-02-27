"""配置输出和确认模块

提供配置预览、确认写入、备份和草稿保存功能。
"""

import re
from pathlib import Path
from typing import Optional, Tuple, Dict, List, Any
from rich.panel import Panel
from rich.syntax import Syntax
from rich.prompt import Confirm
from rich.console import Console
from rich.markup import escape

console = Console()


# 敏感信息过滤模式（继承自 logging.py）
SECRET_PATTERNS = [
    re.compile(r"ANTHROPIC_API_KEY\s*=\s*[\'\"]?[\w-]+[\'\"]?"),
    re.compile(r"OPENAI_API_KEY\s*=\s*[\'\"]?[\w-]+[\'\"]?"),
    re.compile(r"api_key['\"]?\s*[:=]\s*[\'\"]?[\w-]+[\'\"]?"),
    re.compile(r"sk-[a-zA-Z0-9]{20,}"),
    re.compile(r"Bearer\s+[a-zA-Z0-9-._~+/]+"),
]


def _filter_secrets(message: str) -> str:
    """过滤敏感信息

    Args:
        message: 原始消息

    Returns:
        过滤后的消息
    """
    for pattern in SECRET_PATTERNS:
        message = pattern.sub("***REDACTED***", message)
    return message


# 错误消息字典
_ERROR_MESSAGES: Dict[str, Dict[str, Any]] = {
    "ConfigGenerationError": {
        "description": "配置生成过程中发生错误",
        "suggestions": [
            "检查项目依赖文件是否完整（requirements.txt、package.json 等）",
            "查看详细日志了解具体失败原因",
            "尝试手动创建配置文件",
            "确保项目根目录正确",
        ],
    },
    "ValidationError": {
        "description": "生成的配置格式验证失败",
        "suggestions": [
            "报告此问题到项目仓库",
            "查看生成的草稿文件（如有）",
            "尝试手动修复草稿文件",
            "检查项目配置是否包含特殊字符",
        ],
    },
    "ProjectAnalysisError": {
        "description": "项目分析失败",
        "suggestions": [
            "确保在项目根目录运行（包含 .git 目录）",
            "检查项目是否支持（Python、Node.js、Go、Java）",
            "手动指定项目类型",
            "确保依赖文件存在且格式正确",
        ],
    },
    "LLMConfigError": {
        "description": "LLM 配置或 API Key 验证失败",
        "suggestions": [
            "检查配置文件：~/config/devops-agent/config.yaml",
            "验证 API Key 是否正确",
            "确认 API Key 未被撤销",
            "确保账户有可用额度",
            "确认使用正确的提供商（claude/openai）",
        ],
    },
    "LLMCallError": {
        "description": "LLM 调用失败",
        "suggestions": [
            "检查网络连接",
            "验证 LLM 提供商的 API 状态",
            "稍后重试",
            "检查防火墙是否阻止请求",
        ],
    },
    "FileNotFoundError": {
        "description": "找不到文件或目录",
        "suggestions": [
            "检查路径是否正确",
            "确保文件存在",
            "检查是否有权限访问该路径",
        ],
    },
    "PermissionError": {
        "description": "没有权限访问文件或目录",
        "suggestions": [
            "检查文件权限设置",
            "确保 .github/workflows 目录可写",
            "尝试使用 sudo 运行（不推荐）",
        ],
    },
    "IOError": {
        "description": "文件读写失败",
        "suggestions": [
            "检查磁盘空间是否充足",
            "确保目录存在",
            "检查文件权限",
            "确认文件未被其他程序占用",
        ],
    },
}


def format_error(
    error: Exception,
    context: Optional[str] = None,
    show_details: bool = True,
) -> str:
    """格式化错误消息

    使用 Rich Panel 美化错误显示，提供错误类型、描述和修复建议。
    自动过滤敏感信息。

    Args:
        error: 异常对象
        context: 可选的上下文信息
        show_details: 是否显示技术细节

    Returns:
        格式化的错误消息字符串
    """
    error_type = type(error).__name__
    error_msg = str(error)

    # 过滤敏感信息
    error_msg = _filter_secrets(error_msg)
    if context:
        context = _filter_secrets(context)

    # 获取错误描述和建议
    error_info = _ERROR_MESSAGES.get(error_type, {
        "description": f"未知错误 ({error_type})",
        "suggestions": [
            "查看详细日志了解问题",
            "检查系统配置",
            "报告此问题",
        ],
    })

    # 构建错误消息
    lines = [
        f"[bold red]错误: {error_type}[/bold red]",
        "",
        f"{error_info['description']}",
    ]

    # 添加上下文
    if context:
        lines.extend(["", f"[dim]上下文: {context}[/dim]"])

    # 添加错误详情
    if error_msg and error_msg != error_info["description"]:
        lines.extend(["", f"[dim]{escape(error_msg)}[/dim]"])

    # 添加修复建议
    lines.extend([
        "",
        "[bold yellow]💡 修复建议:[/bold yellow]",
    ])
    for i, suggestion in enumerate(error_info["suggestions"], 1):
        lines.append(f"  {i}. {suggestion}")

    # 添加技术细节
    if show_details:
        lines.extend([
            "",
            "[dim]📍 详细信息:[/dim]",
            f"[dim]  错误类型: {error_type}[/dim]",
        ])
        if hasattr(error, "__traceback__"):
            import traceback
            tb_lines = traceback.format_tb(error.__traceback__)
            if tb_lines:
                # 只显示最后一帧（最相关的调用点）
                last_frame = tb_lines[-1].strip()
                lines.append(f"[dim]  位置: {escape(last_frame)}[/dim]")

    # 使用 Rich Panel 渲染
    panel = Panel(
        "\n".join(lines),
        title="[bold red]错误[/bold red]",
        title_align="left",
        border_style="red",
        padding=(1, 2),
    )

    # 使用 Console 捕获输出
    from io import StringIO
    buffer = StringIO()
    error_console = Console(file=buffer, force_terminal=True)
    error_console.print(panel)
    return buffer.getvalue()


def print_error(
    error: Exception,
    context: Optional[str] = None,
    show_details: bool = True,
) -> None:
    """打印错误到控制台

    Args:
        error: 异常对象
        context: 可选的上下文信息
        show_details: 是否显示技术细节
    """
    error_message = format_error(error, context, show_details)
    console.print(error_message)


def print_config_preview(config: str, language: str) -> None:
    """打印配置预览

    使用 Rich Panel 和 Syntax 高亮显示生成的配置。

    Args:
        config: 生成的 YAML 配置字符串
        language: 编程语言（用于标题）
    """
    # 使用语法高亮
    syntax = Syntax(config, "yaml", theme="monokai", line_numbers=True)

    # 创建 Panel
    panel = Panel(
        syntax,
        title=f"[bold green]GitHub Actions 配置预览 ({language})[/bold green]",
        title_align="left",
        border_style="green",
        padding=(1, 1),
    )

    console.print(panel)


def confirm_write() -> bool:
    """确认是否写入配置文件

    Returns:
        True 用户确认写入，False 用户拒绝
    """
    return Confirm.ask(
        "\n[bold yellow]确认写入 .github/workflows/ci.yml？[/bold yellow]",
        default=True,
    )


def confirm_save_draft() -> bool:
    """确认是否保存为草稿文件

    Returns:
        True 用户保存草稿，False 用户不保存
    """
    return Confirm.ask(
        "[bold yellow]保存为草稿文件 (ci.yml.draft)？[/bold yellow]",
        default=False,
    )


def write_config_with_backup(
    config: str,
    target_path: Path,
    project_path: Path,
) -> Tuple[bool, Optional[str]]:
    """写入配置并备份现有文件

    如果目标文件已存在，先创建带时间戳的备份。

    Args:
        config: 配置内容
        target_path: 目标文件路径（.github/workflows/ci.yml）
        project_path: 项目根目录（用于相对路径）

    Returns:
        (成功, 错误消息)
    """
    from datetime import datetime

    try:
        # 创建目标目录
        target_path.parent.mkdir(parents=True, exist_ok=True)

        # 备份现有文件
        if target_path.exists():
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = target_path.with_suffix(f".yml.bak.{timestamp}")

            # 复制文件到备份位置
            import shutil
            shutil.copy2(target_path, backup_path)

            console.print(
                f"[yellow]已备份现有配置到: {backup_path.relative_to(project_path)}[/yellow]"
            )

        # 写入新配置
        target_path.write_text(config, encoding="utf-8")

        console.print(
            f"[green]配置已写入: {target_path.relative_to(project_path)}[/green]"
        )

        return True, None

    except Exception as e:
        error_msg = f"写入配置失败: {e}"
        console.print(f"[red]{error_msg}[/red]")
        return False, error_msg


def save_draft(config: str, project_path: Path) -> Tuple[bool, Optional[str]]:
    """保存配置为草稿文件

    Args:
        config: 配置内容
        project_path: 项目根目录

    Returns:
        (成功, 错误消息)
    """
    try:
        draft_path = project_path / "ci.yml.draft"

        # 写入草稿文件
        content = f"# 此文件为草稿，请手动移动到 .github/workflows/ci.yml\n{config}"
        draft_path.write_text(content, encoding="utf-8")

        console.print(f"[green]草稿已保存到: {draft_path.name}[/green]")
        console.print(
            f"[dim]提示: 您可以手动编辑此文件，然后移动到 .github/workflows/ci.yml[/dim]"
        )

        return True, None

    except Exception as e:
        error_msg = f"保存草稿失败: {e}"
        console.print(f"[red]{error_msg}[/red]")
        return False, error_msg


def print_generation_summary(
    language: str,
    config_path: Optional[Path] = None,
    is_draft: bool = False,
) -> None:
    """打印生成摘要

    Args:
        language: 编程语言
        config_path: 配置文件路径（如果已写入）
        is_draft: 是否为草稿文件
    """
    if is_draft:
        console.print("\n[bold cyan]配置生成完成（草稿模式）[/bold cyan]")
    else:
        console.print("\n[bold cyan]配置生成完成[/bold cyan]")
        console.print(f"[dim]配置文件: {config_path}[/dim]")

    console.print(f"[dim]语言: {language}[/dim]")
    console.print("[dim]下一步: 推送代码到 GitHub 触发 CI[/dim]")
