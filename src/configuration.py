import sys
from pathlib import Path
from typing import Any, Dict, Optional
import yaml


class Configuration:
    _instance = None

    def __new__(cls, *args, **kwargs):  # pylint: disable=unused-argument
        """
        Creates and returns a new instance of the Configuration class.

        This method is responsible for implementing the singleton pattern, ensuring that only one
        instance of the Utilities class is created.

        Parameters:
            cls (type): The class object.
            *args: Variable length argument list.
            **kwargs: Arbitrary keyword arguments.

        Returns:
            Configuration: The singleton instance of the Configuration class.

        """
        if not cls._instance:
            cls._instance = super().__new__(cls)
            # print("Configuration.__new__", file=sys.stderr)
        return cls._instance

    def __init__(self, config_file_path: str) -> None:
        # print("begin Configuration.__init__", file=sys.stderr)
        self._config_content = None
        self.safe_load_config(config_file_path)
        # print("end Configuration.__init__", file=sys.stderr)

    def safe_load_config(self, file_path: str) -> None:
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
                    elif isinstance(e, yaml.parser.ParserError):
                        raise yaml.YAMLError(
                            f"YAML parsing error in {file_path}: {str(e)}"
                        )
                    else:
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
        except Exception as e:
            raise Exception(f"Unexpected error reading {file_path}: {str(e)}") from e

    def validate_config(self) -> bool:
        """
        Validate the loaded configuration against a predefined schema.
        """
        # validate the loaded configuration against a predefined schema
        # TODO add configuration validation
        return True

    def get_value(self, key: str, default_value: Any = None) -> Any:
        """
        Retrieve values from the config_dict with a default value if the key does not exist.

        Parameters:
            key (str): The key to retrieve the value from the config_dict.
            default_value (Any): The default value to return if the key does not exist.

        Returns:
            Any: The value associated with the key in the config_dict, or the default value if
              the key does not exist.
        """
        return self._config_content.get(key, default_value)

    def set_value(self, key: str, value: Any) -> None:
        """
        Set a value in the config_dict.

        Parameters:
            key (str): The key to set the value in the config_dict.
            value (Any): The value to set in the config_dict.
        """
        self._config_content[key] = value
