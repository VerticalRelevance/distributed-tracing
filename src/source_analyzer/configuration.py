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
