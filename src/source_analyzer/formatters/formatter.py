from typing import Dict
from configuration import Configuration
from utilities import LoggingUtils, JsonUtils, GenericUtils


class FormatterError(Exception):
    """
    A custom exception class for handling formatting-related errors.

    This exception provides a generic error mechanism for various formatting operations,
    allowing detailed error messages to be passed and handled appropriately.

    Attributes:
        message (str): A descriptive error message explaining the formatting issue.
    """

    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)


class FormatterObject:  # pylint: disable=too-few-public-methods
    def __init__(self, configuration: Configuration):
        """
        Initialize a new instance of the FormatterObject class.

        This method sets up utility objects and configuration for formatter operations.
        It prepares the necessary resources for subsequent formatting tasks.

        Args:
            configuration (Configuration): A configuration object containing
                settings and parameters for the formatter.

        Attributes:
            _logging_utils (LoggingUtils): Utility for logging operations.
            _json_utils (JsonUtils): Utility for JSON-related operations.
            _generic_utils (GenericUtils): Generic utility functions.
            _config (Configuration): Configuration object for the formatter.
        """
        self._logging_utils = LoggingUtils()
        self._json_utils = JsonUtils()
        self._generic_utils = GenericUtils()
        self._config = configuration

    def format_json(
        self, data: Dict[str, str], variables: Dict[str, str] = None
    ) -> str:  # pylint: disable=unused-argument
        """
        Abstract method to format JSON data.

        This method must be implemented by subclasses to provide specific
        JSON formatting logic. The base implementation raises a NotImplementedError.

        Args:
            data (Dict[str, str]): The input data to be formatted.
            variables (Dict[str, str], optional): Additional variables
                that might be used in formatting. Defaults to None.

        Returns:
            str: The formatted output.

        Raises:
            NotImplementedError: If the method is not overridden by a subclass.
        """
        raise NotImplementedError("Subclasses must implement this method")


class FormatterFactory:
    _instance = None

    def __new__(cls, *args, **kwargs):  # pylint: disable=unused-argument
        """
        Implement the singleton pattern for the FormatterFactory.

        This method ensures that only one instance of the FormatterFactory
        is created and returned throughout the application's lifecycle.

        Args:
            cls (type): The class being instantiated.
            *args: Variable length argument list.
            **kwargs: Arbitrary keyword arguments.

        Returns:
            FormatterFactory: The singleton instance of the class.
        """
        if not cls._instance:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, configuration: Configuration):
        """
        Initialize the FormatterFactory with configuration.

        Args:
            configuration (Configuration): Configuration object for the factory.

        Attributes:
            _generic_utils (GenericUtils): Utility for generic operations.
            _config (Configuration): Configuration for the factory.
        """
        self._generic_utils: GenericUtils = GenericUtils()
        self._config: Configuration = configuration

    def get_formatter(self, module_name: str, class_name: str) -> FormatterObject:
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
        formatter_class = self._generic_utils.load_class(
            module_name="formatters." + module_name,
            class_name=class_name,
            package_name="formatters",
        )
        return formatter_class(configuration=self._config)
