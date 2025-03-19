# pylint: disable=line-too-long
"""
Configuration Management Module

This module provides a singleton Configuration class for loading, managing,
and accessing configuration settings from YAML files with robust error handling
and validation.

Key Features:
    - Singleton pattern implementation
    - Safe YAML configuration file loading
    - Configuration value retrieval and modification
    - Comprehensive error handling for file and parsing issues

Classes:
    Configuration: A configuration management class with methods for loading
    and accessing configuration values.
"""
# pylint: enable=line-too-long

from pathlib import Path
import yaml
from common.parameterized_property import ParameterizedProperty


class Configuration:
    # pylint: disable=line-too-long
    """
    A singleton configuration management class for loading and accessing configuration settings.

    This class provides a robust mechanism for loading configuration files, with comprehensive
    error handling, validation, and safe access to configuration values. It follows the
    singleton pattern to ensure only one configuration instance exists.

    Attributes:
        _instance (Configuration): The single instance of the Configuration class.
        _config_content (Dict[str, Any]): Loaded configuration content.
    """
    # pylint: enable=line-too-long

    _instance = None

    def __new__(cls, *args, **kwargs):  # pylint: disable=unused-argument
        # pylint: disable=line-too-long
        """
        Creates and returns a new instance of the Configuration class.

        This method implements the singleton pattern, ensuring that only one instance of the Configuration
        class is created.

        Parameters:
            cls (type): The class object.
            *args: Variable length argument list.
            **kwargs: Arbitrary keyword arguments.

        Returns:
            Configuration: The singleton instance of the Configuration class.
        """
        # pylint: enable=line-too-long
        if not cls._instance:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, config_file_path: str) -> None:
        # pylint: disable=line-too-long
        """
        Initialize the Configuration instance by loading a configuration file.

        Args:
            config_file_path (str): Path to the YAML configuration file to load.
        """
        # pylint: enable=line-too-long
        self._config_content: Configuration = None
        self.safe_load_config(config_file_path)

    def __str__(self):
        # pylint: disable=line-too-long
        """
        Return a string representation of the configuration content.

        Returns:
            str: A formatted string representation of the configuration content.
        """
        # pylint: enable=line-too-long

        def dict_to_string(d, prefix: str = ""):
            if isinstance(d, dict):
                return (
                    "{"
                    + f"\n{prefix}".join(
                        f"{k}: {dict_to_string(v, prefix=prefix+"    ")}"
                        for k, v in sorted(d.items())
                    )
                    + "}"
                )
            if isinstance(d, list):
                return (
                    "[\n"
                    + f"\n{prefix}".join(
                        dict_to_string(x, prefix=prefix + "    ") for x in d
                    )
                    + "\n]"
                )
            return str(d)

        return dict_to_string(self._config_content)

    def safe_load_config(self, file_path: str) -> None:
        # pylint: disable=line-too-long
        """
        Safely load a configuration YAML file with comprehensive error handling.

        Args:
            file_path (str): Path to the YAML file to load.

        Raises:
            FileNotFoundError: If the file doesn't exist.
            PermissionError: If there are insufficient permissions to read the file.
            yaml.YAMLError: For YAML parsing errors.
            ValueError: If the file is empty or doesn't contain valid YAML content.
            TypeError: If the file content is not a dictionary.
        """
        # pylint: enable=line-too-long
        try:
            # Convert to Path object for better path handling
            path: Path = Path(file_path)

            # Check if file exists
            if not path.exists():
                raise FileNotFoundError(f"The file {file_path} does not exist")

            # Check if path is actually a file
            if not path.is_file():
                raise IsADirectoryError(f"{file_path} is not a file")

            # Check if file is empty
            if path.stat().st_size == 0:
                raise ValueError(f"The file {file_path} is empty")

            # Check file extension
            if path.suffix.lower() not in [".yaml", ".yml"]:
                raise ValueError(
                    f"File {file_path} does not have a .yaml or .yml extension"
                )

            # Attempt to read and parse the YAML file
            with path.open("r", encoding="utf-8") as file:
                try:
                    # Use safe_load instead of load for security
                    self._config_content = yaml.safe_load(file)

                    # Check if content is None or not a dictionary
                    if self._config_content is None:
                        raise ValueError(
                            f"The file {file_path} contains no valid YAML content"
                        )
                    if not isinstance(self._config_content, dict):
                        raise TypeError(
                            f"The file {file_path} must contain a YAML dictionary/object"
                        )

                    return

                except yaml.YAMLError as e:
                    # Handle specific YAML parsing errors
                    if isinstance(e, yaml.scanner.ScannerError):
                        raise yaml.YAMLError(
                            f"YAML syntax error in {file_path}: {str(e)}"
                        )
                    if isinstance(e, yaml.parser.ParserError):
                        raise yaml.YAMLError(
                            f"YAML parsing error in {file_path}: {str(e)}"
                        )

                    raise yaml.YAMLError(
                        f"Error parsing YAML file {file_path}: {str(e)}"
                    )

        except PermissionError as pe:
            raise PermissionError(
                f"Insufficient permissions to read {file_path}"
            ) from pe
        except UnicodeDecodeError as ude:
            raise UnicodeDecodeError(
                f"The file {file_path} is not valid UTF-8 encoded text"
            ) from ude
        except Exception as e:  # pylint: disable=broad-exception-caught
            raise Exception(  # pylint: disable=broad-exception-raised
                f"Unexpected error reading {file_path}: {str(e)}"
            ) from e

    def validate_config(self) -> bool:
        # pylint: disable=line-too-long
        """
        Validate the loaded configuration against a predefined schema.

        Returns:
            bool: True if the configuration is valid, False otherwise.

        Note:
            This is a placeholder method for future implementation of configuration validation.
        """
        # pylint: enable=line-too-long
        # validate the loaded configuration against a predefined schema
        # FUTURE add configuration validation

        return True

    def items(self):
        # pylint: disable=line-too-long
        """
        Return a copy of the configuration items.

        Returns:
            dict: A copy of the configuration content.
        """
        # pylint: enable=line-too-long
        return self._config_content.copy()

    def _config_getter(self, key_path: str, default_value=None):
        # pylint: disable=line-too-long
        """
        Retrieve a value from a nested configuration dictionary using a dot-notation path.

        This is an internal helper method used by other configuration getters. It traverses a nested
        dictionary structure using the provided dot-notation path. If any segment of the path is not
        found or if any intermediate value is not a dictionary, it returns the default_value.

        Args:
            key_path (str): Period-delimited path to the configuration value (e.g., 'database.host.port').
            default_value (Any, optional): Value to return if the key_path is not found or if any part of
                the path is invalid. Defaults to None.

        Returns:
            Any: The value found at the specified path in the configuration dictionary, or the default_value
                if the path is not found.

        Examples:
            Get a deeply nested configuration value:
                >>> config._config_getter('database.primary.connection.port', default_value=5432)

            Get a top-level configuration value:
                >>> config._config_getter('app_name', default_value='MyApp')

        """
        # pylint: enable=line-too-long

        keys = key_path.split(".")

        # Start with the config dictionary
        value = self._config_content

        for key in keys:
            # Check if current is a dictionary and contains the key
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                # Key not found, use the default value
                value = None

        # Return the final value
        return default_value if value is None else value

    @ParameterizedProperty
    def list_value(
        self,
        key_path,
        default_value=None,
    ) -> list:
        # pylint: disable=line-too-long
        """
        Retrieve a configuration value and ensure it is a list.

        Args:
            key_path (str): Path to the configuration value in the configuration hierarchy.
            default_value (list, optional): Value to return if the key_path is not found. If
                provided, this value must also be a list. Defaults to None.

        Returns:
            list: The configuration value as a list.

        Raises:
            TypeError: If the retrieved value or default value is not a list.

        Examples:
            >>> allowed_hosts = config.list_value('security.allowed_hosts', default_value=['localhost'])
            >>> replicas = config.list_value('database.replicas')
        """
        # pylint: enable=line-too-long

        list_value = self._config_getter(key_path=key_path, default_value=default_value)
        if not isinstance(list_value, list):
            raise TypeError(
                f"Value '{list_value}' for {key_path} is invalid. Value must be a list."
            )

        return list_value

    @ParameterizedProperty
    def str_value(
        self,
        key_path,
        default_value=None,
    ) -> str:
        # pylint: disable=line-too-long
        """
        Retrieve a configuration value and ensure it is a string.

        Args:
            key_path (str): Path to the configuration value in the configuration hierarchy.
            default_value (str, optional): Value to return if the key_path is not found. If provided,
                this value must also be a string. Defaults to None.

        Returns:
            str: The configuration value as a string.

        Raises:
            TypeError: If the retrieved value or default value is not a string.

        Examples:
            >>> api_url = config.str_value('service.api.endpoint', default_value='https://api.default.com')
            >>> conn_str = config.str_value('database.connection_string')
        """
        # pylint: enable=line-too-long

        str_value = self._config_getter(key_path=key_path, default_value=default_value)
        if not isinstance(str_value, str):
            raise TypeError(
                f"Value '{str_value}' for {key_path} is invalid. Value must be a string."
            )

        return str_value

    @ParameterizedProperty
    def int_value(
        self,
        key_path,
        expected_min=None,
        expected_max=None,
        default_value=None,
    ) -> int:
        # pylint: disable=line-too-long
        """
        Retrieve and convert a configuration value to an integer with optional range validation.

        Args:
            key_path (str): Path to the configuration value in the configuration hierarchy.
            expected_min (int, optional): Minimum allowed value for the integer. Defaults to None.
            expected_max (int, optional): Maximum allowed value for the integer. Defaults to None.
            default_value (int, optional): Value to return if the key_path is not found. Defaults to None.

        Returns:
            int: The configuration value converted to an integer.

        Raises:
            TypeError: If the value cannot be converted to an integer.
            ValueError: If the value is outside the specified range.

        Examples:
            >>> max_retries = config.int_value('app.max_retries', expected_min=0, expected_max=5)
        """
        # pylint: enable=line-too-long

        int_value = self._config_getter(key_path=key_path, default_value=default_value)
        try:
            _ = int(int_value)
        except ValueError as ve:
            raise TypeError(
                f"Type {type(int_value)} of value '{int_value}' for {key_path} is invalid. "
                f"Value must be a valid integer."
            ) from ve
        if expected_min is not None:
            if int_value < expected_min:
                raise ValueError(
                    f"Value '{int_value}' for {key_path} is invalid. "
                    f"Value must be greater than or equal to {expected_min}."
                )
        if expected_max is not None:
            if int_value > expected_max:
                raise ValueError(
                    f"Value '{int_value}' for {key_path} is invalid. "
                    f"Value must be less than or equal to {expected_max}."
                )

        return int_value

    @ParameterizedProperty
    def float_value(
        self,
        key_path,
        expected_min=None,
        expected_max=None,
        default_value=None,
    ) -> float:
        # pylint: disable=line-too-long
        """
        Retrieve and convert a configuration value to a float with optional range validation.

        Args:
            key_path (str): Path to the configuration value in the configuration hierarchy.
            expected_min (float, optional): Minimum allowed value for the float. Defaults to None.
            expected_max (float, optional): Maximum allowed value for the float. Defaults to None.
            default_value (float, optional): Value to return if the key_path is not found. Defaults to None.

        Returns:
            float: The configuration value converted to a floating-point number.

        Raises:
            TypeError: If the value cannot be converted to a float.
            ValueError: If the value is outside the specified range.

        Examples:
            >>> timeout = config.float_value('app.timeout', expected_min=0.1, expected_max=30.0)
        """
        # pylint: enable=line-too-long
        float_value = self._config_getter(
            key_path=key_path, default_value=default_value
        )
        try:
            float_value = float(float_value)
        except ValueError as ve:
            raise TypeError(
                f"Type {type(float_value)} of value '{float_value}' for {key_path} is invalid. "
                "Value must be a valid floating point."
            ) from ve
        if expected_min:
            if float_value < expected_min:
                raise ValueError(
                    f"Value '{float_value}' for {key_path} is invalid. "
                    f"Value must be greater than or equal to {expected_min}."
                )
        if expected_max:
            if float_value > expected_max:
                raise ValueError(
                    f"Value '{float_value}' for {key_path} is invalid. "
                    f"Value must be less than or equal to {expected_max}."
                )
        return float_value

    @ParameterizedProperty
    def bool_value(
        self,
        key_path,
        default_value=None,
    ) -> bool:
        # pylint: disable=line-too-long
        """
        Retrieve and convert a configuration value to a boolean based on common truth string representations.

        Args:
            key_path (str): Path to the configuration value in the configuration hierarchy.
            default_value (Any, optional): Value to return if the key_path is not found. Defaults to None.

        Returns:
            bool: True if the value (case-insensitive) is "true", "1", "yes", or "on"; False otherwise.

        Note:
            The method converts the configuration value to lowercase before comparison.
        """
        # pylint: enable=line-too-long
        bool_value = self._config_getter(key_path=key_path, default_value=default_value)
        return bool_value.lower() in ("true", "1", "yes", "on")

    def _config_setter(self, key_path: str, value):
        # pylint: disable=line-too-long
        """
        Recursively set a value in the configuration using a dot-separated key path.

        This is an internal helper method used by other configuration setters. It traverses a nested
        dictionary structure using the provided dot-notation path. If any segment of the path is not
        found or if any intermediate value is not a dictionary, it returns the default_value.

        Args:
            key_path (str): Dot-separated path to the desired key (e.g., "ai_model.custom.key").
            value: The value to set at the specified key path.
        """
        # pylint: enable=line-too-long
        keys = key_path.split(".")
        current = self._config_content

        # Traverse through each key in the path, except the last one
        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]

        # Set the value at the last key
        current[keys[-1]] = value

    @str_value.setter
    def str_value(self, str_value: int, key_path: str):
        # pylint: disable=line-too-long
        """
        Set a string value in the configuration using a dot-separated key path.

        Args:
            str_value (str): The string value to set.
            key_path (str): Dot-separated path to the desired key (e.g., "app.name").
        """
        # pylint: enable=line-too-long
        self._config_setter(str_value, key_path)

    @int_value.setter
    def int_value(self, int_value: int, key_path: str):
        # pylint: disable=line-too-long
        """
        Set an integer value in the configuration using a dot-separated key path.

        Args:
            int_value (int): The integer value to set.
            key_path (str): Dot-separated path to the desired key (e.g., "app.max_connections").
        """
        # pylint: enable=line-too-long
        self._config_setter(int_value, key_path)

    @float_value.setter
    def float_value(self, float_value: int, key_path: str):
        # pylint: disable=line-too-long
        """
        Set a float value in the configuration using a dot-separated key path.

        Args:
            float_value (float): The float value to set.
            key_path (str): Dot-separated path to the desired key (e.g., "app.timeout").
        """
        # pylint: enable=line-too-long
        self._config_setter(float_value, key_path)

    @bool_value.setter
    def bool_value(self, bool_value: int, key_path: str):
        # pylint: disable=line-too-long
        """
        Set a boolean value in the configuration using a dot-separated key path.

        Args:
            bool_value (bool): The boolean value to set.
            key_path (str): Dot-separated path to the desired key (e.g., "feature.enabled").
        """
        # pylint: enable=line-too-long
        self._config_setter(bool_value, key_path)

    @list_value.setter
    def list_value(self, list_value: int, key_path: str):
        # pylint: disable=line-too-long
        """
        Set a list value in the configuration using a dot-separated key path.

        Args:
            list_value (list): The list value to set.
            key_path (str): Dot-separated path to the desired key (e.g., "app.allowed_hosts").
        """
        # pylint: enable=line-too-long
        self._config_setter(key_path, list_value)
