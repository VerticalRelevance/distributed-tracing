"""
Custom Logging Module with Success Level

This module extends Python's standard logging module by introducing a custom 'SUCCESS'
log level and a corresponding logging method. The module allows for a new logging level
between INFO and WARNING, providing more granular logging capabilities.

Key Features:
    - Adds a custom SUCCESS log level (value 25)
    - Extends logging.Logger with a success() method
    - Allows logging success messages with a dedicated log level

Classes:
    CustomLoggerSuccess: A custom Logger class that adds a success logging method.

Constants:
    SUCCESS (int): Custom logging level with value 25, positioned between INFO and WARNING.
"""

import logging

# Define custom level
SUCCESS = 25

# Add the custom level
logging.addLevelName(SUCCESS, "SUCCESS")


class CustomLoggerSuccess(logging.Logger):
    """
    A custom Logger class that extends the standard logging.Logger
    with a success() method for logging success-level messages.

    The CustomLoggerSuccess class allows logging messages at a new 'SUCCESS'
    log level, providing more nuanced logging between INFO and WARNING levels.

    Attributes:
        Inherits all attributes from the standard logging.Logger class.

    Methods:
        success: Logs a message at the SUCCESS log level.
    """

    def success(self, message, *args, **kwargs):
        """
        Log a message with severity 'SUCCESS' on this logger.

        This method allows logging messages at a custom SUCCESS level, which is
        more specific than INFO but less severe than WARNING.

        Args:
            message (str): The log message to be recorded.
            *args: Variable positional arguments to be passed to the logging method.
            **kwargs: Variable keyword arguments to be passed to the logging method.

        Example:
            >>> logger = logging.getLogger(__name__)
            >>> logger.success("Operation completed successfully")
        """
        if self.isEnabledFor(SUCCESS):
            self._log(SUCCESS, message, args, **kwargs)


# Attach the method to the Logger class
logging.Logger.success = CustomLoggerSuccess.success
