"""
CodedJsonToMarkdownFormatter module that provides functionality for formatting JSON analysis data
into structured Markdown reports. This module implements a singleton pattern for the formatter
and provides methods for transforming JSON data into readable Markdown documentation.
"""

from typing import Dict
from formatters.formatter import FormatterObject
from configuration import Configuration


class CodedJsonToMarkdownFormatter(
    FormatterObject
):  # pylint: disable=too-few-public-methods
    """A formatter class that converts coded JSON analysis data into structured Markdown reports.

    This class extends FormatterObject to provide specialized formatting capabilities for
    transforming JSON-formatted analysis data into readable Markdown documentation.

    Attributes:
        _config (Configuration): Configuration settings for the formatter.
        _logging_utils (LoggingUtils): Utility for debug logging operations.

    Methods:
        __init__(configuration): Initializes the formatter with configuration settings.
        format_json(data, variables): Converts JSON analysis data into a Markdown report.

    Example:
        Create and use the formatter:
            >>> config = Configuration()
            >>> formatter = CodedJsonToMarkdownFormatter(config)
            >>> markdown = formatter.format_json(analysis_data, model_variables)

    Input JSON Structure:
        The input JSON should contain:
        - overall_analysis_summary
        - priorities (list of priority levels)
        - critical_locations (per priority)
        - code blocks and recommendations

    Output Format:
        The generated Markdown includes:
        - Model information header
        - Analysis summary
        - Priority-based findings
        - Code block analysis
        - Token usage statistics

    Notes:
        The formatter requires proper configuration of tracing priorities and expects specific JSON
        structure for analysis data. It handles missing data gracefully and provides detailed debug
        logging.
    """

    def __init__(self, configuration: Configuration):
        """
        Initializes the CodedJsonToMarkdownFormatter with the given configuration.

        Sets up the formatter by calling the parent class's initialization method
        with the provided configuration object. This ensures that the formatter
        is properly configured with the necessary settings for processing.

        Args:
            configuration (Configuration): The configuration object containing
                settings and parameters for the formatter.
        """
        super().__init__(configuration=configuration)

    def format_json(
        self, data: Dict[str, str], variables: Dict[str, str] = None
    ) -> str:
        """
        Transforms JSON-formatted analysis data into a structured Markdown report.

        This method takes analysis data and variables as input, and generates
        a comprehensive Markdown-formatted report. The report includes:
        - A header with model vendor and name
        - Overall analysis summary
        - Detailed findings for each tracing priority
        - Critical locations with specific code blocks, rationales, and trace recommendations
        - Summary of token usage and stop reason

        Args:
            data (Dict[str, str]): A dictionary containing analysis data,
                including priorities, critical locations, and summaries.
            variables (Dict[str, str], optional): A dictionary of additional
                variables such as model details, token counts, and stop reason.
                Defaults to None.

        Returns:
            str: A markdown-formatted report of the analysis results.

        Note:
            - Requires 'tracing_priorities' to be configured in the configuration.
            - Logs debug information using the internal logging utility.
            - Handles cases where no critical findings exist for a priority.
        """
        output_strings = []
        output_strings.append("")
        output_strings.append(
            f"## {variables['model_vendor']} {variables['model_name']} Analysis",
        )
        output_strings.append(data.get("overall_analysis_summary"))

        priorities: dict = data.get("priorities", {})
        self._logging_utils.debug(
            __class__, f"type(data.get('priorities'): {type(priorities)}"
        )
        self._logging_utils.debug(
            __name__, f"priorities: {priorities}", enable_pformat=True
        )
        tracing_priorities: list = self._config.list_value("tracing_priorities", [])
        self._logging_utils.debug(
            __class__,
            f"type(self._config('tracing_priorities')): {type(tracing_priorities)}",
        )
        for tracing_priority in tracing_priorities:
            self._logging_utils.debug(
                __class__, f"type(tracing_priority): {type(tracing_priority)}"
            )
            self._logging_utils.debug(
                __class__, f"tracing_priority: {tracing_priority}"
            )
            output_strings.append("")
            output_strings.append(f"### {tracing_priority}")
            output_strings.append("")
            locations = [
                element
                for element in priorities
                if element["priority"] == tracing_priority
            ][0].get("critical_locations")
            self._logging_utils.debug(__class__, f"locations: {locations}")
            self._logging_utils.debug(__class__, f"len(locations): {len(locations)}")
            if len(locations) == 0:
                output_strings.append("No critical findings for this priority.")
                continue
            for location in locations:
                self._logging_utils.debug(__class__, f"location: {location}")
                output_strings.append(f"#### Location {location.get('function_name')}")
                output_strings.append(
                    f"- **Specific code blocks/lines to trace:**\n```python\n{location.get('code_block')}\n```"  # pylint: disable=line-too-long
                )
                output_strings.append(
                    f"- **Rationale for tracing:** {location.get('rationale')}"
                )
                output_strings.append(
                    f"- **Recommended trace information to capture**\n{location.get('trace_info')}"
                )

        output_strings.append("")
        output_strings.append("## Summary")
        output_strings.append(
            f"* Total prompt tokens: {variables['total_prompt_tokens']}"
        )
        output_strings.append(
            f"* Total completion tokens: {variables['total_completion_tokens']}"
        )
        output_strings.append(f"* Stop reason: {variables['stop_reason']}")

        return "\n".join(output_strings)
