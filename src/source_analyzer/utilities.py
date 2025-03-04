"""
A collection of utility classes providing various helper methods for application functionality.

This module contains several utility classes that implement the singleton pattern and provide
methods for logging, file operations, context management, and general utilities.

Key Features:
    - Logging utilities with configurable output streams and log levels
    - File and directory management operations
    - Context managers for timing operations
    - JSON serialization with datetime support
    - Environment variable handling

Classes:
    CtxMgrUtils: Context manager utilities for timing operations
    LoggingUtils: Comprehensive logging functionality with stdout/stderr support
    DirUtils: File and directory management operations
    GenericUtils: General utility methods for serialization and environment handling
"""

import sys
import os
import logging
import importlib
import re
from pathlib import Path
from datetime import datetime
from contextlib import contextmanager
from timeit import default_timer
import json
from pprint import pformat
from configuration import Configuration
from custom_logger_success import CustomLoggerSuccess  # pylint: disable=unused-import
from custom_logger_trace import CustomLoggerTrace  # pylint: disable=unused-import


class CtxMgrUtils:
    """
    A singleton class providing context manager utilities for timing operations.

    This class implements the singleton pattern to ensure only one instance exists
    throughout the application lifecycle.
    """

    _instance = None

    def __new__(cls, *args, **kwargs):  # pylint: disable=unused-argument
        """
        Creates and returns a singleton instance of the class.

        This method ensures that only one instance of the class is created
        throughout the application, implementing the singleton design pattern.

        Parameters:
            cls (type): The class being instantiated.
            *args: Variable length argument list.
            **kwargs: Arbitrary keyword arguments.

        Returns:
            CtxMgrUtils: The singleton instance of the class.
        """
        if not cls._instance:
            cls._instance = super().__new__(cls)
        return cls._instance

    @contextmanager
    def elapsed_timer(self):
        """
        A context manager that measures the elapsed time of a code block.

        Provides a function to retrieve the elapsed time when exiting the block.
        The timer starts when entering the context and stops when exiting.

        Yields:
            function: A callable that returns the elapsed time in seconds.

        Example:
            with utils.elapsed_timer() as timer:
                # Code to measure
                time.sleep(1)
            print(f"Operation took {timer():.2f} seconds")
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

        # pylint: disable=function-redefined
        def elapsed_keeper():
            """
            Handles the start of the context manager code block.

            Returns:
                int: The end time of the context manager in seconds when called.
            """
            return end - start

        # pylint: enable=function-redefined


class LoggingUtils:
    """
    A singleton class providing comprehensive logging functionality.

    Configures and manages separate loggers for stdout and stderr streams with
    configurable log levels. Automatically suppresses verbose logging from common
    libraries like boto3, botocore, urllib3, httpcore, and httpx.
    """

    _instance = None

    def __new__(cls, *args, **kwargs):  # pylint: disable=unused-argument
        """
        Creates and returns a singleton instance of the class.

        This method ensures that only one instance of the class is created
        throughout the application, implementing the singleton design pattern.

        Parameters:
            cls (type): The class being instantiated.
            *args: Variable length argument list.
            **kwargs: Arbitrary keyword arguments.

        Returns:
            LoggingUtils: The singleton instance of the class.
        """
        if not cls._instance:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        """
        Initializes the class instance by configuring log levels for various libraries.

        Sets critical log levels for boto3, botocore, urllib3, httpcore, and httpx to
        suppress verbose logging from these libraries.
        """
        logging.getLogger("boto3").setLevel(logging.CRITICAL)
        logging.getLogger("botocore").setLevel(logging.CRITICAL)
        logging.getLogger("urllib3").setLevel(logging.CRITICAL)
        logging.getLogger("httpcore").setLevel(logging.CRITICAL)
        logging.getLogger("httpx").setLevel(logging.CRITICAL)

    def debug(
        self, name: str, msg: str, exc_info: bool = False, enable_pformat: bool = False
    ) -> None:
        """
        Logs a debug message to the stderr stream.

        Parameters:
            name (str): The name of the logger.
            msg (str): The debug message to log.
            exc_info (bool, optional): Whether to include exception information. Defaults to False.
        """
        self.get_stderr_logger(name).debug(
            (pformat(msg) if enable_pformat else msg), exc_info=exc_info
        )

    def debug_info(
        self, name: str, msg: str, exc_info=False, enable_pformat: bool = False
    ) -> None:
        """
        Sends a message to the debug and info loggers.

        Parameters:
            name (str): The name of the logger.
            msg (str): The debug message to log.
            exc_info (bool, optional): Whether to include exception information. Defaults to False.
        """
        self.get_stderr_logger(name).debug(
            pformat(msg) if enable_pformat else msg, exc_info=exc_info
        )
        self.get_stdout_logger(name).info(
            pformat(msg) if enable_pformat else msg, exc_info=exc_info
        )

    def error(
        self, name: str, msg: str, exc_info=False, enable_pformat: bool = False
    ) -> None:
        """
        Logs an error message to the stderr stream.

        Parameters:
            name (str): The name of the logger.
            msg (str): The error message to log.
            exc_info (bool, optional): Whether to include exception information. Defaults to False.
        """
        self.get_stderr_logger(name).error(
            pformat(msg) if enable_pformat else msg, exc_info=exc_info
        )

    def info(
        self, name: str, msg: str, exc_info=False, enable_pformat: bool = False
    ) -> None:
        """
        Logs an informational message to the stdout stream.

        Parameters:
            name (str): The name of the logger.
            msg (str): The informational message to log.
            exc_info (bool, optional): Whether to include exception information. Defaults to False.
        """
        self.get_stdout_logger(name).info(
            pformat(msg) if enable_pformat else msg, exc_info=exc_info
        )

    def success(
        self, name: str, msg: str, exc_info=False, enable_pformat: bool = False
    ) -> None:
        """
        Logs a success message to the stdout stream.

        Parameters:
            name (str): The name of the logger.
            msg (str): The success message to log.
            exc_info (bool, optional): Whether to include exception information. Defaults to False.
        """
        self.get_stdout_logger(name).success(
            pformat(msg) if enable_pformat else msg, exc_info=exc_info
        )

    def trace(
        self, name: str, msg: str, exc_info=False, enable_pformat: bool = False
    ) -> None:
        """
        Logs a trace message to the stderr stream.

        Parameters:
            name (str): The name of the logger.
            msg (str): The debug message to log.
            exc_info (bool, optional): Whether to include exception information. Defaults to False.
        """
        self.get_stderr_logger(name).trace(
            pformat(msg) if enable_pformat else msg, exc_info=exc_info
        )

    def warning(
        self, name: str, msg: str, exc_info=False, enable_pformat: bool = False
    ) -> None:
        """
        Logs a warning message to the stdout stream.

        Parameters:
            name (str): The name of the logger.
            msg (str): The warning message to log.
            exc_info (bool, optional): Whether to include exception information. Defaults to False.
        """
        self.get_stdout_logger(name).warning(
            pformat(msg) if enable_pformat else msg, exc_info=exc_info
        )

    def get_stdout_logger(self, name: str) -> logging.Logger:
        """
        Creates and retrieves a logger that outputs to the stdout stream.

        The logger's level is determined by the LOG_LEVEL_STDOUT environment variable,
        defaulting to the SUCCESS level if not specified.

        Parameters:
            name (str): The name of the logger.

        Returns:
            logging.Logger: A configured logger for standard output.
        """
        logger: logging.Logger = logging.getLogger(f"{name}.stdout")
        if not logger.handlers:
            logger_level = os.getenv("LOG_LEVEL_STDOUT", "SUCCESS").upper()
            self.debug(__class__, f"setting stdout logger level to {logger_level}")
            logger.setLevel(logger_level)
            console_handler: logging.Handler = logging.StreamHandler(stream=sys.stdout)
            console_handler.setLevel(logger_level)

            formatter: logging.Formatter = logging.Formatter("%(message)s")
            console_handler.setFormatter(formatter)

            logger.addHandler(console_handler)

        return logger

    def get_stderr_logger(self, name: str) -> logging.Logger:
        """
        Creates or retrieves a logger for stderr stream.

        Configures a logger with level based on LOG_LEVEL_STDERR environment variable,
        defaulting to the DEBUG level if not specified.

        Args:
            name (str): Logger name/identifier

        Returns:
            logging.Logger: Configured logger for stderr
        """
        logger = logging.getLogger(f"{name}.stderr")
        if not logger.handlers:
            logger_level = os.getenv(
                "LOG_LEVEL_STDERR", logging.getLevelName(logging.DEBUG)
            ).upper()
            logger.setLevel(logger_level)

            console_handler = logging.StreamHandler(stream=sys.stderr)
            console_handler.setLevel(logger_level)

            formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
            console_handler.setFormatter(formatter)

            logger.addHandler(console_handler)

        return logger

    def is_stderr_logger_level(self, name: str, level: str) -> bool:
        """
        Checks if the stderr logger is set to a specific logging level.

        Args:
            name (str): Logger name/identifier
            level (str): Logging level to check against (e.g., DEBUG, INFO, ERROR)

        Returns:
            bool: True if logger's effective level matches specified level
        """
        if self.get_stderr_logger(name).getEffectiveLevel() == level:
            return True
        return False


class PathUtils:
    """
    A singleton class providing comprehensive logging functionality.

    Configures and manages separate loggers for stdout and stderr streams with
    configurable log levels. Automatically suppresses verbose logging from common
    libraries like boto3, botocore, urllib3, httpcore, and httpx.
    """

    _instance = None

    def __new__(cls, *args, **kwargs):  # pylint: disable=unused-argument
        """
        Creates and returns a singleton instance of the PathUtils class.

        This method ensures that only one instance of the PathUtils class is created
        throughout the application, implementing the singleton design pattern.

        Parameters:
            cls (type): The class being instantiated.
            *args: Variable length argument list.
            **kwargs: Arbitrary keyword arguments.

        Returns:
            PathUtils: The singleton instance of the PathUtils class.
        """
        if not cls._instance:
            cls._instance = super().__new__(cls)
        return cls._instance

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
        LoggingUtils().trace(__class__, "start get_source_code")
        with open(source_path, "r", encoding="utf-8") as file:
            source_code = file.read()

        LoggingUtils().trace(__class__, "end get_source_code")
        return source_code


class GenericUtils:
    """
    A singleton class providing file and directory management utilities.

    Offers methods for checking existence and types of filesystem paths,
    and reading file contents.
    """

    _instance = None

    def __new__(cls, *args, **kwargs):  # pylint: disable=unused-argument
        """
        Creates and returns a singleton instance of the GenericUtils class.

        This method ensures that only one instance of the GenericUtils class is created
        throughout the application, implementing the singleton design pattern.

        Parameters:
            cls (type): The class being instantiated.
            *args: Variable length argument list.
            **kwargs: Arbitrary keyword arguments.

        Returns:
            Utilities: The singleton instance of the GenericUtils class.
        """
        if not cls._instance:
            cls._instance = super().__new__(cls)
        return cls._instance

    def load_class(
        self, module_name: str, class_name: str, package_name: str
    ) -> object:
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
        """
        Determines if a value is considered "truthy".

        Checks if the value is equivalent to common truthy representations like "1", "true", "yes".

        Parameters:
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
        # If no value exists, return True
        if value is None:
            return True

        # Convert to lowercase for case-insensitive comparison
        value = str(value).lower().strip()

        # Return result based on common truthy values
        return value in ["1", "true", "yes", "on", "y"]


class ModelUtils:

    def __init__(self, configuration: Configuration):
        """
        Initializes the SourceCodeAnalyzerUtils with default None values.

        The actual values will be lazily loaded when the respective getter
        methods are called for the first time.
        """
        self._config: Configuration = configuration

    # TODO convert to property
    def get_desired_model_class_name(self):
        return os.getenv(
            "AI_MODEL_CLASS_NAME",
            self._config.value("ai_model.class.name"),
        )

    # TODO convert to property
    def get_desired_model_module_name(self) -> str:
        return os.getenv(
            "AI_MODEL_MODULE_NAME",
            self._config.value("ai_model.module.name"),
        )

    # TODO convert to property
    def get_region_name(self) -> str:
        """
        Retrieves the AWS region name.

        Returns the region name from the 'AWS_REGION' environment variable.
        If not set, defaults to 'us-east-1'.

        Returns:
            str: The AWS region name.

        Example:
            >>> utils = SourceCodeAnalyzerUtils()
            >>> region = utils.get_region_name()
            # Returns 'us-west-2' if AWS_REGION is not set, or uses the env value
        """
        return os.getenv(
            "AWS_REGION", self._config.get_value("aws").get("region", "us-west-2")
        )


class JsonUtils:
    _instance = None

    def __new__(cls, *args, **kwargs):  # pylint: disable=unused-argument
        """
        Creates and returns a singleton instance of the JsonUtils class.

        This method ensures that only one instance of the class is created
        throughout the application, implementing the singleton design pattern.

        Parameters:
            cls (type): The class being instantiated.
            *args: Variable length argument list.
            **kwargs: Arbitrary keyword arguments.

        Returns:
            CtxMgrUtils: The singleton instance of the JsonUtils class.
        """
        if not cls._instance:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        """
        Initializes the JsonUtils class.
        """
        self._logging_utils = LoggingUtils()

    def json_loads(self, json_string: str):
        """
        Deserializes a JSON formatted string to a Python object.

        This method takes a JSON formatted string as input and deserializes it to a Python dictionary
        """
        return json.loads(json_string)

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
            >>> json_utils = JsonUtils()
            >>> data = {'name': 'John', 'age': 30, 'timestamp': datetime.now()}
            >>> json_string = json_utils.json_dumps_with_datetime_serialization(data)
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
            >>> utils = JsonUtils()
            >>> dt = datetime(2022, 1, 1, 12, 0, 0)
            >>> iso_string = utils.handle_datetime_serialization(dt)
            >>> print(iso_string)
            '2022-01-01T12:00:00'
        """
        if isinstance(obj, datetime):
            return obj.isoformat()
        raise TypeError(f"Type {type(obj)} not serializable")

    def extract_code_blocks(self, text: str, block_type: str) -> list | str:
        """Extract all json blocks from the given input."""
        self._logging_utils.debug(__class__, "start extract_code_blocks")
        self._logging_utils.debug(__class__, "end extract_code_blocks")
        return re.findall(rf"```{block_type}\s*(.*?)\s*```", text, re.DOTALL)

    def extract_json(self, text: str) -> list | str:
        """Extract the first json block from the given input."""
        self._logging_utils.debug(__class__, "start extract_json")
        json_blocks = self.extract_code_blocks(text, "json")
        if json_blocks:
            self._logging_utils.debug(
                __class__, f"type(json_blocks): {type(json_blocks)}"
            )
            self._logging_utils.debug(
                __class__,
                f"extract_json json_blocks: {json_blocks[0] if isinstance(json_blocks, list) else json_blocks}",
                enable_pformat=True,
            )
            self._logging_utils.debug(__class__, "end extract_json")
            return json_blocks[0] if isinstance(json_blocks, list) else json_blocks
        self._logging_utils.warning(__class__, "No json blocks found")
        self._logging_utils.debug(__class__, "end extract_json empty")
        return "{}"


class FormatterUtils:
    _instance = None

    def __new__(cls, *args, **kwargs):  # pylint: disable=unused-argument
        """
        Creates and returns a singleton instance of the FormatterUtils class.

        This method ensures that only one instance of the class is created
        throughout the application, implementing the singleton design pattern.

        Parameters:
            cls (type): The class being instantiated.
            *args: Variable length argument list.
            **kwargs: Arbitrary keyword arguments.

        Returns:
            formatterUtils: The singleton instance of the FormatterUtils class.
        """
        if not cls._instance:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, configuration: Configuration):
        self._config = configuration

    # TODO convert to property
    def get_desired_formatter_class_name(self):
        return os.getenv(
            "FORMATTER_CLASS_NAME",
            self._config.value("formatter.class.name"),
        )

    # TODO convert to property
    def get_desired_formatter_module_name(self) -> str:
        return os.getenv(
            "FORMATTER_MODULE_NAME",
            self._config.value("formatter.module.name"),
        )
