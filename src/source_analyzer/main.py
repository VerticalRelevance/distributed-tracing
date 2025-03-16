import sys
import os
from pathlib import Path
from common.utilities import (
    LoggingUtils,
    PathUtils,
    GenericUtils,
)
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

    logging_utils: LoggingUtils = LoggingUtils()
    path_utils: PathUtils = PathUtils()
    generic_utils = GenericUtils()

    def usage(script_name: str = "", invalid_args: bool = False, **invalid_arg_values):
        print(f"Usage: python {script_name} [FILE|DIRECTORY]")
        print(
            f"Invalid argument(s): {invalid_arg_values}"
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
    LOG_LEVEL_STDERR:
        Sets the level of the logger writing to the file defined by LOG_FILE_STDERR.
        Preferred values are TRACE, DEBUG, ERROR, or CRITICAL. All valid level
        values are listed below. Default is DEBUG.
    LOG_LEVEL_STDOUT:
        Sets the level of the logger writing to STDOUT. Preferred values are
        TRACE, DEBUG, ERROR, or CRITICAL. All valid level values are listed
        below. Default is SUCCESS.
    LOG_FILE_STDERR:
        Set the name of the file to be written by the STDERR logger.

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

    logging_utils.info(__name__, "Starting...")

    use_assistant = generic_utils.is_truthy(os.getenv("USE_ASSISTANT", "false"))
    logging_utils.info(
        __name__,
        f"Using OpenAI with {'code interpreter' if use_assistant else 'no'} assistant",
    )

    # Initialize the SourceCodeAnalyzerUtils with the configuration
    analyzer: SourceCodeAnalyzer = SourceCodeAnalyzer()

    # Analyze the source code
    source_path = sys.argv[1]
    logging_utils.debug(__name__, f"source_path: {source_path}")

    if path_utils.is_file(source_path):
        logging_utils.debug(__name__, "Path(source_path)")
        logging_utils.debug(__name__, Path(source_path))
        try:
            analyzer.process_file(source_path, display_results=True)
        except Exception as e:  # pylint: disable=broad-exception-caught
            logging_utils.error(__name__, f"Failed to process file: {str(e)}")
            logging_utils.trace(__name__, "end __main__ (file error)")
    else:
        if path_utils.is_dir(source_path):
            try:
                analyzer.process_directory(source_path)
            except Exception as e:  # pylint: disable=broad-exception-caught
                logging_utils.error(__name__, f"Failed to process file: {str(e)}")
                logging_utils.trace(__name__, "end __main__ (file error)")
        else:
            logging_utils.error(
                __name__,
                f"Source path '{source_path}' is neither a file nor a directory",
            )

    logging_utils.debug(__name__, "end __main__")


if __name__ == "__main__":
    main()
