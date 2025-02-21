from abc import ABC, abstractmethod
from utilities import LoggingUtils, JsonUtils, Utilities
from configuration import Configuration


class FormatterObject(ABC):
    def __init__(self, configuration: Configuration):
        """
        Initializes a new instance of the JsonToMarkdownFormatter class.

        This method is called automatically when a new instance of the class is created.
        It initializes the instance with any necessary attributes or configurations.

        """
        super().__init__()

        self._logging_utils = LoggingUtils()
        self._json_utils = JsonUtils()
        self._utils = Utilities()
        self._config = configuration

    @abstractmethod
    def format_text(self, text_to_format: str, **kwargs):
        pass


class FormatterFactory:

    _instance = None

    def __new__(cls, *args, **kwargs):  # pylint: disable=unused-argument
        """
        Creates and returns a new instance of the FormatterFactory class.

        This method is responsible for implementing the singleton pattern, ensuring that only one
        instance of the Configuration class is created.

        Parameters:
            cls (type): The class object.
            *args: Variable length argument list.
            **kwargs: Arbitrary keyword arguments.

        Returns:
            FormatterFactory: The singleton instance of the FormatterFactory class.

        """
        if not cls._instance:
            cls._instance = super().__new__(cls)
            # print("Configuration.__new__", file=sys.stderr)
        return cls._instance

    def __init__(self, configuration: Configuration):
        self._utils = Utilities()
        self._config = configuration

    def get_formatter(self, module_name: str, class_name: str) -> FormatterObject:
        """
        Retrieves a formatter instance based on the provided module name, class name, and package name.

        This method uses the Utilities class to load the specified class from the given module and
        package. It then creates and returns an instance of the loaded class.

        Parameters:
            module_name (str): The name of the module containing the formatter class.
            class_name (str): The name of the formatter class to be instantiated.
            package_name (str): The name of the package containing the module.

        Returns:
            Formatter: An instance of the formatter class.

        Raises:
            ImportError: If the specified module or class cannot be imported.
            AttributeError: If the specified class is not found in the module.
        """
        # print(
        #     f"module_name: {module_name}, class_name: {class_name}, package_name: {package_name}",
        #     file=sys.stderr,
        # )

        formatter_class = self._utils.load_class(
            module_name="formatters." + module_name,
            # module_name=module_name,
            class_name=class_name,
            package_name="formatters",
        )
        return formatter_class(configuration=self._config)
