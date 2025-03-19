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
    if len(sys.argv) < 4:
        print(
            "Usage: python call_tracer.py <source_file> <entry_point> <search_path1> "
            "[<search_path2> ...]"
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
