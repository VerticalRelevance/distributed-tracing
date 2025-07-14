# pylint: disable=line-too-long
"""
Module for interacting with Meta's Llama 3.2 3B Instruct model through AWS Bedrock.

This module provides a class for generating text using the Meta Llama 3.2 3B Instruct model,
handling the specific formatting requirements and response parsing for this model.
"""
# pylint: enable=line-too-long

import json
from botocore.exceptions import ClientError
from source_analyzer.models.model import BedrockModelObject, ModelException
from common.configuration import Configuration

MAX_GEN_LEN_EXPECTED_MIN = 0
MAX_GEN_LEN_EXPECTED_MAX = 204800
MAX_GEN_LEN_DEFAULT = 6144


class MetaLlama323bInstructV1(BedrockModelObject):
    # pylint: disable=line-too-long
    """
    Client for interacting with Meta's Llama 3.2 3B Instruct model via AWS Bedrock.

    This class handles the specific prompt formatting, request structure, and response
    parsing required for the Llama 3.2 3B Instruct model. It provides methods for
    generating text and processing responses, including JSON extraction and token
    usage tracking.

    Attributes:
        completion_json (dict): Structured data extracted from the model's response,
            containing overall analysis summary and priorities.
    """
    # pylint: enable=line-too-long

    def __init__(self, configuration: Configuration):
        # pylint: disable=line-too-long
        """
        Initialize the Llama 3.2 3B Instruct model client.

        Args:
            configuration (Configuration): Configuration object containing model settings
                and parameters for the Llama 3.2 3B Instruct model.
        """
        # pylint: enable=line-too-long

        super().__init__(configuration=configuration)

    def generate_text(self, prompt):
        # pylint: disable=line-too-long
        """
        Generate text using the Llama 3.2 3B Instruct model.

        This method formats the prompt according to the model's expected input format,
        sends the request to the model, and processes the response. The prompt is
        wrapped with the appropriate chat template tokens for the Llama 3.2 format.

        Args:
            prompt (str): The input prompt to send to the model.

        Raises:
            ModelException: If there's an error invoking the model through AWS Bedrock.
        """
        # pylint: enable=line-too-long

        self._logger.trace("start generate_text")

        self._logger.debug("prompt:")
        self._logger.debug(prompt)
        formatted_prompt = f"""
<|begin_of_text|><|start_header_id|>user<|end_header_id|>
{prompt}
<|eot_id|>
<|start_header_id|>assistant<|end_header_id|>
"""
        # Format the request payload using the model's native structure.
        max_gen_len: int = self._config.int_value(
            "ai_model.custom.max_gen_len",
            MAX_GEN_LEN_EXPECTED_MIN,
            MAX_GEN_LEN_EXPECTED_MAX,
            MAX_GEN_LEN_DEFAULT,
        )
        self._logger.debug(f"max_gen_len: {max_gen_len}")
        self.max_completion_tokens = max_gen_len
        native_request = {
            "prompt": formatted_prompt,
            "max_gen_len": max_gen_len,
            "temperature": self.temperature,
        }
        self._logger.debug("native_request:")
        self._logger.debug(native_request, enable_pformat=True)

        # Convert the native request to JSON.
        request = json.dumps(native_request)

        try:
            # Get a client for the model.
            client = self.model_client
            # Invoke the model with the request.
            response = client.invoke_model(modelId=self.model_id, body=request)
            self._logger.debug("response:")
            self._logger.debug(response, enable_pformat=True)
        except ClientError as ce:
            error_code = ce.response["Error"]["Code"]
            self._logger.trace(
                __class__,
                f"end generate_text with Bedrock invoke_model error ({error_code}): {str(ce)}",
            )
            raise ModelException(
                f"Bedrock invoke_model error ({error_code}): {str(ce)}"
            ) from ce

        # return self._handle_response(response=response)
        self._handle_response(response=response)
        self._logger.trace("end generate_text")

    def _handle_response(self, response):
        # pylint: disable=line-too-long
        """
        Process the raw response from the model.

        This method extracts the generated text from the model's response,
        parses any JSON content, and updates token usage statistics. It specifically
        looks for an overall_analysis_summary structure and extracts the message
        and priorities from the JSON response.

        Args:
            response: The raw response from the model invocation containing the
                response body and metadata.
        """
        # pylint: enable=line-too-long

        self._logger.trace("start _handle_response")
        # Decode the response body.
        model_response: dict = json.loads(response["body"].read())
        self._logger.debug("model_response keys")
        self._logger.debug(model_response.keys(), enable_pformat=True)
        self._logger.debug("model_response")
        self._logger.debug(model_response, enable_pformat=True)

        # Extract and return the response text.
        response_text = model_response["generation"]
        self._logger.debug(
            __class__, f"response_text: {response_text}", enable_pformat=True
        )

        extracted_json = self._json_utils.extract_json(response_text)
        self._logger.debug(
            __class__, f"Extracted code blocks type: {type(extracted_json)}"
        )
        self._logger.debug(
            __class__, f"Extracted code blocks len: {len(extracted_json)}"
        )
        self._logger.debug("Extracted json:")
        self._logger.debug(extracted_json, enable_pformat=True)

        data = self._json_utils.json_loads(json_string=extracted_json)
        data: dict = data[0] if isinstance(data, list) else data
        self._logger.debug("data:")
        self._logger.debug(data, enable_pformat=True)

        self.completion_json = {}
        self.completion_json["overall_analysis_summary"] = data.get(
            "overall_analysis_summary"
        ).get("message")
        self.completion_json["priorities"] = data.get("overall_analysis_summary").get(
            "priorities"
        )

        self.increment_prompt_tokens(value=model_response["prompt_token_count"])
        self.increment_completion_tokens(value=model_response["generation_token_count"])
        self.stopped_reason = model_response["stop_reason"]

        # Return the response text.
        self._logger.debug(
            __class__, f"response text: {response_text}", enable_pformat=True
        )
        self._logger.trace("end _handle_response")

    @property
    def model_id(self) -> str:
        # pylint: disable=line-too-long
        """
        Get the AWS Bedrock model ID for Llama 3.2 3B Instruct.

        Returns:
            str: The AWS Bedrock model identifier for the Llama 3.2 1B Instruct model.
                Note: Despite the class name suggesting 3B, this returns the 1B model ID.
        """
        # pylint: enable=line-too-long

        return "us.meta.llama3-2-1b-instruct-v1:0"

    @property
    def model_name(self) -> str:
        # pylint: disable=line-too-long
        """
        Get the human-readable name of the model.

        Returns:
            str: The display name of the Llama 3.2 3B Instruct model.
        """
        # pylint: enable=line-too-long

        return "Llama 3.2 3B Instruct"

    @property
    def model_vendor(self) -> str:
        # pylint: disable=line-too-long
        """
        Get the vendor name for the model.

        Returns:
            str: The name of the model vendor (Meta).
        """
        # pylint: enable=line-too-long

        return "Meta"
