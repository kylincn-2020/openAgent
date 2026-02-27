"""LLM prompt templates for DevOps Agent."""

from typing import Any


INTENT_RECOGNITION_PROMPT = """Classify the user's intent from the following request:

Request: "{user_input}"

Valid intents:
- generate_ci: Generate CI/CD configuration (GitHub Actions, GitLab CI, etc.)
- analyze_project: Analyze project structure, dependencies, or build configuration
- update_config: Update tool or application configuration
- unknown: Unable to classify or doesn't match any intent

Return only the intent name (generate_ci, analyze_project, update_config, or unknown).
"""


def format_prompt(template: str, **kwargs: Any) -> str:
    """
    Format a prompt template with the provided keyword arguments.

    Args:
        template: The prompt template string with placeholders
        **kwargs: Keyword arguments to substitute into the template

    Returns:
        The formatted prompt string

    Example:
        >>> prompt = format_prompt(INTENT_RECOGNITION_PROMPT, user_input="generate CI")
        >>> print(prompt)
    """
    try:
        return template.format(**kwargs)
    except KeyError as e:
        missing_key = str(e).strip("'")
        raise ValueError(
            f"Missing required placeholder '{missing_key}' in prompt template. "
            f"Provided kwargs: {list(kwargs.keys())}"
        ) from e
