"""LLM integration module."""

from devops_agent.cfg import LLMConfig
from devops_agent.llm.client import LLMClient, LLMCallError, LLMConfigError

__all__ = ["LLMClient", "LLMConfigError", "LLMCallError", "create_llm_client"]


def create_llm_client(config: LLMConfig) -> LLMClient:
    """
    Factory function to create an LLM client.

    Args:
        config: LLM configuration

    Returns:
        Configured LLMClient instance

    Example:
        >>> from devops_agent.cfg import load_config
        >>> from devops_agent.llm import create_llm_client
        >>> config = load_config()
        >>> client = create_llm_client(config.llm)
    """
    return LLMClient(config)
