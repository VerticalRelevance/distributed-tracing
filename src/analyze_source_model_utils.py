"""
Source Code Analyzer Utilities Module

This module provides a utility class for managing configuration settings
for source code analysis, primarily focused on AI model and LLM (Large Language Model)
configuration parameters.

The class retrieves configuration values from environment variables with
sensible defaults and ensures minimum valid values.

Classes:
    SourceCodeAnalyzerUtils: A utility class for managing AI model and LLM configuration settings.
"""

import os
from .configuration import Configuration


class ModelUtils:
    """
    A utility class for managing pluggable model classes.

    This class provides methods to retrieve AI model configuration parameters
    from environment variables, with default values and validation.

    Attributes:
        _ai_model (str): The AI model to be used for analysis.
        _max_llm_retries (int): Maximum number of retries for LLM operations.
        _retry_delay (int): Delay between retry attempts.
        _temperature (float): Temperature setting for AI model randomness.
    """

    def __init__(self, configuration: Configuration):
        """
        Initializes the SourceCodeAnalyzerUtils with default None values.

        The actual values will be lazily loaded when the respective getter
        methods are called for the first time.
        """
        self._ai_model = None
        self._max_llm_retries = None
        self._retry_delay = None
        self._temperature = None
        self._config: Configuration = configuration

    def get_ai_model_name(self) -> str:
        """
        Retrieves the AI model to be used for source code analysis.

        Returns the AI model name from the 'AI_MODEL' environment variable.
        If not set, defaults to 'gpt-4o-mini'.

        Returns:
            str: The name of the AI model to be used.

        Example:
            >>> model_utils = ModelUtils()
            >>> model = model_utils.get_ai_model()
            # Returns 'gpt-4o-mini' if AI_MODEL is not set in environment
        """

        if not self._ai_model:
            self._ai_model = os.getenv(
                "AI_MODEL", self._config.get_value("ai_model", "gpt-4o-mini")
            )
        return self._ai_model

    def get_max_llm_retries(self) -> int:
        """
        Retrieves the maximum number of retries for LLM operations.

        Returns the number of retries from the 'MAX_LLM_RETRIES' environment variable.
        If not set, defaults to 10. Ensures a minimum of 1 retry.

        Returns:
            int: The maximum number of retry attempts, guaranteed to be at least 1.

        Example:
            >>> utils = SourceCodeAnalyzerUtils()
            >>> max_retries = utils.get_max_llm_retries()
            # Returns 10 if MAX_LLM_RETRIES is not set, or uses the env value
        """
        if not self._max_llm_retries:
            self._max_llm_retries = int(
                os.getenv(
                    "MAX_LLM_RETRIES", self._config.get_value("max_llm_retries", "10")
                )
            )
        self._max_llm_retries = max(self._max_llm_retries, 1)
        return self._max_llm_retries

    def get_retry_delay(self) -> int:
        """
        Retrieves the delay between retry attempts.

        Returns the retry delay from the 'RETRY_DELAY' environment variable.
        If not set, defaults to 0. Ensures a non-negative delay.

        Returns:
            int: The delay between retry attempts in seconds, guaranteed to be non-negative.

        Example:
            >>> utils = SourceCodeAnalyzerUtils()
            >>> delay = utils.get_retry_delay()
            # Returns 0 if RETRY_DELAY is not set, or uses the env value
        """
        if not self._retry_delay:
            self._retry_delay = int(
                os.getenv("RETRY_DELAY", self._config.get_value("retry_delay", "0"))
            )
        self._retry_delay = max(self._retry_delay, 0)
        return self._retry_delay

    def get_temperature(self) -> float:
        """
        Retrieves the temperature setting for the AI model.

        Returns the temperature from the 'TEMPERATURE' environment variable.
        If not set, defaults to 0.0. Ensures a non-negative temperature value.

        Returns:
            float: The temperature setting for the AI model, guaranteed to be non-negative.

        Example:
            >>> utils = SourceCodeAnalyzerUtils()
            >>> temperature = utils.get_temperature()
            # Returns 0.0 if TEMPERATURE is not set, or uses the env value
        """
        if not self._temperature:
            self._temperature = float(
                os.getenv("TEMPERATURE", self._config.get_value("temperature", "0.0"))
            )
        self._temperature = max(self._temperature, 0.0)
        return self._temperature
