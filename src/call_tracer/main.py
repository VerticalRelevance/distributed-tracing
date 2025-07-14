# pylint: disable=line-too-long
"""
This module serves as the entry point for the call tracer tool.

It provides functionality to analyze Python source code files or directories containing Python files.
The module parses command line arguments to determine the target file or directory for analysis,
configures logging based on environment variables, and delegates the actual analysis to the
SourceCodeAnalyzer class.
"""
# pylint: enable=line-too-long

from itertools import chain
import sys
from typing import Dict, Any
from common.configuration import Configuration
from call_tracer.call_tracer_class import CallTracer

def main():
    # pylint: disable=line-too-long
    """
    Main function to run the call tracer.

    Args:
        source_file: Path to the source file to trace
        entry_point: Name of the entry point function to start tracing
        search_paths: List of paths to search for external modules
    """
    # pylint: enable: line-too-long

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

        print(f"Usage: python {script_name} FILE ENTRYPOINT SEARCH")
        print(
            f"Invalid argument(s): {",".join(chain.from_iterable(invalid_arg_values.values()))}"
            if invalid_args
            else "Trace calls starting at the specified entrypoint in the specified source file."
        )
        print(
            """
Arguments:
FILE          Path to an input source file
ENTRYPOINT    Name of a function or method within the source file
SEARCH        A list of paths to search for additional source files for imports
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
    TRACE:
        A custom level for the Loguru package that enables tracing of
        function entry and exit points.
    DEBUG:
        Standard functionality from the Loguru package.
    INFO:
        Standard functionality from the Loguru package. Additional
        progress messages are written to the stdout stream at this level.
    SUCCESS:
        A custom level for the Loguru package that enables normal
        output. This is the preferred level for the stdout stream.
    WARNING:
        Standard functionality from the Loguru package. Program
        warnings are logged to the stdout stream.
    ERROR:
        Standard functionality from the Loguru package. This is the
        preferred level for the stderr stream.
    CRITICAL:
        Standard functionality from the Loguru package.
"""
            )

    if len(sys.argv) < 4:
        usage(script_name=sys.argv[0] if len(sys.argv) > 0 else __name__)
        sys.exit(0)
    if len(sys.argv) > 4:
        usage(
            script_name=sys.argv[0] if len(sys.argv) > 0 else __name__,
            invalid_args=True,
            invalid_arg_values=sys.argv[4:] if len(sys.argv) > 4 else ["none"],
        )
        sys.exit(1)

    main_configuration = Configuration("call_tracer/config.yaml")

    source_file_arg = sys.argv[1]
    entry_point_arg = sys.argv[2]
    search_paths_arg = sys.argv[3:]

    tracer = CallTracer(
        configuration=main_configuration,
        source_file=source_file_arg,
        search_paths=search_paths_arg,
    )
    trace_data: Dict[str, Any] = tracer.trace(entry_point_arg)
    tracer.display_trace(data=trace_data)

if __name__ == "__main__":
    main()
