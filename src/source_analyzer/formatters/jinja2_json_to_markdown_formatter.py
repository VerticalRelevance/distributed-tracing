# pylint: disable=line-too-long
"""
Jinja2JsonToMarkdownFormatter module that provides functionality for formatting JSON data into Markdown using
Jinja2 templates.

This module implements a formatter class that converts JSON data to Markdown format using Jinja2 templating
engine. It provides methods for loading templates and rendering JSON data to structured Markdown documents.
The formatter supports additional variables for template rendering and includes comprehensive logging for
debugging purposes.
"""
# pylint: enable=line-too-long

from typing import Dict
from jinja2 import Environment
from source_analyzer.formatters.formatter import FormatterObject
from common.configuration import Configuration


class Jinja2JsonToMarkdownFormatter(
    FormatterObject
):  # pylint: disable=too-few-public-methods
    # pylint: disable=line-too-long
    """
    A formatter that converts JSON data to Markdown using Jinja2 templates.

    This class extends FormatterObject to provide specialized functionality for converting JSON data into
    Markdown format using Jinja2 templates. It loads templates from configurable file paths and renders
    JSON data with additional variables to produce structured Markdown output. The class includes support
    for debug extensions and comprehensive logging throughout the formatting process.

    Attributes:
        _config (Configuration): Configuration object containing template settings
        _logger: Logger instance for debugging and information output
    """
    # pylint: enable=line-too-long

    def __init__(self, configuration: Configuration):
        # pylint: disable=line-too-long
        """
        Initialize a new instance of the Jinja2JsonToMarkdownFormatter class.

        This method initializes the formatter with the provided configuration object, which contains
        settings for template paths and other formatting parameters. The configuration is passed to
        the parent FormatterObject class for proper initialization.

        Args:
            configuration (Configuration): The configuration object containing formatter settings
                including template name, path, and other formatting parameters
        """
        # pylint: enable=line-too-long
        super().__init__(configuration=configuration)

    def _load_template(self, template_path: str) -> str:
        # pylint: disable=line-too-long
        """
        Load the Jinja2 template from the specified file path.

        This private method reads a Jinja2 template file from the filesystem and returns its contents
        as a string. The template is loaded with UTF-8 encoding to ensure proper handling of special
        characters.

        Args:
            template_path (str): The full file path to the Jinja2 template file to load

        Returns:
            str: The complete contents of the Jinja2 template file as a string

        Raises:
            FileNotFoundError: If the specified template file does not exist
            IOError: If there are issues reading the template file
            UnicodeDecodeError: If the file cannot be decoded as UTF-8
        """
        # pylint: enable=line-too-long

        with open(template_path, "r", encoding="utf-8") as template_file:
            return template_file.read()

    def format_json(self, data: Dict[str, str], variables: Dict[str, str] = None):
        # pylint: disable=line-too-long
        """
        Format JSON data into a Markdown string using the Jinja2 template.

        This method takes JSON data and optional variables, loads the appropriate Jinja2 template
        from the configured path, and renders the template with the provided data to generate
        a formatted Markdown string. The method supports various template variables including
        analysis summaries, priorities, and model information.

        Args:
            data (Dict[str, str]): The JSON data to format, expected to contain keys like
                'overall_analysis_summary' and 'priorities'
            variables (Dict[str, str], optional): Additional variables to include in template
                rendering such as 'model_vendor', 'model_name', 'total_prompt_tokens',
                'total_completion_tokens', and 'stopped_reason'. Defaults to None.

        Returns:
            str: The formatted Markdown string generated from the template and data

        Raises:
            KeyError: If required keys are missing from the data or variables dictionaries
            FileNotFoundError: If the template file cannot be found
            TemplateError: If there are issues with the Jinja2 template rendering
        """
        # pylint: enable=line-too-long

        # FUTURE refactor to use a shared utilities module
        # Get the template file name and path from the configuration
        file_name = self._config.str_value(
            "formatter.template.name",
            "template name not found",
        )
        file_path = self._config.str_value(
            "formatter.template.path",
            "template path not found",
        )
        template_path = (
            f"{file_path}/{file_name if file_name is not None else "notfound.jinja2"}"
        )
        self._logger.debug(f"Template path: {template_path}")
        template_string = self._load_template(template_path=template_path)

        # Create the Jinja2 environment and template
        # FUTURE make jinja debug extension optional
        jinja2_env = Environment(
            extensions=["jinja2.ext.debug"],  # Enable the debug extension
        )
        template = jinja2_env.from_string(template_string)

        self._logger.debug("Formatting json data: ")
        self._logger.debug(data, enable_pformat=True)
        self._logger.debug(f"priorities: {data["priorities"]}")
        # Render the template with the data
        markdown_output = template.render(
            overall_analysis_summary=data["overall_analysis_summary"],
            priorities=data["priorities"],
            model_vendor=variables["model_vendor"],
            model_name=variables["model_name"],
            total_prompt_tokens=variables["total_prompt_tokens"],
            total_completion_tokens=variables["total_completion_tokens"],
            stopped_reason=variables["stopped_reason"],
        )
        self._logger.debug(f"Markdown output: {markdown_output}")

        return markdown_output
