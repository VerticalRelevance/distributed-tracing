# pylint: disable=line-too-long
"""
A Python module for analyzing source code structure and identifying optimal locations for adding trace statements.
This module provides functionality to parse Python source files, build an AST-based tree representation,
and leverage AI-powered analysis for trace point recommendations.
"""
# pylint: enable=line-too-long

# TODO separate main from SourceCodeTracer class

import time
from pathlib import Path
import logging
from pprint import pformat
from common.configuration import Configuration
from common.utilities import (
    LoggingUtils,
    ModelUtils,
    PathUtils,
    GenericUtils,
    FormatterUtils,
)
from source_analyzer.models import model
from source_analyzer.models.model import (
    EXCEPTION_LEVEL_ERROR,
    ModelException,
    ModelFactory,
    ModelObject,
    ModelMaxTokenLimitException,
)
from source_analyzer.formatters.formatter import (
    FormatterError,
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
        """
        Initialize the SourceCodeAnalyzer with required dependencies.
        """
        self._generic_utils: GenericUtils = GenericUtils()
        self._logging_utils = LoggingUtils()
        self._path_utils = PathUtils()
        # FUTURE make config file name dynamic
        self._config: Configuration = Configuration("source_analyzer/config.yaml")

        model_utils = ModelUtils(configuration=self._config)
        self._model: ModelObject = ModelFactory(configuration=self._config).get_model(
            module_name=model_utils.get_desired_model_module_name(),
            class_name=model_utils.get_desired_model_class_name(),
        )

        formatter_utils = FormatterUtils(configuration=self._config)
        self._formatter: FormatterObject = FormatterFactory(
            configuration=self._config
        ).get_formatter(
            module_name=formatter_utils.get_desired_formatter_module_name(),
            class_name=formatter_utils.get_desired_formatter_class_name(),
        )

        self._total_tokens: dict = {"completion": 0, "prompt": 0}

        self._logging_utils.debug(__class__.__name__, f"Model: {self._model.model_id}")
        self._logging_utils.debug(__class__.__name__, f"_config: {pformat(self._config)}")
        self._logging_utils.info(__class__.__name__, "Configuration:")
        self._logging_utils.info(__class__.__name__, pformat(str(self._config)))

    def get_completion_with_retry(self, prompt: str) -> None:
        # pylint: disable=line-too-long
        """
        Get an AI completion with automatic retry logic.

        Args:
            prompt (str): The prompt to send to the AI model

        Raises:
            Exception: If all retry attempts fail or if a token limit exception occurs
        """
        # pylint: enable=line-too-long
        self._logging_utils.trace(__class__.__name__, "start get_completion_with_retry")
        self._logging_utils.debug(__class__.__name__, f"prompt:\n{prompt}")
        self._logging_utils.debug(
            __class__,
            f"max_llm_tries: {self._model.max_llm_tries}, "
            f"retry_delay: {self._model.retry_delay}, "
            f"temperature: {self._model.temperature}",
        )

        self._total_tokens = {"completion": 0, "prompt": 0}
        # break_llm_loop = False
        for attempt in range(self._model.max_llm_tries):
            self._logging_utils.debug_info(
                __class__,
                f"Get completion attempt: (attempt {attempt + 1}/{self._model.max_llm_tries})",  # pylint: disable=line-too-long
            )

            try:
                self._model.generate_text(prompt=prompt)
                break
            except ModelException as me:
                self._logging_utils.error(
                    __class__,
                    f"Cannot generate text from model '{self._model.model_name}'."
                    f"Reason: {me}",
                )
                if me.level == EXCEPTION_LEVEL_ERROR:
                    raise Exception from me
                # if self._model.stopped_reason not in [self._model.stop_valid_reasons, self._model.stop_max_tokens_reasons]:
                #     raise Exception from me  # pylint: disable=broad-exception-raised
                # if attempt >= self._model.max_llm_tries - 1:
                #     raise Exception from me  # pylint: disable=broad-exception-raised

            if attempt < self._model.max_llm_tries - 1:
                self._logging_utils.debug_info(
                    __class__,
                    f"Retrying in {self._model.retry_delay} seconds...",
                )
                time.sleep(self._model.retry_delay)
            # else:
            #     self._logging_utils.debug(
            #         __class__, "setting break_llm_loop to True"
            #     )
            #     break_llm_loop = True

        self._logging_utils.info(__class__.__name__, "LLM response received")
        self._logging_utils.debug(
            __class__,
            f"LLM Prompt Tokens: {self._model.prompt_tokens}, "
            f"LLM Completion Tokens: {self._model.completion_tokens}, "
            f"Stopped Reason: {self._model.stopped_reason}",
        )

        # CLEANUP
        # self._logging_utils.debug(__class__.__name__, "break_llm_loop is True")
        self._logging_utils.debug(
            __class__, f"total tokens after loop: {self._total_tokens}"
        )

        if self._model.stopped_reason in self._model.stop_max_tokens_reasons:
            raise ModelMaxTokenLimitException(
                max_token_limit=self._model.max_completion_tokens,
                prompt_tokens=self._model.prompt_tokens,
                completion_tokens=self._model.completion_tokens,
            )

        if self._model.stopped_reason not in self._model.stop_valid_reasons:
            self._logging_utils.warning(
                __class__,
                f"Invalid stop reason '{self._model.stopped_reason}'",
            )
            raise ModelException(
                f"Invalid stop reason '{self._model.stopped_reason}'",
                model.EXCEPTION_LEVEL_ERROR,
            )

            # except ModelMaxTokenLimitException as mmtle:
            #     raise Exception from mmtle  # pylint: disable=broad-exception-raised)
            # except ModelException as me:  # pylint: disable=broad-exception-raised
            #     self._logging_utils.error(
            #         __class__,
            #         f"Cannot generate text from model '{self._model.model_name}'."
            #         f"Reason: {me}",
            #     )
            #     sys.exit(1)
            # except Exception as e:  # pylint: disable=broad-exception-caught
            #     self._logging_utils.error(__class__.__name__, f"LLM call failed: {str(e)}")
            #     if attempt < self._model.max_llm_tries - 1:
            #         self._logging_utils.info(
            #             __class__,
            #             f"Retrying again in {self._model.retry_delay} seconds...",
            #         )
            #         time.sleep(self._model.retry_delay)
            #     else:
            #         self._logging_utils.error(
            #             __class__, "Max retries reached again. Giving up."
            #         )
            #         self._logging_utils.debug(
            #             __class__, f"end get_completion_with_retry with exception: {e}"
            #         )
            #         # CLEANUP
            #         # raise e
            #         raise ModelMaxTokenLimitException(
            #             max_token_limit=self._model.max_completion_tokens,
            #             prompt_tokens=self._model.prompt_tokens,
            #             completion_tokens=self._model.completion_tokens,
            #         ) from e

        # Update token counts
        self._total_tokens["prompt"] += self._model.prompt_tokens
        self._total_tokens["completion"] += self._model.completion_tokens

        tokens_output = pformat(
            {
                "total_prompt_tokens": self._total_tokens["prompt"],
                "total_completion_tokens": self._total_tokens["completion"],
            }
        )
        if self._logging_utils.is_stderr_logger_level(__class__.__name__, logging.DEBUG):
            self._logging_utils.debug(__class__.__name__, "total tokens:")
            self._logging_utils.debug(__class__.__name__, tokens_output)

        self._logging_utils.trace(__class__.__name__, "end get_completion_with_retry")

    def analyze_source_code_for_decision_points(self, source_code) -> None:
        """
        Analyze source code to identify optimal locations for adding trace statements.

        Args:
            source_code (str): The source code to analyze

        Returns:
            None
        """
        self._logging_utils.trace(
            __class__, "start analyze_source_code_for_decision_points"
        )

        tracing_priorities = self._config.list_value("tracing_priorities", [])
        clarifications = self._config.list_value("clarifications", [])

        # TODO move prompt to config
        prompt = f"""
Analyze the following Python source code and identify critical locations for adding trace statements.
Include every critical locations found. Categorize critical locations based on the following priorities.

Priorities:
{', '.join(tracing_priorities)}

{'\n'.join(clarifications)}

For every critical location found, include the following details:
1. Name of the location function/method.
2. Fully-qualified name of the containing function/method.
3. Specific code blocks/lines to trace. Include the function/method name and parent class.
4. Rationale for tracing
5. Recommended trace information to capture

Format the output as a JSON array with the following keys:
- "overall_analysis_summary": A summary of the source code analysis
- "priorities": for each priority, list the following:
    - the priority
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

        self._logging_utils.info(__class__.__name__, "Analyzing code")
        self.get_completion_with_retry(
            prompt=prompt,
        )
        self._logging_utils.info(__class__.__name__, "Code analysis complete")

        self._logging_utils.trace(
            __class__, "end analyze_source_code_for_decision_points"
        )

    def generate_formatted_output(self, model: ModelObject) -> str:
        # pylint: disable=line-too-long
        """
        Generate formatted output based on the provided model.

        Args:
            model (ModelObject): The model containing completion data to be formatted

        Returns:
            str: The formatted output string
        """
        # pylint: enable=line-too-long
        self._logging_utils.trace(__class__.__name__, "start generate_formatted_output")
        self._logging_utils.debug(__class__.__name__, "completion_json:")
        self._logging_utils.debug(__class__.__name__, model.completion_json, enable_pformat=True)

        formatter_inputs = {}
        formatter_inputs["model_vendor"] = model.model_vendor
        formatter_inputs["model_name"] = model.model_name
        formatter_inputs["total_prompt_tokens"] = self._total_tokens["prompt"]
        formatter_inputs["total_completion_tokens"] = self._total_tokens["completion"]
        formatter_inputs["stopped_reason"] = self._model.stopped_reason

        formatted_output = self._formatter.format_json(
            data=model.completion_json, variables=formatter_inputs
        )

        self._logging_utils.debug(__class__.__name__, "end generate_formatted_output")
        return formatted_output

    def process_file(
        self, input_source_path: str, display_results: bool = False
    ) -> str | None:
        """
        Process a single Python source file.

        Args:
            input_source_path (str): Path to the Python source file

        Returns:
            bool: True if processing succeeded, None otherwise
        """
        self._logging_utils.trace(__class__.__name__, "start process_file")
        self._logging_utils.debug(__class__.__name__, f"input_source_path: {input_source_path}")

        # Load the source file
        try:
            full_code = self._path_utils.get_ascii_file_contents(
                source_path=input_source_path
            )
            self._logging_utils.debug(__class__.__name__, f"full_code len: {len(full_code)}")
            if len(full_code) == 0:
                self._logging_utils.warning(__class__.__name__, "Source file is empty")
                return

            results = []
            results.append(f"# Source File: {Path(input_source_path).name}")
            results.append(f"Full file path: '{input_source_path}'")
            results.append("")
            # self._logging_utils.success(
            #     __class__, f"\n# Source File: {Path(input_source_path).name}"
            # )
            # self._logging_utils.success(
            #     __class__, f"Full file path: '{input_source_path}'"
            # )
        except Exception as e:  # pylint: disable=broad-exception-caught
            e_msg = f"Failed to load source file '{input_source_path}': {str(e)}"
            self._logging_utils.error(__class__.__name__, e_msg, exc_info=True)

            self._logging_utils.trace(__class__.__name__, "end process_file (file error)")
            return f"# {e_msg}" if display_results else e_msg

        # Analyze the code
        try:
            self.analyze_source_code_for_decision_points(full_code)
        except Exception as e:  # pylint: disable=broad-exception-caught
            e_msg = f"Failed to analyze source code: {str(e)}"
            self._logging_utils.error(__class__.__name__, e_msg, exc_info=True)
            self._logging_utils.trace(__class__.__name__, "end process_file (analyzer error)")
            return f"# {e_msg}" if display_results else e_msg

        self._logging_utils.info(__class__.__name__, "Analysis complete")

        # Format the output
        try:
            formatted_output = self.generate_formatted_output(model=self._model)
        except Exception as e:  # pylint: disable=broad-exception-caught
            self._logging_utils.error(
                __class__, f"Failed to format output: {str(e)}", exc_info=True
            )
            self._logging_utils.trace(__class__.__name__, "end process_file (formatter error)")
            raise FormatterError("Failed to format output") from e  # type: ignore

        self._logging_utils.debug(__class__.__name__, formatted_output)
        results.append(formatted_output)

        results_str = "\n".join(results)

        # Write the formatted output to the console or return them to the caller
        if display_results:
            self._logging_utils.success(__class__.__name__, results_str)
            self._logging_utils.trace(__class__.__name__, "end process_file display results")
            return

        self._logging_utils.trace(__class__.__name__, "end process_file return results")
        return results_str

    def process_directory(self, source_path: str) -> None:
        """
        Process all Python files in a directory and its subdirectories.

        Args:
            source_path (str): Path to the directory to process

        Returns:
            None
        """
        self._logging_utils.trace(__class__.__name__, "start process_directory")
        self._logging_utils.debug(__class__.__name__, f"source_path: {source_path}")
        self._logging_utils.info(__class__.__name__, f"Process directory '{source_path}'")

        if not Path(source_path).exists():
            self._logging_utils.error(
                __class__, f"Source path '{source_path}' does not exist"
            )
            self._logging_utils.trace(
                __class__, "end process_directory path does not exist"
            )
            return
        if not Path(source_path).is_dir():
            self._logging_utils.error(
                __class__, f"Source path '{source_path}' is not a directory"
            )
            self._logging_utils.trace(
                __class__, "end process_directory path is not a directory"
            )
            return

        for root, dirs, files in Path(source_path).walk():
            self._logging_utils.debug(__class__.__name__, f"root: {root}")
            self._logging_utils.debug(__class__.__name__, f"dirs: {dirs}")
            self._logging_utils.debug(__class__.__name__, f"files: {files}", enable_pformat=True)
            for file in files:
                self._logging_utils.debug(__class__.__name__, f"file: {file}")
                if Path(file).suffix == ".py":
                    self._logging_utils.debug(__class__.__name__, "Path(file)")
                    self._logging_utils.debug(__class__.__name__, Path(file))
                    source_path = f"{root}/{file}"
                    self.process_file(source_path, display_results=True)

        self._logging_utils.trace(__class__.__name__, "end process_directory")

