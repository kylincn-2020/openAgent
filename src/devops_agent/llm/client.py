"""LLM client with retry logic and error handling."""

import os
from typing import Any

import httpx
from loguru import logger
from litellm import (
    APIConnectionError,
    APIError,
    AuthenticationError,
    RateLimitError,
    ModelResponse,
    completion,
)
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from devops_agent.cfg import LLMConfig


class LLMConfigError(Exception):
    """Raised when LLM configuration is invalid or API key validation fails."""

    def __init__(self, message: str, fix_suggestions: str | None = None) -> None:
        """
        Initialize LLMConfigError.

        Args:
            message: Error message
            fix_suggestions: Optional suggestions for fixing the error
        """
        self.fix_suggestions = fix_suggestions
        super().__init__(message)

    def __str__(self) -> str:
        """Return formatted error message with fix suggestions."""
        msg = super().__str__()
        if self.fix_suggestions:
            msg += f"\n\nHow to fix:\n{self.fix_suggestions}"
        return msg


class LLMCallError(Exception):
    """Raised when LLM call fails due to network, rate limit, or API errors."""

    def __init__(self, message: str, fix_suggestions: str | None = None) -> None:
        """
        Initialize LLMCallError.

        Args:
            message: Error message
            fix_suggestions: Optional suggestions for fixing the error
        """
        self.fix_suggestions = fix_suggestions
        super().__init__(message)

    def __str__(self) -> str:
        """Return formatted error message with fix suggestions."""
        msg = super().__str__()
        if self.fix_suggestions:
            msg += f"\n\nHow to fix:\n{self.fix_suggestions}"
        return msg


class LLMClient:
    """
    LLM client with automatic retry logic and error handling.

    This client wraps LiteLLM to provide a unified interface for calling
    multiple LLM providers (Claude, OpenAI, etc.) with built-in retry logic.
    """

    def __init__(self, config: LLMConfig) -> None:
        """
        Initialize the LLM client.

        Args:
            config: LLM configuration

        Note:
            The API key is set as an environment variable for LiteLLM to read.
            For custom providers, base_url is passed directly to completion() calls.
        """
        self.config = config
        # Set environment variable for LiteLLM
        env_key = f"{config.provider.upper()}_API_KEY"
        os.environ[env_key] = config.api_key
        # Store api_base for custom provider
        self.api_base = config.base_url if config.provider == "custom" else None

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((RateLimitError, APIConnectionError, APIError)),
    )
    async def complete(self, prompt: str, **kwargs: Any) -> str:
        """
        Call LLM with automatic retry on transient errors.

        Args:
            prompt: The prompt to send to the LLM
            **kwargs: Additional arguments to pass to litellm.completion

        Returns:
            The LLM response text

        Raises:
            LLMConfigError: If authentication fails
            LLMCallError: If the call fails after retries
        """
        # Log request initiation
        logger.debug(
            "LLM request initiated",
            extra={
                "provider": self.config.provider,
                "model": self.config.model,
                "base_url": self.api_base if self.api_base else "default",
                "prompt_length": len(prompt),
            }
        )

        try:
            # Prepare completion parameters
            completion_params = {
                "model": self.config.model,
                "messages": [{"role": "user", "content": prompt}],
                "timeout": self.config.timeout,
            }

            # Add api_base for custom provider
            if self.api_base:
                completion_params["api_base"] = self.api_base

            # Merge with additional kwargs
            completion_params.update(kwargs)

            # Handle streaming with fallback
            if kwargs.get("stream", False):
                try:
                    completion_params["stream"] = True
                    response: ModelResponse = await completion(**completion_params)
                    # Process streaming response
                    return self._handle_stream_response(response)
                except (APIError, APIConnectionError) as e:
                    # Check if error is related to streaming
                    error_str = str(e).lower()
                    if any(keyword in error_str for keyword in ["stream", "sse", "streaming"]):
                        # Fallback to non-streaming mode
                        logger.warning(
                            "Streaming not supported by endpoint, falling back to non-streaming mode",
                            extra={
                                "provider": self.config.provider,
                                "base_url": self.api_base
                            }
                        )
                        completion_params.pop("stream", None)
                        kwargs.pop("stream", None)
                        response: ModelResponse = await completion(**completion_params)
                        logger.debug(
                            "LLM request completed (fallback mode)",
                            extra={
                                "provider": self.config.provider,
                                "model": self.config.model,
                                "response_length": len(response.choices[0].message.content) if response.choices else 0,
                            }
                        )
                        return response.choices[0].message.content
                    raise

            response: ModelResponse = await completion(**completion_params)

            logger.debug(
                "LLM request completed",
                extra={
                    "provider": self.config.provider,
                    "model": self.config.model,
                    "response_length": len(response.choices[0].message.content) if response.choices else 0,
                }
            )

            return response.choices[0].message.content

        except AuthenticationError as e:
            logger.error(
                "LLM authentication failed",
                extra={
                    "provider": self.config.provider,
                    "model": self.config.model,
                    "base_url": self.api_base,
                }
            )
            custom_fix = "4. Verify your custom endpoint URL is correct\n" if self.api_base else ""
            raise LLMConfigError(
                "API key validation failed. "
                f"Provider: {self.config.provider}, Model: {self.config.model}",
                fix_suggestions=(
                    "1. Verify your API key is correct in config.yaml\n"
                    "2. Check that the API key hasn't been revoked\n"
                    "3. Ensure your account has active credits\n"
                    + custom_fix
                ),
            ) from e

        except RateLimitError as e:
            logger.error(
                "LLM rate limit exceeded",
                extra={
                    "provider": self.config.provider,
                    "model": self.config.model,
                }
            )
            raise LLMCallError(
                "Rate limit exceeded. Please wait before trying again.",
                fix_suggestions=(
                    "1. Retry after a few seconds\n"
                    "2. Check your usage quota at the provider's dashboard\n"
                    "3. Consider reducing the frequency of requests"
                ),
            ) from e

        except APIConnectionError as e:
            logger.error(
                "LLM connection error",
                extra={
                    "provider": self.config.provider,
                    "model": self.config.model,
                    "base_url": self.api_base,
                }
            )
            raise LLMCallError(
                "Network error or API unavailable.",
                fix_suggestions=(
                    "1. Check your internet connection\n"
                    "2. Verify the LLM provider's API status\n"
                    "3. Try again later\n"
                    "4. Check if a firewall is blocking the request"
                ),
            ) from e

        except APIError as e:
            logger.error(
                "LLM API error",
                extra={
                    "provider": self.config.provider,
                    "model": self.config.model,
                    "base_url": self.api_base,
                    "error": str(e),
                }
            )
            raise LLMCallError(
                f"API error occurred: {str(e)}",
                fix_suggestions=(
                    "1. Check the API status page for the provider\n"
                    "2. Verify your request parameters are valid\n"
                    "3. Try again later"
                ),
            ) from e

        except httpx.TimeoutException as e:
            logger.error(
                "LLM request timeout",
                extra={
                    "provider": self.config.provider,
                    "model": self.config.model,
                    "timeout": self.config.timeout,
                }
            )
            raise LLMCallError(
                f"Request timed out after {self.config.timeout} seconds.",
                fix_suggestions=(
                    "1. Check your internet connection speed\n"
                    "2. Increase the timeout value in config.yaml\n"
                    "3. Try again later"
                ),
            ) from e

    def _handle_stream_response(self, response: Any) -> str:
        """
        Handle streaming response from LLM.

        Args:
            response: Streaming response from litellm

        Returns:
            Complete response text
        """
        full_response = ""
        for chunk in response:
            if chunk.choices:
                delta = chunk.choices[0].delta
                if hasattr(delta, "content") and delta.content:
                    full_response += delta.content
        return full_response

    async def validate_connection(self) -> bool:
        """
        Validate the LLM connection with a lightweight test request.

        Returns:
            True if connection is successful

        Raises:
            LLMConfigError: If validation fails with detailed error message
        """
        try:
            # Send a lightweight test request
            test_prompt = "hi"
            await completion(
                model=self.config.model,
                messages=[{"role": "user", "content": test_prompt}],
                timeout=min(self.config.timeout, 10),  # Use shorter timeout for validation
                max_tokens=10,
            )
            return True

        except AuthenticationError as e:
            raise LLMConfigError(
                "API key validation failed. "
                f"Provider: {self.config.provider}, Model: {self.config.model}",
                fix_suggestions=(
                    "1. Verify your API key is correct in ~/config/devops-agent/config.yaml\n"
                    "2. Check that the API key hasn't been revoked\n"
                    "3. Ensure your account has active credits\n"
                    "4. Confirm you're using the correct provider (claude/openai)"
                ),
            ) from e

        except RateLimitError as e:
            raise LLMConfigError(
                "Rate limit exceeded during connection validation.",
                fix_suggestions=(
                    "1. Wait a few seconds before retrying\n"
                    "2. Check your usage quota at the provider's dashboard\n"
                    "3. Verify you haven't exceeded free tier limits"
                ),
            ) from e

        except ConnectionError as e:
            raise LLMConfigError(
                "Network error or API unavailable during connection validation.",
                fix_suggestions=(
                    "1. Check your internet connection\n"
                    "2. Verify the LLM provider's API status\n"
                    "3. Check if a firewall is blocking the request\n"
                    "4. Try again later"
                ),
            ) from e

        except APIError as e:
            raise LLMConfigError(
                f"API error during validation: {str(e)}",
                fix_suggestions=(
                    "1. Verify the model name in config.yaml is correct\n"
                    "2. Check the API status page for the provider\n"
                    "3. Try again later"
                ),
            ) from e

        except httpx.TimeoutException as e:
            raise LLMConfigError(
                f"Connection validation timed out after {self.config.timeout} seconds.",
                fix_suggestions=(
                    "1. Check your internet connection speed\n"
                    "2. Verify the LLM provider's API is accessible\n"
                    "3. Try increasing the timeout value in config.yaml"
                ),
            ) from e

        except Exception as e:
            raise LLMConfigError(
                f"Unexpected error during connection validation: {type(e).__name__}",
                fix_suggestions=(
                    "1. Check your configuration file format\n"
                    "2. Verify all required fields are present\n"
                    "3. Run with --verbose for more details"
                ),
            ) from e
