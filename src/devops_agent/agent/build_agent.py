"""Build Agent - 生成 GitHub Actions 配置

根据项目分析结果生成定制的 GitHub Actions 工作流配置。
支持配置预览、确认写入、备份和草稿保存。
"""

from pathlib import Path
from typing import Optional

from devops_agent.agent.base import Agent, AgentRegistry
from devops_agent.agent.state import AgentState
from devops_agent.analyzer.analyzer import ProjectAnalyzer
from devops_agent.cfg.generator import ConfigGenerator
from devops_agent.cfg.validator import WorkflowValidator, format_errors
from devops_agent.cfg.models import ConfigGenerationError, ProjectAnalysisError
from devops_agent.cfg.output import (
    print_config_preview,
    confirm_write,
    confirm_save_draft,
    write_config_with_backup,
    save_draft,
    print_generation_summary,
    format_error,
    print_error,
)
from rich.console import Console

console = Console()


@AgentRegistry.register("generate_ci")
class BuildAgent(Agent):
    """Build Agent - 生成 GitHub Actions 配置

    根据项目分析结果生成定制的 GitHub Actions 工作流配置。
    支持配置预览、确认写入、备份和草稿保存。
    """

    async def execute(self) -> AgentState:
        """执行配置生成

        Returns:
            更新后的 Agent 状态
        """
        project_path = Path(self.get_context("project_path", Path.cwd()))

        # 显示进度
        console.print("[bold cyan]正在生成 GitHub Actions 配置...[/bold cyan]")

        try:
            # 步骤 1: 分析项目
            console.print("[dim]1. 分析项目结构...[/dim]")
            try:
                analyzer = ProjectAnalyzer(project_path)
                analysis_result = analyzer.analyze()

                if not analysis_result.languages:
                    # 项目分析失败
                    error_message = (
                        "无法识别项目类型。"
                        "请确保项目包含依赖文件（如 requirements.txt、package.json 等）。"
                    )
                    self.add_error(error_message)
                    self.state["response"] = error_message
                    self.state["status"] = "error"
                    self.state["error"] = {
                        "type": "ProjectAnalysisError",
                        "message": error_message,
                    }
                    return self.state

            except Exception as e:
                # 项目分析异常
                print_error(e, context=f"分析项目路径: {project_path}")
                error_message = f"项目分析失败: {type(e).__name__}"
                self.add_error(error_message)
                self.state["response"] = error_message
                self.state["status"] = "error"
                self.state["error"] = {
                    "type": type(e).__name__,
                    "message": "项目分析失败",
                }
                return self.state

            # 获取主语言
            primary_language = analysis_result.primary_language

            # 步骤 2: 生成配置
            console.print(f"[dim]2. 生成 {primary_language} GitHub Actions 配置...[/dim]")
            config_content = None
            try:
                generator = ConfigGenerator(analysis_result)
                config_content, validation_errors = generator.generate_and_validate()

            except (ConfigGenerationError, ValueError) as e:
                # 配置生成失败
                print_error(e, context=f"生成 {primary_language} 配置")
                error_message = f"配置生成失败: {type(e).__name__}"
                self.add_error(error_message)
                self.state["response"] = error_message
                self.state["status"] = "error"
                self.state["error"] = {
                    "type": type(e).__name__,
                    "message": "配置生成失败",
                }
                return self.state

            # 步骤 3: 验证配置
            if validation_errors:
                console.print("[red]配置验证失败：[/red]")
                console.print(format_errors(validation_errors))
                error_message = "生成的配置验证失败"
                self.add_error(error_message)

                # 尝试保存草稿以便调试
                if config_content:
                    console.print("[yellow]正在保存配置草稿以便调试...[/yellow]")
                    success, _ = save_draft(config_content, project_path)
                    if success:
                        console.print("[dim]草稿已保存到项目根目录[/dim]")

                self.state["response"] = f"配置验证失败：\n{format_errors(validation_errors)}"
                self.state["status"] = "error"
                self.state["error"] = {
                    "type": "ValidationError",
                    "message": "生成的配置验证失败",
                }
                return self.state

            # 步骤 4: 显示预览
            console.print("[dim]3. 显示配置预览...[/dim]")
            print_config_preview(config_content, primary_language)

            # 步骤 5: 确认写入
            target_path = project_path / ".github" / "workflows" / "ci.yml"

            if confirm_write():
                # 写入配置（自动备份）
                console.print("[dim]4. 写入配置文件...[/dim]")
                try:
                    success, error = write_config_with_backup(
                        config_content, target_path, project_path
                    )

                    if not success:
                        # 文件写入失败
                        console.print(f"[red]{error}[/red]")
                        self.add_error(error)
                        self.state["response"] = error
                        self.state["status"] = "error"
                        self.state["error"] = {
                            "type": "IOError",
                            "message": error,
                        }
                        return self.state

                except (IOError, OSError, PermissionError) as e:
                    # 文件操作异常
                    print_error(e, context=f"写入文件: {target_path}")
                    error_message = f"无法写入配置文件: {type(e).__name__}"
                    self.add_error(error_message)
                    self.state["response"] = error_message
                    self.state["status"] = "error"
                    self.state["error"] = {
                        "type": type(e).__name__,
                        "message": "文件写入失败",
                    }

                    # 提供保存草稿选项
                    if config_content:
                        console.print("[yellow]是否保存为草稿文件？[/yellow]")
                        if confirm_save_draft():
                            save_draft(config_content, project_path)
                    return self.state

                # 显示摘要
                print_generation_summary(primary_language, target_path)

                # 格式化响应消息
                response = f"""已为您的 {primary_language} 项目生成 GitHub Actions 配置！

配置文件已写入到 `.github/workflows/ci.yml`

下一步：
1. 检查生成的配置是否符合需求
2. 推送代码到 GitHub 触发 CI
3. 在 GitHub Actions 页面查看运行结果
"""
            else:
                # 用户拒绝写入，询问是否保存草稿
                if confirm_save_draft():
                    console.print("[dim]4. 保存草稿文件...[/dim]")
                    try:
                        success, error = save_draft(config_content, project_path)

                        if not success:
                            self.add_error(error)
                            self.state["response"] = error
                            self.state["status"] = "error"
                            self.state["error"] = {
                                "type": "IOError",
                                "message": error,
                            }
                            return self.state

                    except (IOError, OSError) as e:
                        # 保存草稿失败
                        print_error(e, context="保存草稿文件")
                        error_message = f"保存草稿失败: {type(e).__name__}"
                        self.add_error(error_message)
                        self.state["response"] = error_message
                        self.state["status"] = "error"
                        self.state["error"] = {
                            "type": type(e).__name__,
                            "message": "草稿保存失败",
                        }
                        return self.state

                    print_generation_summary(primary_language, is_draft=True)
                    response = f"""已为您保存草稿配置到 `ci.yml.draft`

您可以：
1. 手动编辑草稿文件
2. 将其移动到 `.github/workflows/ci.yml`
3. 推送到 GitHub 触发 CI
"""
                else:
                    response = """已取消配置写入。

您可以：
1. 使用 `devops-agent build` 命令重新生成
2. 检查项目依赖文件是否正确
"""

            # 更新状态
            self.state["response"] = response
            self.state["status"] = "success"

        except Exception as e:
            # 未预期的异常
            print_error(e, context="配置生成过程")
            error_message = f"配置生成失败: {type(e).__name__}"
            self.add_error(error_message)
            self.state["response"] = error_message
            self.state["status"] = "error"
            self.state["error"] = {
                "type": type(e).__name__,
                "message": "未预期的错误",
            }

        return self.state
