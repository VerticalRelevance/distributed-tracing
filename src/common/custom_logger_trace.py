# pylint: disable=line-too-long
"""
Custom Logging Module with Trace Level

This module extends Python's standard logging module by introducing a custom 'TRACE' log level and a
corresponding logging method. It provides a logging level between NOTSET and DEBUG for more detailed logging.

Key Features:
    - Adds a custom TRACE log level (value 5)
    - Extends logging.Logger with a trace() method
    - Provides a dedicated level for logging fine-grained execution details
"""
# pylint: enable=line-too-long

import logging

# Define custom level
TRACE = 5

# Add the custom level
logging.addLevelName(TRACE, "TRACE")


class CustomLoggerTrace(logging.Logger):
    # pylint: disable=line-too-long
    """
    A custom Logger class that extends the standard logging.Logger with a trace() method.

    This class adds the capability to log messages at the TRACE level (5), which sits between
    the standard NOTSET (0) and DEBUG (10) levels in severity.

    Attributes:
        Inherits all attributes from the standard logging.Logger class.
    """
    # pylint: enable=line-too-long

    def trace(self, message, *args, **kwargs):
        # pylint: disable=line-too-long
        """
        Log a message with severity 'TRACE' on this logger.

        This method logs messages at the custom TRACE level (5), which is more detailed than
        DEBUG and intended for very fine-grained debugging information.

        Args:
            message (str): The message to be logged.
            *args: Variable positional arguments passed to the underlying logger.
            **kwargs: Variable keyword arguments passed to the underlying logger.

        Example:
            >>> logger = logging.getLogger(__name__)
            >>> logger.trace("Entering function with arguments: x=5, y=10")
        """
        # pylint: enable=line-too-long
        if self.isEnabledFor(TRACE):
            self._log(TRACE, message, args, **kwargs)


# Attach the method to the Logger class
logging.Logger.trace = CustomLoggerTrace.trace
