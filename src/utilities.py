"""
Encapsulation of utility methods used by other modules.

This module provides a singleton Utilities class with various utility methods for logging,
file operations, datetime serialization, and user interactions. The class is designed to
provide a centralized set of helper methods that can be used across different parts of a project.

Key Features:
    - Singleton pattern implementation
    - Logging methods with configurable log levels
    - File and path existence checking
    - JSON serialization with datetime support
    - User confirmation method
    - Environment variable parsing

Classes:
    Utilities: A comprehensive utility class with various helper methods.
"""

import sys
import os
import logging
from pathlib import Path
from datetime import datetime
from contextlib import contextmanager
from timeit import default_timer
import json
import custom_logger_success


class Utilities:
    """
    Encapsulation of utility methods used by other modules.

    Classes:
        Utilities

    Methods:
        __init__(self)
        __new__(cls, *args, **kwargs)
        debug
        elapsed_timer(self)
        error
        get_user_confirmation(self, msg: str) -> bool
        handle_datetime_serialization(self, obj)
        info
        json_dumps_with_datetime_serialization(self, obj, json_options=None)
        warning
    """

    _instance = None

    def __new__(cls, *args, **kwargs):  # pylint: disable=unused-argument
        """
        Creates and returns a singleton instance of the Utilities class.

        This method ensures that only one instance of the Utilities class is created
        throughout the application, implementing the singleton design pattern.

        Parameters:
            cls (type): The class being instantiated.
            *args: Variable length argument list.
            **kwargs: Arbitrary keyword arguments.

        Returns:
            Utilities: The singleton instance of the Utilities class.
        """
        if not cls._instance:
            cls._instance = super().__new__(cls)
            # print("Utilities.__new__", file=sys.stderr)
        return cls._instance

    def __init__(self):
        """
        Initializes the Utilities instance by configuring log levels for various libraries.

        Sets critical log levels for boto3, botocore, urllib3, httpcore, and httpx to
        suppress verbose logging from these libraries.
        """
        logging.getLogger("boto3").setLevel(logging.CRITICAL)
        logging.getLogger("botocore").setLevel(logging.CRITICAL)
        logging.getLogger("urllib3").setLevel(logging.CRITICAL)
        logging.getLogger("httpcore").setLevel(logging.CRITICAL)
        logging.getLogger("httpx").setLevel(logging.CRITICAL)

    @contextmanager
    def elapsed_timer(self):
        """
        A context manager for measuring the elapsed time of a code block.

        Starts a timer when entering the code block and provides a function to retrieve
        the elapsed time when exiting the block.

        Usage:
            with elapsed_timer() as timer:
                # Code block to measure
                result = some_function()

            elapsed_time = timer()
            print(f"Execution took {elapsed_time:.2f} seconds")

        Yields:
            function: A function that returns the elapsed time in seconds when called.
        """
        start = default_timer()

        def elapsed_keeper():
            """
            Handles the start of the context manager code block.

            Returns:
                int: The start time of the context manager in seconds when called.
            """
            return default_timer() - start

        yield elapsed_keeper
        end = default_timer()

        # pylint: disable=E0102
        def elapsed_keeper():
            """
            Handles the start of the context manager code block.

            Returns:
                int: The end time of the context manager in seconds when called.
            """
            return end - start

        # pylint: enable=E0102

    def debug(self, name: str, msg: str, exc_info=False) -> None:
        """
        Logs a debug message to the standard error stream.

        Parameters:
            name (str): The name of the logger.
            msg (str): The debug message to log.
            exc_info (bool, optional): Whether to include exception information. Defaults to False.
        """
        self.get_stderr_logger(name).debug(msg, exc_info=exc_info)

    def error(self, name: str, msg: str, exc_info=False) -> None:
        """
        Logs an error message to the standard error stream.

        Parameters:
            name (str): The name of the logger.
            msg (str): The error message to log.
            exc_info (bool, optional): Whether to include exception information. Defaults to False.
        """
        self.get_stderr_logger(name).error(msg, exc_info=exc_info)

    def info(self, name: str, msg: str, exc_info=False) -> None:
        """
        Logs an informational message to the standard output stream.

        Parameters:
            name (str): The name of the logger.
            msg (str): The informational message to log.
            exc_info (bool, optional): Whether to include exception information. Defaults to False.
        """
        self.get_stdout_logger(name).info(msg, exc_info=exc_info)

    def success(self, name: str, msg: str, exc_info=False) -> None:
        """
        Logs a success message to the standard output stream.

        Parameters:
            name (str): The name of the logger.
            msg (str): The success message to log.
            exc_info (bool, optional): Whether to include exception information. Defaults to False.
        """
        self.get_stdout_logger(name).success(msg, exc_info=exc_info)

    def warning(self, name: str, msg: str, exc_info=False) -> None:
        """
        Logs a warning message to the standard output stream.

        Parameters:
            name (str): The name of the logger.
            msg (str): The warning message to log.
            exc_info (bool, optional): Whether to include exception information. Defaults to False.
        """
        self.get_stdout_logger(name).warning(msg, exc_info=exc_info)

    def get_stdout_logger(self, name: str) -> logging.Logger:
        """
        Creates and configures a logger that outputs to the standard output stream.

        The logger's level is determined by the VERBOSE environment variable.
        If VERBOSE is set, the log level is set to INFO; otherwise, it uses a custom SUCCESS level.

        Parameters:
            name (str): The name of the logger.

        Returns:
            logging.Logger: A configured logger for standard output.
        """
        logger = logging.getLogger(f"{name}.stdout")
        if not logger.handlers:
            logger_level = (
                logging.INFO
                if self.is_truthy(os.getenv("VERBOSE", "not true"))
                else custom_logger_success.SUCCESS
            )
            logger.setLevel(logger_level)
            console_handler = logging.StreamHandler(stream=sys.stdout)
            console_handler.setLevel(logger_level)

            formatter = logging.Formatter("%(message)s")
            console_handler.setFormatter(formatter)

            logger.addHandler(console_handler)

        return logger

    def get_stderr_logger(self, name: str) -> logging.Logger:
        """
        Creates and configures a logger that outputs to the standard error stream.

        The logger's level is determined by the LOG_LEVEL environment variable.
        Defaults to ERROR level if no level is specified.

        Parameters:
            name (str): The name of the logger.

        Returns:
            logging.Logger: A configured logger for standard error.
        """
        logger = logging.getLogger(f"{name}.stderr")
        if not logger.handlers:
            logger_level = getattr(logging, os.getenv("LOG_LEVEL", "ERROR").upper())
            # print(f"logger_level from env: {logger_level}", file=sys.stderr)
            logger.setLevel(logger_level)

            console_handler = logging.StreamHandler(stream=sys.stderr)
            console_handler.setLevel(logger_level)

            formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
            console_handler.setFormatter(formatter)

            logger.addHandler(console_handler)

        return logger

    def is_stderr_logger_level(self, name: str, level: str) -> bool:
        """
        Check if the stderr logger for a given name has a specific logging level.

        Args:
            name (str): The name of the logger to check
            level (str): The logging level to compare against (e.g., DEBUG, INFO, WARNING, ERROR)

        Returns:
            bool: True if the logger's effective level matches the specified level, False otherwise
        """
        if self.get_stderr_logger(name).getEffectiveLevel(name) == level:
            return True
        return False

    def is_dir(self, check_path: str) -> bool:
        """
        Checks if the given path is a directory.

        Parameters:
            check_path (str): The path to check.

        Returns:
            bool: True if the path is a directory, False otherwise.
        """
        return Path.is_dir(Path(check_path))

    def is_file(self, check_path: str) -> bool:
        """
        Checks if the given path is a file.

        Parameters:
            check_path (str): The path to check.

        Returns:
            bool: True if the path is a file, False otherwise.
        """
        return Path.is_file(Path(check_path))

    def path_exists(self, check_path: str) -> bool:
        """
        Checks if the given path exists.

        Parameters:
            check_path (str): The path to check.

        Returns:
            bool: True if the path exists, False otherwise.
        """
        return Path.exists(check_path)

    def directory_exists(self, check_path) -> bool:
        """
        Checks if a directory exists at the specified path.

        Parameters:
            check_path (str): The path to check.

        Returns:
            bool: True if the path exists and is a directory.

        Raises:
            ValueError: If the path exists but is not a directory.
        """
        if self.path_exists(check_path):
            if not self.is_dir(check_path):
                raise ValueError(f"Path '{check_path}' is not a directory.")
        return self.path_exists(check_path)

    def file_exists(self, check_path) -> bool:
        """
        Checks if a file exists at the specified path.

        Parameters:
            check_path (str): The path to the file.

        Returns:
            bool: True if the path exists and is a file.

        Raises:
            ValueError: If the path exists but is not a file.
        """
        if self.path_exists(check_path):
            if not self.is_file(check_path):
                raise ValueError(f"Path '{check_path}' is not a file.")
        return Path.exists(check_path)

    def get_ascii_file_contents(self, source_path: str) -> str:
        """
        Reads and returns the contents of a file using UTF-8 encoding.

        Parameters:
            source_path (str): The path to the file to read.

        Returns:
            str: The contents of the file as a string.
        """
        self.debug(__class__, "start get_source_code")
        with open(source_path, "r", encoding="utf-8") as file:
            source_code = file.read()

        self.debug(__class__, "end get_source_code")
        return source_code

    def json_dumps_with_datetime_serialization(self, obj, json_options=None):
        """
        Serializes an object to a JSON formatted string with datetime serialization.

        This method takes an object and serializes it to a JSON formatted string using the
        'json.dumps' function. It uses the 'default' parameter of 'json.dumps' to specify a custom
        serialization function, which is 'self.handle_datetime_serialization'. This custom
        serialization function is responsible for serializing datetime objects to their ISO
        formatted string representation.

        Parameters:
            obj: The object to be serialized.
            json_options (optional): Additional options to be passed to the 'json.dumps' function.

        Returns:
            str: The JSON formatted string representation of the object.

        Example:
            >>> utils = Utilities()
            >>> data = {'name': 'John', 'age': 30, 'timestamp': datetime.now()}
            >>> json_string = utils.json_dumps_with_datetime_serialization(data)
            >>> print(json_string)
            {"name": "John", "age": 30, "timestamp": "2022-01-01T12:00:00"}

        """
        return json.dumps(
            obj, default=self.handle_datetime_serialization, **json_options
        )

    def handle_datetime_serialization(self, obj):
        """
        Serializes a datetime object to its ISO formatted string representation.

        This method takes a datetime object as input and returns its ISO formatted string
        representation using the 'isoformat()' method of the datetime object. If the input object
        is not a datetime object, a TypeError is raised.

        Parameters:
            obj (datetime): The datetime object to be serialized.

        Returns:
            str: The ISO formatted string representation of the datetime object.

        Raises:
            TypeError: If the input object is not a datetime object.

        Example:
            >>> utils = Utilities()
            >>> dt = datetime(2022, 1, 1, 12, 0, 0)
            >>> iso_string = utils.handle_datetime_serialization(dt)
            >>> print(iso_string)
            '2022-01-01T12:00:00'
        """
        if isinstance(obj, datetime):
            return obj.isoformat()
        raise TypeError(f"Type {type(obj)} not serializable")

    def get_user_confirmation(self, msg: str) -> bool:
        """
        Gets user confirmation for a given message.

        This method prompts the user with a message and expects a yes or no response. The user's
        response is case-insensitive and can be either "yes" or "no". If the response is "yes" or
        "y", the method returns True. If the response is "no" or "n", the method returns False.
        If the response is neither "yes" nor "no", the method returns None to indicate an invalid
        input.

        Parameters:
            msg (str): The message to display to the user.

        Returns:
            bool: True if the user confirms with "yes" or "y", False if the user confirms with
            "no" or "n", None if the user provides an invalid input.

        Example:
            >>> utils = Utilities()
            >>> confirmation = utils.get_confirmation("delete the file")
            Are you sure you want to delete the file (yes/no): yes
            >>> print(confirmation)
            True

        """
        response = input(f"Are you sure you want to {msg} (yes/no): ").strip().lower()
        if response in ("yes", "y"):
            return True
        elif response in ("no", "n"):
            return False
        else:
            return None  # Returning None to indicate invalid input

    def is_truthy(self, value: str) -> bool:
        """
        Determines if a value is considered "truthy".

        Checks if the value is equivalent to common truthy representations like "1", "true", "yes".

        Parameters:
            value (str): The value to check for truthiness.

        Returns:
            bool: True if the value is considered truthy, False otherwise.

        Examples:
            >>> utils = Utilities()
            >>> utils.is_truthy("1")
            True
            >>> utils.is_truthy("true")
            True
            >>> utils.is_truthy("false")
            False
        """
        # If no value exists, return True
        if value is None:
            return True

        # Convert to lowercase for case-insensitive comparison
        value = str(value).lower().strip()

        # Return result based on common truthy values
        return value in ["1", "true", "yes", "on", "y"]
