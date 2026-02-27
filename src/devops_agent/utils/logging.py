"""Logging configuration for DevOps Agent."""

import re
import sys
from typing import Any

from loguru import logger
from rich.console import Console
from rich.logging import RichHandler


# Patterns to filter out from logs (API keys, secrets)
SECRET_PATTERNS = [
    re.compile(r"ANTHROPIC_API_KEY\s*=\s*[\'\"]?[\w-]+[\'\"]?"),
    re.compile(r"OPENAI_API_KEY\s*=\s*[\'\"]?[\w-]+[\'\"]?"),
    re.compile(r"api_key['\"]?\s*[:=]\s*[\'\"]?[\w-]+[\'\"]?"),
    re.compile(r"sk-[a-zA-Z0-9]{20,}"),
    re.compile(r"Bearer\s+[a-zA-Z0-9-._~+/]+"),
]


class SecretFilter:
    """Filter to hide secrets from log output."""

    def __init__(self) -> None:
        """Initialize the secret filter."""
        self.patterns = SECRET_PATTERNS

    def __call__(self, record: dict[str, Any]) -> bool:
        """
        Filter secrets from the log record.

        Args:
            record: Log record dictionary

        Returns:
            True to allow the record, False otherwise
        """
        message = record.get("message", "")
        for pattern in self.patterns:
            message = pattern.sub("***REDACTED***", message)
        record["message"] = message
        return True


def setup_logging(level: str = "INFO", verbose: bool = False) -> "Console":
    """
    Configure logging with Rich handler and secret filtering.

    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        verbose: Enable verbose output (DEBUG level)

    Returns:
        Configured Rich Console instance
    """
    # Remove default handler
    logger.remove()

    # Determine log level
    log_level = "DEBUG" if verbose else level

    # Add Rich handler for console output
    console = Console()
    handler = RichHandler(
        console=console,
        show_time=True,
        show_path=verbose,
        rich_tracebacks=True,
        tracebacks_show_locals=verbose,
        markup=True,
    )

    logger.add(
        handler,
        format="<level>{level: <8}</level> | <level>{message}</level>",
        level=log_level,
        colorize=True,
        filter=SecretFilter(),
    )

    # Log to file if verbose (for debugging)
    if verbose:
        logger.add(
            "devops-agent-debug.log",
            rotation="10 MB",
            retention="1 day",
            level="DEBUG",
            filter=SecretFilter(),
            format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        )

    # Configure stderr for errors
    logger.add(
        sys.stderr,
        level="ERROR",
        format="<level>{level: <8}</level> | <level>{message}</level>",
        colorize=True,
        filter=SecretFilter(),
    )

    return console
