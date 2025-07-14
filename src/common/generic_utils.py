# pylint: disable=line-too-long
"""
A utility module providing general-purpose functionality for dynamic class loading
and boolean value interpretation.

This module contains the GenericUtils class, which implements the singleton pattern
and provides utility methods for dynamic class loading from modules and packages,
as well as string-to-boolean conversion using common truthy value representations.
"""
# pylint: enable=line-too-long

import importlib


class GenericUtils:
    # pylint: disable=line-too-long
    """
    A singleton utility class providing general-purpose functionality for dynamic class loading
    and boolean value interpretation.

    This class implements the singleton pattern and provides utility methods for dynamic
    class loading from modules and packages, as well as string-to-boolean conversion using
    common truthy value representations.

    Features:
        - Singleton pattern implementation
        - Dynamic class loading from modules
        - Flexible boolean value interpretation
        - Package-aware module importing

    Methods:
        __new__(cls, *args, **kwargs): Creates singleton instance
        load_class(module_name, class_name, package_name): Dynamically loads a class
        is_truthy(value): Determines if a string value represents a truthy value

    Dynamic Class Loading:
        Supports loading classes from modules with:
        - Relative and absolute imports
        - Package-aware module resolution
        - Proper error handling for missing modules/classes

    Truthy Value Interpretation:
        Recognizes the following as True:
        - "1", "true", "yes", "on", "y"
        - Case-insensitive matching
        - None values (default to True)
        All other values are considered False

    Example:
        >>> utils = GenericUtils()  # Creates or returns existing instance
        >>> # Dynamic class loading
        >>> MyClass = utils.load_class("my_module", "MyClass", "my_package")
        >>> # Truthy value checking
        >>> utils.is_truthy("yes")  # Returns True
        >>> utils.is_truthy("no")   # Returns False

    Error Handling:
        load_class():
            - ImportError: When module cannot be found
            - AttributeError: When class doesn't exist in module

    Dependencies:
        - importlib: For dynamic module importing
        - typing: For type hints

    Notes:
        - The singleton pattern ensures consistent behavior across the application
        - String comparisons for truthy values are case-insensitive
        - Whitespace is stripped from truthy value inputs
    """
    # pylint: enable=line-too-long

    _instance = None

    def __new__(cls, *args, **kwargs):  # pylint: disable=unused-argument
        # pylint: disable=line-too-long
        """
        Creates and returns a singleton instance of the GenericUtils class.

        This method ensures that only one instance of the GenericUtils class is created
        throughout the application, implementing the singleton design pattern.

        Args:
            cls (type): The class being instantiated.
            *args: Variable length argument list.
            **kwargs: Arbitrary keyword arguments.

        Returns:
            Utilities: The singleton instance of the GenericUtils class.
        """
        # pylint: enable=line-too-long

        if not cls._instance:
            cls._instance = super().__new__(cls)
        return cls._instance

    def load_class(
        self, module_name: str, class_name: str, package_name: str
    ) -> object:
        # pylint: disable=line-too-long
        """
        Dynamically loads a class from a specified module and package.

        This method attempts to import a module and retrieve a class by name
        from that module. It raises an ImportError if the module cannot be
        found and an AttributeError if the class does not exist within the
        module.

        Args:
            module_name (str): The name of the module to import.
            class_name (str): The name of the class to retrieve.
            package_name (str): The package name to use for relative imports.

        Returns:
            object: The class object if found.

        Raises:
            ImportError: If the module cannot be imported.
            AttributeError: If the class cannot be found in the module.
        """
        # pylint: enable=line-too-long

        try:
            module = importlib.import_module(module_name, package_name)
            return getattr(module, class_name)
        except ImportError as ie:
            raise ImportError(f"Module {module_name} not found") from ie
        except AttributeError as ae:
            raise AttributeError(
                f"Class {class_name} not found in module {module_name}"
            ) from ae

    def is_truthy(self, value: str) -> bool:
        # pylint: disable=line-too-long
        """
        Determines if a value is considered "truthy".

        Checks if the value is equivalent to common truthy representations like "1", "true", "yes".

        Args:
            value (str): The value to check for truthiness.

        Returns:
            bool: True if the value is considered truthy, False otherwise.

        Examples:
            >>> utils = GenericUtils()
            >>> utils.is_truthy("1")
            True
            >>> utils.is_truthy("true")
            True
            >>> utils.is_truthy("false")
            False
        """
        # pylint: enable=line-too-long

        # If no value exists, return True
        if value is None:
            return True

        # Convert to lowercase for case-insensitive comparison
        value = str(value).lower().strip()

        # Return result based on common truthy values
        return value in ["1", "true", "yes", "on", "y"]
