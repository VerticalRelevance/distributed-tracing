import json
import boto3
from botocore.exceptions import ClientError
from ..utilities import ModelUtils
from .model import ModelObject
from .model import ModelError
from ..configuration import Configuration


class MetaLlama3_2_3b_instruct_v1_0(ModelObject):
    def __init__(self, configuration: Configuration):
        self._model_utils = ModelUtils(configuration=configuration)

    def get_model_client(self):
        return boto3.client("bedrock-runtime", region_name="us-west-2")

    def get_model_id(self):
        return "meta.llama3-2-3b-instruct-v1:0"

    def get_model_name(self):
        return "Llama 3.2 3B Instruct"

    def get_max_llm_retries(self) -> int:
        return 3

    def get_retry_delay(self) -> int:
        return 5

    def generate_text(self, *args, **kwargs) -> str:
        prompt = kwargs.get("prompt")
        formatted_prompt = f"""
<|begin_of_text|><|start_header_id|>user<|end_header_id|>
{prompt}
<|eot_id|>
<|start_header_id|>assistant<|end_header_id|>
"""
        # Format the request payload using the model's native structure.
        native_request = {
            "prompt": formatted_prompt,
            "max_gen_len": 512,
            "temperature": self,
        }
        # Convert the native request to JSON.
        request = json.dumps(native_request)
        # Create a Bedrock Runtime client
        # TODO get region_name from AWS_REGION environment variable
        try:
            client = boto3.client("bedrock-runtime", region_name="us-west-2")
            # Invoke the model with the request.
            response = client.invoke_model(modelId=self.get_model_id(), body=request)
        except ClientError as ce:
            error_code = ce.response["Error"]["Code"]
            raise ModelError(f"Bedrock invoke_model found: {str(ce)}") from ce

        # Decode the response body.
        model_response = json.loads(response["body"].read())
        # Extract and return the response text.
        response_text = model_response["generation"]

        return response_text
