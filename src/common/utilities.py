# pylint: disable=line-too-long
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
# pylint: enable=line-too-long

# TODO break up into separate modules

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
from common.configuration import Configuration
from common.custom_logger_success import CustomLoggerSuccess  # pylint: disable=unused-import
from common.custom_logger_trace import CustomLoggerTrace  # pylint: disable=unused-import


class MissingEnvironmentVariable(Exception):
    # pylint: disable=line-too-long
    """
    Custom exception for missing log stderr filename.

    This exception is raised when a required environment variable is not found.

    Attributes:
        _env_var_name (str): The name of the missing environment variable.
    """
    # pylint: enable=line-too-long

    def __init__(self, env_var_name):
        super().__init__(f"Missing environment variable '{env_var_name}'")
        self._env_var_name = env_var_name

    def __str__(self):
        return f"Missing environment variable '{self._env_var_name}'"

class CtxMgrUtils:
    # pylint: disable=line-too-long
    """
    A singleton utility class providing context managers for time measurement and
    performance monitoring.

    This class implements the singleton pattern and offers context managers for measuring
    execution time of code blocks. It provides precise timing functionality using Python's
    timeit.default_timer for maximum accuracy across different platforms.

    Features:
        - Singleton pattern implementation
        - High-precision time measurement
        - Context manager support
        - Platform-independent timing
        - Callable timer function access

    Methods:
        __new__(cls, *args, **kwargs): Creates singleton instance
        elapsed_timer(): Context manager for time measurement

    Time Measurement:
        - Uses timeit.default_timer for highest available precision
        - Platform-independent timing functionality
        - Provides both running and final elapsed time
        - Returns callable function for accessing elapsed time

    Context Manager Usage:
        The elapsed_timer context manager:
        - Starts timing when entering the context
        - Provides access to elapsed time during execution
        - Updates to final time when exiting context
        - Returns time in seconds with floating-point precision

    Example:
        >>> utils = CtxMgrUtils()  # Creates or returns existing instance
        >>> with utils.elapsed_timer() as timer:
        ...     # Perform operations
        ...     time.sleep(1)
        ...     current_time = timer()  # Get current elapsed time
        >>> final_time = timer()  # Get total elapsed time
        >>> print(f"Operation took {final_time:.2f} seconds")

    Timer Function:
        The yielded timer function:
        - Takes no arguments
        - Returns elapsed time in seconds
        - Can be called multiple times
        - Updates automatically at context exit

    Dependencies:
        - contextlib: For context manager implementation
        - timeit.default_timer: For high-precision timing
        - typing: For type hints

    Notes:
        - Timer precision depends on platform-specific implementation
        - All times are returned in seconds as floating-point numbers
        - The context manager is reentrant and can be nested
        - The singleton pattern ensures consistent timing across the application
    """
    # pylint: enable=line-too-long

    _instance = None

    def __new__(cls, *args, **kwargs):  # pylint: disable=unused-argument
        # pylint: disable=line-too-long
        """
        Creates and returns a singleton instance of the class.

        This method ensures that only one instance of the class is created
        throughout the application, implementing the singleton design pattern.

        Args:
            cls (type): The class being instantiated.
            *args: Variable length argument list.
            **kwargs: Arbitrary keyword arguments.

        Returns:
            CtxMgrUtils: The singleton instance of the class.
        """
        # pylint: enable=line-too-long
        if not cls._instance:
            cls._instance = super().__new__(cls)
        return cls._instance

    @contextmanager
    def elapsed_timer(self):
        # pylint: disable=line-too-long
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
        # pylint: enable=line-too-long
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


LOG_FILE_STDERR = "LOG_FILE_STDERR"


class LoggingUtils:
    # pylint: disable=line-too-long
    """
    A singleton utility class providing advanced logging functionality with separate stdout and stderr streams.

    This class implements a comprehensive logging system with support for different log levels,
    formatted output, and separate handling of stdout and stderr streams. It includes special
    handling for AWS and HTTP-related libraries to suppress verbose logging.

    Features:
        - Singleton pattern implementation
        - Dual-stream logging (stdout and stderr)
        - Multiple logging levels (debug, info, error, success)
        - Pretty-format support for complex objects
        - Exception information logging
        - Automatic suppression of verbose third-party logging
        - Environment variable configuration support

    Methods:
        __new__(cls, *args, **kwargs): Creates singleton instance
        __init__(): Configures initial logging settings
        debug(name, msg, exc_info, enable_pformat): Logs debug messages to stderr
        debug_info(name, msg, exc_info, enable_pformat): Logs to both debug and info streams
        error(name, msg, exc_info, enable_pformat): Logs error messages to stderr
        info(name, msg, exc_info, enable_pformat): Logs info messages to stdout
        success(name, msg, exc_info, enable_pformat): Logs success messages to stdout
        get_stdout_logger(name): Creates/retrieves stdout logger
        get_stderr_logger(name): Creates/retrieves stderr logger

    Stream Configuration:
        stdout:
            - Default level: SUCCESS
            - Format: %(message)s
            - Used for: info, success messages
        stderr:
            - Default level: DEBUG
            - Format: %(asctime)s - %(levelname)s - %(message)s
            - Used for: debug, error messages

    Environment Variables:
        LOG_LEVEL_STDOUT: Controls stdout logging level
        LOG_LEVEL_STDERR: Controls stderr logging level

    Example:
        >>> logger = LoggingUtils()  # Creates or returns existing instance
        >>> logger.info("module_name", "Operation completed")
        >>> logger.debug("module_name", {"complex": "data"}, enable_pformat=True)
        >>> logger.error("module_name", "Error occurred", exc_info=True)

    Third-party Logging Control:
        Automatically sets CRITICAL level for:
        - boto3
        - botocore
        - urllib3
        - httpcore
        - httpx

    Dependencies:
        - logging: Python's standard logging module
        - pprint.pformat: For pretty-printing complex objects
        - os: For environment variable access

    Notes:
        - All logging methods are thread-safe
        - Pretty-formatting is optional for complex objects
        - Exception stack traces can be included via exc_info parameter
        - Logging levels follow standard Python logging hierarchy
    """
    # pylint: enable=line-too-long

    _instance = None

    def __new__(cls, *args, **kwargs):  # pylint: disable=unused-argument
        # pylint: disable=line-too-long
        """
        Creates and returns a singleton instance of the class.

        This method ensures that only one instance of the class is created
        throughout the application, implementing the singleton design pattern.

        Args:
            cls (type): The class being instantiated.
            *args: Variable length argument list.
            **kwargs: Arbitrary keyword arguments.

        Returns:
            LoggingUtils: The singleton instance of the class.
        """
        # pylint: enable=line-too-long
        if not cls._instance:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        # pylint: disable=line-too-long
        """
        Initializes the class instance by configuring log levels for various libraries.

        Sets critical log levels for boto3, botocore, urllib3, httpcore, and httpx to
        suppress verbose logging from these libraries.
        """
        # pylint: enable=line-too-long
        logging.getLogger("boto3").setLevel(logging.CRITICAL)
        logging.getLogger("botocore").setLevel(logging.CRITICAL)
        logging.getLogger("urllib3").setLevel(logging.CRITICAL)
        logging.getLogger("httpcore").setLevel(logging.CRITICAL)
        logging.getLogger("httpx").setLevel(logging.CRITICAL)

    def debug(
        self, name: str, msg: str, exc_info: bool = False, enable_pformat: bool = False
    ) -> None:
        # pylint: disable=line-too-long
        """
        Logs a debug message to the stderr stream.

        Args:
            name (str): The name of the logger.
            msg (str): The debug message to log.
            exc_info (bool, optional): Whether to include exception information. Defaults to False.
            enable_pformat (bool, optional): Whether to pretty-format the message. Defaults to False.
        """
        # pylint: enable=line-too-long
        self.get_stderr_logger(name).debug(
            (pformat(msg) if enable_pformat else msg), exc_info=exc_info
        )

    def debug_info(
        self, name: str, msg: str, exc_info=False, enable_pformat: bool = False
    ) -> None:
        # pylint: disable=line-too-long
        """
        Sends a message to the debug and info loggers.

        Args:
            name (str): The name of the logger.
            msg (str): The debug message to log.
            exc_info (bool, optional): Whether to include exception information. Defaults to False.
            enable_pformat (bool, optional): Whether to pretty-format the message. Defaults to False.
        """
        # pylint: enable=line-too-long
        self.get_stderr_logger(name).debug(
            pformat(msg) if enable_pformat else msg, exc_info=exc_info
        )
        self.get_stdout_logger(name).info(
            pformat(msg) if enable_pformat else msg, exc_info=exc_info
        )

    def error(
        self, name: str, msg: str, exc_info=False, enable_pformat: bool = False
    ) -> None:
        # pylint: disable=line-too-long
        """
        Logs an error message to the stderr stream.

        Args:
            name (str): The name of the logger.
            msg (str): The error message to log.
            exc_info (bool, optional): Whether to include exception information. Defaults to False.
            enable_pformat (bool, optional): Whether to pretty-format the message. Defaults to False.
        """
        # pylint: enable=line-too-long
        self.get_stderr_logger(name).error(
            pformat(msg) if enable_pformat else msg, exc_info=exc_info
        )

    def info(
        self, name: str, msg: str, exc_info=False, enable_pformat: bool = False
    ) -> None:
        # pylint: disable=line-too-long
        """
        Logs an informational message to the stdout stream.

        Args:
            name (str): The name of the logger.
            msg (str): The informational message to log.
            exc_info (bool, optional): Whether to include exception information. Defaults to False.
            enable_pformat (bool, optional): Whether to pretty-format the message. Defaults to False.
        """
        # pylint: enable=line-too-long
        self.get_stdout_logger(name).info(
            pformat(msg) if enable_pformat else msg, exc_info=exc_info
        )

    def success(
        self, name: str, msg: str, exc_info=False, enable_pformat: bool = False
    ) -> None:
        # pylint: disable=line-too-long
        """
        Logs a success message to the stdout stream.

        Args:
            name (str): The name of the logger.
            msg (str): The success message to log.
            exc_info (bool, optional): Whether to include exception information. Defaults to False.
            enable_pformat (bool, optional): Whether to pretty-format the message. Defaults to False.
        """
        # pylint: enable=line-too-long
        self.get_stdout_logger(name).success(
            pformat(msg) if enable_pformat else msg, exc_info=exc_info
        )

    def trace(
        self, name: str, msg: str, exc_info=False, enable_pformat: bool = False
    ) -> None:
        # pylint: disable=line-too-long
        """
        Logs a trace message to the stderr stream.

        Args:
            name (str): The name of the logger.
            msg (str): The debug message to log.
            exc_info (bool, optional): Whether to include exception information. Defaults to False.
            enable_pformat (bool, optional): Whether to pretty-format the message. Defaults to False.
        """
        # pylint: enable=line-too-long
        self.get_stderr_logger(name).trace(
            pformat(msg) if enable_pformat else msg, exc_info=exc_info
        )

    def warning(
        self, name: str, msg: str, exc_info=False, enable_pformat: bool = False
    ) -> None:
        # pylint: disable=line-too-long
        """
        Logs a warning message to the stdout stream.

        Args:
            name (str): The name of the logger.
            msg (str): The warning message to log.
            exc_info (bool, optional): Whether to include exception information. Defaults to False.
            enable_pformat (bool, optional): Whether to pretty-format the message. Defaults to False.
        """
        # pylint: enable=line-too-long
        self.get_stdout_logger(name).warning(
            pformat(msg) if enable_pformat else msg, exc_info=exc_info
        )

    def get_stdout_logger(self, name: str) -> logging.Logger:
        # pylint: disable=line-too-long
        """
        Creates and retrieves a logger that outputs to the stdout stream.

        The logger's level is determined by the LOG_LEVEL_STDOUT environment variable,
        defaulting to the SUCCESS level if not specified.

        Args:
            name (str): The name of the logger.

        Returns:
            logging.Logger: A configured logger for standard output.
        """
        # pylint: enable=line-too-long
        logger: logging.Logger = logging.getLogger(f"{name}.stdout")
        if not logger.handlers:
            logger_level = os.getenv("LOG_LEVEL_STDOUT", "SUCCESS").upper()
            self.debug(__class__.__name__, f"setting stdout logger level to {logger_level}")
            logger.setLevel(logger_level)
            console_handler: logging.Handler = logging.StreamHandler(stream=sys.stdout)
            console_handler.setLevel(logger_level)

            formatter: logging.Formatter = logging.Formatter("%(message)s")
            console_handler.setFormatter(formatter)

            logger.addHandler(console_handler)

        return logger

    def get_stderr_logger(self, name: str) -> logging.Logger:
        # pylint: disable=line-too-long
        """
        Creates or retrieves a logger for stderr stream.

        Configures a logger with level based on LOG_LEVEL_STDERR environment variable,
        defaulting to the DEBUG level if not specified.

        Args:
            name (str): Logger name/identifier

        Returns:
            logging.Logger: Configured logger for stderr

        Raises:
            MissingEnvironmentVariable: If LOG_FILE_STDERR environment variable is not set
        """
        # pylint: enable=line-too-long
        logger = logging.getLogger(f"{name}.stderr")
        if not logger.handlers:
            logger_level = os.getenv(
                "LOG_LEVEL_STDERR", logging.getLevelName(logging.DEBUG)
            ).upper()
            logger.setLevel(logger_level)

            file_handler_filename = os.getenv(LOG_FILE_STDERR)
            if file_handler_filename is None:
                raise MissingEnvironmentVariable(LOG_FILE_STDERR)
            file_handler = logging.FileHandler(filename=file_handler_filename, mode="a")
            file_handler.setLevel(logger_level)

            formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")

            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)

        return logger

    def is_stderr_logger_level(self, name: str, level: str) -> bool:
        # pylint: disable=line-too-long
        """
        Checks if the stderr logger is set to a specific logging level.

        Args:
            name (str): Logger name/identifier
            level (str): Logging level to check against (e.g., DEBUG, INFO, ERROR)

        Returns:
            bool: True if logger's effective level matches specified level
        """
        # pylint: enable=line-too-long
        if self.get_stderr_logger(name).getEffectiveLevel() == level:
            return True
        return False


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
        return Path.is_dir(Path(check_path))

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
        return Path.is_file(Path(check_path))

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
        return Path.exists(check_path)

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
        return Path.exists(check_path)

    def get_ascii_file_contents(self, source_path: str) -> str:
        # pylint: disable=line-too-long
        """
        Reads and returns the contents of a file using UTF-8 encoding.

        Args:
            source_path (str): The path to the file to read.

        Returns:
            str: The contents of the file as a string.
        """
        # pylint: enable=line-too-long
        LoggingUtils().trace(__class__.__name__, "start get_source_code")
        with open(source_path, "r", encoding="utf-8") as file:
            source_code = file.read()

        LoggingUtils().trace(__class__.__name__, "end get_source_code")
        return source_code


class GenericUtils:
    # pylint: disable=line-too-long
    """
    A singleton utility class providing general-purpose functionality for dynamic class loading
    and boolean value interpretation.

    This class implements the singleton pattern and provides utility methods for dynamic
    class loading from modules and packages, as well as string-to-boolean conversion using
    common truthy value representations.

    Features:
        - Singleton pattern implementation
        - Dynamic class loading from modules
        - Flexible boolean value interpretation
        - Package-aware module importing

    Methods:
        __new__(cls, *args, **kwargs): Creates singleton instance
        load_class(module_name, class_name, package_name): Dynamically loads a class
        is_truthy(value): Determines if a string value represents a truthy value

    Dynamic Class Loading:
        Supports loading classes from modules with:
        - Relative and absolute imports
        - Package-aware module resolution
        - Proper error handling for missing modules/classes

    Truthy Value Interpretation:
        Recognizes the following as True:
        - "1", "true", "yes", "on", "y"
        - Case-insensitive matching
        - None values (default to True)
        All other values are considered False

    Example:
        >>> utils = GenericUtils()  # Creates or returns existing instance
        >>> # Dynamic class loading
        >>> MyClass = utils.load_class("my_module", "MyClass", "my_package")
        >>> # Truthy value checking
        >>> utils.is_truthy("yes")  # Returns True
        >>> utils.is_truthy("no")   # Returns False

    Error Handling:
        load_class():
            - ImportError: When module cannot be found
            - AttributeError: When class doesn't exist in module

    Dependencies:
        - importlib: For dynamic module importing
        - typing: For type hints

    Notes:
        - The singleton pattern ensures consistent behavior across the application
        - String comparisons for truthy values are case-insensitive
        - Whitespace is stripped from truthy value inputs
    """
    # pylint: enable=line-too-long

    _instance = None

    def __new__(cls, *args, **kwargs):  # pylint: disable=unused-argument
        # pylint: disable=line-too-long
        """
        Creates and returns a singleton instance of the GenericUtils class.

        This method ensures that only one instance of the GenericUtils class is created
        throughout the application, implementing the singleton design pattern.

        Args:
            cls (type): The class being instantiated.
            *args: Variable length argument list.
            **kwargs: Arbitrary keyword arguments.

        Returns:
            Utilities: The singleton instance of the GenericUtils class.
        """
        # pylint: enable=line-too-long
        if not cls._instance:
            cls._instance = super().__new__(cls)
        return cls._instance

    def load_class(
        self, module_name: str, class_name: str, package_name: str
    ) -> object:
        # pylint: disable=line-too-long
        """
        Dynamically loads a class from a specified module and package.

        This method attempts to import a module and retrieve a class by name
        from that module. It raises an ImportError if the module cannot be
        found and an AttributeError if the class does not exist within the
        module.

        Args:
            module_name (str): The name of the module to import.
            class_name (str): The name of the class to retrieve.
            package_name (str): The package name to use for relative imports.

        Returns:
            object: The class object if found.

        Raises:
            ImportError: If the module cannot be imported.
            AttributeError: If the class cannot be found in the module.
        """
        # pylint: enable=line-too-long
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
        # pylint: disable=line-too-long
        """
        Determines if a value is considered "truthy".

        Checks if the value is equivalent to common truthy representations like "1", "true", "yes".

        Args:
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
        # pylint: enable=line-too-long
        # If no value exists, return True
        if value is None:
            return True

        # Convert to lowercase for case-insensitive comparison
        value = str(value).lower().strip()

        # Return result based on common truthy values
        return value in ["1", "true", "yes", "on", "y"]


class ModelUtils:
    # pylint: disable=line-too-long
    """
    A utility class for managing AI model configuration and AWS region settings.

    This class provides methods for retrieving AI model-related configuration values and
    AWS region settings from either environment variables or a configuration object. It
    implements lazy loading of values and supports environment variable overrides.

    Features:
        - AI model class and module name configuration
        - AWS region configuration management
        - Environment variable override support
        - Configuration fallback values
        - Lazy loading of configuration values

    Methods:
        __init__(configuration): Initializes with Configuration object
        get_desired_model_class_name(): Retrieves AI model class name
        get_desired_model_module_name(): Retrieves AI model module name
        get_region_name(): Retrieves AWS region name

    Configuration Priority:
        1. Environment variables (AI_MODEL_CLASS_NAME, AI_MODEL_MODULE_NAME, AWS_REGION)
        2. Configuration object values (ai_model.class.name, ai_model.module.name, aws.region)
        3. Default values (us-west-2 for region)

    Example:
        >>> config = Configuration()
        >>> model_utils = ModelUtils(config)
        >>> class_name = model_utils.get_desired_model_class_name()
        >>> module_name = model_utils.get_desired_model_module_name()
        >>> region = model_utils.get_region_name()

    Environment Variables:
        - AI_MODEL_CLASS_NAME: Override for model class name
        - AI_MODEL_MODULE_NAME: Override for model module name
        - AWS_REGION: Override for AWS region

    Configuration Keys:
        - ai_model.class.name: Default model class name
        - ai_model.module.name: Default model module name
        - aws.region: Default AWS region (defaults to 'us-west-2')

    Dependencies:
        - os: For environment variable access
        - Configuration: For default configuration values

    Notes:
        - All getter methods are planned to be converted to properties (TODO)
        - Values are lazily loaded when first accessed
        - Region configuration follows AWS standard region format
    """
    # pylint: enable=line-too-long

    def __init__(self, configuration: Configuration):
        # pylint: disable=line-too-long
        """
        Initializes the SourceCodeAnalyzerUtils with default None values.

        The actual values will be lazily loaded when the respective getter
        methods are called for the first time.

        Args:
            configuration (Configuration): The configuration object to use for retrieving settings.
        """
        # pylint: enable=line-too-long
        self._config: Configuration = configuration

    @property
    def desired_model_class_name(self):
        # pylint: disable=line-too-long
        """
        Retrieves the configured AI model class name from the configuration.

        This method fetches the class name for the AI model from the configuration using a dot-notation path.
        If the configuration value is not found, it returns a default value of "not found".

        Returns:
            str: The configured class name for the AI model, or "not found" if not configured.
        """
        # pylint: enable=line-too-long
        return self._config.str_value("ai_model.class.name", "not found")

    @property
    def desired_model_module_name(self) -> str:
        # pylint: disable=line-too-long
        """
        Retrieves the configured AI model module name from the configuration.

        This method fetches the module name for the AI model from the configuration using a dot-notation path.
        If the configuration value is not found, it returns a default value of "not found".

        Returns:
            str: The configured module name for the AI model, or "not found" if not configured.
        """
        # pylint: enable=line-too-long
        return self._config.str_value("ai_model.module.name", "not found")

    @property
    def region_name(self) -> str:
        # pylint: disable=line-too-long
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
        # pylint: enable=line-too-long
        return os.getenv(
            # "AWS_REGION", self._config.str_value("aws").get("region", "us-west-2")
            "AWS_REGION", self._config.str_value("aws.region", "us-west-2")
        )


class JsonUtils:
    # pylint: disable=line-too-long
    """
    A utility class for JSON-related operations with singleton pattern implementation.

    This class provides various utility methods for handling JSON operations, including
    serialization, deserialization, and extraction of JSON blocks from text. It implements
    the singleton pattern to ensure only one instance exists throughout the application.

    Features:
        - JSON serialization with datetime support
        - JSON deserialization
        - Code block extraction from text
        - JSON block extraction from text
        - Singleton pattern implementation

    Methods:
        __new__(cls, *args, **kwargs): Creates singleton instance
        __init__(): Initializes the class with logging utilities
        json_loads(json_string): Deserializes JSON string to Python object
        json_dumps_with_datetime_serialization(obj, json_options): Serializes object to JSON string
        handle_datetime_serialization(obj): Converts datetime objects to ISO format
        extract_code_blocks(text, block_type): Extracts code blocks of specified type
        extract_json(text): Extracts JSON blocks from text

    Example:
        >>> json_utils = JsonUtils()  # Creates or returns existing instance
        >>> data = {'timestamp': datetime.now(), 'value': 42}
        >>> json_str = json_utils.json_dumps_with_datetime_serialization(data)
        >>> print(json_str)
        {"timestamp": "2023-12-20T10:30:00", "value": 42}

    Notes:
        - The class uses LoggingUtils for debug and warning messages
        - DateTime objects are automatically serialized to ISO format strings
        - JSON extraction supports markdown-style code blocks

    Dependencies:
        - json: For JSON serialization/deserialization
        - re: For regular expression operations
        - datetime: For datetime handling
        - LoggingUtils: For logging functionality
    """
    # pylint: enable=line-too-long

    _instance = None

    def __new__(cls, *args, **kwargs):  # pylint: disable=unused-argument
        # pylint: disable=line-too-long
        """
        Creates and returns a singleton instance of the JsonUtils class.

        This method ensures that only one instance of the class is created
        throughout the application, implementing the singleton design pattern.

        Args:
            cls (type): The class being instantiated.
            *args: Variable length argument list.
            **kwargs: Arbitrary keyword arguments.

        Returns:
            CtxMgrUtils: The singleton instance of the JsonUtils class.
        """
        # pylint: enable=line-too-long
        if not cls._instance:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        # pylint: disable=line-too-long
        """
        Initializes the JsonUtils class.
        """
        # pylint: enable=line-too-long
        self._logging_utils = LoggingUtils()

    def json_loads(self, json_string: str):
        # pylint: disable=line-too-long
        """
        Deserializes a JSON formatted string to a Python object.

        This method takes a JSON formatted string as input and deserializes
        it to a Python dictionary

        Args:
            json_string (str): The JSON string to deserialize.

        Returns:
            dict: The deserialized Python object.
        """
        # pylint: enable=line-too-long
        return json.loads(json_string)

    def json_dumps_with_datetime_serialization(self, obj, json_options=None):
        # pylint: disable=line-too-long
        """
        Serializes an object to a JSON formatted string with datetime serialization.

        This method takes an object and serializes it to a JSON formatted string using the
        'json.dumps' function. It uses the 'default' parameter of 'json.dumps' to specify a custom
        serialization function, which is 'self.handle_datetime_serialization'. This custom
        serialization function is responsible for serializing datetime objects to their ISO
        formatted string representation.

        Args:
            obj: The object to be serialized.
            json_options (dict, optional): Additional options to be passed to the 'json.dumps' function.

        Returns:
            str: The JSON formatted string representation of the object.

        Example:
            >>> json_utils = JsonUtils()
            >>> data = {'name': 'John', 'age': 30, 'timestamp': datetime.now()}
            >>> json_string = json_utils.json_dumps_with_datetime_serialization(data)
            >>> print(json_string)
            {"name": "John", "age": 30, "timestamp": "2022-01-01T12:00:00"}
        """
        # pylint: enable=line-too-long
        return json.dumps(
            obj, default=self.handle_datetime_serialization, **(json_options or {})
        )

    def handle_datetime_serialization(self, obj):
        # pylint: disable=line-too-long
        """
        Serializes a datetime object to its ISO formatted string representation.

        This method takes a datetime object as input and returns its ISO formatted string
        representation using the 'isoformat()' method of the datetime object. If the input object
        is not a datetime object, a TypeError is raised.

        Args:
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
        # pylint: enable=line-too-long
        if isinstance(obj, datetime):
            return obj.isoformat()
        raise TypeError(f"Type {type(obj)} not serializable")

    def extract_code_blocks(self, text: str, block_type: str) -> list | str:
        # pylint: disable=line-too-long
        """
        Extract all code blocks of a specific type from the given input text.

        This method uses regular expressions to find and extract all code blocks of the specified type
        from the input text. Code blocks are expected to be formatted in markdown style with triple backticks.

        Args:
            text (str): The input text containing code blocks.
            block_type (str): The type of code block to extract (e.g., 'json', 'python').

        Returns:
            list | str: A list of extracted code blocks or a single string if only one block is found.
        """
        # pylint: enable=line-too-long
        self._logging_utils.debug(__class__.__name__, "start extract_code_blocks")
        self._logging_utils.debug(__class__.__name__, "end extract_code_blocks")
        return re.findall(rf"```{block_type}\s*(.*?)\s*```", text, re.DOTALL)

    def extract_json(self, text: str) -> list | str:
        # pylint: disable=line-too-long
        """
        Extract the first JSON block from the given input text.

        This method finds and extracts the first JSON code block from the input text.
        JSON blocks are expected to be formatted in markdown style with triple backticks and 'json' identifier.

        Args:
            text (str): The input text containing JSON code blocks.

        Returns:
            list | str: The extracted JSON block as a string, or an empty JSON object string "{}" if no JSON blocks are found.
        """
        # pylint: enable=line-too-long
        self._logging_utils.debug(__class__.__name__, "start extract_json")
        json_blocks = self.extract_code_blocks(text, "json")
        if json_blocks:
            self._logging_utils.debug(
                __class__, f"type(json_blocks): {type(json_blocks)}"
            )
            self._logging_utils.debug(
                __class__,
                f"extract_json json_blocks: "
                f"{json_blocks[0] if isinstance(json_blocks, list) else json_blocks}",
                enable_pformat=True,
            )
            self._logging_utils.debug(__class__.__name__, "end extract_json")
            return json_blocks[0] if isinstance(json_blocks, list) else json_blocks
        self._logging_utils.warning(__class__.__name__, "No json blocks found")
        self._logging_utils.debug(__class__.__name__, "end extract_json empty")
        return "{}"


class FormatterUtils:
    # pylint: disable=line-too-long
    """
    A utility class for managing formatter configuration with singleton pattern implementation.

    This class provides methods for retrieving formatter-related configuration values from
    either environment variables or a configuration object. It implements the singleton pattern
    to ensure consistent formatter configuration throughout the application.

    Features:
        - Singleton pattern implementation
        - Environment variable override support
        - Configuration fallback values
        - Formatter class and module name retrieval

    Methods:
        __new__(cls, *args, **kwargs): Creates singleton instance
        __init__(configuration): Initializes with Configuration object
        get_desired_formatter_class_name(): Retrieves formatter class name
        get_desired_formatter_module_name(): Retrieves formatter module name

    Configuration Priority:
        1. Environment variables (FORMATTER_CLASS_NAME, FORMATTER_MODULE_NAME)
        2. Configuration object values (formatter.class.name, formatter.module.name)

    Example:
        >>> config = Configuration()
        >>> formatter_utils = FormatterUtils(config)
        >>> class_name = formatter_utils.get_desired_formatter_class_name()
        >>> module_name = formatter_utils.get_desired_formatter_module_name()

    Environment Variables:
        - FORMATTER_CLASS_NAME: Override for formatter class name
        - FORMATTER_MODULE_NAME: Override for formatter module name

    Configuration Keys:
        - formatter.class.name: Default formatter class name
        - formatter.module.name: Default formatter module name

    Dependencies:
        - os: For environment variable access
        - Configuration: For default configuration values
    """
    # pylint: enable=line-too-long

    _instance = None

    def __new__(cls, *args, **kwargs):  # pylint: disable=unused-argument
        # pylint: disable=line-too-long
        """
        Creates and returns a singleton instance of the FormatterUtils class.

        This method ensures that only one instance of the class is created
        throughout the application, implementing the singleton design pattern.

        Args:
            cls (type): The class being instantiated.
            *args: Variable length argument list.
            **kwargs: Arbitrary keyword arguments.

        Returns:
            formatterUtils: The singleton instance of the FormatterUtils class.
        """
        # pylint: enable=line-too-long
        if not cls._instance:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, configuration: Configuration):
        # pylint: disable=line-too-long
        """
        Initializes a new instance of the FormatterUtils class.

        This method sets up the FormatterUtils instance with a configuration object
        that will be used to retrieve formatter settings. Since this class implements
        the singleton pattern, this initialization will only take effect the first time
        an instance is created.

        Args:
            configuration (Configuration): The configuration object containing formatter settings.
                                        This object should provide a 'value' method to retrieve
                                        configuration properties.

        Note:
            Due to the singleton implementation, subsequent initializations with different
            configuration objects will not affect the existing instance.
        """
        # pylint: enable=line-too-long

        self._config = configuration

    def get_desired_formatter_class_name(self) -> str:
        # pylint: disable=line-too-long
        """
        Retrieves the desired formatter class name from configuration.

        This method returns the formatter class name based on the following priority:
        1. FORMATTER_CLASS_NAME environment variable if set
        2. Value from configuration using the key 'formatter.class.name'

        Returns:
            str: The name of the formatter class to be used.

        Example:
            >>> formatter_utils = FormatterUtils(config)
            >>> formatter_class_name = formatter_utils.get_desired_formatter_class_name()
            >>> print(formatter_class_name)
            'JsonFormatter'
        """
        # pylint: enable=line-too-long
        return self._config.str_value("formatter.class.name", "not found")

    def get_desired_formatter_module_name(self) -> str:
        # pylint: disable=line-too-long
        """
        Retrieves the desired formatter module name from configuration.

        This method returns the formatter module name based on the following priority:
        1. FORMATTER_MODULE_NAME environment variable if set
        2. Value from configuration using the key 'formatter.module.name'

        Returns:
            str: The name of the module containing the formatter class.

        Example:
            >>> formatter_utils = FormatterUtils(config)
            >>> formatter_module_name = formatter_utils.get_desired_formatter_module_name()
            >>> print(formatter_module_name)
            'formatters.json'
        """
        # pylint: enable=line-too-long
        return self._config.str_value("formatter.module.name", "not found")
