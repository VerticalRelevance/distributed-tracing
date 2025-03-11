# Add a New Model Class

## Overview
This guide explains how to add a new model class to the existing Python package that interfaces with AWS Bedrock models.
# Adding a New Model Class to the Python Package

This guide explains how to add a new model class to the existing Python package. The model could 
be one that inferfaces with Amazon Bedrock, or one that makes direct API calls.

## Step 1: Create a New Model File

Create a new Python file in the models directory with a descriptive name for your model. Follow the naming convention of existing model files (e.g., `provider_model_version.py`).

```python
# Example: openai_gpt4_v1.py
```

## Step 2: Import Required Modules

Start your file with the necessary imports:

```python
# pylint: disable=line-too-long
"""
Module for interacting with OpenAI's GPT-4 model.

This module provides a class for generating text using the GPT-4 model,
handling API requests and responses, and processing the returned data.
"""
# pylint: enable=line-too-long

import json
import requests
from models.model import ModelObject, ModelError
from configuration import Configuration

# Define model-specific constants
MAX_TOKENS_EXPECTED_MIN = 0
MAX_TOKENS_EXPECTED_MAX = 8192
MAX_TOKENS_DEFAULT = 1024
```

## Step 3: Create Your Model Class

Define your model class that inherits from `ModelObject`:

```python
class OpenAIGPT4V1(ModelObject):
    # pylint: disable=line-too-long
    """
    Client for OpenAI's GPT-4 model.

    This class handles text generation requests to the GPT-4 model, processes responses,
    and extracts relevant information from the model output.
    """
    # pylint: enable=line-too-long

    def __init__(self, configuration: Configuration):
        """
        Initialize the GPT-4 model client.

        Args:
            configuration: Configuration object containing model settings.
        """
        super().__init__(configuration=configuration)
        self._max_completion_tokens = None
        self._api_key = self._config.str_value("openai.api_key", "")
        self._api_base = self._config.str_value("openai.api_base", "https://api.openai.com/v1")
```

## Step 4: Override the model_client Property

Since we're not using AWS Bedrock, we need to override the `model_client` property:

```python
@property
def model_client(self):
    """
    Create a custom client for the model provider.
    
    For non-Bedrock models, this returns None as we'll handle the API calls directly.
    
    Returns:
        None: This implementation doesn't use boto3 clients
    """
    # We're not using boto3 for this model, so return None
    return None
```

## Step 5: Implement Required Methods

Implement the abstract methods from the `ModelObject` base class:

### 5.1. Implement `generate_text()`

```python
def generate_text(self, prompt):
    """
    Generate text using the GPT-4 model.

    Args:
        prompt (str): The text prompt to send to the model.

    Raises:
        ModelError: If there's an error with the API call or response.
    """
    self._logging_utils.trace(__class__, "start generate_text")
    self._logging_utils.debug(__class__, "prompt:")
    self._logging_utils.debug(__class__, prompt)
    
    # Reset token counters
    self.reset_tokens()
    
    # Configure model parameters
    self._max_completion_tokens = self._config.int_value(
        "ai_model.custom.max_tokens",
        MAX_TOKENS_EXPECTED_MIN,
        MAX_TOKENS_EXPECTED_MAX,
        MAX_TOKENS_DEFAULT,
    )
    
    # Format the request according to the model's requirements
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {self._api_key}"
    }
    
    payload = {
        "model": self.model_id,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": self._max_completion_tokens,
        "temperature": self.temperature
    }
    
    try:
        # Make the API request
        response = requests.post(
            f"{self._api_base}/chat/completions",
            headers=headers,
            json=payload,
            timeout=60
        )
        response.raise_for_status()  # Raise exception for HTTP errors
        
        self._logging_utils.debug(__class__, "response:")
        self._logging_utils.debug(__class__, response.json(), enable_pformat=True)
        
    except requests.RequestException as e:
        self._logging_utils.trace(
            __class__,
            f"end generate_text with API error: {str(e)}",
        )
        raise ModelError(f"API request error: {str(e)}") from e
    
    self._handle_response(response=response)
    self._logging_utils.trace(__class__, "end generate_text")
```

### 5.2. Implement `_handle_response()`

```python
def _handle_response(self, response):
    """
    Process the raw response from the GPT-4 model.

    Args:
        response: Raw response object from the API call.
    """
    self._logging_utils.trace(__class__, "start _handle_response")
    
    # Parse the response JSON
    model_response = response.json()
    self._logging_utils.debug(__class__, "model_response")
    self._logging_utils.debug(__class__, model_response, enable_pformat=True)
    
    # Extract the response text
    response_text = model_response["choices"][0]["message"]["content"]
    
    # Extract JSON content if present
    extracted_json = self._json_utils.extract_json(response_text)
    self._logging_utils.debug(__class__, "Extracted json:")
    self._logging_utils.debug(__class__, extracted_json, enable_pformat=True)
    
    # Parse the JSON content
    data = self._json_utils.json_loads(json_string=extracted_json)
    data = data[0] if isinstance(data, list) else data
    self._logging_utils.debug(__class__, "data:")
    self._logging_utils.debug(__class__, data)
    
    # Store the parsed JSON
    self.completion_json = data
    
    # Update token counts
    self.increment_completion_tokens(value=model_response["usage"]["completion_tokens"])
    self.increment_prompt_tokens(value=model_response["usage"]["prompt_tokens"])
    
    # Set the stop reason
    self.stopped_reason = model_response["choices"][0]["finish_reason"]
    
    self._logging_utils.trace(__class__, "end _handle_response")
```

### 5.3. Implement Required Properties

```python
@property
def model_id(self) -> str:
    """
    Get the model ID for GPT-4.

    Returns:
        str: The model ID string.
    """
    return "gpt-4"

@property
def model_name(self) -> str:
    """
    Get the human-readable name of the model.

    Returns:
        str: The model name.
    """
    return "GPT-4"

@property
def model_vendor(self) -> str:
    """
    Get the vendor name for the model.

    Returns:
        str: The model vendor.
    """
    return "OpenAI"
```

## Step 6: Create a Base Class for Non-Bedrock Models (Optional)

For better organization, you might want to create an intermediate base class for non-Bedrock models:

```python
# In a new file: models/external_model.py

from models.model import ModelObject, ModelError
from configuration import Configuration

class ExternalModelObject(ModelObject):
    """
    Base class for models that don't use AWS Bedrock.
    
    This class extends ModelObject to provide common functionality for external API-based models.
    """
    
    def __init__(self, configuration: Configuration) -> None:
        """
        Initialize an ExternalModelObject with the given configuration.
        
        Args:
            configuration: Configuration object containing model settings and parameters
        """
        super().__init__(configuration=configuration)
        
    @property
    def model_client(self):
        """
        External models don't use boto3 clients.
        
        Returns:
            None: External models handle API calls directly
        """
        return None
    
    def get_api_key(self, key_config_path: str) -> str:
        """
        Get the API key for the external model service.
        
        Args:
            key_config_path: Configuration path for the API key
            
        Returns:
            str: The API key
            
        Raises:
            ModelError: If the API key is not configured
        """
        api_key = self._config.str_value(key_config_path, "")
        if not api_key:
            raise ModelError(f"API key not configured at {key_config_path}")
        return api_key
```

Then your model class would inherit from `ExternalModelObject` instead:

```python
from models.external_model import ExternalModelObject

class OpenAIGPT4V1(ExternalModelObject):
    # Implementation as before, but inheriting from ExternalModelObject
    pass
```

## Step 7: Update the ModelFactory

You might need to update the `ModelFactory` class to handle non-Bedrock models:

```python
# This is likely not necessary if the factory is already generic enough,
# but if needed, you could extend it to handle different types of models.
```

## Step 8: Test Your Model Class

Create a test script to verify that your model class works correctly:

```python
from configuration import Configuration
from models.model import ModelFactory

# Initialize configuration
config = Configuration()

# Create model factory
factory = ModelFactory(configuration=config)

# Get your model instance
model = factory.get_model(
    module_name="openai_gpt4_v1",
    class_name="OpenAIGPT4V1"
)

# Test the model
prompt = "Explain quantum computing in simple terms."
model.generate_text(prompt)

# Print results
print(f"Response: {model.completion_json}")
print(f"Prompt tokens: {model.prompt_tokens}")
print(f"Completion tokens: {model.completion_tokens}")
print(f"Stop reason: {model.stopped_reason}")
```

## Step 2: Place the Module in the Correct Location
├── __init__.py
├── coded_json_to_markdown_formatter.py
├── csv_formatter.py
├── formatter.py
├── jinja2_json_to_markdown_formatter.jinja2
├── jinja2_json_to_markdown_formatter.py
├── provider_model_version.py  # The new formatter

## Step 4: Configure the New Model

## Step 9: Update Configuration

TODO Add the necessary configuration parameters for your model:

```
# Example configuration entries
openai.api_key=your_api_key_here
openai.api_base=https://api.openai.com/v1
ai_model.custom.max_tokens=1024
```

## Step 10: Handle Model-Specific Features

If your model has unique features or requirements:

1. Add model-specific configuration parameters
2. Implement custom handling for model-specific response formats
3. Add any special error handling needed for this model

## Summary

To add a new model class that doesn't rely on AWS Bedrock:

1. Create a new Python file with a descriptive name
2. Define your model class inheriting from `ModelObject` or a new intermediate class like `ExternalModelObject`
3. Override the `model_client` property to handle non-Bedrock API interactions
4. Implement the required abstract methods and properties
5. Add proper error handling and logging
6. Update configuration to include model-specific settings
7. Test your implementation
8. Update documentation

This approach allows you to integrate models from any provider while maintaining a consistent interface across your application.