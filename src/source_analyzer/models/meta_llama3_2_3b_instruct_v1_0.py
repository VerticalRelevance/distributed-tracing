import json
from botocore.exceptions import ClientError
from configuration import Configuration

MAX_GEN_LEN_EXPECTED_MIN = 0
MAX_GEN_LEN_EXPECTED_MAX = 204800
MAX_GEN_LEN_DEFAULT = 6144


class MetaLlama3_2_3b_InstructV1_0(ModelObject):
    def __init__(self, configuration: Configuration):
        super().__init__(configuration=configuration)

    def generate_text(self, prompt):
        self._logging_utils.trace(__class__, "start generate_text")

        self._logging_utils.debug(__class__, "prompt:")
        self._logging_utils.debug(__class__, prompt)
        formatted_prompt = f"""
<|begin_of_text|><|start_header_id|>user<|end_header_id|>
{prompt}
<|eot_id|>
<|start_header_id|>assistant<|end_header_id|>
"""
        # Format the request payload using the model's native structure.
        max_gen_len: int = self._config.value(
            "ai_model.custom.max_gen_len",
            expected_type=int,
            expected_min=MAX_GEN_LEN_EXPECTED_MIN,
            expected_max=MAX_GEN_LEN_EXPECTED_MAX,
            default=MAX_GEN_LEN_DEFAULT,
        )
        self._logging_utils.debug(__class__, f"max_gen_len: {max_gen_len}")
        self._max_completion_tokens = max_gen_len
        native_request = {
            "prompt": formatted_prompt,
            "max_gen_len": max_gen_len,
            "temperature": self.temperature,
        }
        self._logging_utils.debug(__class__, "native_request:")
        self._logging_utils.debug(__class__, native_request, enable_pformat=True)

        # Convert the native request to JSON.
        request = json.dumps(native_request)

        try:
            # Get a client for the model.
            client = self.model_client
            # Invoke the model with the request.
            response = client.invoke_model(modelId=self.model_id, body=request)
            self._logging_utils.debug(__class__, "response:")
            self._logging_utils.debug(__class__, response, enable_pformat=True)
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
        model_response: dict = json.loads(response["body"].read())
        self._logging_utils.debug(__class__, "model_response keys")
        self._logging_utils.debug(__class__, model_response.keys(), enable_pformat=True)
        self._logging_utils.debug(__class__, "model_response")
        self._logging_utils.debug(__class__, model_response, enable_pformat=True)

        self.increment_prompt_tokens(value=model_response["prompt_token_count"])
        self.increment_completion_tokens(value=model_response["generation_token_count"])
        self.stopped_reason = model_response["stop_reason"]

        self._logging_utils.debug(
            __class__, f"response text: {response_text}", enable_pformat=True
        )
        self._logging_utils.trace(__class__, "end _handle_response")

    @property
    def model_id(self) -> str:
        return "us.meta.llama3-2-1b-instruct-v1:0"

    @property
    def model_name(self) -> str:
        return "Llama 3.2 3B Instruct"

    @property
    def model_vendor(self) -> str:
        return "Meta"
