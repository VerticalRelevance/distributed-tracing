# pylint: disable=line-too-long
"""
Module for handling AI model interactions with AWS Bedrock.

This module provides classes for managing AI model operations, including error handling,
model configuration, and text generation. It defines base classes for model objects and
a factory pattern for creating model instances.
"""
# pylint: enable=line-too-long

from typing import Dict, List
import boto3
from configuration import Configuration
from utilities import JsonUtils, LoggingUtils, ModelUtils, GenericUtils

MAX_LLM_RETRIES_EXPECTED_MIN = 0
MAX_LLM_RETRIES_EXPECTED_MAX = 10
MAX_LLM_RETRIES_DEFAULT = 3

RETRY_DELAY_EXPECTED_MIN = 0
RETRY_DELAY_EXPECTED_MAX = 30
RETRY_DELAY_DEFAULT = 1

TEMPERATURE_EXPECTED_MIN = 0.0
TEMPERATURE_EXPECTED_MAX = 1.0
TEMPERATURE_DEFAULT = 0.0


class ModelError(Exception):
    # pylint: disable=line-too-long
    """Base exception class for model-related errors.

    This exception hides AWS implementation details from users of the model classes.
    """
    # pylint: enable=line-too-long

    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)


class ModelMaxTokenLimitException(ModelError):
    # pylint: disable=line-too-long
    """Exception raised when the model's token limit is exceeded.

    This exception provides details about the token limits and actual token usage that caused the error.
    """
    # pylint: enable=line-too-long

    def __init__(
        self, max_token_limit: int, prompt_tokens: int, completion_tokens: int
    ):
        self._max_token_limit = max_token_limit
        self._prompt_tokens = prompt_tokens
        self._completion_tokens = completion_tokens
        self.message = (
            f"Max tokens limit of {max_token_limit} exceeded. "
            f"Number of prompt tokens: {prompt_tokens}, completion tokens: {completion_tokens}"
        )
        super().__init__(self.message)


class ModelObject:
    # pylint: disable=line-too-long
    """Base class for AI model objects that interact with language models.

    This class provides common functionality for model interactions, including
    configuration management, token counting, and error handling. It implements
    the singleton pattern to ensure only one instance exists.
    """
    # pylint: enable=line-too-long

    _instance = None

    def __new__(cls, *args, **kwargs):  # pylint: disable=unused-argument
        if not cls._instance:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, configuration: Configuration) -> None:
        # pylint: disable=line-too-long
        """Initialize a ModelObject with the given configuration.

        Args:
            configuration: Configuration object containing model settings and parameters
        """
        # pylint: enable=line-too-long
        self._config = configuration
        self._logging_utils = LoggingUtils()
        self._model_utils = ModelUtils(configuration=configuration)
        self._max_llm_retries = None
        self._retry_delay = None
        self._temperature = None
        self._completion_tokens = 0
        self._prompt_tokens = 0
        self._max_completion_tokens = None
        self._completion_json = None
        self._json_utils = JsonUtils()
        self._stopped_reason = None
        self._stop_valid_reasons = None

    def generate_text(self, prompt: str):
        # pylint: disable=line-too-long
        """Generate text based on the provided prompt.

        Args:
            prompt: The input text to generate a response for

        Raises:
            NotImplementedError: This method must be implemented by subclasses
        """
        # pylint: enable=line-too-long
        raise NotImplementedError("Subclasses must implement this method")

    @property
    def max_llm_retries(self) -> int:
        # pylint: disable=line-too-long
        """Get the maximum number of retries for LLM API calls.

        Returns:
            The maximum number of retries configured for LLM API calls

        Raises:
            ModelError: If the configuration value is invalid or outside the expected range
        """
        # pylint: enable=line-too-long
        if self._max_llm_retries is None:
            try:
                self._max_llm_retries = self._config.int_value(
                    "ai_model.max_llm_retries",
                    MAX_LLM_RETRIES_EXPECTED_MIN,
                    MAX_LLM_RETRIES_EXPECTED_MAX,
                    MAX_LLM_RETRIES_DEFAULT,
                )
            except TypeError as te:
                raise ModelError(
                    "Type for max LLM retries is invalid. "
                    "Value must be a valid integer between "
                    f"{MAX_LLM_RETRIES_EXPECTED_MIN} and {MAX_LLM_RETRIES_EXPECTED_MAX}."
                ) from te
            except ValueError as ve:
                raise ModelError(
                    "Value for max LLM retries is invalid. "
                    "Value must be a valid integer between "
                    f"{MAX_LLM_RETRIES_EXPECTED_MIN} and {MAX_LLM_RETRIES_EXPECTED_MAX}."
                ) from ve

        return self._max_llm_retries

    @property
    def model_client(self) -> boto3.client:
        # pylint: disable=line-too-long
        """Get the boto3 client for interacting with AWS Bedrock.

        Returns:
            A configured boto3 client for bedrock-runtime with appropriate region settings
        """
        # pylint: enable=line-too-long
        # TODO refactor into separate Bedrock-specific middle-layer class
        return boto3.client(
            "bedrock-runtime",
            region_name=self._config.str_value("aws.region", "us-west-2"),
        )

    @property
    def completion_tokens(self) -> int:
        # pylint: disable=line-too-long
        """Get the count of completion tokens used in the current or most recent request.

        Returns:
            The number of completion tokens
        """
        # pylint: enable=line-too-long
        return self._completion_tokens

    def increment_completion_tokens(self, value: int) -> None:
        # pylint: disable=line-too-long
        """Increment the completion token count by the specified value.

        Args:
            value: The number of tokens to add to the completion token count
        """
        # pylint: enable=line-too-long
        self._completion_tokens += value

    @completion_tokens.setter
    def completion_tokens(self, value: int) -> None:
        # pylint: disable=line-too-long
        """Set the completion token count to the specified value.

        Args:
            value: The new completion token count
        """
        # pylint: enable=line-too-long
        self._completion_tokens = value

    @property
    def prompt_tokens(self) -> int:
        # pylint: disable=line-too-long
        """Get the count of prompt tokens used in the current or most recent request.

        Returns:
            The number of prompt tokens
        """
        # pylint: enable=line-too-long
        return self._prompt_tokens

    def increment_prompt_tokens(self, value: int) -> None:
        # pylint: disable=line-too-long
        """Increment the prompt token count by the specified value.

        Args:
            value: The number of tokens to add to the prompt token count
        """
        # pylint: enable=line-too-long
        self._prompt_tokens += value

    @prompt_tokens.setter
    def prompt_tokens(self, value: int) -> None:
        # pylint: disable=line-too-long
        """Set the prompt token count to the specified value.

        Args:
            value: The new prompt token count
        """
        # pylint: enable=line-too-long
        self._prompt_tokens = value

    def reset_tokens(self) -> None:
        # pylint: disable=line-too-long
        """Reset both completion and prompt token counters to zero.

        This method should be called before starting a new model interaction to ensure accurate token counting.
        """
        # pylint: enable=line-too-long
        self.completion_tokens = 0
        self.prompt_tokens = 0

    @property
    def max_completion_tokens(self) -> int:
        # pylint: disable=line-too-long
        """Get the maximum number of completion tokens allowed for the model.

        Returns:
            The maximum number of completion tokens
        """
        # pylint: enable=line-too-long
        return self._max_completion_tokens

    @property
    def model_id(self) -> str:
        # pylint: disable=line-too-long
        """Get the model ID used for API calls.

        Returns:
            The model ID

        Raises:
            NotImplementedError: This method must be implemented by subclasses
        """
        # pylint: enable=line-too-long
        raise NotImplementedError("Subclasses must implement this method")

    @property
    def model_name(self) -> str:
        # pylint: disable=line-too-long
        """Get the human-readable model name.

        Returns:
            The model name

        Raises:
            NotImplementedError: This method must be implemented by subclasses
        """
        # pylint: enable=line-too-long
        raise NotImplementedError("Subclasses must implement this method")

    @property
    def model_vendor(self) -> str:
        # pylint: disable=line-too-long
        """Get the model vendor name.

        Returns:
            The model vendor

        Raises:
            NotImplementedError: This method must be implemented by subclasses
        """
        # pylint: enable=line-too-long
        raise NotImplementedError("Subclasses must implement this method")

    @property
    def retry_delay(self) -> int:
        # pylint: disable=line-too-long
        """Get the delay between retry attempts in seconds.

        Returns:
            The retry delay in seconds

        Raises:
            ModelError: If the configuration value is invalid or outside the expected range
        """
        # pylint: enable=line-too-long
        if not self._retry_delay:
            try:
                self._retry_delay = self._config.int_value(
                    "ai_model.retry_delay",
                    RETRY_DELAY_EXPECTED_MIN,
                    RETRY_DELAY_EXPECTED_MAX,
                    RETRY_DELAY_DEFAULT,
                )
            except TypeError as te:
                raise ModelError(
                    f"Type for retry delay is invalid. Value must be a valid integer between "
                    f"{RETRY_DELAY_EXPECTED_MIN} and {RETRY_DELAY_EXPECTED_MAX}."
                ) from te
            except ValueError as ve:
                raise ModelError(
                    "Value for retry delay is invalid. "
                    "Value must be a valid integer between "
                    f"{RETRY_DELAY_EXPECTED_MIN} and {RETRY_DELAY_EXPECTED_MAX}."
                ) from ve

        return self._retry_delay

    @property
    def temperature(self) -> float:
        # pylint: disable=line-too-long
        """Get the temperature setting for the model.

        The temperature controls randomness in the model's output. Higher values (closer to 1.0) make output
        more random, while lower values (closer to 0.0) make output more deterministic.

        Returns:
            The temperature value for model randomness

        Raises:
            ModelError: If the configuration value is invalid or outside the expected range
        """
        # pylint: enable=line-too-long
        if not self._temperature:
            try:
                self._temperature = self._config.float_value(
                    "ai_model.temperature",
                    TEMPERATURE_EXPECTED_MIN,
                    TEMPERATURE_EXPECTED_MAX,
                    TEMPERATURE_DEFAULT,
                )
            except TypeError as te:
                raise ModelError(
                    "Type for temperature is invalid. Value must be a valid floating point "
                    f"between {TEMPERATURE_EXPECTED_MIN} and {TEMPERATURE_EXPECTED_MAX}."
                ) from te
            except ValueError as ve:
                raise ModelError(
                    "Value for temperature is invalid. "
                    "Value must be a valid floating point between "
                    f"{TEMPERATURE_EXPECTED_MIN} and {TEMPERATURE_EXPECTED_MAX}."
                ) from ve
        return self._temperature

    @property
    def stop_valid_reasons(self) -> List[str]:
        # pylint: disable=line-too-long
        """Get the list of valid stop reasons for the model.

        Stop reasons indicate why the model stopped generating text (e.g., reaching a token limit,
        encountering a stop sequence, etc.).

        Returns:
            A list of valid stop reason strings

        Raises:
            ModelError: If the configuration value is invalid
        """
        # pylint: enable=line-too-long
        if self._stop_valid_reasons is None:
            try:
                self._stop_valid_reasons = self._config.list_value(
                    "ai_model.model_stop.reasons.valid",
                    [],
                )
            except TypeError as te:
                raise ModelError(
                    "Type for model stop valid reasons is invalid. Value must be a valid list."
                ) from te
            except ValueError as ve:
                raise ModelError(
                    "Value for model stop valid reasons is invalid. Value must be a valid list."
                ) from ve

        return self._stop_valid_reasons

    @property
    def stopped_reason(self) -> str:
        # pylint: disable=line-too-long
        """Get the reason why the model stopped generating text in the most recent request.

        Returns:
            The stop reason string
        """
        # pylint: enable=line-too-long
        return self._stopped_reason

    @stopped_reason.setter
    def stopped_reason(self, stopped_reason: str) -> None:
        # pylint: disable=line-too-long
        """Set the reason why the model stopped generating text.

        Args:
            stopped_reason: The stop reason string
        """
        # pylint: enable=line-too-long
        self._stopped_reason = stopped_reason

    @property
    def completion_json(self) -> Dict[str, str]:
        # pylint: disable=line-too-long
        """Get the JSON response from the model completion.

        Returns:
            The completion response as a dictionary
        """
        # pylint: enable=line-too-long
        return self._completion_json

    @completion_json.setter
    def completion_json(self, completion_json: Dict[str, str]) -> None:
        # pylint: disable=line-too-long
        """Set the JSON response from the model completion.

        Args:
            completion_json: The completion response as a dictionary
        """
        # pylint: enable=line-too-long
        self._completion_json = completion_json


class ModelFactory:
    # pylint: disable=line-too-long
    """Factory class for creating model objects based on configuration.

    This class implements the singleton pattern to ensure only one factory instance exists.
    It dynamically loads and instantiates model classes based on provided module and class names.
    """
    # pylint: enable=line-too-long

    _instance = None

    def __new__(cls, *args, **kwargs):
        # pylint: disable=line-too-long
        """Create a new instance of ModelFactory or return the existing instance.

        This method implements the singleton pattern, ensuring that only one instance of the ModelFactory
        class is created.

        Args:
            cls: The class object
            *args: Variable length argument list
            **kwargs: Arbitrary keyword arguments

        Returns:
            The singleton instance of the ModelFactory class
        """
        # pylint: enable=line-too-long
        if not cls._instance:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, configuration: Configuration):
        # pylint: disable=line-too-long
        """Initialize the ModelFactory with the given configuration.

        Args:
            configuration: Configuration object containing model settings and parameters
        """
        # pylint: enable=line-too-long
        self._generic_utils = GenericUtils()
        self._configuration = configuration

    def get_model(self, module_name: str, class_name: str) -> ModelObject:
        # pylint: disable=line-too-long
        """Create and return a model object of the specified type.

        This method dynamically loads the specified model class and instantiates it with the
        current configuration.

        Args:
            module_name: The name of the module containing the model class
            class_name: The name of the model class to instantiate

        Returns:
            An instance of the specified model class
        """
        # pylint: enable=line-too-long
        model_class = self._generic_utils.load_class(
            module_name="models." + module_name,
            class_name=class_name,
            package_name="models",
        )
        return model_class(configuration=self._configuration)
