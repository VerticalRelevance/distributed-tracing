from source_analyzer.models.openai_gpt import OpenAiGpt
from source_analyzer.models.model import ModelError


class OpenAiGpt4oMini(OpenAiGpt):

    def __init__(self, configuration):
        super().__init__(configuration)
        self._max_completion_tokens = None

    def generate_text(self, prompt):
        # pylint: disable=line-too-long
        """
        Generate text using the OpenAI GPT-4o mini model.

        Args:
            prompt (str): The input prompt for the model.

        Raises:
            ModelError: If the prompt is empty or if the model fails to generate text.

        Returns:
            None: Results are stored in instance attributes.
        """
        # pylint: enable=line-too-long
        self._logging_utils.trace(__class__, "start generate_text")

        if not prompt:
            raise ModelError("Prompt is empty")

        messages = [
            {
                "role": "system",
                "content": "You are an AI assistant specialized in Python code analysis.",
            },
            {"role": "user", "content": prompt},
        ]

        if "starcoder2" in self.model_name.lower():
            # remove the system message
            messages = messages[1:]

        try:
            # Get a client for the model.
            client = self.model_client
            # Configure a chat completion request.
            chat_completion = client.chat.completions.create(
                messages=messages,
                model=self.model_id,
                temperature=self.temperature,
            )
            # Invoke the model with the prompt.
            response = chat_completion.choices[0].message.content
            self._logging_utils.debug(__class__, "response:")
            self._logging_utils.debug(__class__, response)

            # Extract the generated text from the response.
            self._completion_json = response.choices[0].message.content
            self._stopped_reason = response.choices[0].finish_reason

            # Update token counts
            self.increment_completion_tokens(
                value=chat_completion.usage.completion_tokens
            )
            self.increment_prompt_tokens(value=chat_completion.usage.prompt_tokens)

            self._logging_utils.debug(__class__, "completion_json:")
            self._logging_utils.debug(__class__, self._completion_json)
            self._logging_utils.debug(__class__, "stopped_reason:")
            self._logging_utils.debug(__class__, self._stopped_reason)
        except Exception as e:
            raise ModelError(f"Failed to generate text: {e}") from e

    @property
    def model_id(self) -> str:
        # pylint: disable=line-too-long
        """
        Get the model ID for the OpenAI GPT-4o mini model.

        Returns:
            str: The model ID.
        """
        # pylint: enable=line-too-long
        return "gpt-4o-mini"

    @property
    def model_name(self) -> str:
        # pylint: disable=line-too-long
        """
        Get the name of the OpenAI GPT-4o mini model.

        Returns:
            str: The model name.
        """
        # pylint: enable=line-too-long
        return "GPT-4o mini"
