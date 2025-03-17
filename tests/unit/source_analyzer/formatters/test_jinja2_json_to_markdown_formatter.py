import json
import sys
from formatters.formatter import FormatterFactory, FormatterObject


class TestUtilsDirectoryExists:

    def test_jinja2_json_to_markdown_formatter(self):
        formatter_config: dict = {
            "formatter": {
                "template": {
                    "name": "jinja2_json_to_markdown_formatter.jinja2",
                    "path": "formatters",
                }
            },
        }
        formatter_factory: FormatterFactory = FormatterFactory(
            config_dict=formatter_config
        )
        formatter_object: FormatterObject = formatter_factory.get_formatter(
            class_name="Jinja2JsonToMarkdownFormatter",
            module_name="jinja2_json_to_markdown_formatter",
        )

        with open("tests/test_jinja2_json_to_markdown_formatter.md") as md_file:
            expected_response = md_file.read()
        print(f"type(expected_response): {type(expected_response)}")
        print(f"len(expected_response): {len(expected_response)}")
        print("expected_response:")
        print(expected_response)
        with open(
            "tests/test_jinja2_json_to_markdown_formatter.json", "r"
        ) as json_file:
            data = json.load(json_file)

        variables = {"model_vendor": "Anthropic", "model_name": "Claude 3 Sonnet"}
        response = formatter_object.format_json(data=data, variables=variables)
        print(f"type(response): {type(response)}")
        print(f"len(response): {len(response)}")
        print("response:")
        print(response)

        assert response is not None
        assert response == expected_response
