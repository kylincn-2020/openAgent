"""
GitHub Actions 工作流验证器

验证生成的 YAML 配置是否符合 GitHub Actions 规范。
"""

import yaml
from pathlib import Path
from typing import List, Optional
from pydantic import BaseModel


class WorkflowValidationError(BaseModel):
    """工作流验证错误"""

    field: str
    message: str
    line: Optional[int] = None


class WorkflowValidator:
    """GitHub Actions 工作流验证器

    验证生成的 YAML 配置是否符合 GitHub Actions 规范。
    """

    REQUIRED_FIELDS = ["name", "on", "jobs"]
    REQUIRED_JOB_FIELDS = ["runs-on", "steps"]

    # YAML 解析后，GitHub Actions 的 'on' 和 'runs-on' 字段会被解析为布尔值
    # 因为 'on' 是 Python 的保留字，PyYAML 会进行特殊处理
    FIELD_ALTERNATIVES = {
        "on": ["on", True],
        "runs-on": ["runs-on", True],
    }

    def validate(self, yaml_content: str) -> List[WorkflowValidationError]:
        """验证 YAML 配置

        Args:
            yaml_content: YAML 配置字符串

        Returns:
            错误列表（空列表表示验证通过）
        """
        errors = []

        try:
            # 解析 YAML
            data = yaml.safe_load(yaml_content)
            if not isinstance(data, dict):
                errors.append(
                    WorkflowValidationError(field="root", message="配置必须是字典类型")
                )
                return errors

            # 验证必需字段
            # 特殊处理 'on' 字段（会被解析为 True）
            for field in self.REQUIRED_FIELDS:
                alternatives = self.FIELD_ALTERNATIVES.get(field, [field])
                if not any(alt in data for alt in alternatives):
                    errors.append(
                        WorkflowValidationError(
                            field=field, message=f"缺少必需字段: {field}"
                        )
                    )

            # 验证 jobs
            if "jobs" in data:
                jobs = data["jobs"]
                if not isinstance(jobs, dict) or not jobs:
                    errors.append(
                        WorkflowValidationError(
                            field="jobs", message="jobs 必须是非空字典"
                        )
                    )

                # 验证每个 job
                for job_name, job_config in jobs.items():
                    job_errors = self._validate_job(job_name, job_config)
                    errors.extend(job_errors)

        except yaml.YAMLError as e:
            errors.append(
                WorkflowValidationError(field="yaml", message=f"YAML 解析错误: {e}")
            )

        return errors

    def _validate_job(self, job_name: str, job_config: dict) -> List[WorkflowValidationError]:
        """验证单个 job 配置

        Args:
            job_name: job 名称
            job_config: job 配置字典

        Returns:
            错误列表
        """
        errors = []

        if not isinstance(job_config, dict):
            errors.append(
                WorkflowValidationError(
                    field=f"jobs.{job_name}", message="job 配置必须是字典类型"
                )
            )
            return errors

        for field in self.REQUIRED_JOB_FIELDS:
            alternatives = self.FIELD_ALTERNATIVES.get(field, [field])
            if not any(alt in job_config for alt in alternatives):
                errors.append(
                    WorkflowValidationError(
                        field=f"jobs.{job_name}", message=f"缺少必需字段: {field}"
                    )
                )

        # 验证 steps
        if "steps" in job_config:
            steps = job_config["steps"]
            if not isinstance(steps, list) or not steps:
                errors.append(
                    WorkflowValidationError(
                        field=f"jobs.{job_name}.steps", message="steps 必须是非空列表"
                    )
                )

        return errors


def format_errors(errors: List[WorkflowValidationError]) -> str:
    """格式化错误消息为人类可读的字符串

    Args:
        errors: 错误列表

    Returns:
        格式化后的错误消息
    """
    if not errors:
        return "配置验证通过"

    lines = ["配置验证失败："]
    for error in errors:
        if error.line:
            lines.append(f"  - {error.field} (行 {error.line}): {error.message}")
        else:
            lines.append(f"  - {error.field}: {error.message}")
    return "\n".join(lines)
