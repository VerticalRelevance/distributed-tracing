# pylint: disable=line-too-long
"""
This module provides formatting functionality through a factory pattern implementation.

The module contains base classes and factories for handling various formatting operations,
particularly JSON formatting. It implements a singleton pattern to ensure consistent formatter
instances across the application.

Classes:
    FormatterError: Custom exception for handling formatting-related errors.
    FormatterObject: Base class for formatter implementations with singleton pattern.
    FormatterFactory: Factory class for dynamically creating formatter instances.

The module supports dynamic loading of formatter implementations and provides a configuration-based
approach to formatter instantiation. It includes utility integration for logging, JSON operations,
and generic functionality.

Typical usage example:
    config = Configuration()
    factory = FormatterFactory(config)
    formatter = factory.get_formatter('json_formatter', 'JsonFormatter')
    formatted_output = formatter.format_json(data)
"""
# pylint: enable=line-too-long

from typing import Dict
from common.configuration import Configuration
from common.utilities import LoggingUtils, JsonUtils, GenericUtils


class FormatterError(Exception):
    # pylint: disable=line-too-long
    """
    A custom exception class for handling formatting-related errors.

    This exception provides a generic error mechanism for various formatting operations,
    allowing detailed error messages to be passed and handled appropriately.

    Attributes:
        message (str): A descriptive error message explaining the formatting issue.
    """
    # pylint: enable=line-too-long

    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)


class FormatterObject:  # pylint: disable=too-few-public-methods
    # pylint: disable=line-too-long
    """
    Base formatter class implementing a singleton pattern for JSON data formatting operations.

    This class serves as an abstract base class for specific formatter implementations. It provides
    core functionality for JSON formatting while enforcing a singleton pattern to ensure only one
    instance exists.

    Attributes:
        _instance (FormatterObject): The singleton instance of the formatter class.
        _logging_utils (LoggingUtils): Utility instance for logging operations.
        _json_utils (JsonUtils): Utility instance for JSON-related operations.
        _generic_utils (GenericUtils): Utility instance for generic operations.
        _config (Configuration): Configuration instance containing formatter settings.

    Example:
        class JsonFormatter(FormatterObject):
            def format_json(self, data, variables=None):
                # Implementation specific formatting logic
                return formatted_output
    """
    # pylint: enable=line-too-long

    _instance = None

    def __new__(cls, *args, **kwargs):  # pylint: disable=unused-argument
        # pylint: disable=line-too-long
        """
        Create a new instance of the formatter class or return the existing singleton instance.

        This method implements the singleton pattern, ensuring that only one instance of the formatter
        class is created throughout the application.

        Args:
            cls: The class object.
            *args: Variable length argument list.
            **kwargs: Arbitrary keyword arguments.

        Returns:
            FormatterObject: The singleton instance of the formatter class.
        """
        # pylint: enable=line-too-long
        if not cls._instance:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, configuration: Configuration):
        # pylint: disable=line-too-long
        """
        Initialize a new instance of the FormatterObject class.

        This method sets up utility objects and configuration for formatter operations.
        It prepares the necessary resources for subsequent formatting tasks.

        Args:
            configuration: A configuration object containing settings and parameters for the formatter.
        """
        # pylint: enable=line-too-long
        self._logging_utils = LoggingUtils()
        self._json_utils = JsonUtils()
        self._generic_utils = GenericUtils()
        self._config = configuration

    def format_json(
        self, data: Dict[str, str], variables: Dict[str, str] = None
    ) -> str:  # pylint: disable=unused-argument
        # pylint: disable=line-too-long
        """
        Format JSON data according to implementation-specific rules.

        This method must be implemented by subclasses to provide specific JSON formatting logic.
        The base implementation raises a NotImplementedError.

        Args:
            data: The input JSON data to be formatted as a dictionary.
            variables: Additional variables that might be used in formatting. Defaults to None.

        Returns:
            The formatted output as a string.

        Raises:
            NotImplementedError: If the method is not overridden by a subclass.
        """
        # pylint: enable=line-too-long
        raise NotImplementedError("Subclasses must implement this method")


class FormatterFactory:
    # pylint: disable=line-too-long
    """
    A singleton factory class for creating and managing formatter instances dynamically.

    This class implements the Singleton pattern to ensure only one formatter factory exists in the
    application. It provides functionality to dynamically load and instantiate formatter classes
    based on configuration settings.

    Attributes:
        _instance: The singleton instance of the factory.
        _generic_utils: Utility instance for generic operations.
        _config: Configuration instance used for formatter initialization.

    Example:
        Create a formatter factory:
            >>> config = Configuration()
            >>> factory = FormatterFactory(config)
            >>> json_formatter = factory.get_formatter('json_formatter', 'JsonFormatter')
    """
    # pylint: enable=line-too-long

    _instance = None

    def __new__(cls, *args, **kwargs):  # pylint: disable=unused-argument
        # pylint: disable=line-too-long
        """
        Implement the singleton pattern for the FormatterFactory.

        This method ensures that only one instance of the FormatterFactory is created and returned
        throughout the application's lifecycle.

        Args:
            cls: The class being instantiated.
            *args: Variable length argument list.
            **kwargs: Arbitrary keyword arguments.

        Returns:
            The singleton instance of the FormatterFactory class.
        """
        # pylint: enable=line-too-long
        if not cls._instance:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, configuration: Configuration):
        # pylint: disable=line-too-long
        """
        Initialize the FormatterFactory with configuration.

        Args:
            configuration: Configuration object containing settings for formatter instantiation.
        """
        # pylint: enable=line-too-long
        self._generic_utils: GenericUtils = GenericUtils()
        self._config: Configuration = configuration

    def get_formatter(self, module_name: str, class_name: str) -> FormatterObject:
        # pylint: disable=line-too-long
        """
        Dynamically load and instantiate a formatter based on module and class names.

        This method uses reflection to load a formatter class from a specified module
        and create an instance with the current configuration.

        Args:
            module_name: Name of the module containing the formatter class.
            class_name: Name of the formatter class to instantiate.

        Returns:
            An instance of the specified formatter class.

        Raises:
            ImportError: If the module cannot be imported.
            AttributeError: If the specified class is not found in the module.
        """
        # pylint: enable=line-too-long
        formatter_class = self._generic_utils.load_class(
            module_name="formatters." + module_name,
            class_name=class_name,
            package_name="formatters",
        )
        return formatter_class(configuration=self._config)
