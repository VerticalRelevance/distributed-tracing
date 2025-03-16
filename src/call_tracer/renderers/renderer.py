from typing import Any, Dict
from common.configuration import Configuration
from common.utilities import GenericUtils, LoggingUtils


class RendererUtils:
    _instance = None

    def __new__(cls, *args, **kwargs):  # pylint: disable=unused-argument
        if not cls._instance:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, configuration: Configuration):
        # pylint: disable=line-too-long
        """
        Initialize the RendererFactory with configuration.

        Args:
            configuration: Configuration object containing settings for formatter instantiation.
        """
        # pylint: enable=line-too-long
        self._config: Configuration = configuration

    @property
    def desired_renderer_class_name(self):
        # pylint: disable=line-too-long
        """
        Retrieves the configured renderer class name from the configuration.

        This method fetches the class name for the renderer from the configuration using a dot-notation path.
        If the configuration value is not found, it returns a default value of "not found".

        Returns:
            str: The configured class name for the renderer, or "not found" if not configured.
        """
        # pylint: enable=line-too-long
        return self._config.str_value("renderer.class.name", "not found")

    @property
    def desired_renderer_module_name(self) -> str:
        # pylint: disable=line-too-long
        """
        Retrieves the configured renderer module name from the configuration.

        This method fetches the module name for the renderer from the configuration using a dot-notation path.
        If the configuration value is not found, it returns a default value of "not found".

        Returns:
            str: The configured module name for the renderer, or "not found" if not configured.
        """
        # pylint: enable=line-too-long
        return self._config.str_value("renderer.module.name", "not found")


class RendererObject:
    def __init__(
        self, configuration: Configuration, data: Dict[str, Any]
    ):
        self._logging_utils = LoggingUtils()
        self._renderer_utils = RendererUtils(configuration=configuration)
        self._config = configuration
        self.data = data

    def render(self):
        raise NotImplementedError("Subclasses must implement the render method")


class RendererFactory:
    _instance = None

    def __new__(cls, *args, **kwargs):  # pylint: disable=unused-argument
        # pylint: disable=line-too-long
        """
        Implement the singleton pattern for the RendererFactory.

        This method ensures that only one instance of the RendererFactory is created and returned
        throughout the application's lifecycle.

        Args:
            cls: The class being instantiated.
            *args: Variable length argument list.
            **kwargs: Arbitrary keyword arguments.

        Returns:
            The singleton instance of the RendererFactory class.
        """
        # pylint: enable=line-too-long
        if not cls._instance:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, configuration: Configuration):
        # pylint: disable=line-too-long
        """
        Initialize the RendererFactory with configuration.

        Args:
            configuration: Configuration object containing settings for formatter instantiation.
        """
        # pylint: enable=line-too-long
        self._generic_utils: GenericUtils = GenericUtils()
        self._config: Configuration = configuration

    def get_renderer(
        self, module_name: str, class_name: str, data: Dict[str, Any]
    ) -> RendererObject:
        # pylint: disable=line-too-long
        """Dynamically load and instantiate a formatter based on module and class names.

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
        renderer_class = self._generic_utils.load_class(
            module_name="renderers." + module_name,
            class_name=class_name,
            package_name="renderers",
        )
        return renderer_class(configuration=self._config, data=data)
