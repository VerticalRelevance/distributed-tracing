from formatters.formatter import FormatterObject
from configuration import Configuration


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

    def __init__(self, configuration: Configuration):
        """
        Initializes a new instance of the CodedJsonToMarkdownFormatter class.

        This method is called automatically when a new instance of the class is created.
        It initializes the instance with any necessary attributes or configurations.

        """
        super().__init__(configuration=configuration)

    # TODO rework kwargs
    def format_text(self, text_to_format: str, **kwargs):
        """
        Formats the given text using the CodedJsonToMarkdownFormatter.

        Args:
            text_to_format (str): The text to be formatted.

        Returns:
            None
        """
        self._logging_utils.debug(__class__, f"Formatting text: ")
        self._logging_utils.debug(__class__, text_to_format)
        extracted_json = self._json_utils.extract_code_blocks(text_to_format)
        self._logging_utils.debug(
            __class__, f"Extracted code blocks type: {type(extracted_json)}"
        )
        self._logging_utils.debug(
            __class__, f"Extracted code blocks len: {len(extracted_json)}"
        )
        self._logging_utils.debug(__class__, f"Extracted json:")
        self._logging_utils.debug(__class__, extracted_json[0], enable_pformat=True)
        dict_to_format = self._json_utils.json_loads(json_string=extracted_json[0])
        dict_to_format = (
            dict_to_format[0] if isinstance(dict_to_format, list) else dict_to_format
        )
        self._logging_utils.debug(__class__, f"Dict type: {type(dict_to_format)}")
        self._logging_utils.debug(__class__, f"Dict to format:")
        self._logging_utils.debug(__class__, dict_to_format, enable_pformat=True)
        self._logging_utils.debug(__class__, "Dict keys:")
        self._logging_utils.debug(__class__, dict_to_format.keys(), enable_pformat=True)

        output_strings = []
        output_strings.append("")
        output_strings.append(
            f"## {kwargs['model_vendor']} {kwargs['model_name']} Analysis",
        )
        output_strings.append(dict_to_format.get("overall_analysis_summary"))
        for priority in self._config.get_value("tracing_priorities"):
            output_strings.append("")
            output_strings.append(f"### {priority}")
            output_strings.append("")
            locations: list = dict_to_format.get(priority, [])
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

        for s in output_strings:
            self._logging_utils.success(__class__, s)
