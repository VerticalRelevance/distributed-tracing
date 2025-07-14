# pylint: disable=too-few-public-methods
# pylint: disable=line-too-long
"""
YAML utility module providing safe parsing functionality for YAML files.

This module contains utilities for reading and parsing YAML files with proper
error handling and security considerations.
"""
# pylint: enable=line-too-long

import pathlib
from pathlib import Path
import yaml

class YamlUtils:
    # pylint: disable=line-too-long
    """
    Utility class for YAML file operations.

    This class provides methods for safely parsing YAML files with comprehensive
    error handling for common YAML parsing issues.
    """
    # pylint: enable=line-too-long

    def parse(self, file_path: str):
        # pylint: disable=line-too-long
        """
        Parse a YAML file and return its contents as a Python object.

        Args:
            file_path (str): Path to the YAML file to be parsed.

        Returns:
            dict or list: The parsed YAML content as a Python data structure.

        Raises:
            yaml.YAMLError: If there are syntax errors, parsing errors, or other
                          issues with the YAML file content.
        """
        # pylint: enable=line-too-long

        # Attempt to read and parse the YAML file
        path: Path = pathlib.Path(file_path)
        with path.open("r", encoding="utf-8") as file:
            try:
                # Use safe_load instead of load for security
                return yaml.safe_load(file)

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
