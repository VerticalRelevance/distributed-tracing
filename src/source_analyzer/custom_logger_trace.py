"""
Custom Logging Module with Trace Level

This module extends Python's standard logging module by introducing a custom 'TRACE'
log level and a corresponding logging method. The module allows for a new logging level
between NOTSET and DEBUG, providing more granular logging capabilities.

Key Features:
    - Adds a custom TRACE log level (value 5)
    - Extends logging.Logger with a trace() method
    - Allows logging trace messages with a dedicated log level

Classes:
    CustomLoggerSuccess: A custom Logger class that adds a trace logging method.

Constants:
    TRACE (int): Custom logging level with value 5, positioned between NOTSET and DEBUG.
"""

import logging

# Define custom level
TRACE = 5

# Add the custom level
logging.addLevelName(TRACE, "TRACE")


class CustomLoggerTrace(logging.Logger):
    """
    A custom Logger class that extends the standard logging.Logger
    with a trace() method for logging trace-level messages.

    The CustomLoggerTrace class allows logging messages at a new 'TRACE'
    log level, providing more nuanced logging between NOTSET and TRACE levels.

    Attributes:
        Inherits all attributes from the standard logging.Logger class.

    Methods:
        trace: Logs a message at the SUCCESS log level.
    """

    def trace(self, message, *args, **kwargs):
        """
        Log a message with severity 'TRACE' on this logger.

        This method allows logging messages at a custom TRACE level, which is
        more specific than NOTSET and less than DEBUG.

        Args:
            message (str): The log message to be recorded.
            *args: Variable positional arguments to be passed to the logging method.
            **kwargs: Variable keyword arguments to be passed to the logging method.

        Example:
            >>> logger = logging.getLogger(__name__)
            >>> logger.trace("start something")
        """
        if self.isEnabledFor(TRACE):
            self._log(TRACE, message, args, **kwargs)


# Attach the method to the Logger class
logging.Logger.trace = CustomLoggerTrace.trace
