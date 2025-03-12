import json
import openai
from common.configuration import Configuration
from common.utilities import Boto3Utils
from source_analyzer.models.model import ModelObject


class OpenAiGpt(ModelObject):
    def __init__(self, configuration: Configuration):
        # pylint: disable=line-too-long
        """
        Initialize the Claude 3 Sonnet model client.

        Args:
            configuration: Configuration object containing model settings.
        """
        # pylint: enable=line-too-long
        super().__init__(configuration=configuration)
        self._max_completion_tokens = None
        self._boto3_utils = Boto3Utils(configuration=configuration)
        self._api_key = None

    def generate_text(self, prompt):
        pass

    @property
    def model_client(self):
        if self._api_key is None:
            secret_value = self._boto3_utils.get_secret_value(
                secret_name="",
                region_name=self._model_utils.get_region_name(),
            )
            print(f"api_key: {self._api_key}")
            self._api_key = json.loads(secret_value).get("OPENAI_API_SECRET_KEY")

        return openai.OpenAI(api_key=self._api_key)

    @property
    def model_vendor(self) -> str:
        # pylint: disable=line-too-long
        """
        Get the vendor name for the model.

        Returns:
            str: The vendor name.
        """
        # pylint: enable=line-too-long
        return "OpenAI"

    @property
    def model_id(self) -> str:
        # pylint: disable=line-too-long
        """
        Get the model ID.

        Returns:
            str: The model ID.
        """
        # pylint: enable=line-too-long
        raise NotImplementedError("Subclasses must implement this method")

    @property
    def model_name(self) -> str:
        # pylint: disable=line-too-long
        """
        Get the name of the model.

        Returns:
            str: The model name.
        """
        # pylint: enable=line-too-long
        raise NotImplementedError("Subclasses must implement this method")
