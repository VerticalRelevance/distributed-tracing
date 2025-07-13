# pylint: disable=line-too-long
"""
A utility module for file system operations and path management.

This module provides the PathUtils class, which implements a singleton pattern for
consistent path handling throughout the application. It offers comprehensive methods
for checking and validating file system paths, including existence verification for
both files and directories, and file content reading capabilities.

The module is designed to provide a centralized interface for all path-related
operations, ensuring consistency and reducing code duplication across the application.

Classes:
    PathUtils: A singleton utility class for file system operations and path management.

Dependencies:
    - os: For operating system interface operations
    - pathlib: For object-oriented path handling
    - typing: For type hints and annotations
    - common.logging_utils: For logging functionality

Example:
    >>> from path_utils import PathUtils
    >>> path_utils = PathUtils()
    >>> if path_utils.file_exists("config.txt"):
    ...     content = path_utils.get_ascii_file_contents("config.txt")
"""
# pylint: enable=line-too-long

import os
from pathlib import Path
from typing import List
from common.logging_utils import LoggingUtils


class PathUtils:
    # pylint: disable=line-too-long
    """
    A singleton utility class for file system operations and path management.

    This class provides a comprehensive set of methods for checking and validating file system
    paths, including existence verification for both files and directories, and file content
    reading capabilities. It implements the singleton pattern to ensure consistent path
    handling throughout the application.

    Features:
        - Singleton pattern implementation
        - File and directory existence checking
        - Path type validation
        - File content reading with UTF-8 support
        - Error handling for invalid path types

    Methods:
        __new__(cls, *args, **kwargs): Creates singleton instance
        is_dir(check_path): Checks if path is a directory
        is_file(check_path): Checks if path is a file
        path_exists(check_path): Verifies path existence
        directory_exists(check_path): Validates directory existence
        file_exists(check_path): Validates file existence
        get_ascii_file_contents(source_path): Reads file contents

    Path Validation:
        - Supports both file and directory path checking
        - Provides type-specific validation
        - Raises appropriate errors for mismatched path types

    File Operations:
        - UTF-8 encoded file reading
        - Trace logging for file operations
        - Safe file handling with context managers

    Example:
        >>> path_utils = PathUtils()  # Creates or returns existing instance
        >>> # Check if path is a directory
        >>> path_utils.is_dir("/path/to/dir")  # Returns True/False
        >>> # Read file contents
        >>> content = path_utils.get_ascii_file_contents("/path/to/file.txt")

    Error Handling:
        directory_exists():
            - ValueError: When path exists but is not a directory
        file_exists():
            - ValueError: When path exists but is not a file
        get_ascii_file_contents():
            - FileNotFoundError: When file doesn't exist
            - UnicodeDecodeError: When file is not UTF-8 encoded

    Dependencies:
        - pathlib.Path: For path operations
        - LoggingUtils: For operation tracing
        - typing: For type hints

    Notes:
        - All path operations are performed using pathlib.Path for consistency
        - File reading operations use UTF-8 encoding by default
        - Logging is implemented for file reading operations
        - Path existence checks are performed before type validation
    """
    # pylint: enable=line-too-long

    _instance = None

    def __new__(cls, *args, **kwargs):  # pylint: disable=unused-argument
        # pylint: disable=line-too-long
        """
        Creates and returns a singleton instance of the PathUtils class.

        This method ensures that only one instance of the PathUtils class is created
        throughout the application, implementing the singleton design pattern.

        Args:
            cls (type): The class being instantiated.
            *args: Variable length argument list.
            **kwargs: Arbitrary keyword arguments.

        Returns:
            PathUtils: The singleton instance of the PathUtils class.
        """
        # pylint: enable=line-too-long

        if not cls._instance:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        # pylint: disable=line-too-long
        """
        Initializes the PathUtils instance with a logger.

        Sets up the logger for the PathUtils class using the LoggingUtils utility.
        This method is called during instance creation but due to the singleton pattern,
        it will only execute once for the lifetime of the application.

        Attributes:
            _logger: A logger instance for tracing and debugging path operations.
        """
        # pylint: enable=line-too-long

        self._logger = LoggingUtils().get_class_logger(class_name=__class__.__name__)

    def get_path(self, path_str: str) -> Path:
        # pylint: disable=line-too-long
        """
        Converts a string path to a Path object.

        Args:
            path_str (str): The path string to be converted.

        Returns:
            Path: The Path object representing the given path.
        """
        # pylint: enable=line-too-long

        return Path(path_str)

    def is_dir(self, check_path: str) -> bool:
        # pylint: disable=line-too-long
        """
        Checks if the given path is a directory.

        Args:
            check_path (str): The path to check.

        Returns:
            bool: True if the path is a directory, False otherwise.
        """
        # pylint: enable=line-too-long

        return Path.is_dir(self.get_path(check_path))

    def is_file(self, check_path: str) -> bool:
        # pylint: disable=line-too-long
        """
        Checks if the given path is a file.

        Args:
            check_path (str): The path to check.

        Returns:
            bool: True if the path is a file, False otherwise.
        """
        # pylint: enable=line-too-long

        return Path.is_file(self.get_path(check_path))

    def path_exists(self, check_path: str) -> bool:
        # pylint: disable=line-too-long
        """
        Checks if the given path exists.

        Args:
            check_path (str): The path to check.

        Returns:
            bool: True if the path exists, False otherwise.
        """
        # pylint: enable=line-too-long

        return Path.exists(self.get_path(check_path))

    def directory_exists(self, check_path) -> bool:
        # pylint: disable=line-too-long
        """
        Checks if a directory exists at the specified path.

        Args:
            check_path (str): The path to check.

        Returns:
            bool: True if the path exists and is a directory.

        Raises:
            ValueError: If the path exists but is not a directory.
        """
        # pylint: enable=line-too-long

        if self.path_exists(check_path):
            if not self.is_dir(check_path):
                raise ValueError(f"Path '{check_path}' is not a directory.")
        return self.path_exists(check_path)

    def file_exists(self, check_path) -> bool:
        # pylint: disable=line-too-long
        """
        Checks if a file exists at the specified path.

        Args:
            check_path (str): The path to the file.

        Returns:
            bool: True if the path exists and is a file.

        Raises:
            ValueError: If the path exists but is not a file.
        """
        # pylint: enable=line-too-long

        if self.path_exists(check_path):
            if not self.is_file(check_path):
                raise ValueError(f"Path '{check_path}' is not a file.")
        return Path.exists(self.get_path(check_path))

    def get_ascii_file_contents(self, source_path: str) -> str:
        # pylint: disable=line-too-long
        """
        Reads and returns the contents of a file using UTF-8 encoding.

        Args:
            source_path (str): The path to the file to read.

        Returns:
            str: The contents of the file as a string.

        Raises:
            FileNotFoundError: If the specified file does not exist.
            UnicodeDecodeError: If the file cannot be decoded using UTF-8 encoding.
            PermissionError: If the file cannot be read due to insufficient permissions.
        """
        # pylint: enable=line-too-long

        self._logger.trace(__class__.__name__, "start get_source_code")
        with open(source_path, "r", encoding="utf-8") as file:
            source_code = file.read()

        self._logger.trace(__class__.__name__, "end get_source_code")
        return source_code

    def abspath(self, this_path: str) -> str:
        # pylint: disable=line-too-long
        """
        Returns the absolute path of the given path.

        Args:
            this_path (str): The path to convert to an absolute path.

        Returns:
            str: The absolute path as a string.
        """
        # pylint: enable=line-too-long

        return os.path.abspath(path=this_path)

    def stat(self, this_path: str) -> os.stat_result:
        # pylint: disable=line-too-long
        """
        Returns the status information about the specified path.

        Args:
            this_path (str): The path to get status information for.

        Returns:
            os.stat_result: The status information about the path, including
                           file size, modification time, permissions, etc.

        Raises:
            FileNotFoundError: If the specified path does not exist.
            PermissionError: If access to the path is denied.
        """
        # pylint: enable=line-too-long

        return os.stat(path=self.get_path(this_path))

    def with_suffix(self, this_path: str, suffix: str) -> str:
        # pylint: disable=line-too-long
        """
        Returns the path with the specified suffix.

        Args:
            this_path (str): The path to modify.
            suffix (str): The suffix to append (should include the dot, e.g., '.txt').

        Returns:
            str: The path with the specified suffix.

        Note:
            This method replaces the existing suffix if one exists, or adds
            the new suffix if no suffix is present.
        """
        # pylint: enable=line-too-long

        return self.get_path(this_path).suffix.with_suffix(suffix=suffix)

    def lower_suffix(self, this_path: str) -> str:
        # pylint: disable=line-too-long
        """
        Returns the suffix of the path in lowercase.

        Args:
            this_path (str): The path to get the lowercase suffix from.

        Returns:
            str: The suffix of the path in lowercase (e.g., '.txt', '.py').
                 Returns an empty string if the path has no suffix.
        """
        # pylint: enable=line-too-long

        return self.get_path(this_path).suffix.lower()

    def has_suffix(self, this_path: str, suffixes: List[str]):
        # pylint: disable=line-too-long
        """
        Checks if the path has one of the specified suffixes.

        Args:
            this_path (str): The path to check.
            suffixes (List[str]): A list of suffixes to check against
                                 (e.g., ['.txt', '.py', '.json']).

        Returns:
            bool: True if the path has one of the specified suffixes, False otherwise.
        """
        # pylint: enable=line-too-long

        return self.get_path(this_path).suffix in suffixes

