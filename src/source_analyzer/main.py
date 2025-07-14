# pylint: disable=line-too-long
"""
This module serves as the entry point for the source code analyzer tool.

It provides functionality to analyze Python source code files or directories containing Python files.
The module parses command line arguments to determine the target file or directory for analysis,
configures logging based on environment variables, and delegates the actual analysis to the
SourceCodeAnalyzer class.
"""
# pylint: enable=line-too-long

import sys
import os
from itertools import chain
from pathlib import Path
from common.path_utils import PathUtils
from common.logging_utils import LoggingUtils
from common.generic_utils import GenericUtils
from source_analyzer.source_analyzer_class import SourceCodeAnalyzer

def main():
    # pylint: disable=line-too-long
    """
    Main entry point for the source code analyzer.
    Processes either a single Python file or a directory of Python files based on command line arguments.

    Usage:
        python script.py source_directory_path|source_file_path

    Returns:
        None
    """
    # pylint: enable=line-too-long

    main_logger: LoggingUtils = LoggingUtils().get_class_logger(class_name=__name__)
    path_utils: PathUtils = PathUtils()
    generic_utils = GenericUtils()

    def usage(script_name: str = "", invalid_args: bool = False, **invalid_arg_values):
        # pylint: disable=line-too-long
        """
        Display usage information for the script.

        Args:
            script_name (str, optional): The name of the script being executed. Defaults to an empty string.
            invalid_args (bool, optional): Flag indicating whether invalid arguments were provided. Defaults to False.
            **invalid_arg_values: Dictionary containing invalid argument values to display in the error message.

        Returns:
            None
        """
        # pylint: enable=line-too-long

        print(f"Usage: python {script_name} [FILE|DIRECTORY]")
        print(
            f"Invalid argument(s): {",".join(chain.from_iterable(invalid_arg_values.values()))}"
            if invalid_args
            else "Analyze the source code in the specified file or directory."
        )
        print(
            """
Arguments:
FILE          Path to an input file
DIRECTORY     Path to an input directory
            """
        )
        if not invalid_args:
            print(
                """
Environment variables:
    LOG_LEVEL:
        Sets the level of the logger writing to the file defined by LOG_FILE.
        Preferred values are TRACE, DEBUG, ERROR, or CRITICAL. All valid level
        values are listed below. Default is DEBUG.
    LOG_FILE_STDERR:
        Set the name of the file to be written by the logger.

Log Levels:
    NOTSET:
        Standard functionality from the Python logging package.
    TRACE:
        A custom level for the Python logging package that enables tracing of
        function entry and exit points.
    DEBUG:
        Standard functionality from the Python logging package.
    INFO:
        Standard functionality from the Python logging package. Additional
        progress messages are written to the stdout stream at this level.
    SUCCESS:
        A custom level for the Python logging package that enables normal
        output. This is the preferred level for the stdout stream.
    WARNING:
        Standard functionality from the Python logging package. Program
        warnings are logged to the stdout stream.
    ERROR:
        Standard functionality from the Python logging package. This is the
        preferred level for the stderr stream.
    CRITICAL:
        Standard functionality from the Python logging package.
"""
            )

    # Check if file path is provided
    if len(sys.argv) < 2:
        usage(script_name=sys.argv[0] if len(sys.argv) > 0 else __name__)
        sys.exit(0)
    if len(sys.argv) > 2:
        usage(
            script_name=sys.argv[0] if len(sys.argv) > 0 else __name__,
            invalid_args=True,
            invalid_arg_values=sys.argv[2:] if len(sys.argv) > 2 else ["none"],
        )
        sys.exit(1)

    print("Starting...")

    use_assistant = generic_utils.is_truthy(os.getenv("USE_ASSISTANT", "false"))
    print(f"Using GenAI with {'code interpreter' if use_assistant else 'no'} assistant")

    # Initialize the SourceCodeAnalyzerUtils with the configuration
    analyzer: SourceCodeAnalyzer = SourceCodeAnalyzer()

    # Analyze the source code
    source_path = sys.argv[1]
    main_logger.debug(f"source_path: {source_path}")

    if path_utils.is_file(source_path):
        main_logger.debug("Path(source_path)")
        main_logger.debug(Path(source_path))
        try:
            analyzer.process_file(source_path, display_results=True)
        except Exception as e:  # pylint: disable=broad-exception-caught
            main_logger.error(f"Failed to process file: {str(e)}")
            main_logger.trace("end __main__ (file error)")
    else:
        if path_utils.is_dir(source_path):
            try:
                analyzer.process_directory(source_path)
            except Exception as e:  # pylint: disable=broad-exception-caught
                main_logger.error(f"Failed to process file: {str(e)}")
                main_logger.trace("end __main__ (file error)")
        else:
            main_logger.error(
                __name__,
                f"Source path '{source_path}' is neither a file nor a directory",
            )

    main_logger.trace("end __main__")


if __name__ == "__main__":
    main()
