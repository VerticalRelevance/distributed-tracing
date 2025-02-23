from collections import deque
from formatters.formatter import FormatterObject
from configuration import Configuration


class IterativeMarkdownFormatter(FormatterObject):
    _instance = None

    def __new__(cls, *args, **kwargs):  # pylint: disable=unused-argument
        """
        Creates and returns a new instance of the IterativeMarkdownFormatter class.

        This method is responsible for implementing the singleton pattern, ensuring that only one
        instance of the Configuration class is created.

        Parameters:
            cls (type): The class object.
            *args: Variable length argument list.
            **kwargs: Arbitrary keyword arguments.

        Returns:
            FormatterFactory: The singleton instance of the IterativeMarkdownFormatter class.

        if not cls._instance:
        """
        cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, configuration: Configuration):
        """
        Initializes a new instance of the JsonToMarkdownFormatter class.

        This method is called automatically when a new instance of the class is created.
        It initializes the instance with any necessary attributes or configurations.

        """
        super().__init__(configuration=configuration)
        self._formatting_config = self._config.get_value("")

    # TODO rework kwargs
    def format_text(self, text_to_format: str, **kwargs):
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

        markdown_parts = []

        # Initialize the stack with the root node
        # Stack items are tuples: (data, indent_level, is_list_item, parent_key)
        stack = deque([(data, 0, False, None)])

        while stack:
            current_data, indent_level, is_list_item, parent_key = stack.pop()
            indent = " " * (
                self.config["formatting"].get("indent_size", 2) * indent_level
            )
            bullet = self.config["formatting"].get("bullet_style", "-")

            if isinstance(current_data, dict):
                # Process dictionary items in reverse order to maintain original order when using stack
                items = list(current_data.items())
                for key, value in reversed(items):
                    if isinstance(value, (dict, list)):
                        # Add the nested structure to the stack
                        stack.append((value, indent_level + 1, False, key))
                        # Add the key as a header
                        formatted_key = self._apply_style(
                            key, self.config["styles"].get("keys", {})
                        )
                        markdown_parts.append(f"{indent}{bullet} {formatted_key}:\n")
                    else:
                        # Process primitive value
                        formatted_key = self._apply_style(
                            key, self.config["styles"].get("keys", {})
                        )
                        formatted_value = self._format_value(value)
                        markdown_parts.append(
                            f"{indent}{bullet} {formatted_key}: {formatted_value}\n"
                        )

            elif isinstance(current_data, list):
                # Process list items in reverse order
                for item in reversed(current_data):
                    if isinstance(item, (dict, list)):
                        stack.append((item, indent_level, True, None))
                    else:
                        formatted_value = self._format_value(item)
                        markdown_parts.append(f"{indent}{bullet} {formatted_value}\n")

            elif is_list_item:
                # Handle primitive list item
                formatted_value = self._format_value(current_data)
                markdown_parts.append(f"{indent}{bullet} {formatted_value}\n")

            elif parent_key is not None:
                # Handle primitive value with key
                formatted_key = self._apply_style(
                    parent_key, self.config["styles"].get("keys", {})
                )
                formatted_value = self._format_value(current_data)
                markdown_parts.append(
                    f"{indent}{bullet} {formatted_key}: {formatted_value}\n"
                )

        return "".join(markdown_parts)

    def _format_value(self, value):
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

    def _apply_style(self, text, style):
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
