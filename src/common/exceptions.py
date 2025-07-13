"""
Custom exception module for environment variable handling.

This module provides a custom exception class for handling cases where
required environment variables are missing from the system environment.
The exception provides clear error messaging and maintains the name of
the missing variable for debugging purposes.

Classes:
    MissingEnvVarException: Exception raised when a required environment
                           variable is not found in the system environment.
"""

class MissingEnvVarException(Exception):
    # pylint: disable=line-too-long
    """
    Custom exception for missing required environment variable.

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
