"""
Jinja2JsonToMarkdownFormatter module that provides functionality for formatting JSON data
into Markdown using Jinja2 templates. This module implements a singleton pattern for the formatter
and provides methods for loading templates and rendering JSON data to Markdown.
"""

from typing import Dict
from jinja2 import Environment
from formatters.formatter import FormatterObject
from configuration import Configuration


class Jinja2JsonToMarkdownFormatter(FormatterObject):
    """
    A formatter that converts JSON data to Markdown using Jinja2 templates.

    This class implements the singleton pattern to ensure only one instance exists.
    It provides methods for loading Jinja2 templates and formatting JSON data into
    structured Markdown documents based on those templates.

    Attributes:
        _instance (Jinja2JsonToMarkdownFormatter): The singleton instance of this class
    """

    _instance = None

    def __new__(cls, *args, **kwargs):  # pylint: disable=unused-argument
        """
        Creates and returns a new instance of the Jinja2JsonToMarkdownFormatter class.

        This method is responsible for implementing the singleton pattern, ensuring that only one
        instance of the Configuration class is created.

        Parameters:
            cls (type): The class object.
            *args: Variable length argument list.
            **kwargs: Arbitrary keyword arguments.

        Returns:
            FormatterFactory: The singleton instance of the Jinja2JsonToMarkdownFormatter class.

        """
        if not cls._instance:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, configuration: Configuration):
        """
        Initializes a new instance of the Jinja2JsonToMarkdownFormatter class.

        This method is called automatically when a new instance of the class is created.
        It initializes the instance with any necessary attributes or configurations.

        """
        super().__init__(configuration=configuration)

    def _load_template(self, template_path: str) -> str:
        """
        Load the Jinja2 template from the specified file path.

        Args:
            template_path (str): The path to the Jinja2 template file.

        Returns:
            str: The contents of the Jinja2 template file.
        """
        with open(template_path, "r", encoding="utf-8") as template_file:
            return template_file.read()

    def format_json(self, data: Dict[str, str], variables: Dict[str, str] = None):
        """
        Format the source code tree into a Markdown string using the Jinja2 template.

        Args:
            source_code_tree (SourceCodeNode): The root node of the source code tree.

        Returns:
            str: The formatted Markdown string.
        """
        # FUTURE refactor to use a shared utilities module
        # Get the template file name and path from the configuration
        file_name = self._config.value(
            "formatter.template.name",
            expected_type=str,
            default="template name not found",
        )
        file_path = self._config.value(
            "formatter.template.path",
            expected_type=str,
            default="template path not found",
        )
        template_path = (
            f"{file_path}/{file_name if file_name is not None else "notfound.jinja2"}"
        )
        self._logging_utils.debug(__class__, f"Template path: {template_path}")
        template_string = self._load_template(template_path=template_path)

        # Create the Jinja2 environment and template
        # FUTURE make jinja debug extension optional
        jinja2_env = Environment(
            extensions=["jinja2.ext.debug"],  # Enable the debug extension
        )
        template = jinja2_env.from_string(template_string)

        self._logging_utils.debug(__class__, "Formatting json data: ")
        self._logging_utils.debug(__class__, data, enable_pformat=True)
        self._logging_utils.debug(__class__, f"priorities: {data["priorities"]}")
        # Render the template with the data
        markdown_output = template.render(
            overall_analysis_summary=data["overall_analysis_summary"],
            priorities=data["priorities"],
            model_vendor=variables["model_vendor"],
            model_name=variables["model_name"],
            total_prompt_tokens=variables["total_prompt_tokens"],
            total_completion_tokens=variables["total_completion_tokens"],
            stopped_reason=variables["stopped_reason"],
            # FUTURE add the following variables
            # total_cost=variables["total_cost"],
            # total_time=variables["total_time"],
            # total_time_in_seconds=variables["total_time_in_seconds"],
            # total_time_in_milliseconds=variables["total_time_in_milliseconds"],
            # total_time_in_microseconds=variables["total_time_in_microseconds"],
            # total_time_in_nanoseconds=variables["total_time_in_nanoseconds"],
        )
        self._logging_utils.debug(__class__, f"Markdown output: {markdown_output}")

        return markdown_output
