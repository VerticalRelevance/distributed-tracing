import sys
import logging

# Define custom level
SUCCESS = 25

# Add the custom level
logging.addLevelName(SUCCESS, "SUCCESS")


# Create a custom logger with the new method
class CustomLoggerSuccess(logging.Logger):
    # print("custom logger success loaded", file=sys.stderr)

    def success(self, message, *args, **kwargs):
        if self.isEnabledFor(SUCCESS):
            self._log(SUCCESS, message, args, **kwargs)


# # Replace the default logger class
# logging.setLoggerClass(CustomLoggerSuccess)

# Attach the method to the Logger class
logging.Logger.success = CustomLoggerSuccess.success

# # Create a logger
# logger = logging.getLogger("root")

# # Configure handler
# handler = logging.StreamHandler(sys.stdout)
# # formatter = logging.Formatter("%(message)s")
# formatter = logging.Formatter("%(message)s")
# handler.setFormatter(formatter)
# logger.addHandler(handler)
