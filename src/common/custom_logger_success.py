# pylint: disable=line-too-long
"""
Custom Logging Module with Success Level

This module extends Python's standard logging module by introducing a custom 'SUCCESS' log level and a
corresponding logging method. It provides a logging level between INFO and WARNING for more granular logging.

Key Features:
    - Adds a custom SUCCESS log level (value 25)
    - Extends logging.Logger with a success() method
    - Provides a dedicated level for logging successful operations
"""
# pylint: enable=line-too-long

import logging

# Define custom level
SUCCESS = 25

# Add the custom level
logging.addLevelName(SUCCESS, "SUCCESS")


class CustomLoggerSuccess(logging.Logger):
    # pylint: disable=line-too-long
    """
    A custom Logger class that extends the standard logging.Logger with a success() method.

    This class adds the capability to log messages at the SUCCESS level (25), which sits between
    the standard INFO (20) and WARNING (30) levels in severity.

    Attributes:
        Inherits all attributes from the standard logging.Logger class.
    """
    # pylint: enable=line-too-long

    def success(self, message, *args, **kwargs):
        # pylint: disable=line-too-long
        """
        Log a message with severity 'SUCCESS' on this logger.

        This method logs messages at the custom SUCCESS level (25), which is more significant than
        INFO but less severe than WARNING.

        Args:
            message (str): The message to be logged.
            *args: Variable positional arguments passed to the underlying logger.
            **kwargs: Variable keyword arguments passed to the underlying logger.

        Example:
            >>> logger = logging.getLogger(__name__)
            >>> logger.success("Operation completed successfully")
        """
        # pylint: enable=line-too-long
        if self.isEnabledFor(SUCCESS):
            self._log(SUCCESS, message, args, **kwargs)


# Attach the method to the Logger class
logging.Logger.success = CustomLoggerSuccess.success
