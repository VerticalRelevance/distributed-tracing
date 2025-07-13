# pylint: disable=line-too-long
"""
A Python module for analyzing source code structure and identifying optimal locations for adding trace statements.
This module provides functionality to parse Python source files, build an AST-based tree representation,
and leverage AI-powered analysis for trace point recommendations.
"""
# pylint: enable=line-too-long

import time
from pathlib import Path
from pprint import pformat
from common.path_utils import PathUtils
from common.logging_utils import LoggingUtils
from common.configuration import Configuration
from common.generic_utils import (
    GenericUtils,
)
from source_analyzer.formatters.formatter import FormatterUtils
from source_analyzer.models import model
from source_analyzer.models.model import (
    EXCEPTION_LEVEL_ERROR,
    ModelException,
    ModelFactory,
    ModelObject,
    ModelMaxTokenLimitException,
    ModelUtils,
)
from source_analyzer.formatters.formatter import (
    FormatterObject,
    FormatterFactory,
)

class SourceCodeAnalyzer:
    # pylint: disable=line-too-long
    """
    A class for analyzing Python source code to identify optimal locations for trace statements.
    Uses AST parsing and AI-powered analysis to provide recommendations for code instrumentation.

    Attributes:
        _utils (Utilities): Utility functions instance
        _ast_utils (SourceCodeAnalyzerUtils): AST analysis utility functions
        _openai_client (openai.OpenAI): OpenAI API client
        _config (Configuration): Configuration settings
    """
    # pylint: enable=line-too-long

    def __init__(self):
        # pylint: disable=line-too-long
        """
        Initialize the SourceCodeAnalyzer with required dependencies.

        Sets up utility objects, configuration, model, and formatter needed for source code analysis.
        """
        # pylint: enable=line-too-long

        self._generic_utils: GenericUtils = GenericUtils()
        self._logger = LoggingUtils().get_class_logger(self.__class__.__name__)
        self._path_utils = PathUtils()
        self._config: Configuration = Configuration("source_analyzer/config.yaml")
        # FUTURE make config file name dynamic

        model_utils = ModelUtils(configuration=self._config)
        self._model: ModelObject = ModelFactory(configuration=self._config).get_model(
            module_name=model_utils.desired_model_module_name,
            class_name=model_utils.desired_model_class_name,
        )

        formatter_utils = FormatterUtils(configuration=self._config)
        self._formatter: FormatterObject = FormatterFactory(
            configuration=self._config
        ).get_formatter(
            module_name=formatter_utils.get_desired_formatter_module_name(),
            class_name=formatter_utils.get_desired_formatter_class_name(),
        )

        self._total_tokens: dict = {"completion": 0, "prompt": 0}

        self._logger.debug(f"Model: {self._model.model_id}")
        self._logger.debug("_config:")
        self._logger.debug(self._config, enable_pformat=True)
        self._logger.debug("Configuration:")
        self._logger.debug(pformat(str(self._config)))

    def get_completion_with_retry(self, prompt: str) -> None:
        # pylint: disable=line-too-long
        """
        Get an AI completion with automatic retry logic.

        Attempts to generate text from the AI model with the given prompt, implementing retry logic
        in case of failures. Tracks token usage and handles various error conditions.

        Args:
            prompt (str): The prompt to send to the AI model

        Raises:
            ModelException: If all retry attempts fail or if a token limit exception occurs
        """
        # pylint: enable=line-too-long
        self._logger.trace("start get_completion_with_retry")
        self._logger.debug(f"prompt:\n{prompt}")
        self._logger.debug(
            f"max_llm_tries: {self._model.max_llm_tries}, "
            f"retry_delay: {self._model.retry_delay}, "
            f"temperature: {self._model.temperature}",
        )

        self._total_tokens = {"completion": 0, "prompt": 0}
        # break_llm_loop = False
        for attempt in range(self._model.max_llm_tries):
            print(
                f"Get completion attempt: (attempt {attempt + 1}/{self._model.max_llm_tries})",  # pylint: disable=line-too-long
            )

            try:
                self._model.generate_text(prompt=prompt)
                break
            except ModelException as me:    # pylint: disable=broad-exception-caught
                self._logger.error(
                    f"Cannot generate text from model '{self._model.model_name}'."
                    f"Reason: {me}",
                )
                self._logger.debug(f"ModelException level: {me.level}")
                if me.level == EXCEPTION_LEVEL_ERROR:
                    self._logger.error(
                        "me level is EXCEPTION_LEVEL_ERROR"
                    )
                    raise me # pylint: disable=broad-exception-raised)

            if attempt < self._model.max_llm_tries - 1:
                print(f"Retrying in {self._model.retry_delay} seconds...",)
                time.sleep(self._model.retry_delay)

        print("LLM response received")
        self._logger.debug(
            f"LLM Prompt Tokens: {self._model.prompt_tokens}, "
            f"LLM Completion Tokens: {self._model.completion_tokens}, "
            f"Stopped Reason: {self._model.stopped_reason}",
        )

        self._logger.debug(
            f"total tokens after loop: {self._total_tokens}"
        )

        if self._model.stopped_reason in self._model.stop_max_tokens_reasons:
            raise ModelMaxTokenLimitException(
                max_token_limit=self._model.max_completion_tokens,
                prompt_tokens=self._model.prompt_tokens,
                completion_tokens=self._model.completion_tokens,
            )

        if self._model.stopped_reason not in self._model.stop_valid_reasons:
            self._logger.warning(
                f"Invalid stop reason '{self._model.stopped_reason}'",
            )
            raise ModelException(
                f"Invalid stop reason '{self._model.stopped_reason}'",
                model.EXCEPTION_LEVEL_ERROR,
            )

        # Update token counts
        self._total_tokens["prompt"] += self._model.prompt_tokens
        self._total_tokens["completion"] += self._model.completion_tokens

        tokens_output = pformat(
            {
                "total_prompt_tokens": self._total_tokens["prompt"],
                "total_completion_tokens": self._total_tokens["completion"],
            }
        )
        self._logger.debug("total tokens:")
        self._logger.debug(tokens_output)

        self._logger.trace("end get_completion_with_retry")

    def analyze_source_code_for_decision_points(
            self, source_code: str, function_name: str=None) -> None:
        # pylint: disable=line-too-long
        """
        Analyze source code to identify optimal locations for adding trace statements.

        Constructs a prompt with the source code and tracing priorities from configuration,
        then sends it to the AI model to identify critical locations for adding trace statements.

        Args:
            source_code (str): The source code to analyze
            focus_name (str):

        Returns:
            None
        """
        # pylint: enable=line-too-long
        self._logger.trace(
            "start analyze_source_code_for_decision_points"
        )

        tracing_priorities = self._config.list_value("tracing_priorities", [])
        clarifications = self._config.list_value("clarifications", [])
        embed_function_name = f"only the function or method named {function_name}" if function_name is not None else "all functions and methods"
        exclude_others = " Exclude all other functions and methods." if function_name is not None else ""
        found_text = f" within {function_name}" if function_name is not None else ""

        # FUTURE move prompt to config
        prompt = f"""
Analyze the following Python source code and identify critical locations for adding trace statements.
Within the source code, analyze {embed_function_name}.{exclude_others}
Categorize critical locations based on the following priorities.

Priorities:
{', '.join(tracing_priorities)}

{'\n'.join(clarifications)}

For each critical location found{found_text}, include the following details:
1. Name of the location function/method.
2. Fully-qualified name of the containing function/method.
3. Specific code blocks/lines to trace. Include the function/method name and parent class name.
4. Rationale for tracing.
5. Recommended trace information to capture.

Format the output as a JSON array with the following keys:
- "overall_analysis_summary": A summary of the source code analysis. In the summary describe only the {function_name}.
- "priorities": for each priority, list the following:
    - "priority": the priority
    - "critical_locations": a list of critical locations found for this priority.
        - for each critical location found for this priority, include the following keys:
            - "location_name": Name of the location function/method
            - "function_name": Fully-qualified name of the function/method
            - "code_block": Specific code block/line to trace
            - "rationale": Rationale for tracing
            - "trace_info": Recommended trace information to capture

Source Code:
```python
{source_code}
```
"""

        print("Analyzing code")
        self.get_completion_with_retry(
            prompt=prompt,
        )
        print("Code analysis complete")

        for priority in self._model.completion_json.get("priorities"):
            self._logger.debug(f"priority: {priority}")
            for location in priority.get("critical_locations", priority.get(priority.get("locations"))):
                self._logger.debug(f"location: {location}")
                if location.get("function_name") == function_name:
                    self._logger.debug("function_name matches")
                    location["include"] = True
                else:
                    location["include"] = False

        self._logger.debug("completion json:")
        self._logger.debug(self._model.completion_json, enable_pformat=False)
        self._logger.trace(
            "end analyze_source_code_for_decision_points"
        )

    def generate_formatted_output(self) -> str:
        # pylint: disable=line-too-long
        """
        Generate formatted output based on the model's completion data.

        Uses the configured formatter to convert the model's JSON completion data into a formatted string,
        including metadata about the model and token usage.

        Returns:
            str: The formatted output string containing analysis results
        """
        # pylint: enable=line-too-long
        self._logger.trace("start generate_formatted_output")
        self._logger.debug("completion_json:")
        self._logger.debug(
            self._model.completion_json, enable_pformat=True)

        formatter_inputs = {}
        formatter_inputs["model_vendor"] = self._model.model_vendor
        formatter_inputs["model_name"] = self._model.model_name
        formatter_inputs["total_prompt_tokens"] = self._total_tokens["prompt"]
        formatter_inputs["total_completion_tokens"] = self._total_tokens["completion"]
        formatter_inputs["stopped_reason"] = self._model.stopped_reason

        formatted_output = self._formatter.format_json(
            data=self._model.completion_json, variables=formatter_inputs
        )

        self._logger.debug("end generate_formatted_output")
        return formatted_output

    # pylint: disable=inconsistent-return-statements
    def process_file(
        self, input_source_path: str, function_name: str=None, display_results: bool=False,
    ) -> str | None:
        # pylint: disable=line-too-long
        """
        Process a single Python source file for trace point analysis.

        Loads the source file, analyzes it for trace points, and formats the results.
        Can either display results to console or return them as a string.

        Args:
            input_source_path (str): Path to the Python source file to analyze
            display_results (bool, optional): Whether to display results to console. Defaults to False.

        Returns:
            str | None: Formatted analysis results as a string if display_results is False, None otherwise.
                        Returns error message string if processing fails.
        """
        # pylint: enable=line-too-long
        self._logger.trace("start process_file")
        self._logger.debug(f"input_source_path: {input_source_path}")

        # Load the source file
        try:
            full_code = self._path_utils.get_ascii_file_contents(
                source_path=input_source_path
            )
            self._logger.debug(f"full_code len: {len(full_code)}")
            if len(full_code) == 0:
                self._logger.warning("Source file is empty")
                return

            results = []
            results.append(f"# Source File: {Path(input_source_path).name}")
            results.append(f"Full file path: '{input_source_path}'")
            results.append("")
        except Exception as e:  # pylint: disable=broad-exception-caught
            e_msg = f"Failed to load source file '{input_source_path}': {str(e)}"
            self._logger.error(e_msg, exc_info=True)

            self._logger.trace("end process_file (file error)")
            return f"# {e_msg}" if display_results else e_msg

        # Analyze the code
        try:
            self.analyze_source_code_for_decision_points(full_code, function_name=function_name)
        except Exception as e:  # pylint: disable=broad-exception-caught
            e_msg = f"Failed to analyze source code: {str(e)}"
            self._logger.error(e_msg, exc_info=True)
            self._logger.trace("end process_file (analyzer error)")
            return f"# {e_msg}" if display_results else e_msg

        print("Analysis complete")

        # Format the output
        try:
            formatted_output = self.generate_formatted_output()
        except Exception as e:  # pylint: disable=broad-exception-caught
            self._logger.error(f"Failed to format output: {str(e)}", exc_info=True)
            self._logger.trace("end process_file (formatter error)")
            e_msg = f"Failed to Failed to format results: {str(e)}"
            return f"# {e_msg}" if display_results else e_msg

        self._logger.debug(formatted_output)
        results.append(formatted_output)

        results_str = "\n".join(results)

        # Write the formatted output to the console or return them to the caller
        if display_results:
            self._logger.success(results_str)
            self._logger.trace("end process_file display results")
            return

        self._logger.trace("end process_file return results")
        return results_str
        # pylint: enable=inconsistent-return-statements

    def process_directory(self, source_path: str) -> None:
        # pylint: disable=line-too-long
        """
        Process all Python files in a directory and its subdirectories.

        Recursively walks through the directory structure, identifying Python files and processing
        each one for trace point analysis.

        Args:
            source_path (str): Path to the directory to process

        Returns:
            None
        """
        # pylint: enable=line-too-long
        self._logger.trace("start process_directory")
        self._logger.debug(f"source_path: {source_path}")
        print(f"Process directory '{source_path}'")

        if not Path(source_path).exists():
            self._logger.error(
                f"Source path '{source_path}' does not exist"
            )
            self._logger.trace(
                "end process_directory path does not exist"
            )
            return
        if not Path(source_path).is_dir():
            self._logger.error(
                f"Source path '{source_path}' is not a directory"
            )
            self._logger.trace(
                "end process_directory path is not a directory"
            )
            return

        for root, dirs, files in Path(source_path).walk():
            self._logger.debug(f"root: {root}")
            self._logger.debug(f"dirs: {dirs}")
            self._logger.debug(f"files: {files}", enable_pformat=True)
            for file in files:
                self._logger.debug(f"file: {file}")
                if Path(file).suffix == ".py":
                    self._logger.debug("Path(file)")
                    self._logger.debug(Path(file))
                    source_path = f"{root}/{file}"
                    self.process_file(source_path, display_results=True)

        self._logger.trace("end process_directory")
