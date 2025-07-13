# pylint: disable=line-too-long
"""
This module provides formatting functionality through a factory pattern implementation.

The module contains base classes and factories for handling various formatting operations,
particularly JSON formatting. It implements a singleton pattern to ensure consistent formatter
instances across the application.

Classes:
    FormatterUtils: Utility class for managing formatter configuration with singleton pattern.
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
from common.generic_utils import GenericUtils
from common.logging_utils import LoggingUtils
from common.configuration import Configuration
from common.json_utils import JsonUtils

class FormatterUtils:
    # pylint: disable=line-too-long
    """
    A utility class for managing formatter configuration with singleton pattern implementation.

    This class provides methods for retrieving formatter-related configuration values from
    either environment variables or a configuration object. It implements the singleton pattern
    to ensure consistent formatter configuration throughout the application.

    Features:
        - Singleton pattern implementation
        - Environment variable override support
        - Configuration fallback values
        - Formatter class and module name retrieval

    Attributes:
        _instance: The singleton instance of the FormatterUtils class.
        _config: Configuration object containing formatter settings.

    Methods:
        __new__(cls, *args, **kwargs): Creates singleton instance
        __init__(configuration): Initializes with Configuration object
        get_desired_formatter_class_name(): Retrieves formatter class name
        get_desired_formatter_module_name(): Retrieves formatter module name

    Configuration Priority:
        1. Environment variables (FORMATTER_CLASS_NAME, FORMATTER_MODULE_NAME)
        2. Configuration object values (formatter.class.name, formatter.module.name)

    Example:
        >>> config = Configuration()
        >>> formatter_utils = FormatterUtils(config)
        >>> class_name = formatter_utils.get_desired_formatter_class_name()
        >>> module_name = formatter_utils.get_desired_formatter_module_name()

    Environment Variables:
        - FORMATTER_CLASS_NAME: Override for formatter class name
        - FORMATTER_MODULE_NAME: Override for formatter module name

    Configuration Keys:
        - formatter.class.name: Default formatter class name
        - formatter.module.name: Default formatter module name

    Dependencies:
        - os: For environment variable access
        - Configuration: For default configuration values
    """
    # pylint: enable=line-too-long

    _instance = None

    def __new__(cls, *args, **kwargs):  # pylint: disable=unused-argument
        # pylint: disable=line-too-long
        """
        Creates and returns a singleton instance of the FormatterUtils class.

        This method ensures that only one instance of the class is created
        throughout the application, implementing the singleton design pattern.

        Args:
            cls (type): The class being instantiated.
            *args: Variable length argument list.
            **kwargs: Arbitrary keyword arguments.

        Returns:
            FormatterUtils: The singleton instance of the FormatterUtils class.
        """
        # pylint: enable=line-too-long

        if not cls._instance:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, configuration: Configuration):
        # pylint: disable=line-too-long
        """
        Initializes a new instance of the FormatterUtils class.

        This method sets up the FormatterUtils instance with a configuration object
        that will be used to retrieve formatter settings. Since this class implements
        the singleton pattern, this initialization will only take effect the first time
        an instance is created.

        Args:
            configuration (Configuration): The configuration object containing formatter settings.
                                        This object should provide a 'value' method to retrieve
                                        configuration properties.

        Note:
            Due to the singleton implementation, subsequent initializations with different
            configuration objects will not affect the existing instance.
        """
        # pylint: enable=line-too-long

        self._config = configuration

    def get_desired_formatter_class_name(self) -> str:
        # pylint: disable=line-too-long
        """
        Retrieves the desired formatter class name from configuration.

        This method returns the formatter class name based on the following priority:
        1. FORMATTER_CLASS_NAME environment variable if set
        2. Value from configuration using the key 'formatter.class.name'

        Returns:
            str: The name of the formatter class to be used.

        Example:
            >>> formatter_utils = FormatterUtils(config)
            >>> formatter_class_name = formatter_utils.get_desired_formatter_class_name()
            >>> print(formatter_class_name)
            'JsonFormatter'
        """
        # pylint: enable=line-too-long

        return self._config.str_value("formatter.class.name", "not found")

    def get_desired_formatter_module_name(self) -> str:
        # pylint: disable=line-too-long
        """
        Retrieves the desired formatter module name from configuration.

        This method returns the formatter module name based on the following priority:
        1. FORMATTER_MODULE_NAME environment variable if set
        2. Value from configuration using the key 'formatter.module.name'

        Returns:
            str: The name of the module containing the formatter class.

        Example:
            >>> formatter_utils = FormatterUtils(config)
            >>> formatter_module_name = formatter_utils.get_desired_formatter_module_name()
            >>> print(formatter_module_name)
            'formatters.json'
        """
        # pylint: enable=line-too-long

        return self._config.str_value("formatter.module.name", "not found")

class FormatterError(Exception):
    # pylint: disable=line-too-long
    """
    A custom exception class for handling formatting-related errors.

    This exception provides a generic error mechanism for various formatting operations,
    allowing detailed error messages to be passed and handled appropriately.

    Attributes:
        message (str): A descriptive error message explaining the formatting issue.

    Example:
        >>> try:
        ...     # Some formatting operation
        ...     pass
        ... except Exception as e:
        ...     raise FormatterError(f"Formatting failed: {str(e)}")
    """
    # pylint: enable=line-too-long

    def __init__(self, message: str):
        # pylint: disable=line-too-long
        """
        Initialize a new FormatterError instance.

        Args:
            message (str): A descriptive error message explaining the formatting issue.
        """
        # pylint: enable=line-too-long

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
        _logger (LoggingUtils): Utility instance for logging operations.
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
            configuration (Configuration): A configuration object containing settings and parameters
                                        for the formatter.
        """
        # pylint: enable=line-too-long

        self._logger = LoggingUtils().get_class_logger(class_name=__class__.__name__)
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
            data (Dict[str, str]): The input JSON data to be formatted as a dictionary.
            variables (Dict[str, str], optional): Additional variables that might be used in formatting.
                                                Defaults to None.

        Returns:
            str: The formatted output as a string.

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
            FormatterFactory: The singleton instance of the FormatterFactory class.
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
            configuration (Configuration): Configuration object containing settings for formatter
                                        instantiation.
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
            module_name (str): Name of the module containing the formatter class.
            class_name (str): Name of the formatter class to instantiate.

        Returns:
            FormatterObject: An instance of the specified formatter class.

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
