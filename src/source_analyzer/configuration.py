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

from pathlib import Path
import yaml
from parameterized_property import ParameterizedProperty


class Configuration:
    """
    A singleton configuration management class for loading and accessing configuration settings.

    This class provides a robust mechanism for loading configuration files, with comprehensive
    error handling, validation, and safe access to configuration values. It follows the
    singleton pattern to ensure only one configuration instance exists.

    Attributes:
        _instance (Configuration): The single instance of the Configuration class.
        _config_content (Dict[str, Any]): Loaded configuration content.

    Methods:
        __new__: Ensures only one instance of the class is created.
        __init__: Initializes the configuration by loading the specified YAML file.
        safe_load_config: Safely loads a YAML configuration file with extensive error checking.
        validate_config: Placeholder method for configuration validation.
        get_value: Retrieves a configuration value with an optional default.
        set_value: Sets a configuration value.
    """

    _instance = None

    def __new__(cls, *args, **kwargs):  # pylint: disable=unused-argument
        """
        Creates and returns a new instance of the Configuration class.

        This method is responsible for implementing the singleton pattern, ensuring that only one
        instance of the Configuration class is created.

        Parameters:
            cls (type): The class object.
            *args: Variable length argument list.
            **kwargs: Arbitrary keyword arguments.

        Returns:
            Configuration: The singleton instance of the Configuration class.

        """
        if not cls._instance:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, config_file_path: str) -> None:
        self._config_content: Configuration = None
        self.safe_load_config(config_file_path)

    def __str__(self):
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
            file_path (str): Path to the YAML file to load

        Returns:
            Optional[Dict[str, Any]]: Parsed YAML content as a dictionary if successful, None if failed

        Raises:
            FileNotFoundError: If the file doesn't exist
            PermissionError: If there are insufficient permissions to read the file
            yaml.YAMLError: For YAML parsing errors
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
        """
        Validate the loaded configuration against a predefined schema.
        """
        # validate the loaded configuration against a predefined schema
        # FUTURE add configuration validation

        return True

    def items(self):
        """
        Return the configuration items.

        Returns:
            dict_items: The configuration items.
        """
        return self._config_content.copy()

    def _config_getter(self, key_path: str, default_value=None):
        # pylint: disable=line-too-long
        """
        Retrieves a value from a nested configuration dictionary using a dot-notation path.

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

        Notes:
            This is an internal helper method used by other configuration getters. It traverses a nested
            dictionary structure using the provided dot-notation path. If any segment of the path is not
            found or if any intermediate value is not a dictionary, it returns the default_value.
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
        Retrieves a configuration value and ensures it is a list.

        Args:
            key_path (str): Path to the configuration value in the configuration hierarchy.
            default_value (Any, optional): Value to return if the key_path is not found. If
                provided, this value must also be a list. Defaults to None.

        Returns:
            list: The configuration value as a list.

        Raises:
            TypeError: If the retrieved value or default value is not a list.

        Examples:
            Get list of allowed hosts with default:
                >>> allowed_hosts = config.list_value('security.allowed_hosts',
                ...                                  default_value=['localhost'])

            Get required list of database replicas:
                >>> replicas = config.list_value('database.replicas')

        Notes:
            The method performs type checking to ensure the returned value is a valid list. This validation
            applies to both the retrieved configuration value and any provided default value.
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
        Retrieves a configuration value and ensures it is a string.

        Args:
            key_path (str): Path to the configuration value in the configuration hierarchy.
            default_value (Any, optional): Value to return if the key_path is not found. If provided,
                this value must also be a string. Defaults to None.

        Returns:
            str: The configuration value as a string.

        Raises:
            TypeError: If the retrieved value or default value is not a string.

        Examples:
            Get API endpoint URL with default:
                >>> api_url = config.str_value('service.api.endpoint',
                ...                           default_value='https://api.default.com')

            Get required connection string:
                >>> conn_str = config.str_value('database.connection_string')

        Notes:
            The method performs type checking to ensure the returned value is a valid string. This
            validation applies to both the retrieved configuration value and any provided default value.
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
        Retrieves and converts a configuration value to an integer with optional range validation.

        Args:
            key_path (str): Path to the configuration value in the configuration hierarchy.
            expected_min (int, optional): Minimum allowed value for the integer. If specified, the value must
                be greater than or equal to this minimum. Defaults to None.
            expected_max (int, optional): Maximum allowed value for the integer. If specified, the value must
                be less than or equal to this maximum. Defaults to None.
            default_value (Any, optional): Value to return if the key_path is not found. If provided, this
                value must also be convertible to integer and meet range requirements. Defaults to None.

        Returns:
            int: The configuration value converted to an integer.

        Raises:
            TypeError: If the value cannot be converted to an integer.
            ValueError: If the value is outside the specified range (when expected_min or expected_max are
                provided).

        Examples:
            Configure maximum number of retries between 0 and 5:
                >>> max_retries = config.int_value('app.max_retries', expected_min=0, expected_max=5)

        Notes:
            The method first attempts to convert the configuration value to an integer.
            After successful conversion, if either expected_min or expected_max are specified,
            it validates that the value falls within the acceptable range.
            The range validation is only performed when the respective boundary values are not None.
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
        """
        Retrieves and converts a configuration value to a float with optional range validation.

        Args:
            key_path: Path to the configuration value in the configuration hierarchy.
            expected_min (float, optional): Minimum allowed value for the float. Defaults to None.
                If specified, the value must be greater than or equal to this minimum.
            expected_max (float, optional): Maximum allowed value for the float. Defaults to None.
                If specified, the value must be less than or equal to this maximum.
            default_value (optional): Value to return if the key_path is not found. Defaults
                to None. If provided, this value must also be convertible to float and meet range
                requirements.

        Returns:
            float: The configuration value converted to a floating-point number.

        Raises:
            TypeError: If the value cannot be converted to a float.
            ValueError: If the value is outside the specified range (when expected_min
                or expected_max are provided).

        Example:
            >>> # Configure a timeout value between 0.1 and 30.0 seconds
            >>> timeout = config.float_value('app.timeout', expected_min=0.1, expected_max=30.0)

        Note:
            The method first attempts to convert the configuration value to a float.
            After successful conversion, if either expected_min or expected_max are specified,
            it validates that the value falls within the acceptable range.
        """
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
        """
        Retrieves and converts a configuration value to a boolean based on common truth string
        representations.

        Args:
            key_path: Path to the configuration value in the configuration hierarchy.
            default_value (optional): Value to return if the key_path is not found. Defaults to
            None.

        Returns:
            bool: True if the configuration value (case-insensitive) matches any of the following:
                    - "true"
                    - "1"
                    - "yes"
                    - "on"
                    False for all other values.

        Note:
            The method converts the configuration value to lowercase before comparison.
            If default_value is provided and the key_path is not found, the default_value
            will be processed through the same boolean conversion logic.
        """
        bool_value = self._config_getter(key_path=key_path, default_value=default_value)
        return bool_value.lower() in ("true", "1", "yes", "on")

    def _config_setter(self, key_path: str, value):
        """
        Recursively set a value in a nested dictionary using a dot-separated key path.

        Args:
            dictionary (dict): The nested dictionary to modify
            key_path (str): Dot-separated path to the desired key (e.g., "ai_model.custom.key")
            value: The value to set at the specified key path
        """
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
        """
        Recursively set a value in a nested dictionary using a dot-separated key path.

        Args:
            dictionary (dict): The nested dictionary to modify
            key_path (str): Dot-separated path to the desired key (e.g., "ai_model.custom.key")
            value: The value to set at the specified key path
        """
        self._config_setter(str_value, key_path)

    @int_value.setter
    def int_value(self, int_value: int, key_path: str):
        """
        Recursively set a value in a nested dictionary using a dot-separated key path.

        Args:
            dictionary (dict): The nested dictionary to modify
            key_path (str): Dot-separated path to the desired key (e.g., "ai_model.custom.key")
            value: The value to set at the specified key path
        """
        self._config_setter(int_value, key_path)

    @float_value.setter
    def float_value(self, float_value: int, key_path: str):
        """
        Recursively set a value in a nested dictionary using a dot-separated key path.

        Args:
            dictionary (dict): The nested dictionary to modify
            key_path (str): Dot-separated path to the desired key (e.g., "ai_model.custom.key")
            value: The value to set at the specified key path
        """
        self._config_setter(float_value, key_path)

    @bool_value.setter
    def bool_value(self, bool_value: int, key_path: str):
        """
        Recursively set a value in a nested dictionary using a dot-separated key path.

        Args:
            dictionary (dict): The nested dictionary to modify
            key_path (str): Dot-separated path to the desired key (e.g., "ai_model.custom.key")
            value: The value to set at the specified key path
        """
        self._config_setter(bool_value, key_path)

    @list_value.setter
    def list_value(self, list_value: int, key_path: str):
        """
        Recursively set a value in a nested dictionary using a dot-separated key path.

        Args:
            dictionary (dict): The nested dictionary to modify
            key_path (str): Dot-separated path to the desired key (e.g., "ai_model.custom.key")
            value: The value to set at the specified key path
        """
        self._config_setter(key_path, list_value)

    # @value.setter
    # def value(self, key_path, value):
    #     """
    #     Recursively set a value in a nested dictionary using a dot-separated key path.

    #     Args:
    #         dictionary (dict): The nested dictionary to modify
    #         key_path (str): Dot-separated path to the desired key (e.g., "ai_model.custom.key")
    #         value: The value to set at the specified key path
    #     """
    #     keys = key_path.split(".")
    #     current = self._config_content

    #     # Traverse through each key in the path, except the last one
    #     for key in keys[:-1]:
    #         if key not in current:
    #             current[key] = {}
    #         current = current[key]

    #     # Set the value at the last key
    #     current[keys[-1]] = value
