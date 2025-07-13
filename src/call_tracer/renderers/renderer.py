# pylint: disable=line-too-long
"""
Utility classes for rendering data based on configuration settings.

This module provides utilities for dynamically loading and instantiating renderer classes
based on configuration. It includes a singleton RendererUtils class for accessing renderer
configuration, a base RendererObject class that defines the interface for renderers, and
a RendererFactory for creating renderer instances.
"""
# pylint: enable=line-too-long

from typing import Any, Dict
from common.logging_utils import LoggingUtils
from common.configuration import Configuration
from common.generic_utils import GenericUtils

class RendererUtils:
    # pylint: disable=line-too-long
    """
    Utility class for accessing renderer configuration.

    This singleton class provides access to renderer-specific configuration values,
    such as the desired renderer class name and module name. It ensures consistent
    access to configuration throughout the application.
    """
    # pylint: enable=line-too-long

    _instance = None

    def __new__(cls, *args, **kwargs):  # pylint: disable=unused-argument
        # pylint: disable=line-too-long
        """
        Implement the singleton pattern for the RendererUtils.

        This method ensures that only one instance of the RendererUtils is created and returned
        throughout the application's lifecycle.

        Args:
            cls: The class being instantiated.
            *args: Variable length argument list.
            **kwargs: Arbitrary keyword arguments.

        Returns:
            The singleton instance of the RendererUtils class.
        """
        # pylint: enable=line-too-long

        if not cls._instance:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, configuration: Configuration):
        # pylint: disable=line-too-long
        """
        Initialize the RendererUtils with configuration.

        Args:
            configuration: Configuration object containing settings for renderer instantiation.
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
    # pylint: disable=line-too-long
    """
    Base class for all renderer objects.

    This abstract class defines the interface that all renderer implementations must follow.
    It provides common initialization for renderers and requires subclasses to implement
    the render method.
    """
    # pylint: enable=line-too-long

    _instance = None

    def __new__(cls, *args, **kwargs):  # pylint: disable=unused-argument
        # pylint: disable=line-too-long
        """
        Create a new instance of the renderer class or return the existing singleton instance.

        This method implements the singleton pattern, ensuring that only one instance of the renderer
        class is created throughout the application.

        Args:
            cls: The class object.
            *args: Variable length argument list.
            **kwargs: Arbitrary keyword arguments.

        Returns:
            RendererObject: The singleton instance of the renderer class.
        """
        # pylint: enable=line-too-long

        if not cls._instance:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(
        self, configuration: Configuration, data: Dict[str, Any]
    ):
        # pylint: disable=line-too-long
        """
        Initialize a renderer object with configuration and data.

        Args:
            configuration: Configuration object containing settings for the renderer.
            data: Dictionary containing the data to be rendered.
        """
        # pylint: enable=line-too-long

        self._logger = LoggingUtils().get_class_logger(class_name=__class__.__name__)
        self._renderer_utils = RendererUtils(configuration=configuration)
        self._config = configuration
        self.data = data

    def render(self):
        # pylint: disable=line-too-long
        """
        Render the data according to the implementation in subclasses.

        This is an abstract method that must be implemented by subclasses.

        Raises:
            NotImplementedError: If the subclass does not implement this method.
        """
        # pylint: enable=line-too-long

        raise NotImplementedError("Subclasses must implement the render method")


class RendererFactory:
    # pylint: disable=line-too-long
    """
    Factory class for creating renderer instances.

    This singleton class is responsible for dynamically loading and instantiating renderer classes
    based on provided module and class names. It uses reflection to create the appropriate renderer
    for the given data.
    """
    # pylint: enable=line-too-long

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
            configuration: Configuration object containing settings for renderer instantiation.
        """
        # pylint: enable=line-too-long

        self._generic_utils: GenericUtils = GenericUtils()
        self._config: Configuration = configuration

    def get_renderer(
        self, module_name: str, class_name: str, data: Dict[str, Any]
    ) -> RendererObject:
        # pylint: disable=line-too-long
        """
        Dynamically load and instantiate a renderer based on module and class names.

        This method uses reflection to load a renderer class from a specified module
        and create an instance with the current configuration and data.

        Args:
            module_name: Name of the module containing the renderer class.
            class_name: Name of the renderer class to instantiate.
            data: Dictionary containing the data to be rendered.

        Returns:
            An instance of the specified renderer class.

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
