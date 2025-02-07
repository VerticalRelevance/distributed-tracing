"""
Encapsulation of utility methods used by other modules.

Classes:
    Utilities
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
    # silent = False

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
        Creates and returns a new instance of the Utilities class.

        This method is responsible for implementing the singleton pattern, ensuring that only one
        instance of the Utilities class is created.

        Parameters:
            cls (type): The class object.
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
        logging.getLogger("boto3").setLevel(logging.CRITICAL)
        logging.getLogger("botocore").setLevel(logging.CRITICAL)
        logging.getLogger("urllib3").setLevel(logging.CRITICAL)
        logging.getLogger("httpcore").setLevel(logging.CRITICAL)
        logging.getLogger("httpx").setLevel(logging.CRITICAL)

    @contextmanager
    def elapsed_timer(self):
        """
        Measures the elapsed time of a code block using a context manager.

        This method is a context manager that measures the elapsed time of a code block. It starts
        a timer when the code block is entered and stops the timer when the code block is exited.
        The elapsed time can be obtained by calling the returned function.

        Usage:
            with elapsed_timer() as timer:
                # Code block to measure elapsed time
                ...

            elapsed_time = timer()
            print(f"Took {elapsed_time:.2f})

        Returns:
            function: A function that returns the elapsed time in seconds when called.

        """
        start = default_timer()

        def elapsed_keeper():
            return default_timer() - start

        yield elapsed_keeper
        end = default_timer()

        # pylint: disable=E0102
        def elapsed_keeper():
            return end - start

        # pylint: enable=E0102

    def debug(self, name: str, msg: str, exc_info=False) -> None:
        self.get_stderr_logger(name).debug(msg, exc_info=exc_info)

    def error(self, name: str, msg: str, exc_info=False) -> None:
        self.get_stderr_logger(name).error(msg, exc_info=exc_info)

    def info(self, name: str, msg: str, exc_info=False) -> None:
        self.get_stdout_logger(name).info(msg, exc_info=exc_info)

    def success(self, name: str, msg: str, exc_info=False) -> None:
        self.get_stdout_logger(name).success(msg, exc_info=exc_info)

    def warning(self, name: str, msg: str, exc_info=False) -> None:
        self.get_stdout_logger(name).warning(msg, exc_info=exc_info)

    def get_stdout_logger(self, name: str) -> logging.Logger:
        logger = logging.getLogger(f"{name}.stdout")
        # print(
        #     f"Utilities get_stdout_logger name: {logger.name} level: {logger.level}",
        #     file=sys.stderr,
        # )
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
        logger = logging.getLogger(f"{name}.stderr")
        # print(
        #     f"Utilities get_stderr_logger name: {logger.name} level: {logger.level}",
        #     file=sys.stderr,
        # )
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

    def is_dir(self, check_path: str) -> bool:
        """
        Checks if the given path is a directory.

        Parameters:
            path (str): The path to check.

        Returns:
            bool: True if the path is a directory, False otherwise.
        """
        return Path.is_dir(Path(check_path))

    def is_file(self, check_path: str) -> bool:
        """
        Checks if the given path is a file.

        Parameters:
            path (str): The path to check.

        Returns:
            bool: True if the path is a file, False otherwise.
        """
        return Path.is_file(Path(check_path))

    def path_exists(self, check_path: str) -> bool:
        """
        Checks if the given path exists.

        Parameters:
            path (str): The path to check.

        Returns:
            bool: True if the path exists, False otherwise.
        """
        return Path.exists(check_path)

    def directory_exists(self, check_path) -> bool:
        # TODO test: path exists, is directory
        # TODO test: path exists, is not directory
        # TODO test: path not exists
        if self.path_exists(check_path):
            if not self.is_dir(check_path):
                raise ValueError(f"Path '{check_path}' is not a directory.")
        return self.path_exists(check_path)

    def file_exists(self, check_path) -> bool:
        """
        Checks if a file exists at the specified path.

        Parameters:
            path (str): The path to the file.

        Returns:
            bool: True if the file exists, False otherwise.
        """
        if self.path_exists(check_path):
            if not self.is_file(check_path):
                raise ValueError(f"Path '{check_path}' is not a file.")
        return Path.exists(check_path)

    def get_ascii_file_contents(self, source_path: str) -> str:
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
        # If no value exists, return True
        if value is None:
            return True

        # Convert to lowercase for case-insensitive comparison
        value = str(value).lower().strip()

        # Return result based on common truthy values
        return value in ["1", "true", "yes", "on", "y"]
