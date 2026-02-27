"""CLI interface for DevOps Agent."""

import asyncio
import os
from pathlib import Path

import typer
from rich.console import Console
from rich.panel import Panel
from rich.status import Status

from devops_agent import __version__
from devops_agent.cfg import AppConfig, get_default_config_path, load_config
from devops_agent.llm import LLMConfigError, create_llm_client
from devops_agent.utils.logging import setup_logging
from devops_agent.agent.graph import create_agent_graph
from devops_agent.agent.state import AgentState
from devops_agent.session import SessionManager, set_session_manager, cleanup_session
from devops_agent.analyzer import (
    ProjectAnalyzer,
    print_analysis_result,
    print_error as print_analyzer_error,
)
from devops_agent.analyzer.output import SUPPORTED_LANGUAGES

app = typer.Typer(
    help="DevOps Agent - Natural language DevOps automation",
    no_args_is_help=True,
    add_completion=False,
)
console = Console()


def version_callback(value: bool) -> None:
    """
    Display version information and exit.

    Args:
        value: Whether --version was used
    """
    if value:
        typer.echo(f"DevOps Agent v{__version__}")
        raise typer.Exit()


def print_error(title: str, message: str) -> None:
    """
    Print an error panel with consistent formatting.

    Args:
        title: Error panel title
        message: Error message content
    """
    console.print(
        Panel(
            message,
            title=f"[bold red]Error: {title}[/bold red]",
            title_align="left",
            border_style="red",
            expand=False,
        )
    )


@app.command()
def version() -> None:
    """Show version information."""
    console.print(f"DevOps Agent v{__version__}")


@app.command()
def analyze(
    json_mode: bool = typer.Option(
        False,
        "--json",
        help="Output in JSON format (for CI/CD integration)"
    ),
) -> None:
    """
    Analyze the current project.

    Detects project type, dependencies, build commands, and test commands.
    Supports Python, Node.js, Go, and Java projects.

    Args:
        json_mode: Whether to output in JSON format
    """
    # 获取当前目录
    project_path = Path.cwd()

    try:
        # 显示分析状态
        with Status("[bold blue]Analyzing project...[/bold blue]", console=console):
            # 创建分析器
            analyzer = ProjectAnalyzer(project_path)

            # 执行分析
            result = analyzer.analyze()

        # 检查是否成功
        if not result.languages and not result.subprojects:
            # 分析失败，显示错误消息
            print_analyzer_error(
                "未识别的项目类型",
                SUPPORTED_LANGUAGES,
                console
            )
            raise typer.Exit(code=1)

        # 输出结果
        print_analysis_result(result, console, json_mode=json_mode)

    except Exception as e:
        print_error(
            "Analysis Failed",
            f"Failed to analyze project: {e}"
        )
        raise typer.Exit(code=1)


@app.command()
def build(
    json_mode: bool = typer.Option(
        False,
        "--json",
        help="Output in JSON format (for CI/CD integration)"
    ),
) -> None:
    """
    Generate GitHub Actions CI configuration.

    Analyzes the project and generates a customized GitHub Actions workflow.
    Supports Python, Node.js, Go, and Java projects.

    Args:
        json_mode: Whether to output in JSON format (not yet implemented)
    """
    # 获取当前目录
    project_path = Path.cwd()

    try:
        from devops_agent.agent.state import AgentState
        from devops_agent.agent.build_agent import BuildAgent

        # 创建 Agent 状态
        state = AgentState(
            user_input="生成 GitHub Actions 配置",
            intent="generate_ci",
            project_path=str(project_path),
            context={"project_path": project_path},
            agent_results=[],
            errors=[],
            response=None
        )

        # 创建模拟 LLM 客户端（BuildAgent 不使用）
        class MockLLMClient:
            async def validate_connection(self):
                pass

        llm_client = MockLLMClient()

        # 创建 Build Agent 并执行
        agent = BuildAgent(state, llm_client)

        # 执行 Agent（同步调用）
        import asyncio
        result = asyncio.run(agent.execute())

        # 检查是否有错误
        if result.get("errors"):
            print_error(
                "配置生成失败",
                result["errors"][-1] if result["errors"] else "未知错误"
            )
            raise typer.Exit(code=1)

    except Exception as e:
        print_error(
            "配置生成失败",
            f"Failed to generate CI configuration: {e}"
        )
        raise typer.Exit(code=1)


@app.command()
def start(
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Enable verbose output (DEBUG level logging)"
    ),
    config: Path = typer.Option(
        None,
        "--config",
        "-c",
        help="Path to configuration file",
        exists=True,
        file_okay=True,
        dir_okay=False,
    ),
) -> None:
    """
    Start the DevOps Agent interactive session.

    Args:
        verbose: Enable verbose output
        config: Custom configuration file path
    """
    # Run async main function
    asyncio.run(_start_async(verbose=verbose, config_path=config))


async def _start_async(verbose: bool, config_path: Path | None) -> None:
    """
    Async implementation of start command.

    Args:
        verbose: Enable verbose output
        config_path: Custom configuration file path
    """
    # Setup logging first
    _console = setup_logging(level="INFO", verbose=verbose)

    # Load configuration
    try:
        if config_path:
            app_config = load_config(config_path)
        else:
            default_path = get_default_config_path()
            app_config = load_config(default_path)

        logger = _console.log if verbose else console.print
        logger(f"Configuration loaded from: {app_config.config_path}")

    except FileNotFoundError as e:
        print_error(
            "Configuration Not Found",
            f"{e}\n\n"
            f"To get started:\n"
            f"1. Create the configuration directory:\n"
            f"   mkdir -p ~/config/devops-agent\n\n"
            f"2. Create a config.yaml file:\n"
            f"   cat > ~/config/devops-agent/config.yaml << 'EOF'\n"
            f"llm:\n"
            f"  provider: claude\n"
            f"  api_key: your_api_key_here\n"
            f"  model: claude-3-5-sonnet-20241022\n"
            f"  max_retries: 3\n"
            f"  timeout: 30\n"
            f"log_level: INFO\n"
            f"verbose: false\n"
            f"EOF\n\n"
            f"3. Set your API key in the config file\n"
            f"4. Run 'devops-agent start' again"
        )
        raise typer.Exit(code=1)

    except ValueError as e:
        print_error(
            "Invalid Configuration",
            f"{e}\n\n"
            f"Please check your configuration file and try again."
        )
        raise typer.Exit(code=1)

    except Exception as e:
        print_error(
            "Unexpected Error",
            f"Failed to load configuration: {e}"
        )
        raise typer.Exit(code=1)

    # Validate LLM connection
    try:
        client = create_llm_client(app_config.llm)
        console.print("[dim]Validating LLM connection...[/dim]")

        await client.validate_connection()

        console.print(
            f"[green]Connected to LLM provider: {app_config.llm.provider}[/green]"
        )

    except LLMConfigError as e:
        print_error(
            "LLM Connection Failed",
            str(e)
        )
        raise typer.Exit(code=1)

    except Exception as e:
        print_error(
            "Unexpected Error",
            f"Failed to validate LLM connection: {e}"
        )
        raise typer.Exit(code=1)

    # Create session manager
    session_manager = SessionManager()
    set_session_manager(session_manager)
    session_id = session_manager.create_session(project_path=os.getcwd())

    # Create agent graph
    agent_graph = create_agent_graph()

    # Display welcome message
    console.print(f"[dim]Session: {session_id}[/dim]")
    welcome_panel = Panel(
        f"[bold blue]DevOps Agent v{__version__}[/bold blue]\n\n"
        f"Type your request or '[bold]exit[/bold]' to quit.",
        title="[bold]Welcome[/bold]",
        border_style="blue",
        padding=(1, 2),
    )
    console.print(welcome_panel)

    # REPL loop
    while True:
        try:
            # Get user input
            user_input = typer.prompt("\n[bold]Your request[/bold]", default="", show_default=False)

            # Check for exit commands
            if user_input.lower() in ["exit", "quit"]:
                cleanup_session()
                console.print("[yellow]Session cleaned up. Exiting...[/yellow]")
                break

            # Skip empty input
            if not user_input.strip():
                continue

            # Process user input through agent system
            with Status("[bold blue]Processing...[/bold blue]", console=console):
                # Create agent state
                state = AgentState(
                    user_input=user_input,
                    intent=None,
                    project_path=session_manager.get_session(session_id)['project_path'],
                    context=session_manager.get_session(session_id)['context'],
                    agent_results=[],
                    errors=[],
                    response=None
                )

                # Invoke agent graph
                result = await agent_graph.ainvoke(
                    state,
                    config={'configurable': {'llm_client': client}}
                )

            # Display response
            console.print(Panel(
                result['response'],
                title="Response",
                border_style="green"
            ))

            # 如果是项目分析请求，显示 Rich 表格
            if result.get('intent') == 'analyze_project' and result.get('response'):
                # 从 context 获取 project_info
                project_info = result.get('context', {}).get('project_info')
                if project_info:
                    from devops_agent.analyzer.models import ProjectAnalysisResult
                    from devops_agent.analyzer.output import print_project_table

                    # 重建 ProjectAnalysisResult 对象
                    analysis_result = ProjectAnalysisResult(**project_info)
                    print_project_table(analysis_result, console)

            # Update session history
            session_manager.add_to_history(user_input, result['response'], session_id)

        except KeyboardInterrupt:
            console.print("\n[yellow]Interrupted. Type 'exit' to quit.[/yellow]")
            continue

        except EOFError:
            cleanup_session()
            console.print("\n[yellow]Session cleaned up. Exiting...[/yellow]")
            break

        except Exception as e:
            print_error(
                "Processing Error",
                f"Failed to process request: {e}"
            )
            continue


def main() -> None:
    """Main entry point for the CLI."""
    app()


if __name__ == "__main__":
    main()
