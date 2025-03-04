import json
from botocore.exceptions import ClientError, TokenRetrievalError
from configuration import Configuration
from models.model import ModelObject, ModelError


class AnthropicClaude3Sonnet20240229V1(ModelObject):
    def __init__(self, configuration: Configuration):
        super().__init__(configuration=configuration)

    def generate_text(self, prompt) -> str:
        self._logging_utils.trace(__class__, "start generate_text")

        self._logging_utils.debug(__class__, "prompt:")
        self._logging_utils.debug(__class__, prompt)

        system_prompt = """You are Claude, an AI assistant created by Anthropic to be helpful,
            harmless, and honest. Your goal is to provide informative and substantive
            responses to queries while avoiding potential harms. You are also an expert
            in Python source code tracing, with emphasis on identifying critical trace points.
            """
        messages = [{"role": "user", "content": prompt}]
        self._max_completion_tokens = self.get_model_custom_value(
            "max_tokens", expected_type=int, expected_min=0, expected_max=134144
        )
        self._logging_utils.debug(__class__, f"system_prompt: {system_prompt}")
        self._logging_utils.debug(
            __class__, f"max_tokens: {self._max_completion_tokens}"
        )
        request = json.dumps(
            {
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": self._max_completion_tokens,
                "system": system_prompt,
                "messages": messages,
            }
        )

        try:
            # Get a client for the model.
            client = self.get_model_client()
            # Invoke the model with the request.
            response = client.invoke_model(modelId=self.get_model_id(), body=request)
            self._logging_utils.debug(__class__, "response:")
            self._logging_utils.debug(__class__, response, enable_pformat=True)
        except TokenRetrievalError as tre:  # expired or otherwise invalid AWS token
            self._logging_utils.debug(__class__, f"tre: {str(tre)}")
            self._logging_utils.debug(__class__, "tre structure:")
            self._logging_utils.debug(__class__, tre.__dict__)
            raise ModelError(f"TokenRetrievalError error: {str(tre)}") from tre
        except ClientError as ce:
            error_code = ce.response["Error"]["Code"]
            self._logging_utils.trace(
                __class__,
                f"end generate_text with Bedrock invoke_model error ({error_code}): {str(ce)}",
            )
            raise ModelError(
                f"Bedrock invoke_model error ({error_code}): {str(ce)}"
            ) from ce

        # Decode the response body.
        model_response = json.loads(response["body"].read())
        self._logging_utils.debug(__class__, "model_response")
        self._logging_utils.debug(__class__, model_response, enable_pformat=True)

        # Extract and return the response text.
        self._logging_utils.debug(
            __class__, f"len(content): {len(model_response["content"])}"
        )
        response_text = model_response["content"][0].get("text")
        self._logging_utils.debug(__class__, f"usage: {model_response.get("usage")}")

        self.increment_completion_tokens(value=model_response["usage"]["output_tokens"])
        self.increment_prompt_tokens(value=model_response["usage"]["input_tokens"])
        self.set_stop_reason(value=model_response["stop_reason"])

        self._logging_utils.trace(__class__, "end generate_text")
        return response_text

    def get_model_id(self) -> str:
        return "anthropic.claude-3-sonnet-20240229-v1:0"

    def get_model_name(self) -> str:
        return "Claude 3 Sonnet"

    def get_model_vendor(self) -> str:
        return "Anthropic"
