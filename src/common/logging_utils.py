"""
Advanced logging utility module using Loguru for stderr output.

This module provides a singleton utility class for comprehensive logging functionality
using the Loguru logging library with output exclusively to stderr. It offers
a cleaner, more modern alternative to Python's standard logging module with
simplified configuration and enhanced features.

Key Features:
    - Singleton pattern implementation
    - Stderr-only logging with file output
    - Full support for Loguru's built-in logging levels (TRACE, DEBUG, INFO, SUCCESS, WARNING, ERROR, CRITICAL)
    - Pretty-format support for complex objects
    - Exception information logging
    - Automatic suppression of verbose third-party logging
    - Environment variable configuration support
    - Thread-safe operations
    - Simplified configuration with Loguru's intuitive API

Dependencies:
    - loguru: Modern logging library for Python
    - pprint: For pretty-printing complex objects
    - os: For environment variable access

Example:
    >>> logger = LoggingUtils()
    >>> logger.info("module_name", "Operation completed")
    >>> logger.debug("module_name", {"complex": "data"}, enable_pformat=True)
    >>> logger.error("module_name", "Error occurred", exc_info=True)
"""

import os
import logging  # only for lowering the log-levels of external packages still using the Python logging package
from pprint import pformat
from typing import Any

from loguru import logger
from common.exceptions import MissingEnvVarException

LOG_FILE_NAME = "LOG_FILE"
LOG_FILE_COMPRESSION = "LOG_FILE_COMPRESSION"
LOG_FILE_RETENTION = "LOG_FILE_RETENTION"
LOG_FILE_ROTATION = "LOG_FILE_ROTATION"
LOG_LEVEL = "LOG_LEVEL"


class LoggingUtils:
    # pylint: disable=line-too-long
    """
    A singleton utility class providing advanced logging functionality with stderr output.

    This class implements a comprehensive logging system using Loguru with support for all
    standard logging levels, formatted output, and stderr file logging. It includes special
    handling for AWS and HTTP-related libraries to suppress verbose logging.

    Features:
        - Singleton pattern implementation
        - Stderr-only logging with file output
        - Full Loguru logging level support (TRACE, DEBUG, INFO, SUCCESS, WARNING, ERROR, CRITICAL)
        - Pretty-format support for complex objects
        - Exception information logging
        - Automatic suppression of verbose third-party logging
        - Environment variable configuration support
        - Thread-safe operations with Loguru's built-in thread safety

    Attributes:
        CRITICAL (int): Critical logging level (50)
        DEBUG (int): Debug logging level (10)
        ERROR (int): Error logging level (40)
        INFO (int): Info logging level (20)
        SUCCESS (int): Success logging level (25) - Loguru built-in
        TRACE (int): Trace logging level (5) - Loguru built-in
        WARNING (int): Warning logging level (30)

    Configuration:
        stderr:
            - Default level: DEBUG
            - Format: {time:YYYY-MM-DD HH:mm:ss} - {level} - {name}: {message}
            - Output: File specified by LOG_FILE environment variable

    Environment Variables:
        LOG_LEVEL: Controls logging level (default: DEBUG)
        LOG_FILE: Path to stderr log file (required)

    Example:
        >>> logger_utils = LoggingUtils()  # Creates or returns existing instance
        >>> logger_utils.info("module_name", "Operation completed")
        >>> logger_utils.debug("module_name", {"complex": "data"}, enable_pformat=True)
        >>> logger_utils.error("module_name", "Error occurred", exc_info=True)
        >>> logger_utils.success("module_name", "Task completed successfully")
        >>> logger_utils.trace("module_name", "Detailed trace information")

    Third-party Logging Control:
        Automatically sets CRITICAL level for:
        - boto3
        - botocore
        - urllib3
        - httpcore
        - httpx

    Dependencies:
        - loguru: A library which aims to bring enjoyable logging in Python.
        - pprint.pformat: For pretty-printing complex objects
        - os: For environment variable access

    Notes:
        - All logging methods are thread-safe
        - Pretty-formatting is optional for complex objects
        - Exception stack traces can be included via exc_info parameter
        - Uses Loguru's efficient and modern logging implementation
        - Supports all Loguru built-in logging levels
    """
    # pylint: enable=line-too-long

    # Expose logging levels as class attributes (Loguru built-in values)
    CRITICAL = 50
    DEBUG = 10
    ERROR = 40
    INFO = 20
    SUCCESS = 25  # Loguru built-in
    TRACE = 5     # Loguru built-in
    WARNING = 30

    _instance = None
    _initialized = False

    def __new__(cls, *args, **kwargs) -> 'LoggingUtils': # pylint: disable=unused-argument
        # pylint: disable=line-too-long
        """
        Creates and returns a singleton instance of the class.

        This method ensures that only one instance of the class is created
        throughout the application, implementing the singleton design pattern.

        Args:
            cls (type): The class being instantiated.
            *args: Variable length argument list (unused).
            **kwargs: Arbitrary keyword arguments (unused).

        Returns:
            LoggingUtils: The singleton instance of the class.
        """
        # pylint: enable=line-too-long

        if not cls._instance:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self) -> None:
        # pylint: disable=line-too-long
        """
        Initializes the class instance by configuring the stderr logger.

        Sets up Loguru logger for stderr file output with appropriate
        formatting and log level. Also suppresses verbose logging from
        third-party libraries (boto3, botocore, urllib3, httpcore, httpx).

        Note:
            This method uses a flag to ensure initialization only occurs once
            for the singleton instance.

        Raises:
            MissingEnvVarException: If LOG_FILE environment variable is not set.
        """
        # pylint: enable=line-too-long

        if LoggingUtils._initialized:
            return

        # Configure third-party library logging
        self._configure_third_party_logging()

        # Remove default logger to avoid duplicate logs
        logger.remove()

        # Setup stderr logger
        self._setup_logger()

        LoggingUtils._initialized = True

    def _configure_third_party_logging(self) -> None:
        # pylint: disable=line-too-long
        """
        Configures logging levels for third-party libraries to suppress verbose output.

        Sets critical log levels for boto3, botocore, urllib3, httpcore, and httpx
        to minimize noise in the application logs.
        """
        # pylint: enable=line-too-long
        logging.getLogger("boto3").setLevel(logging.CRITICAL)
        logging.getLogger("botocore").setLevel(logging.CRITICAL)
        logging.getLogger("urllib3").setLevel(logging.CRITICAL)
        logging.getLogger("httpcore").setLevel(logging.CRITICAL)
        logging.getLogger("httpx").setLevel(logging.CRITICAL)

    def log(self, level: str, name: str, msg: Any, exc_info: bool = False, enable_pformat: bool = False) -> None:
        # pylint: disable=line-too-long
        """
        Logs a message with the specified level, name, and optional exception information.

        Args:
            level (str): The logging level (e.g., "INFO", "ERROR").
            name (str): The name/identifier of the logger context.
            msg (Any): The message to log.
            exc_info (bool): Whether to include exception information.
            enable_pformat (bool): Whether to pretty-format the message.
        """
        # pylint: enable=line-too-long
        self._log_with_context(level, name, msg, exc_info, enable_pformat)

    def _setup_logger(self) -> None:
        # pylint: disable=line-too-long
        """
        Sets up the stderr logger with file output and detailed formatting.

        Configures a logger that outputs to a file for all log levels
        with detailed formatting including timestamp, level, and logger name.

        Raises:
            MissingEnvVarException: If LOG_FILE environment variable is not set.
        """
        # pylint: enable=line-too-long
        stderr_level = os.getenv(LOG_LEVEL, "DEBUG").upper()
        log_file = os.getenv(LOG_FILE_NAME)

        if log_file is None:
            raise MissingEnvVarException(LOG_FILE_NAME)

        logger.add(
            log_file,
            format="{time:YYYY-MM-DD HH:mm:ss} - {level:8} {message}",
            level=stderr_level,
            rotation=os.getenv(LOG_FILE_ROTATION, "10 MB"),  # Rotate when file reaches 10MB
            retention=os.getenv(LOG_FILE_RETENTION, "7 days"),  # Keep logs for 7 days
            compression=os.getenv(LOG_FILE_COMPRESSION, "zip")  # Compress old logs
        )

    def _format_message(self, name: str, msg: Any, enable_pformat: bool = False) -> str:
        # pylint: disable=line-too-long
        """
        Formats a message for logging, optionally using pretty-printing.

        Args:
            msg (Any): The message to format.
            enable_pformat (bool): Whether to use pretty-printing for complex objects.

        Returns:
            str: The formatted message.
        """
        # pylint: enable=line-too-long
        return f"({name}) {pformat(msg)}" if enable_pformat else str(msg)


    def _log_with_context(
            self, level: str, name: str, msg: Any, exc_info: bool = False, enable_pformat: bool = False) -> None:
        # pylint: disable=line-too-long
        """
        Internal method to log messages with context binding.

        Args:
            level (str): The logging level.
            name (str): The name/identifier of the logger context.
            msg (Any): The message to log.
            exc_info (bool): Whether to include exception information.
            enable_pformat (bool): Whether to pretty-format the message.
        """
        formatted_msg = self._format_message(name, msg, enable_pformat)
        final_msg = f"{name}: {formatted_msg}"
        log_method = getattr(logger, level.lower())

        if exc_info:
            # Use loguru's exception method for exception logging
            logger.exception(final_msg)
        else:
            log_method(final_msg)

    def get_class_logger(self, class_name: str) -> 'ClassLogger':
        """
        Creates a class-specific logger that automatically includes the class name.

        Args:
            class_name (str): The name of the class.

        Returns:
            ClassLogger: A logger instance bound to the class name.

        Example:
            >>> class MyService:
            ...     def __init__(self):
            ...         self.logger = LoggingUtils().get_class_logger(self.__class__.__name__)
            ...     def do_work(self):
            ...         self.logger.info("Starting work")  # Logs: "MyService: Starting work"
        """
        return ClassLogger(self, class_name)

    def trace(
        self, name: str, msg: Any, exc_info: bool = False, enable_pformat: bool = False
    ) -> None:
        # pylint: disable=line-too-long
        """
        Logs a trace message using Loguru's built-in TRACE level.

        Trace messages are used for very detailed diagnostic information,
        typically only of interest when diagnosing problems.

        Args:
            name (str): The name/identifier of the logger context.
            msg (Any): The trace message to log.
            exc_info (bool, optional): Whether to include exception information. Defaults to False.
            enable_pformat (bool, optional): Whether to pretty-format the message. Defaults to False.
        """
        # pylint: enable=line-too-long

        self._log_with_context("TRACE", name, msg, exc_info, enable_pformat)

    def debug(
        self, name: str, msg: Any, exc_info: bool = False, enable_pformat: bool = False
    ) -> None:
        # pylint: disable=line-too-long
        """
        Logs a debug message using Loguru's built-in DEBUG level.

        Debug messages are used for detailed diagnostic information,
        typically only of interest when diagnosing problems.

        Args:
            name (str): The name/identifier of the logger context.
            msg (Any): The debug message to log.
            exc_info (bool, optional): Whether to include exception information. Defaults to False.
            enable_pformat (bool, optional): Whether to pretty-format the message. Defaults to False.
        """
        # pylint: enable=line-too-long

        self._log_with_context("DEBUG", name, msg, exc_info, enable_pformat)

    def info(
        self, name: str, msg: str, exc_info=False, enable_pformat: bool = False
    ) -> None:
        # pylint: disable=line-too-long
        """
        Logs an informational message using Loguru's built-in INFO level.

        Info messages are used for general informational messages that
        confirm things are working as expected.

        Args:
            name (str): The name/identifier of the logger context.
            msg (Any): The informational message to log.
            exc_info (bool, optional): Whether to include exception information. Defaults to False.
            enable_pformat (bool, optional): Whether to pretty-format the message. Defaults to False.
        """
        # pylint: enable=line-too-long
        self._log_with_context("INFO", name, msg, exc_info, enable_pformat)

    def success(
        self, name: str, msg: Any, exc_info: bool = False, enable_pformat: bool = False
    ) -> None:
        # pylint: disable=line-too-long
        """
        Logs a success message using Loguru's built-in SUCCESS level.

        Success messages are used to indicate successful completion of
        operations or positive outcomes.

        Args:
            name (str): The name/identifier of the logger context.
            msg (Any): The success message to log.
            exc_info (bool, optional): Whether to include exception information. Defaults to False.
            enable_pformat (bool, optional): Whether to pretty-format the message. Defaults to False.
        """
        # pylint: enable=line-too-long
        self._log_with_context("SUCCESS", name, msg, exc_info, enable_pformat)

    def warning(
        self, name: str, msg: Any, exc_info: bool = False, enable_pformat: bool = False
    ) -> None:
        # pylint: disable=line-too-long
        """
        Logs a warning message using Loguru's built-in WARNING level.

        Warning messages are used to indicate that something unexpected
        happened, or to indicate some problem in the near future.

        Args:
            name (str): The name/identifier of the logger context.
            msg (Any): The warning message to log.
            exc_info (bool, optional): Whether to include exception information. Defaults to False.
            enable_pformat (bool, optional): Whether to pretty-format the message. Defaults to False.
        """
        # pylint: enable=line-too-long
        self._log_with_context("WARNING", name, msg, exc_info, enable_pformat)

    def error(
        self, name: str, msg: Any, exc_info: bool = False, enable_pformat: bool = False
    ) -> None:
        """
        Logs an error message using Loguru's built-in ERROR level.

        Error messages are used to indicate a serious problem that prevented
        the application from performing a function.

        Args:
            name (str): The name/identifier of the logger context.
            msg (Any): The error message to log.
            exc_info (bool, optional): Whether to include exception information. Defaults to False.
            enable_pformat (bool, optional): Whether to pretty-format the message. Defaults to False.
        """
        self._log_with_context("ERROR", name, msg, exc_info, enable_pformat)

    def critical(
        self, name: str, msg: Any, exc_info: bool = False, enable_pformat: bool = False
    ) -> None:
        """
        Logs a critical message using Loguru's built-in CRITICAL level.

        Critical messages are used to indicate a very serious error that
        may prevent the application from continuing to run.

        Args:
            name (str): The name/identifier of the logger context.
            msg (Any): The critical message to log.
            exc_info (bool, optional): Whether to include exception information. Defaults to False.
            enable_pformat (bool, optional): Whether to pretty-format the message. Defaults to False.
        """
        self._log_with_context("CRITICAL", name, msg, exc_info, enable_pformat)


    def get_logger_level(self) -> str:
        """
        Gets the current logging level for the stderr logger.

        Returns:
            str: The current logging level name.
        """
        return os.getenv("LOG_LEVEL", "DEBUG").upper()

    def is_level_enabled(self, level: str) -> bool:
        """
        Checks if a specific logging level is enabled.

        Args:
            level (str): The logging level to check (e.g., "DEBUG", "INFO", "ERROR").

        Returns:
            bool: True if the specified level is enabled.
        """
        current_level = self.get_logger_level()
        level_values = {
            "TRACE": self.TRACE,
            "DEBUG": self.DEBUG,
            "INFO": self.INFO,
            "SUCCESS": self.SUCCESS,
            "WARNING": self.WARNING,
            "ERROR": self.ERROR,
            "CRITICAL": self.CRITICAL
        }

        return level_values.get(level.upper(), 0) >= level_values.get(current_level, 0)

    def is_logger_level(self, level: str) -> bool:
        # pylint: disable=line-too-long
        """
        Backward compatibility method for checking stderr logger level.

        Args:
            name (str): Logger name/identifier (unused in this implementation).
            level (str): Logging level to check against.

        Returns:
            bool: True if logger's effective level matches specified level.
        """
        return self.is_level_enabled(level)


class ClassLogger:
    """
    A class-specific logger that automatically includes the class name in all log messages.

    This class provides a convenient interface for logging within a specific class context,
    automatically prefixing all log messages with the class name.

    Args:
        logging_utils (LoggingUtils): The parent logging utility instance.
        class_name (str): The name of the class this logger is bound to.

    Example:
        >>> class MyService:
        ...     def __init__(self):
        ...         self.logger = LoggingUtils().get_class_logger(self.__class__.__name__)
        ...     def process_data(self):
        ...         self.logger.info("Processing started")  # Logs: "MyService: Processing started"
        ...         self.logger.success("Processing completed")  # Logs: "MyService: Processing completed"
    """

    def __init__(self, this_logger: LoggingUtils, class_name: str):
        """
        Initialize the class logger.

        Args:
            logging_utils (LoggingUtils): The parent logging utility instance.
            class_name (str): The name of the class this logger is bound to.
        """
        self._logger = this_logger
        self._class_name = class_name

    def is_logger_level(self, level: str) -> bool:
        """Is the logger level set to the level argument value."""
        return self._logger.is_level_enabled(level)

    def trace(self, msg: Any, exc_info: bool = False, enable_pformat: bool = False) -> None:
        """Log a trace message with automatic class name inclusion."""
        self._logger.trace(self._class_name, msg, exc_info, enable_pformat)

    def debug(self, msg: Any, exc_info: bool = False, enable_pformat: bool = False) -> None:
        """Log a debug message with automatic class name inclusion."""
        self._logger.debug(self._class_name, msg, exc_info, enable_pformat)

    def info(self, msg: Any, exc_info: bool = False, enable_pformat: bool = False) -> None:
        """Log an info message with automatic class name inclusion."""
        self._logger.info(self._class_name, msg, exc_info, enable_pformat)

    def success(self, msg: Any, exc_info: bool = False, enable_pformat: bool = False) -> None:
        """Log a success message with automatic class name inclusion."""
        self._logger.success(self._class_name, msg, exc_info, enable_pformat)
        print(msg)

    def warning(self, msg: Any, exc_info: bool = False, enable_pformat: bool = False) -> None:
        """Log a warning message with automatic class name inclusion."""
        self._logger.warning(self._class_name, msg, exc_info, enable_pformat)

    def error(self, msg: Any, exc_info: bool = False, enable_pformat: bool = False) -> None:
        """Log an error message with automatic class name inclusion."""
        self._logger.error(self._class_name, msg, exc_info, enable_pformat)
        print(msg)

    def critical(self, msg: Any, exc_info: bool = False, enable_pformat: bool = False) -> None:
        """Log a critical message with automatic class name inclusion."""
        self._logger.critical(self._class_name, msg, exc_info, enable_pformat)
