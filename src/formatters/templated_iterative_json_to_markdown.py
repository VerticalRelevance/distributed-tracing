from collections import deque
from string import Template
from typing import Any, Dict, List
from configuration import Configuration
from formatter import FormatterObject


class TemplatedIterativeMarkdownFormatter(FormatterObject):
    _instance = None

    def __new__(cls, *args, **kwargs):  # pylint: disable=unused-argument
        """
        Creates and returns a new instance of the TemplatedIterativeMarkdownFormatter class.

        This method is responsible for implementing the singleton pattern, ensuring that only one
        instance of the Configuration class is created.

        Parameters:
            cls (type): The class object.
            *args: Variable length argument list.
            **kwargs: Arbitrary keyword arguments.

        Returns:
            FormatterFactory: The singleton instance of the TemplatedIterativeMarkdownFormatter class.

        if not cls._instance:
        """
        cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, configuration: Configuration):
        """
        Initializes a new instance of the TemplatedIterativeMarkdownFormatter class.

        This method is called automatically when a new instance of the class is created.
        It initializes the instance with any necessary attributes or configurations.

        """
        super().__init__(configuration=configuration)
        self._formatting_config = self._config.get_value("")

    def _interpolate_variables(self, text: str, variables: Dict[str, str]) -> str:
        """Replace template variables in text with provided values"""
        if not text or not variables:
            return text
        return Template(text).safe_substitute(variables)

    def _get_value_by_path(self, data: Dict, path: str) -> Any:
        """Get a value from nested dictionary using dot notation path"""
        try:
            for key in path.split("."):
                if key.isdigit():
                    data = data[int(key)]
                else:
                    data = data[key]
            return data
        except (KeyError, IndexError, TypeError):
            return None

    def _format_tree_iterative(
        self,
        data: Any,
        initial_indent: int = 0,
        bullet: str = "-",
        variables: Dict[str, str] = None,
    ) -> str:
        """Format nested data as a tree structure using iteration"""
        if not data:
            return ""

        result = []
        # Stack items: (data, indent_level, is_key, key_name)
        stack = deque([(data, initial_indent, False, None)])

        while stack:
            current_data, indent_level, is_key, key_name = stack.pop()
            indent = " " * (2 * indent_level)

            if isinstance(current_data, dict):
                # Add items to stack in reverse order to maintain original order
                items = list(current_data.items())
                for key, value in reversed(items):
                    if isinstance(value, (dict, list)):
                        key_style = self.config["styles"].get("keys", {})
                        formatted_key = self._apply_style(key, key_style)
                        result.append(f"{indent}{bullet} {formatted_key}:\n")
                        stack.append((value, indent_level + 1, False, None))
                    else:
                        stack.append((value, indent_level, True, key))

            elif isinstance(current_data, list):
                # Add items to stack in reverse order
                for item in reversed(current_data):
                    stack.append((item, indent_level, False, None))

            else:
                # Handle primitive values
                if is_key:
                    key_style = self.config["styles"].get("keys", {})
                    formatted_key = self._apply_style(key_name, key_style)
                    formatted_value = self._format_value(current_data)
                    if isinstance(current_data, str) and variables:
                        formatted_value = self._interpolate_variables(
                            formatted_value, variables
                        )
                    result.append(
                        f"{indent}{bullet} {formatted_key}: {formatted_value}\n"
                    )
                else:
                    formatted_value = self._format_value(current_data)
                    if isinstance(current_data, str) and variables:
                        formatted_value = self._interpolate_variables(
                            formatted_value, variables
                        )
                    result.append(f"{indent}{bullet} {formatted_value}\n")

        return "".join(result)

    def _format_section(
        self, section_config: Dict, data: Dict, variables: Dict[str, str]
    ) -> str:
        """Format a single section based on its configuration"""
        section_type = section_config.get("type", "default")
        content = []

        if section_type == "header":
            level = section_config.get("level", 1)
            if "title" in section_config:
                title = self._interpolate_variables(section_config["title"], variables)
            elif "data_path" in section_config:
                title = str(self._get_value_by_path(data, section_config["data_path"]))
            else:
                title = ""
            content.append(f"{'#' * level} {title}\n")

        elif section_type == "paragraph":
            if "text" in section_config:
                text = self._interpolate_variables(section_config["text"], variables)
                content.append(f"{text}\n")
            if "data_path" in section_config:
                value = self._get_value_by_path(data, section_config["data_path"])
                if value:
                    content.append(f"{value}\n")

        elif section_type == "list":
            if "items" in section_config:
                bullet = section_config.get("bullet", "-")
                items = section_config["items"]
                for item in items:
                    interpolated_item = self._interpolate_variables(item, variables)
                    content.append(f"{bullet} {interpolated_item}\n")
            elif "data_path" in section_config:
                list_data = self._get_value_by_path(data, section_config["data_path"])
                if isinstance(list_data, list):
                    bullet = section_config.get("bullet", "-")
                    for item in list_data:
                        content.append(f"{bullet} {self._format_value(item)}\n")

        elif section_type == "tree":
            data_path = section_config.get("data_path")
            if data_path:
                tree_data = self._get_value_by_path(data, data_path)
                if tree_data:
                    content.append(
                        self._format_tree_iterative(
                            tree_data,
                            initial_indent=section_config.get("indent_level", 0),
                            bullet=section_config.get("bullet", "-"),
                            variables=variables,
                        )
                    )

        elif section_type == "table":
            if "data" in section_config:
                table_data = [
                    {
                        k: self._interpolate_variables(str(v), variables)
                        for k, v in row.items()
                    }
                    for row in section_config["data"]
                ]
                content.extend(self._format_table(table_data, section_config))
            elif "data_path" in section_config:
                table_data = self._get_value_by_path(data, section_config["data_path"])
                if isinstance(table_data, list) and table_data:
                    content.extend(self._format_table(table_data, section_config))

        if "separator" in section_config:
            content.append(f"\n{section_config['separator']}\n")

        return "\n".join(content)

    def _format_table(self, data: List[Dict], config: Dict) -> List[str]:
        """Format data as a markdown table"""
        if not data:
            return []

        columns = config.get("columns", list(data[0].keys()))
        headers = config.get("headers", columns)

        table = ["| " + " | ".join(headers) + " |"]
        alignments = config.get("alignments", ["left"] * len(columns))
        align_row = []
        for align in alignments:
            if align == "center":
                align_row.append(":---:")
            elif align == "right":
                align_row.append("---:")
            else:
                align_row.append(":---")
        table.append("| " + " | ".join(align_row) + " |")

        for row in data:
            values = []
            for col in columns:
                value = row.get(col, "")
                values.append(str(value))
            table.append("| " + " | ".join(values) + " |")

        return table

    def _format_value(self, value: Any) -> str:
        """Format value based on its type and configuration"""
        value_style = self.config["styles"].get("values", {})

        if isinstance(value, bool):
            style = value_style.get("boolean", {})
            value_str = str(value).lower()
        elif isinstance(value, (int, float)):
            style = value_style.get("number", {})
            value_str = str(value)
        elif isinstance(value, str):
            style = value_style.get("string", {})
            value_str = value
        elif value is None:
            style = value_style.get("null", {})
            value_str = "null"
        else:
            style = {}
            value_str = str(value)

        return self._apply_style(value_str, style)

    def _apply_style(self, text: str, style: Dict) -> str:
        """Apply formatting based on style configuration"""
        if not style:
            return text

        if style.get("bold"):
            text = f"**{text}**"
        if style.get("italic"):
            text = f"_{text}_"
        if style.get("code"):
            text = f"`{text}`"

        return text

    def format_text(self, text_to_format: str, variables: Dict[str, str] = None) -> str:
        self._logging_utils.debug(__class__, f"Formatting text: ")
        self._logging_utils.debug(__class__, text_to_format)

        extracted_json = self._json_utils.extract_json(text_to_format)
        self._logging_utils.debug(
            __class__, f"Extracted code blocks type: {type(extracted_json)}"
        )
        self._logging_utils.debug(
            __class__, f"Extracted code blocks len: {len(extracted_json)}"
        )
        self._logging_utils.debug(__class__, f"Extracted json:")
        self._logging_utils.debug(__class__, extracted_json[0], enable_pformat=True)

        data = self._json_utils.json_loads(json_string=extracted_json[0])
        data = data[0] if isinstance(data, list) else data
        self._logging_utils.debug(__class__, f"Dict type: {type(data)}")
        self._logging_utils.debug(__class__, f"Dict to format:")
        self._logging_utils.debug(__class__, data, enable_pformat=True)
        self._logging_utils.debug(__class__, "Dict keys:")
        self._logging_utils.debug(__class__, data.keys(), enable_pformat=True)

        variables = variables or {}
        markdown_parts = []

        for section in self.config["sections"]:
            section_content = self._format_section(section, data, variables)
            if section_content:
                markdown_parts.append(section_content)

        return "\n".join(markdown_parts)
