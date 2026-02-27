"""Configuration management for DevOps Agent."""

import os
from pathlib import Path
from typing import Literal, Optional

import yaml
from pydantic import BaseModel, Field, field_validator, model_validator, ValidationInfo


class LLMConfig(BaseModel):
    """LLM provider configuration."""

    provider: Literal["claude", "openai", "custom"] = Field(
        default="claude",
        description="LLM provider to use"
    )
    api_key: str = Field(
        ...,
        description="API key for the LLM provider"
    )
    model: str = Field(
        default="claude-3-5-sonnet-20241022",
        description="Model identifier to use"
    )
    base_url: Optional[str] = Field(
        default=None,
        description="Custom API base URL for OpenAI-compatible endpoints"
    )
    max_retries: int = Field(
        default=3,
        ge=0,
        le=10,
        description="Maximum number of retries for API calls"
    )
    timeout: int = Field(
        default=30,
        gt=0,
        description="Timeout in seconds for API calls"
    )

    @model_validator(mode="after")
    def validate_base_url(self) -> "LLMConfig":
        """Validate base_url format when provider is custom."""
        if self.provider == "custom":
            if not self.base_url:
                raise ValueError(
                    "base_url is required when provider is 'custom'. "
                    "Example: https://api.example.com/v1"
                )
            if not self.base_url.startswith(("http://", "https://")):
                raise ValueError(
                    f"base_url must start with http:// or https://, got: {self.base_url}"
                )
        return self

    def __str__(self) -> str:
        """Return string representation without exposing API key."""
        if self.provider == "custom":
            return f"LLMConfig(provider={self.provider}, base_url={self.base_url}, model={self.model})"
        return f"LLMConfig(provider={self.provider}, model={self.model})"


class AppConfig(BaseModel):
    """Application configuration."""

    llm: LLMConfig = Field(
        ...,
        description="LLM configuration"
    )
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = Field(
        default="INFO",
        description="Logging level"
    )
    verbose: bool = Field(
        default=False,
        description="Enable verbose output"
    )
    config_path: Path | None = Field(
        default=None,
        description="Path to the configuration file"
    )

    @field_validator("log_level", mode="before")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Validate and normalize log level."""
        if isinstance(v, str):
            return v.upper()
        return v

    def __str__(self) -> str:
        """Return string representation without exposing sensitive data."""
        return (
            f"AppConfig(log_level={self.log_level}, verbose={self.verbose}, "
            f"llm={self.llm})"
        )


def get_default_config_path() -> Path:
    """
    Get the default configuration file path.

    Returns:
        Path to the default configuration file
    """
    # Check for environment variable override
    env_path = os.environ.get("DEVOPS_AGENT_CONFIG")
    if env_path:
        return Path(env_path).expanduser().resolve()

    # Default to ~/config/devops-agent/config.yaml
    return Path("~").expanduser() / "config" / "devops-agent" / "config.yaml"


def load_config(config_path: Path | None = None) -> AppConfig:
    """
    Load configuration from a YAML file.

    Args:
        config_path: Path to the configuration file.
                     If None, uses the default path.

    Returns:
        AppConfig instance

    Raises:
        FileNotFoundError: If the configuration file doesn't exist
        ValueError: If the configuration file is invalid
    """
    if config_path is None:
        config_path = get_default_config_path()

    config_path = config_path.expanduser().resolve()

    if not config_path.exists():
        raise FileNotFoundError(
            f"Configuration file not found: {config_path}\n"
            f"Please create a configuration file at this location, "
            f"or set the DEVOPS_AGENT_CONFIG environment variable."
        )

    try:
        with open(config_path, "r") as f:
            data = yaml.safe_load(f)
    except yaml.YAMLError as e:
        raise ValueError(
            f"Invalid YAML in configuration file {config_path}: {e}"
        )

    if not isinstance(data, dict):
        raise ValueError(
            f"Configuration file must contain a YAML dictionary, got {type(data).__name__}"
        )

    # Validate required top-level keys
    if "llm" not in data:
        raise ValueError(
            f"Missing required key 'llm' in configuration file {config_path}"
        )

    if not isinstance(data["llm"], dict):
        raise ValueError("'llm' must be a dictionary in the configuration")

    if "api_key" not in data["llm"]:
        raise ValueError(
            f"Missing required key 'llm.api_key' in configuration file {config_path}"
        )

    try:
        return AppConfig(**data, config_path=config_path)
    except Exception as e:
        # Construct a helpful error message without exposing sensitive data
        errors = str(e).replace(data.get("llm", {}).get("api_key", ""), "***")
        raise ValueError(
            f"Configuration validation failed: {errors}\n"
            f"Please check your configuration file at {config_path}"
        )
