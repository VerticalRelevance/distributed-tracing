"""
Encapsulation of utility methods used by other modules.

Classes:
    Utilities
"""

import sys
import os
import logging
from datetime import datetime
from contextlib import contextmanager
from timeit import default_timer
import json


class Utilities:
    silent = False

    """
    Encapsulation of utility methods used by other modules.

    Classes:
        Utilities

    Methods:
        __new__(cls, *args, **kwargs)
        elapsed_timer(self)
        generate_assessment_name(self)
        generate_version_name(self)
        generate_random_name(self, prefix: str, random_size: int)
        setup_double_logger(self, name: str, logger_1_level: int = logging.INFO, logger_2_level: int = logging.ERROR) -> tuple[logging.Logger, logging.Logger] # pylint: disable=line-too-long
        setup_logger(self, name: str, log_level: int = logging.INFO) -> logging.Logger
        json_dumps_with_datetime_serialization(self, obj, json_options=None)
        handle_datetime_serialization(self, obj)
        get_confirmation(self, msg: str) -> bool
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
            Utilities: The instance of the Utilities class.

        """
        if not cls._instance:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        self.silent = None

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
        if not self.silent:
            self.get_stdout_logger(name).info(msg, exc_info=exc_info)

    def get_stdout_logger(self, name: str) -> logging.Logger:
        logger = logging.getLogger(f"{name}.stdout")
        # TODO get logger level from os envs
        logger_level = logging.INFO
        if not logger.handlers:
            logger.setLevel(logger_level)

            console_handler = logging.StreamHandler(stream=sys.stdout)
            console_handler.setLevel(logger_level)

            formatter = logging.Formatter("%(message)s")
            console_handler.setFormatter(formatter)

            logger.addHandler(console_handler)

        return logger

    def get_stderr_logger(self, name: str) -> logging.Logger:
        logger = logging.getLogger(f"{name}.stderr")
        # TODO get logger level from os envs
        # TODO set default to ERROR
        logger_level = logging.DEBUG
        if not logger.handlers:
            logger.setLevel(logger_level)

            console_handler = logging.StreamHandler(stream=sys.stderr)
            console_handler.setLevel(logger_level)

            formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
            console_handler.setFormatter(formatter)

            logger.addHandler(console_handler)

        return logger

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
        return json.dumps(obj, default=self.handle_datetime_serialization, **json_options)

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

    def is_silent(self) -> bool:
        if not self.silent:
            self.silent = bool(os.getenv("SILENT", False))

        return self.silent

