import sys
import os
import boto3
from configuration import Configuration
from utilities import LoggingUtils, ModelUtils


class ModelError(Exception):
    """Generic error for storage operations, hiding AWS implementation details"""


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

    def generate_text(self, prompt: str) -> str:
        pass

    def get_model_custom_value(
        self, key: str, expected_type: type, expected_min=None, expected_max=None
    ) -> str:
        print(
            f"custom value: {self._config.get_value("ai_model", {}).get("custom", {}).get(key, "")}",
            file=sys.stderr,
        )
        value = self._config.get_value("ai_model", {}).get("custom", {}).get(key, "")
        if not isinstance(value, expected_type):
            raise ModelError(
                f"Expected custom value type {expected_type.__name__}, got {type(value).__name__}"
            )

        print(f"expected_type.__name__: {expected_type.__name__}", file=sys.stderr)
        match expected_type.__name__:
            case "str":
                return str(value)
            case "int":
                try:
                    int_value = int(value)
                    print(
                        f"expected type is int, value: {int_value}, expected_min: {expected_min}, expected_max: {expected_max}",
                        file=sys.stderr,
                    )
                except ValueError as ve:
                    raise ModelError(
                        f"Value '{value}' for {key} is invalid. Value must be a valid integer."
                    ) from ve

                if expected_min is not None:
                    print(
                        f"expected_min: {expected_min} int_value < expected_min: {int_value < expected_min}",
                        file=sys.stderr,
                    )
                    if int_value < expected_min:
                        raise ValueError(
                            f"Value '{int_value}' for {key} is invalid. Value must be greater than or equal to {expected_min}."
                        )
                if expected_max is not None:
                    print(
                        f"expected_max: {expected_max}",
                        file=sys.stderr,
                    )
                    if int_value > expected_max:
                        raise ValueError(
                            f"Value '{int_value}' for {key} is invalid. Value must be less than or equal to {expected_max}."
                        )

                return int_value
            case "float":
                try:
                    float_value = float(value)
                except ValueError as ve:
                    raise ModelError(
                        f"Value '{value}' for {key} is invalid. Value must be a valid float."
                    ) from ve
                if expected_min:
                    if float_value < expected_min:
                        raise ValueError(
                            f"Value '{float_value}' for {key} is invalid. Value must be greater than or equal to {expected_min}."
                        )
                if expected_max:
                    if float_value > expected_max:
                        raise ValueError(
                            f"Value '{float_value}' for {key} is invalid. Value must be less than or equal to {expected_max}."
                        )
                return float_value
            case "bool":
                return value.lower() in ("true", "1", "yes", "on")
            case _:
                raise ModelError(
                    f"Unsupported type {expected_type} for {key}. Supported types are str, int, float, and bool."
                )

    def get_max_llm_retries(self) -> int:
        if self._max_llm_retries is None:
            ai_model: dict = self._config.get_value("ai_model")
            value = os.getenv(
                "MAX_LLM_RETRIES",
                ai_model.get("max_llm_retries", "10"),
            )
            try:
                self._max_llm_retries = int(value)
            except ValueError as ve:
                raise ModelError(
                    f"Value '{value}' for max LLM retries is invalid. Value must be a valid integer zero between 0 and 10."
                ) from ve
            if self._max_llm_retries < 0 or self._max_llm_retries > 10:
                raise ModelError(
                    f"Value '{self._max_llm_retries}' for max LLM retries is invalid. Value must be between 0 and 10."
                )

        return self._max_llm_retries

    def get_model_client(self):
        return boto3.client(
            "bedrock-runtime", region_name=self._model_utils.get_region_name()
        )

    def get_completion_tokens(self) -> int:
        print(f"value to return: {self._completion_tokens}")
        return self._completion_tokens

    def increment_completion_tokens(self, value: int) -> None:
        print(
            f"completion tokens before implement: {self._completion_tokens}",
            file=sys.stderr,
        )
        print(f"value to add: {value}", file=sys.stderr)
        self._completion_tokens += value
        print(
            f"completion tokens after implement: {self._completion_tokens}",
            file=sys.stderr,
        )

    def set_completion_tokens(self, value: int) -> None:
        self._completion_tokens = value

    def get_prompt_tokens(self) -> int:
        return self._prompt_tokens

    def increment_prompt_tokens(self, value: int) -> None:
        self._prompt_tokens += value

    def set_prompt_tokens(self, value: int) -> None:
        self._prompt_tokens = value

    def reset_tokens(self) -> None:
        self.set_completion_tokens(value=0)
        self.set_prompt_tokens(value=0)

    def get_model_id(self) -> str:
        pass

    def get_model_name(self) -> str:
        pass

    def get_model_vendor(self) -> str:
        pass

    def get_retry_delay(self) -> int:
        if not self._retry_delay:
            value = os.getenv(
                "RETRY_DELAY",
                self._config.get_value("ai_model", {}).get("retry_delay", "0"),
            )
            try:
                self._retry_delay = int(value)
            except ValueError as ve:
                raise ModelError(
                    f"Value '{value}' for retry delay is invalid. Value must be a valid integer 0 or greater."
                ) from ve
            if self._retry_delay < 0:
                raise ModelError(
                    f"Value '{self._retry_delay}' is invalid. Value must be 0 or greater."
                )

        return self._retry_delay

    def get_temperature(self) -> float:
        if not self._temperature:
            value = os.getenv(
                "TEMPERATURE",
                self._config.get_value("ai_model", {}).get("temperature", "0.0"),
            )
            try:
                self._temperature = float(value)
            except ValueError as ve:
                raise ModelError(
                    f"Value '{value}' for temperature is invalid. Value must be a valid floating point between 0.0 and 1.0."
                ) from ve
            if self._temperature < 0.0 or self._temperature > 1.0:
                raise ModelError(
                    f"Value '{self._temperature}' for temperature is invalid. Value must be between 0.0 and 1.0."
                )

        return self._temperature

    def get_stop_reason(self) -> str:
        return self._stop_reason

    def set_stop_reason(self, value: str) -> None:
        self._stop_reason = value
