# pylint: disable=line-too-long
"""
Module for interacting with Anthropic's Claude 3 Sonnet model via AWS Bedrock.

This module provides a class for generating text using the Claude 3 Sonnet model,
handling API requests and responses, and processing the returned data.
"""
# pylint: enable=line-too-long

import json
from botocore.exceptions import ClientError, TokenRetrievalError
from common.configuration import Configuration
from source_analyzer.models import model
from source_analyzer.models.model import BedrockModelObject, ModelException

MAX_TOKENS_EXPECTED_MIN = 0
MAX_TOKENS_EXPECTED_MAX = 134144
MAX_TOKENS_DEFAULT = 2048


class AnthropicClaude3Sonnet20240229V1(BedrockModelObject):
    # pylint: disable=line-too-long
    """
    Client for Anthropic's Claude 3 Sonnet model via AWS Bedrock.

    This class handles text generation requests to the Claude 3 Sonnet model, processes responses,
    and extracts relevant information from the model output.

    Attributes:
        _max_completion_tokens (int): Maximum number of tokens for model completion.
        completion_json (dict): Processed JSON data from the model response.
        stopped_reason (str): Reason why the model stopped generating text.
    """
    # pylint: enable=line-too-long

    def __init__(self, configuration: Configuration):
        # pylint: disable=line-too-long
        """
        Initialize the Claude 3 Sonnet model client.

        Args:
            configuration (Configuration): Configuration object containing model settings.
        """
        # pylint: enable=line-too-long
        super().__init__(configuration=configuration)
        self._max_completion_tokens = None

    def generate_text(self, prompt):
        # pylint: disable=line-too-long
        """
        Generate text using the Claude 3 Sonnet model.

        This method sends a prompt to the Claude 3 Sonnet model and processes the response.
        It handles token configuration, request formatting, and error handling.

        Args:
            prompt (str): The text prompt to send to the model.

        Raises:
            ModelException: If there's an error with token retrieval or model invocation.

        Returns:
            None: Results are stored in instance attributes.
        """
        # pylint: enable=line-too-long
        self._logger.trace(__class__.__name__, "start generate_text")

        self._logger.debug(__class__.__name__, "prompt:")
        self._logger.debug(__class__.__name__, prompt)

        system_prompt = """You are Claude, an AI assistant created by Anthropic to be helpful,
            harmless, and honest. Your goal is to provide informative and substantive
            responses to queries while avoiding potential harms. You are also an expert
            in Python source code tracing, with emphasis on identifying critical trace points.
            """
        messages = [{"role": "user", "content": prompt}]
        self.max_completion_tokens = self._config.int_value(
            "ai_model.custom.max_tokens",
            MAX_TOKENS_EXPECTED_MIN,
            MAX_TOKENS_EXPECTED_MAX,
            MAX_TOKENS_DEFAULT,
        )
        self._logger.debug(__class__.__name__, f"system_prompt: {system_prompt}")
        self._logger.debug(__class__.__name__, f"max_tokens: {self.max_completion_tokens}")
        request = json.dumps(
            {
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": self.max_completion_tokens,
                "system": system_prompt,
                "messages": messages,
            }
        )

        try:
            # Get a client for the model.
            client = self.model_client
            # Invoke the model with the request.
            response = client.invoke_model(modelId=self.model_id, body=request)
            self._logger.debug(__class__.__name__, "response:")
            self._logger.debug(__class__.__name__, response, enable_pformat=True)
        except TokenRetrievalError as tre:  # expired or otherwise invalid AWS token
            self._logger.debug(__class__.__name__, f"raising ModelException for TokenRetrievalError: {str(tre)}")
            raise ModelException(
                f"TokenRetrievalError error: {str(tre)}",
                model.EXCEPTION_LEVEL_ERROR,
            ) from tre
        except ClientError as ce:
            error_code = ce.response["Error"]["Code"]
            self._logger.trace(
                __class__.__name__,
                f"end generate_text with Bedrock invoke_model error ({error_code}): {str(ce)}"
            )
            raise ModelException(
                f"Bedrock invoke_model error ({error_code}): {str(ce)}", model.EXCEPTION_LEVEL_WARN
            ) from ce

        self._handle_response(response=response)
        self._logger.trace(__class__.__name__, "end generate_text")

    def _handle_response(self, response):
        # pylint: disable=line-too-long
        """
        Process the raw response from the Claude 3 Sonnet model.

        This method extracts text from the model response, processes any JSON content,
        and updates token usage statistics.

        Args:
            response: Raw response object from the AWS Bedrock API.

        Returns:
            None: Results are stored in instance attributes.
        """
        # pylint: enable=line-too-long
        self._logger.trace(__class__.__name__, "start _handle_response")

        # Decode the response body.
        model_response = json.loads(response["body"].read())
        self._logger.debug(__class__.__name__, "model_response")
        self._logger.debug(__class__.__name__, model_response, enable_pformat=False)

        # Extract and return the response text.
        self._logger.debug(
            __class__.__name__, f"len(content): {len(model_response["content"])}"
        )
        response_text = model_response["content"][0].get("text")
        self._logger.debug(__class__.__name__, f"usage: {model_response.get("usage")}")
        extracted_json = self._json_utils.extract_json(response_text)
        self._logger.debug(__class__.__name__, "Extracted json:")
        self._logger.debug(__class__.__name__, extracted_json, enable_pformat=True)

        data = self._json_utils.json_loads(json_string=extracted_json)
        data = data[0] if isinstance(data, list) else data
        self._logger.debug(__class__.__name__, "data:")
        self._logger.debug(__class__.__name__, data)
        self.completion_json = data

        # Increment the
        self.increment_completion_tokens(value=model_response["usage"]["output_tokens"])
        self.increment_prompt_tokens(value=model_response["usage"]["input_tokens"])
        self.stopped_reason = model_response["stop_reason"]

        self._logger.trace(__class__.__name__, "end _handle_response")

    @property
    def model_id(self) -> str:
        # pylint: disable=line-too-long
        """
        Get the AWS Bedrock model ID for Claude 3 Sonnet.

        Returns:
            str: The model ID string.
        """
        # pylint: enable=line-too-long
        return "anthropic.claude-3-sonnet-20240229-v1:0"

    @property
    def model_name(self) -> str:
        # pylint: disable=line-too-long
        """
        Get the human-readable name of the model.

        Returns:
            str: The model name.
        """
        # pylint: enable=line-too-long
        return "Claude 3 Sonnet"

    @property
    def model_vendor(self) -> str:
        # pylint: disable=line-too-long
        """
        Get the vendor name for the model.

        Returns:
            str: The vendor name.
        """
        # pylint: enable=line-too-long
        return "Anthropic"
