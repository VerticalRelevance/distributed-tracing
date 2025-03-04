import sys
import os
import boto3
from configuration import Configuration

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
    """Generic error for storage operations, hiding AWS implementation details"""

    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)


class ModelMaxTokenLimitException(ModelError):

    def __init__(
        self, max_token_limit: int, prompt_tokens: int, completion_tokens: int
    ):
        self._max_token_limit = max_token_limit
        self._prompt_tokens = prompt_tokens
        self._completion_tokens = completion_tokens
        self.message = f"Max tokens limit of {max_token_limit} exceeded. Number of prompt tokens: {prompt_tokens}, completion tokens: {completion_tokens}"
        super().__init__(self.message)


class ModelObject:
    def __init__(self, configuration: Configuration) -> None:
        self._config = configuration
        self._logging_utils = LoggingUtils()
        self._model_utils = ModelUtils(configuration=configuration)
        self._max_llm_retries = None
        self._retry_delay = None
        self._temperature = None
        self._completion_tokens = 0
        self._prompt_tokens = 0
        self._stop_reason = None
        self._max_completion_tokens = None
    @property
    def max_llm_retries(self) -> int:
        if self._max_llm_retries is None:
                self._max_llm_retries = self._config.value(
                    key_path="ai_model.max_llm_retries",
                    expected_type=int,
                    expected_min=MAX_LLM_RETRIES_EXPECTED_MIN,
                    expected_max=MAX_LLM_RETRIES_EXPECTED_MAX,
                    default=MAX_LLM_RETRIES_DEFAULT,
                )
            except TypeError as te:
            except ValueError as ve:
                raise ModelError(
                    f"Value '{value}' for max LLM retries is invalid. Value must be a valid integer zero between 0 and 10."
                ) from ve
            if self._max_llm_retries < 0 or self._max_llm_retries > 10:
                raise ModelError(
                    f"Value '{self._max_llm_retries}' for max LLM retries is invalid. Value must be between 0 and 10."
                )

        return self._max_llm_retries

    @property
    def model_client(self) -> boto3.client:
        return boto3.client(
            region_name=self._config.value(
                "aws.region", expected_type=str, default="us-west-2"
            ),
        )

    @property
    def completion_tokens(self) -> int:
        return self._completion_tokens

    def increment_completion_tokens(self, value: int) -> None:
        self._completion_tokens += value

    @completion_tokens.setter
    def completion_tokens(self, value: int) -> None:
        self._completion_tokens = value

    @property
    def prompt_tokens(self) -> int:
        return self._prompt_tokens

    def increment_prompt_tokens(self, value: int) -> None:
        self._prompt_tokens += value

    @prompt_tokens.setter
    def prompt_tokens(self, value: int) -> None:
        self._prompt_tokens = value

    def reset_tokens(self) -> None:
        self.completion_tokens = 0
        self.prompt_tokens = 0

    @property
    def max_completion_tokens(self) -> int:
        return self._max_completion_tokens

    @property
    def model_id(self) -> str:

    @property
    def model_name(self) -> str:

    @property
    def model_vendor(self) -> str:
        raise NotImplementedError("Subclasses must implement this method")

    @property
    def retry_delay(self) -> int:
        if not self._retry_delay:
                self._retry_delay = self._config.value(
                    key_path="ai_model.retry_delay",
                    expected_type=int,
                    expected_min=RETRY_DELAY_EXPECTED_MIN,
                    expected_max=RETRY_DELAY_EXPECTED_MAX,
                    default=RETRY_DELAY_DEFAULT,
                )
            except TypeError as te:
            except ValueError as ve:
                raise ModelError(
                    f"Value '{value}' for retry delay is invalid. Value must be a valid integer 0 or greater."
                ) from ve
            if self._retry_delay < 0:
                raise ModelError(
                    f"Value '{self._retry_delay}' is invalid. Value must be 0 or greater."
                )

        return self._retry_delay

    @property
    def temperature(self) -> float:
        if not self._temperature:
                self._temperature = self._config.value(
                    "ai_model.temperature",
                    expected_type=float,
                    expected_min=TEMPERATURE_EXPECTED_MIN,
                    expected_max=TEMPERATURE_EXPECTED_MAX,
                    default=TEMPERATURE_DEFAULT,
                )
            except TypeError as te:
            except ValueError as ve:
                raise ModelError(
                    f"Value '{value}' for temperature is invalid. Value must be a valid floating point between 0.0 and 1.0."
                ) from ve
            if self._temperature < 0.0 or self._temperature > 1.0:
                raise ModelError(
                    f"Value '{self._temperature}' for temperature is invalid. Value must be between 0.0 and 1.0."
                )

        return self._temperature

    @property
    def stopped_reason(self) -> str:
        return self._stopped_reason

    @stopped_reason.setter
    def stopped_reason(self, stopped_reason: str) -> None:
        self._stopped_reason = stopped_reason

    @property
    def completion_json(self) -> Dict[str, str]:
        """Getter for the completion_json property"""
        return self._completion_json

    @completion_json.setter
    def completion_json(self, completion_json: Dict[str, str]) -> None:
        """Setter for the completion_json property"""
        self._completion_json = completion_json

