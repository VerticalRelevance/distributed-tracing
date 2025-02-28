from typing import Dict
from formatters.formatter import FormatterObject


class CodedJsonToMarkdownFormatter(FormatterObject):

    _instance = None

    def __new__(cls, *args, **kwargs):  # pylint: disable=unused-argument
        """
        Creates and returns a new instance of the CodedJsonToMarkdownFormatter class.

        This method is responsible for implementing the singleton pattern, ensuring that only one
        instance of the Configuration class is created.

        Parameters:
            cls (type): The class object.
            *args: Variable length argument list.
            **kwargs: Arbitrary keyword arguments.

        Returns:
            FormatterObject: The singleton instance of the CodedJsonToMarkdownFormatter class.

        """
        if not cls._instance:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, config_dict: Dict[str, str]):
        """
        Initializes a new instance of the CodedJsonToMarkdownFormatter class.

        This method is called automatically when a new instance of the class is created.
        It initializes the instance with any necessary attributes or configurations.

        """
        super().__init__(config_dict=config_dict)
        # self._formatting_config = self._config.get_value("")

    def format_json(self, data: Dict[str, str], variables: Dict[str, str]) -> str:
        """
        Formats the given text using the CodedJsonToMarkdownFormatter.

        Args:
            text_to_format (str): The text to be formatted.

        Returns:
            None
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
        self._logging_utils.debug(
            __class__,
            f"type(self._config_dict('tracing_priorities')): {type(self._config_dict('tracing_priorities'))}",
        )
        for priority in self._config_dict.get("tracing_priorities"):
            output_strings.append("")
            output_strings.append(f"### {priority}")
            output_strings.append("")
            locations: list = priorities.get(priority, [])
            if len(locations) == 0:
                output_strings.append("No critical findings for this priority.")
                continue
            for location in locations:
                output_strings.append(f"#### Location {location.get('function_name')}")
                output_strings.append(
                    f"- **Specific code blocks/lines to trace:**\n```python\n{location.get('code_block')}\n```"
                )
                output_strings.append(
                    f"- **Rationale for tracing:** {location.get('rationale')}"
                )
                output_strings.append(
                    f"- **Recommended trace information to capture**\n{location.get('trace_info')}"
                )

        return "\n".join(output_strings)
