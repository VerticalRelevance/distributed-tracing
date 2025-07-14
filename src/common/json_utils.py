# pylint: disable=line-too-long
"""
JSON Utilities Module

This module provides a comprehensive utility class for JSON-related operations with singleton pattern implementation.
The JsonUtils class offers various methods for handling JSON serialization, deserialization, and extraction of JSON
blocks from text content.

Key Features:
    - JSON serialization with automatic datetime handling
    - JSON deserialization from strings
    - Code block extraction from markdown-formatted text
    - JSON block extraction with fallback handling
    - Singleton pattern implementation for consistent instance management
    - Comprehensive logging integration

Classes:
    JsonUtils: Main utility class providing JSON operations with singleton pattern

Dependencies:
    - json: Standard library for JSON operations
    - re: Regular expression operations for text parsing
    - datetime: Date and time handling
    - common.logging_utils.LoggingUtils: Custom logging utilities

Usage Example:
    >>> from json_utils import JsonUtils
    >>> json_utils = JsonUtils()
    >>> data = {'name': 'example', 'timestamp': datetime.now()}
    >>> json_string = json_utils.json_dumps_with_datetime_serialization(data)
    >>> parsed_data = json_utils.json_loads(json_string)
"""
# pylint: disable=line-too-long

import json
import re
from datetime import datetime
from common.logging_utils import LoggingUtils


class JsonUtils:
    # pylint: disable=line-too-long
    """
    A utility class for JSON-related operations with singleton pattern implementation.

    This class provides various utility methods for handling JSON operations, including
    serialization, deserialization, and extraction of JSON blocks from text. It implements
    the singleton pattern to ensure only one instance exists throughout the application.

    Features:
        - JSON serialization with datetime support
        - JSON deserialization
        - Code block extraction from text
        - JSON block extraction from text
        - Singleton pattern implementation

    Methods:
        __new__(cls, *args, **kwargs): Creates singleton instance
        __init__(): Initializes the class with logging utilities
        json_loads(json_string): Deserializes JSON string to Python object
        json_dumps_with_datetime_serialization(obj, json_options): Serializes object to JSON string
        handle_datetime_serialization(obj): Converts datetime objects to ISO format
        extract_code_blocks(text, block_type): Extracts code blocks of specified type
        extract_json(text): Extracts JSON blocks from text

    Example:
        >>> json_utils = JsonUtils()  # Creates or returns existing instance
        >>> data = {'timestamp': datetime.now(), 'value': 42}
        >>> json_str = json_utils.json_dumps_with_datetime_serialization(data)
        >>> print(json_str)
        {"timestamp": "2023-12-20T10:30:00", "value": 42}

    Notes:
        - The class uses LoggingUtils for debug and warning messages
        - DateTime objects are automatically serialized to ISO format strings
        - JSON extraction supports markdown-style code blocks

    Dependencies:
        - json: For JSON serialization/deserialization
        - re: For regular expression operations
        - datetime: For datetime handling
        - LoggingUtils: For logging functionality
    """
    # pylint: enable=line-too-long

    _instance = None

    def __new__(cls, *args, **kwargs):  # pylint: disable=unused-argument
        # pylint: disable=line-too-long
        """
        Creates and returns a singleton instance of the JsonUtils class.

        This method ensures that only one instance of the class is created
        throughout the application, implementing the singleton design pattern.

        Args:
            cls (type): The class being instantiated.
            *args: Variable length argument list.
            **kwargs: Arbitrary keyword arguments.

        Returns:
            JsonUtils: The singleton instance of the JsonUtils class.
        """
        # pylint: enable=line-too-long

        if not cls._instance:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        # pylint: disable=line-too-long
        """
        Initializes the JsonUtils class.
        """
        # pylint: enable=line-too-long

        self._logger = LoggingUtils().get_class_logger(class_name=__class__.__name__)

    def json_loads(self, json_string: str):
        # pylint: disable=line-too-long
        """
        Deserializes a JSON formatted string to a Python object.

        This method takes a JSON formatted string as input and deserializes
        it to a Python dictionary

        Args:
            json_string (str): The JSON string to deserialize.

        Returns:
            dict: The deserialized Python object.
        """
        # pylint: enable=line-too-long

        return json.loads(json_string)

    def json_dumps_with_datetime_serialization(self, obj, json_options=None):
        # pylint: disable=line-too-long
        """
        Serializes an object to a JSON formatted string with datetime serialization.

        This method takes an object and serializes it to a JSON formatted string using the
        'json.dumps' function. It uses the 'default' parameter of 'json.dumps' to specify a custom
        serialization function, which is 'self.handle_datetime_serialization'. This custom
        serialization function is responsible for serializing datetime objects to their ISO
        formatted string representation.

        Args:
            obj: The object to be serialized.
            json_options (dict, optional): Additional options to be passed to the 'json.dumps' function.

        Returns:
            str: The JSON formatted string representation of the object.

        Example:
            >>> json_utils = JsonUtils()
            >>> data = {'name': 'John', 'age': 30, 'timestamp': datetime.now()}
            >>> json_string = json_utils.json_dumps_with_datetime_serialization(data)
            >>> print(json_string)
            {"name": "John", "age": 30, "timestamp": "2022-01-01T12:00:00"}
        """
        # pylint: enable=line-too-long

        return json.dumps(
            obj, default=self.handle_datetime_serialization, **(json_options or {})
        )

    def handle_datetime_serialization(self, obj):
        # pylint: disable=line-too-long
        """
        Serializes a datetime object to its ISO formatted string representation.

        This method takes a datetime object as input and returns its ISO formatted string
        representation using the 'isoformat()' method of the datetime object. If the input object
        is not a datetime object, a TypeError is raised.

        Args:
            obj (datetime): The datetime object to be serialized.

        Returns:
            str: The ISO formatted string representation of the datetime object.

        Raises:
            TypeError: If the input object is not a datetime object.

        Example:
            >>> utils = JsonUtils()
            >>> dt = datetime(2022, 1, 1, 12, 0, 0)
            >>> iso_string = utils.handle_datetime_serialization(dt)
            >>> print(iso_string)
            '2022-01-01T12:00:00'
        """
        # pylint: enable=line-too-long

        if isinstance(obj, datetime):
            return obj.isoformat()
        raise TypeError(f"Type {type(obj)} not serializable")

    def extract_code_blocks(self, text: str, block_type: str) -> list | str:
        # pylint: disable=line-too-long
        """
        Extract all code blocks of a specific type from the given input text.

        This method uses regular expressions to find and extract all code blocks of the specified type
        from the input text. Code blocks are expected to be formatted in markdown style with triple backticks.

        Args:
            text (str): The input text containing code blocks.
            block_type (str): The type of code block to extract (e.g., 'json', 'python').

        Returns:
            list | str: A list of extracted code blocks or a single string if only one block is found.
        """
        # pylint: enable=line-too-long

        self._logger.debug(__class__.__name__, "start extract_code_blocks")
        self._logger.debug(__class__.__name__, "end extract_code_blocks")
        return re.findall(rf"```{block_type}\s*(.*?)\s*```", text, re.DOTALL)

    def extract_json(self, text: str) -> list | str:
        # pylint: disable=line-too-long
        """
        Extract the first JSON block from the given input text.

        This method finds and extracts the first JSON code block from the input text.
        JSON blocks are expected to be formatted in markdown style with triple backticks and 'json' identifier.

        Args:
            text (str): The input text containing JSON code blocks.

        Returns:
            list | str: The extracted JSON block as a string, or an empty JSON object string "{}" if no JSON blocks are found.
        """
        # pylint: enable=line-too-long

        self._logger.debug(__class__.__name__, "start extract_json")
        json_blocks = self.extract_code_blocks(text, "json")
        if json_blocks:
            self._logger.debug(
                __class__, f"type(json_blocks): {type(json_blocks)}"
            )
            self._logger.debug(
                __class__,
                f"extract_json json_blocks: "
                f"{json_blocks[0] if isinstance(json_blocks, list) else json_blocks}",
                enable_pformat=False,
            )
            self._logger.debug(__class__.__name__, "end extract_json")
            return json_blocks[0] if isinstance(json_blocks, list) else json_blocks
        self._logger.warning(__class__.__name__, "No json blocks found")
        self._logger.debug(__class__.__name__, "end extract_json empty")

        return "{}"
