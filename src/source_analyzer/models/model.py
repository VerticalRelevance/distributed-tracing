# pylint: disable=line-too-long
"""
Module for handling AI model interactions with AWS Bedrock.

This module provides classes for managing AI model operations, including error handling,
model configuration, and text generation. It defines base classes for model objects and
a factory pattern for creating model instances.
"""
# pylint: enable=line-too-long

import os
from abc import ABC
from typing import Dict, List
import boto3
from botocore.exceptions import ClientError, TokenRetrievalError
from common.generic_utils import GenericUtils
from common.logging_utils import LoggingUtils
from common.configuration import Configuration
from common.json_utils import JsonUtils

EXCEPTION_LEVEL_WARN = 10
EXCEPTION_LEVEL_ERROR = 20

MAX_LLM_TRIES_EXPECTED_MIN = 0
MAX_LLM_TRIES_EXPECTED_MAX = 10
MAX_LLM_TRIES_DEFAULT = 3

RETRY_DELAY_EXPECTED_MIN = 0
RETRY_DELAY_EXPECTED_MAX = 30
RETRY_DELAY_DEFAULT = 1

TEMPERATURE_EXPECTED_MIN = 0.0
TEMPERATURE_EXPECTED_MAX = 1.0
TEMPERATURE_DEFAULT = 0.0

class ModelException(Exception):
    # pylint: disable=line-too-long
    """
    Base exception class for model-related errors.

    This exception hides AWS implementation details from users of the model classes.
    """
    # pylint: enable=line-too-long

    def __init__(self, message: str, level: int=EXCEPTION_LEVEL_ERROR):
        self._level: int = level
        self._message: str = message
        super().__init__(self._message)

    @property
    def level(self):
        """ The level this exception belongs to. """
        return self._level

class ModelMaxTokenLimitException(ModelException):
    # pylint: disable=line-too-long
    """
    Exception raised when the model's token limit is exceeded.

    This exception provides details about the token limits and actual token usage that caused the error.
    """
    # pylint: enable=line-too-long

    def __init__(
        self, max_token_limit: int, prompt_tokens: int, completion_tokens: int
    ):
        self._max_token_limit = max_token_limit
        self._prompt_tokens = prompt_tokens
        self._completion_tokens = completion_tokens
        self._message = (
            f"Max tokens limit of {max_token_limit} exceeded. "
            f"Number of prompt tokens: {prompt_tokens}, completion tokens: {completion_tokens}"
        )
        super().__init__(message=self._message, level=EXCEPTION_LEVEL_WARN)

    def __str__(self):
        return self._message

class ModelObject:
    # pylint: disable=line-too-long
    """
    Base class for AI model objects that interact with language models.

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
        """
        Initialize a ModelObject with the given configuration.

        Args:
            configuration: Configuration object containing model settings and parameters
        """
        # pylint: enable=line-too-long

        self._config = configuration
        self._logger = LoggingUtils().get_class_logger(class_name=__class__.__name__)
        self._model_utils = ModelUtils(configuration=configuration)
        self._max_llm_tries = None
        self._retry_delay = None
        self._temperature = None
        self._completion_tokens = 0
        self._prompt_tokens = 0
        self._max_completion_tokens = None
        self._completion_json = None
        self._json_utils = JsonUtils()
        self._stopped_reason = None
        self._stop_valid_reasons = None
        self._stop_max_tokens_reasons = None

    def generate_text(self, prompt: str) -> str:
        # pylint: disable=line-too-long
        """
        Generate text based on the provided prompt.

        Args:
            prompt: The input text to generate a response for

        Raises:
            NotImplementedError: This method must be implemented by subclasses
        """
        # pylint: enable=line-too-long

        raise NotImplementedError("Subclasses must implement this method")

    @property
    def max_llm_tries(self) -> int:
        # pylint: disable=line-too-long
        """
        Get the maximum number of retries for LLM API calls.

        Returns:
            The maximum number of retries configured for LLM API calls

        Raises:
            ModelException: If the configuration value is invalid or outside the expected range
        """
        # pylint: enable=line-too-long

        if self._max_llm_tries is None:
            try:
                self._max_llm_tries = self._config.int_value(
                    "ai_model.max_llm_tries",
                    MAX_LLM_TRIES_EXPECTED_MIN,
                    MAX_LLM_TRIES_EXPECTED_MAX,
                    MAX_LLM_TRIES_DEFAULT,
                )
            except TypeError as te:
                raise ModelException(
                    "Type for max LLM retries is invalid. "
                    "Value must be a valid integer between "
                    f"{MAX_LLM_TRIES_EXPECTED_MIN} and {MAX_LLM_TRIES_EXPECTED_MAX}."
                ) from te
            except ValueError as ve:
                raise ModelException(
                    "Value for max LLM retries is invalid. "
                    "Value must be a valid integer between "
                    f"{MAX_LLM_TRIES_EXPECTED_MIN} and {MAX_LLM_TRIES_EXPECTED_MAX}."
                ) from ve

        return self._max_llm_tries

    @property
    def completion_tokens(self) -> int:
        # pylint: disable=line-too-long
        """
        Get the count of completion tokens used in the current or most recent request.

        Returns:
            The number of completion tokens
        """
        # pylint: enable=line-too-long

        return self._completion_tokens

    def increment_completion_tokens(self, value: int) -> None:
        # pylint: disable=line-too-long
        """
        Increment the completion token count by the specified value.

        Args:
            value: The number of tokens to add to the completion token count
        """
        # pylint: enable=line-too-long

        self._completion_tokens += value

    @completion_tokens.setter
    def completion_tokens(self, value: int) -> None:
        # pylint: disable=line-too-long
        """
        Set the completion token count to the specified value.

        Args:
            value: The new completion token count
        """
        # pylint: enable=line-too-long

        self._completion_tokens = value

    @property
    def prompt_tokens(self) -> int:
        # pylint: disable=line-too-long
        """
        Get the count of prompt tokens used in the current or most recent request.

        Returns:
            The number of prompt tokens
        """
        # pylint: enable=line-too-long

        return self._prompt_tokens

    def increment_prompt_tokens(self, value: int) -> None:
        # pylint: disable=line-too-long
        """
        Increment the prompt token count by the specified value.

        Args:
            value: The number of tokens to add to the prompt token count
        """
        # pylint: enable=line-too-long

        self._prompt_tokens += value

    @prompt_tokens.setter
    def prompt_tokens(self, value: int) -> None:
        # pylint: disable=line-too-long
        """
        Set the prompt token count to the specified value.

        Args:
            value: The new prompt token count
        """
        # pylint: enable=line-too-long
        self._prompt_tokens = value

    def reset_tokens(self) -> None:
        # pylint: disable=line-too-long
        """
        Reset both completion and prompt token counters to zero.

        This method should be called before starting a new model interaction to ensure accurate token counting.
        """
        # pylint: enable=line-too-long

        self.completion_tokens = 0
        self.prompt_tokens = 0

    @property
    def max_completion_tokens(self) -> int:
        # pylint: disable=line-too-long
        """
        Get the maximum number of completion tokens allowed for the model.

        Returns:
            The maximum number of completion tokens
        """
        # pylint: enable=line-too-long

        return self._max_completion_tokens

    @max_completion_tokens.setter
    def max_completion_tokens(self, value: int):
        self._max_completion_tokens = value

    @property
    def model_id(self) -> str:
        # pylint: disable=line-too-long
        """
        Get the model ID used for API calls.

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
        """
        Get the human-readable model name.

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
        """
        Get the model vendor name.

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
        """
        Get the delay between retry attempts in seconds.

        Returns:
            The retry delay in seconds

        Raises:
            ModelException: If the configuration value is invalid or outside the expected range
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
                raise ModelException(
                    f"Type for retry delay is invalid. Value must be a valid integer between "
                    f"{RETRY_DELAY_EXPECTED_MIN} and {RETRY_DELAY_EXPECTED_MAX}."
                ) from te
            except ValueError as ve:
                raise ModelException(
                    "Value for retry delay is invalid. "
                    "Value must be a valid integer between "
                    f"{RETRY_DELAY_EXPECTED_MIN} and {RETRY_DELAY_EXPECTED_MAX}."
                ) from ve

        return self._retry_delay

    @property
    def temperature(self) -> float:
        # pylint: disable=line-too-long
        """
        Get the temperature setting for the model.

        The temperature controls randomness in the model's output. Higher values (closer to 1.0) make output
        more random, while lower values (closer to 0.0) make output more deterministic.

        Returns:
            The temperature value for model randomness

        Raises:
            ModelException: If the configuration value is invalid or outside the expected range
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
                raise ModelException(
                    "Type for temperature is invalid. Value must be a valid floating point "
                    f"between {TEMPERATURE_EXPECTED_MIN} and {TEMPERATURE_EXPECTED_MAX}."
                ) from te
            except ValueError as ve:
                raise ModelException(
                    "Value for temperature is invalid. "
                    "Value must be a valid floating point between "
                    f"{TEMPERATURE_EXPECTED_MIN} and {TEMPERATURE_EXPECTED_MAX}."
                ) from ve
        return self._temperature

    @property
    def stop_max_tokens_reasons(self) -> int:
        # pylint: disable=line-too-long
        """
        Get the maximum number of stop reasons allowed for the model.

        Returns:
            The maximum number of stop reasons
        """
        # pylint: enable=line-too-long

        if self._stop_max_tokens_reasons is None:
            try:
                self._stop_max_tokens_reasons = self._config.list_value(
                    "ai_model.model_stop.reasons.max_tokens",
                    [],
                )
            except TypeError as te:
                raise ModelException(
                    "Type for model stop max tokens reasons is invalid. Value must be a valid list."
                ) from te
            except ValueError as ve:
                raise ModelException(
                    "Value for model stop max tokens reasons is invalid. "
                    "Value must be a valid list."
                ) from ve

        return self._stop_max_tokens_reasons

    @stop_max_tokens_reasons.setter
    def stop_max_tokens_reasons(self, stop_max_reasons: int) -> None:
        # pylint: disable=line-too-long
        """
        Set the maximum number of stop reasons allowed for the model.

        Args:
            stop_max_reasons: The maximum number of stop reasons
        """
        # pylint: enable=line-too-long

        self._stop_max_tokens_reasons = stop_max_reasons

    @property
    def stop_valid_reasons(self) -> List[str]:
        # pylint: disable=line-too-long
        """
        Get the list of valid stop reasons for the model.

        Stop reasons indicate why the model stopped generating text (e.g., reaching a token limit,
        encountering a stop sequence, etc.).

        Returns:
            A list of valid stop reason strings

        Raises:
            ModelException: If the configuration value is invalid
        """
        # pylint: enable=line-too-long

        if self._stop_valid_reasons is None:
            try:
                self._stop_valid_reasons = self._config.list_value(
                    "ai_model.model_stop.reasons.valid",
                    [],
                )
            except TypeError as te:
                raise ModelException(
                    "Type for model stop valid reasons is invalid. Value must be a valid list."
                ) from te
            except ValueError as ve:
                raise ModelException(
                    "Value for model stop valid reasons is invalid. Value must be a valid list."
                ) from ve

        return self._stop_valid_reasons

    @property
    def stopped_reason(self) -> str:
        # pylint: disable=line-too-long
        """
        Get the reason why the model stopped generating text in the most recent request.

        Returns:
            The stop reason string
        """
        # pylint: enable=line-too-long

        return self._stopped_reason

    @stopped_reason.setter
    def stopped_reason(self, stopped_reason: str) -> None:
        # pylint: disable=line-too-long
        """
        Set the reason why the model stopped generating text.

        Args:
            stopped_reason: The stop reason string
        """
        # pylint: enable=line-too-long
        self._stopped_reason = stopped_reason

    @property
    def completion_json(self) -> Dict[str, str]:
        # pylint: disable=line-too-long
        """
        Get the JSON response from the model completion.

        Returns:
            The completion response as a dictionary
        """
        # pylint: enable=line-too-long

        return self._completion_json

    @completion_json.setter
    def completion_json(self, completion_json: Dict[str, str]) -> None:
        # pylint: disable=line-too-long
        """
        Set the JSON response from the model completion.

        Args:
            completion_json: The completion response as a dictionary
        """
        # pylint: enable=line-too-long

        self._completion_json = completion_json


class BedrockModelObject(ModelObject, ABC):
    # pylint: disable=line-too-long
    """
    AWS Bedrock-specific model object that extends the base ModelObject.

    This class provides AWS Bedrock-specific functionality including client management,
    error handling for Bedrock-specific exceptions, and AWS region configuration.
    This is an abstract base class that requires subclasses to implement the abstract methods.
    """
    # pylint: enable=line-too-long

    @property
    def model_client(self) -> boto3.client:
        # pylint: disable=line-too-long
        """
        Get the boto3 client for interacting with AWS Bedrock.

        Returns:
            A configured boto3 client for bedrock-runtime with appropriate region settings
        """
        # pylint: enable=line-too-long

        return boto3.client(
            "bedrock-runtime",
            region_name=self._model_utils.region_name,
            config=boto3.session.Config(read_timeout=300, retries={"max_attempts": 3}),
        )

    def _handle_bedrock_exceptions(self, func, *args, **kwargs):
        # pylint: disable=line-too-long
        """
        Handle common AWS Bedrock exceptions and convert them to ModelExceptions.

        Args:
            func: The function to execute with exception handling
            *args: Arguments to pass to the function
            **kwargs: Keyword arguments to pass to the function

        Returns:
            The result of the function call

        Raises:
            ModelException: If a Bedrock-specific error occurs
        """
        # pylint: enable=line-too-long

        try:
            return func(*args, **kwargs)
        except TokenRetrievalError as tre:
            self._logger.debug(
                __class__.__name__,
                f"raising ModelException for TokenRetrievalError: {str(tre)}"
            )
            raise ModelException(
                f"TokenRetrievalError error: {str(tre)}",
                EXCEPTION_LEVEL_ERROR,
            ) from tre
        except ClientError as ce:
            error_code = ce.response["Error"]["Code"]
            self._logger.trace(
                __class__.__name__,
                f"Bedrock invoke_model error ({error_code}): {str(ce)}"
            )
            raise ModelException(
                f"Bedrock invoke_model error ({error_code}): {str(ce)}",
                EXCEPTION_LEVEL_WARN
            ) from ce

    def invoke_model(self, request: str):
        # pylint: disable=line-too-long
        """
        Invoke the Bedrock model with the given request.

        Args:
            request: JSON string containing the model request

        Returns:
            The response from the Bedrock model

        Raises:
            ModelException: If there's an error invoking the model
        """
        # pylint: enable=line-too-long

        def _invoke():
            client = self.model_client
            return client.invoke_model(modelId=self.model_id, body=request)

        return self._handle_bedrock_exceptions(_invoke)

class ModelUtils:
    # pylint: disable=line-too-long
    """
    A utility class for managing AI model configuration and AWS region settings.

    This class provides methods for retrieving AI model-related configuration values and
    AWS region settings from either environment variables or a configuration object. It
    implements lazy loading of values and supports environment variable overrides.

    Features:
        - AI model class and module name configuration
        - AWS region configuration management
        - Environment variable override support
        - Configuration fallback values
        - Lazy loading of configuration values

    Methods:
        __init__(configuration): Initializes with Configuration object
        get_desired_model_class_name(): Retrieves AI model class name
        get_desired_model_module_name(): Retrieves AI model module name
        get_region_name(): Retrieves AWS region name

    Configuration Priority:
        1. Environment variables (AI_MODEL_CLASS_NAME, AI_MODEL_MODULE_NAME, AWS_REGION)
        2. Configuration object values (ai_model.class.name, ai_model.module.name, aws.region)
        3. Default values (us-west-2 for region)

    Example:
        >>> config = Configuration()
        >>> model_utils = ModelUtils(config)
        >>> class_name = model_utils.get_desired_model_class_name()
        >>> module_name = model_utils.get_desired_model_module_name()
        >>> region = model_utils.get_region_name()

    Environment Variables:
        - AI_MODEL_CLASS_NAME: Override for model class name
        - AI_MODEL_MODULE_NAME: Override for model module name
        - AWS_REGION: Override for AWS region

    Configuration Keys:
        - ai_model.class.name: Default model class name
        - ai_model.module.name: Default model module name
        - aws.region: Default AWS region (defaults to 'us-west-2')

    Dependencies:
        - os: For environment variable access
        - Configuration: For default configuration values

    Notes:
        - All getter methods are planned to be converted to properties (TODO)
        - Values are lazily loaded when first accessed
        - Region configuration follows AWS standard region format
    """
    # pylint: enable=line-too-long

    _instance = None

    def __new__(cls, *args, **kwargs):  # pylint: disable=unused-argument
        # pylint: disable=line-too-long
        """
        Creates and returns a singleton instance of the ModelUtils class.

        This method ensures that only one instance of the class is created
        throughout the application, implementing the singleton design pattern.

        Args:
            cls (type): The class being instantiated.
            *args: Variable length argument list.
            **kwargs: Arbitrary keyword arguments.

        Returns:
            ModelUtils: The singleton instance of the ModelUtils class.
        """
        # pylint: enable=line-too-long

        if not cls._instance:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, configuration: Configuration):
        # pylint: disable=line-too-long
        """
        Initializes the SourceCodeAnalyzerUtils with default None values.

        The actual values will be lazily loaded when the respective getter
        methods are called for the first time.

        Args:
            configuration (Configuration): The configuration object to use for retrieving settings.
        """
        # pylint: enable=line-too-long

        self._config: Configuration = configuration

    @property
    def desired_model_class_name(self):
        # pylint: disable=line-too-long
        """
        Retrieves the configured AI model class name from the configuration.

        This method fetches the class name for the AI model from the configuration using a dot-notation path.
        If the configuration value is not found, it returns a default value of "not found".

        Returns:
            str: The configured class name for the AI model, or "not found" if not configured.
        """
        # pylint: enable=line-too-long

        return self._config.str_value("ai_model.class.name", "not found")

    @property
    def desired_model_module_name(self) -> str:
        # pylint: disable=line-too-long
        """
        Retrieves the configured AI model module name from the configuration.

        This method fetches the module name for the AI model from the configuration using a dot-notation path.
        If the configuration value is not found, it returns a default value of "not found".

        Returns:
            str: The configured module name for the AI model, or "not found" if not configured.
        """
        # pylint: enable=line-too-long

        return self._config.str_value("ai_model.module.name", "not found")

    @property
    def region_name(self) -> str:
        # pylint: disable=line-too-long
        """
        Retrieves the AWS region name.

        Returns the region name from the 'AWS_REGION' environment variable.
        If not set, defaults to 'us-east-1'.

        Returns:
            str: The AWS region name.

        Example:
            >>> utils = SourceCodeAnalyzerUtils()
            >>> region = utils.get_region_name()
            # Returns 'us-west-2' if AWS_REGION is not set, or uses the env value
        """
        # pylint: enable=line-too-long

        return os.getenv(
            "AWS_REGION", self._config.str_value("aws.region", "us-west-2")
        )


class ModelFactory:
    # pylint: disable=line-too-long
    """
    Factory class for creating model objects based on configuration.

    This class implements the singleton pattern to ensure only one factory instance exists.
    It dynamically loads and instantiates model classes based on provided module and class names.
    """
    # pylint: enable=line-too-long

    _instance = None

    def __new__(cls, *args, **kwargs):
        # pylint: disable=line-too-long
        """
        Create a new instance of ModelFactory or return the existing instance.

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
        """
        Initialize the ModelFactory with the given configuration.

        Args:
            configuration: Configuration object containing model settings and parameters
        """
        # pylint: enable=line-too-long

        self._generic_utils = GenericUtils()
        self._configuration = configuration

    def get_model(self, module_name: str, class_name: str) -> ModelObject:
        # pylint: disable=line-too-long
        """
        Create and return a model object of the specified type.

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
            module_name="source_analyzer.models." + module_name,
            class_name=class_name,
            package_name="models",
        )
        return model_class(configuration=self._configuration)
