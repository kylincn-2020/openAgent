"""
DevOps Agent 配置生成模块

该模块提供 GitHub Actions 配置生成功能，支持多种编程语言。
"""

# 从父目录的 config.py 导入配置管理
from devops_agent.config import AppConfig, get_default_config_path, load_config, LLMConfig

# 从子模块导入配置生成相关功能
from devops_agent.cfg.templates import get_template, list_templates
from devops_agent.cfg.generator import ConfigGenerator, generate_workflow
from devops_agent.cfg.models import CIConfig, WorkflowConfig
from devops_agent.cfg.validator import (
    WorkflowValidator,
    WorkflowValidationError,
    format_errors,
)
from devops_agent.cfg.output import (
    print_config_preview,
    confirm_write,
    confirm_save_draft,
    write_config_with_backup,
    save_draft,
    print_generation_summary,
)

__all__ = [
    # 配置管理
    "AppConfig",
    "get_default_config_path",
    "load_config",
    "LLMConfig",
    # 配置生成
    "get_template",
    "list_templates",
    "ConfigGenerator",
    "generate_workflow",
    "CIConfig",
    "WorkflowConfig",
    "WorkflowValidator",
    "WorkflowValidationError",
    "format_errors",
    "print_config_preview",
    "confirm_write",
    "confirm_save_draft",
    "write_config_with_backup",
    "save_draft",
    "print_generation_summary",
]
