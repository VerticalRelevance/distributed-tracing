# Adding a New Formatter Class to the Python Package

## Overview
This guide explains how to add a new formatter class to the existing formatter package. The 
package uses a factory pattern to dynamically load and instantiate formatter classes.

## Step 1: Create a New Formatter Module

Create a new Python file for your formatter class. Name it according to its functionality, for example `csv_formatter.py`.

```python
# pylint: disable=line-too-long
"""
CsvFormatter module that provides functionality for formatting data into CSV format.

This module implements a singleton pattern for the formatter and provides methods for transforming
data into CSV format.
"""
# pylint: enable=line-too-long

from typing import Dict
from formatters.formatter import FormatterObject
from configuration import Configuration


class CsvFormatter(FormatterObject):  # pylint: disable=too-few-public-methods
    # pylint: disable=line-too-long
    """
    A formatter class that converts data into CSV format.

    This class extends FormatterObject to provide specialized formatting capabilities for transforming
    data into CSV format.

    Attributes:
        _config: Configuration settings for the formatter.
        _logging_utils: Utility for debug logging operations.
    """
    # pylint: enable=line-too-long

    def __init__(self, configuration: Configuration):
        # pylint: disable=line-too-long
        """
        Initialize the CsvFormatter with the given configuration.

        Parameters:
            configuration: The configuration object containing settings and parameters for the formatter.
        """
        # pylint: enable=line-too-long
        super().__init__(configuration=configuration)

    def format_json(self, data: Dict[str, str], variables: Dict[str, str] = None) -> str:
        # pylint: disable=line-too-long
        """
        Transform JSON data into CSV format.

        Parameters:
            data: A dictionary containing the data to be formatted.
            variables: A dictionary of additional variables. Defaults to None.

        Returns:
            A CSV-formatted string of the data.
        """
        # pylint: enable=line-too-long
        # Your implementation here
        csv_lines = []
        
        # Example implementation - customize based on your needs
        if not data:
            return ""
            
        # Add headers
        headers = list(data.keys())
        csv_lines.append(",".join(headers))
        
        # Add data rows
        # This is a simplified example - adjust based on your data structure
        values = [str(data[key]) for key in headers]
        csv_lines.append(",".join(values))
        
        return "\n".join(csv_lines)
```

## Step 2: Place the Module in the Correct Location

Save your new formatter module in the `formatters` package directory. The directory structure should look like:

```
formatters/
├── __init__.py
├── formatter.py
├── coded_json_to_markdown_formatter.py
├── jinja2_json_to_markdown_formatter.py
└── csv_formatter.py  # The new formatter
```

## Step 4: Configure the New Formatter

Add the necessary settings to the `src/source_analyzer/config.yaml` configuration file. For example:

```yaml
formatter:
  class:
    name: CsvFormatter
  module:
    name: csv_formatter
```

If the new formatter class needs configuration specific to itself, add that configuration to the
formatter configuration as well. For example:

```yaml
formatter:
  class:
    name: CsvFormatter
  module:
    name: csv_formatter
  csv:
      delimiter: ",",
      quotechar: "\"",
      lineterminator: "\n"
```

## Step 5: Use Your New Formatter

Now you can use your new formatter through the factory pattern:

```python
from configuration import Configuration
from formatters.formatter import FormatterFactory

# Create configuration and factory
config = Configuration()
factory = FormatterFactory(config)

# Get your new formatter
csv_formatter = factory.get_formatter('csv_formatter', 'CsvFormatter')

# Use the formatter
data = {"name": "John", "age": "30", "city": "New York"}
csv_output = csv_formatter.format_json(data)
print(csv_output)
```

## Best Practices

1. **Follow the Singleton Pattern**: Ensure your formatter class follows the singleton pattern implemented in the base `FormatterObject` class.

2. **Document Your Code**: Include comprehensive docstrings that explain what your formatter does, its parameters, and return values.

3. **Handle Errors Gracefully**: Use the `FormatterError` class for error handling.

4. **Add Unit Tests**: Create tests for your new formatter to ensure it works correctly.

5. **Follow Coding Standards**: Adhere to the project's coding standards, including pylint rules.

6. **Update Documentation**: If the project has separate documentation, update it to include your new formatter.

By following these steps, you can successfully add a new formatter class to the existing Python package while maintaining its design patterns and structure.