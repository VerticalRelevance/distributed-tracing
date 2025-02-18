class ModelError(Exception):
    """Generic error for storage operations, hiding AWS implementation details"""


class ModelObject:
    def get_model_id(self):
        pass

    def get_model_name(self):
        pass

    def get_native_request(self, formatted_prompt: str) -> dict:
        pass

    def get_max_llm_retries(self):
        pass

    def get_retry_delay(self):
        pass

    def generate_text(self, *args, **kwargs) -> str:
        pass
