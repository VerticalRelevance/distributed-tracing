import sys
import os
from pathlib import Path
import time
import ast
import re
import json
import logging
import openai
from pprint import pformat

class Utils:
    # Class attributes
    stdout_logger = None
    stderr_logger = None

    @staticmethod
    def setup_stdout_logger(name: str, logger_level: int = logging.INFO) ->  None:
        Utils.stdout_logger = logging.getLogger(f"{name}.stdout")
        if not Utils.stdout_logger:
            # Configure the stdout logger
            Utils.stdout_logger = logging.getLogger(f"{name}.stdout")
            Utils.stdout_logger.setLevel(logger_level)

            console_handler = logging.StreamHandler(stream=sys.stdout)
            console_handler.setLevel(logger_level)

            formatter = logging.Formatter("%(message)s")
            console_handler.setFormatter(formatter)

            Utils.stdout_logger.addHandler(console_handler)

    @staticmethod
    def setup_stderr_logger(name: str, logger_level: int = logging.ERROR) -> None:
        Utils.stderr_logger = logging.getLogger(f"{name}.stderr")
        if not Utils.stderr_logger.handlers:
            # Configure the stderr logger
            Utils.stderr_logger = logging.getLogger(f"{name}.stderr")
            Utils.stderr_logger.setLevel(logger_level)

            console_handler = logging.StreamHandler(stream=sys.stderr)
            console_handler.setLevel(logger_level)

            formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
            console_handler.setFormatter(formatter)

            Utils.stderr_logger.addHandler(console_handler)

    @staticmethod
    def setup_loggers(name: str, logger_stdout_level: int = logging.INFO, logger_stderr_level: int = logging.ERROR) -> None:
        Utils.setup_stdout_logger(name, logger_stdout_level)
        Utils.setup_stderr_logger(name, logger_stderr_level)

    @staticmethod
    def get_source_code(source_path: str) -> str:
        Utils.stderr_logger.debug("start get_source_code")
        with open(source_path, "r", encoding="utf-8") as file:
            source_code = file.read()

        Utils.stderr_logger.debug("end get_source_code")
        return source_code


    @staticmethod
    def create_dependency_graph(graph_items):
        Utils.stderr_logger.debug("start create_dependency_graph")
        graph = {item_name: set() for item_name in graph_items}
        for item_name, item_code in graph_items.items():
            for other_item in graph_items:
                if other_item in item_code and other_item != item_name:
                    graph[item_name].add(other_item)

        Utils.stderr_logger.debug("end create_dependency_graph")
        return graph


    @staticmethod
    def topological_sort(graph):
        Utils.stderr_logger.debug("start topological_sort")
        visited = set()
        stack = []

        def dfs(node):
            visited.add(node)
            for neighbor in graph[node]:
                if neighbor not in visited:
                    dfs(neighbor)
            stack.append(node)

        for node in graph:
            if node not in visited:
                dfs(node)

        Utils.stderr_logger.debug("end topological_sort")
        return stack

    @staticmethod
    def extract_imports(code):
        Utils.stderr_logger.debug("start extract_imports")
        Utils.stdout_logger.info("Extracting imports from code")
        tree = ast.parse(code)
        imports = {}
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports[alias.name] = alias.asname or alias.name
            elif isinstance(node, ast.ImportFrom):
                module = node.module
                for alias in node.names:
                    imports[alias.name] = f"{module}.{alias.name}"
        Utils.stdout_logger.info(f"Extracted {len(imports)} imports: {', '.join(imports.keys())}")

        Utils.stderr_logger.debug("end extract_imports")
        return imports

    @staticmethod
    def extract_functions(code):
        Utils.stderr_logger.debug("start extract_functions")
        Utils.stdout_logger.info("Extracting functions from code")
        tree = ast.parse(code)
        functions = {}
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                func_code = ast.get_source_segment(code, node)
                functions[node.name] = func_code
        Utils.stdout_logger.info(f"Extracted {len(functions)} functions: {', '.join(functions.keys())}")

        Utils.stderr_logger.debug("end extract_functions")
        return functions


    @staticmethod
    def extract_code_blocks(response):
        """Extract all code blocks from the response."""
        Utils.stderr_logger.debug("start extract_code_blocks")
        Utils.stderr_logger.debug("end extract_code_blocks")
        return re.findall(r'```python\s*(.*?)\s*```', response, re.DOTALL)


    @staticmethod
    def extract_function(code_block, function_name):
        """Extract a specific function from a code block."""
        Utils.stderr_logger.debug("start extract_function")
        try:
            tree = ast.parse(code_block)
        except:
            Utils.stderr_logger.error(f"Failed to parse code block for function: {function_name} from\n{code_block}")
            return None
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name == function_name:
                return ast.get_source_segment(code_block, node)

        Utils.stderr_logger.debug("end extract_function")
        return None

    @staticmethod
    def get_dependency_graph_str(graph, root=None, prefix="", is_last=True):
        Utils.stderr_logger.debug("start get_dependency_graph_str")
        result = []

        if root is None:
            # Collect all roots if no specific root is given
            roots = [node for node in graph if not any(node in children for children in graph.values())]
            for i, root in enumerate(roots):
                result.append(Utils.get_dependency_graph_str(graph, root, "", i == len(roots) - 1))
            return "\n".join(result)

        connector = "└── " if is_last else "├── "
        result.append(prefix + connector + root)

        if root in graph:
            children = sorted(graph[root])
            new_prefix = prefix + ("    " if is_last else "│   ")
            for i, child in enumerate(children):
                is_last_child = (i == len(children) - 1)
                result.append(Utils.get_dependency_graph_str(graph, child, new_prefix, is_last_child))

        Utils.stderr_logger.debug("end get_dependency_graph_str")
        return "\n".join(result)


    @staticmethod
    def extract_functions_from_code(node, parent=None):
        """ Recursively extract functions and set parents. """
        Utils.stderr_logger.debug("start extract_functions_from_code")
        if isinstance(node, ast.Module):
            for n in node.body:
                Utils.extract_functions_from_code(n, parent=node)
        elif isinstance(node, ast.FunctionDef):
            node.parent = parent
            if parent is not None and isinstance(parent, (ast.FunctionDef, ast.Module)):
                parent.children.append(node)
            for n in node.body:
                Utils.extract_functions_from_code(n, parent=node)

        Utils.stderr_logger.debug("end extract_functions_from_code")

    @staticmethod
    def split_nested_functions(code):
        Utils.stderr_logger.debug("start split_nested_functions")
        tree = ast.parse(code)
        for node in ast.walk(tree):
            node.children = []
        Utils.extract_functions_from_code(tree)

        flat_functions = []

        def flatten_functions(node):
            if isinstance(node, ast.FunctionDef):
                flat_functions.append(node)
                # Remove nested function definitions from the body
                node.body = [n for n in node.body if not isinstance(n, ast.FunctionDef)]
            for child in node.children:
                flatten_functions(child)

        flatten_functions(tree)

        # Function to correct indentation for function docstrings
        def correct_indentation(functions):
            for func in functions:
                # Get existing docstring if present
                docstring = ast.get_docstring(func)
                if docstring:
                    # Replace existing docstring node with corrected indentation
                    corrected_docstring = "\n".join([line if line.strip() != "" else "" for line in docstring.split("\n")])
                    func.body[0].value.s = corrected_docstring

        correct_indentation(flat_functions)

        Utils.stderr_logger.debug("end split_nested_functions")
        return '\n\n'.join(ast.unparse(f).strip() for f in flat_functions)

    @staticmethod
    def get_dependency_graph_str(graph, root=None, prefix="", is_last=True):
        Utils.stderr_logger.debug("start get_dependency_graph_str")

        result = []

        if root is None:
            # Collect all roots if no specific root is given
            roots = [node for node in graph if not any(node in children for children in graph.values())]
            for i, root in enumerate(roots):
                result.append(Utils.get_dependency_graph_str(graph, root, "", i == len(roots) - 1))
            Utils.stderr_logger.debug("end get_dependency_graph_str root is None")
            return "\n".join(result)

        connector = "└── " if is_last else "├── "
        result.append(prefix + connector + root)

        if root in graph:
            children = sorted(graph[root])
            new_prefix = prefix + ("    " if is_last else "│   ")
            for i, child in enumerate(children):
                is_last_child = (i == len(children) - 1)
                result.append(Utils.get_dependency_graph_str(graph, child, new_prefix, is_last_child))

        Utils.stderr_logger.debug("end get_dependency_graph_str")
        return "\n".join(result)


class SourceLocationTraceAnalyzer:
    # Class attributes
    MODEL = "gpt-4o-mini"

    # MAX_VLLM_RETRIES = 10  # maximum number of retries for the VLLM call
    MAX_VLLM_RETRIES = 3  # maximum number of retries for the VLLM call
    RETRY_DELAY = 0  # seconds
    REPEAT_CONVERT_HIERARCHICAL_NUM = 1  # seems unimportant    MODEL = "gpt-4o-mini"
    # TEMPERATURE = 0.8  # 0.8 better than 1.0 better than 0.2
    TEMPERATURE = 0.0

    TOTAL_PROMPT_TOKENS = 0
    TOTAL_COMPLETION_TOKENS = 0
    TOTAL_CONVERT_HIERARCHICAL_CALLS = 0

    client = openai.OpenAI()

    # Class methods
    @staticmethod
    def get_file_extension(file_path):
        _, ext = os.path.splitext(file_path)
        return ext.lower()

    @staticmethod
    def what_language(file_type: str) -> str:
        file_type_language_mapping = {".py": "python 3", ".js": "node"}
        return file_type_language_mapping.get(file_type, None)

    @staticmethod
    def load_language_search_config(language: str) -> dict:
        file_path = "".join(language.split()) + "-search-config2.json"
        with open(file_path, "r", encoding="utf-8") as file:
            config_data = json.load(file)

        return config_data

    @staticmethod
    def format_search_instructions(language_config: dict):
        Utils.stderr_logger.debug("start format_search_instructions")
        formatted_search_instructions = []

        prompt_override = language_config.get("prompt_override", [])
        if len(prompt_override) > 0:
            formatted_search_instructions = prompt_override[:]
        else:
            prompt_clarifications = language_config.get("prompt_clarifications", [])
            if len(prompt_clarifications) > 0:
                formatted_search_instructions.append("\n".join(prompt_clarifications))
            prompt_locators = language_config.get("prompt_locators")
            for locator in prompt_locators:
                statements = ",".join(locator.get("statements"))
                rank = locator.get("rank")
                category = locator.get("category")
                line1 = f"Locate lines containing one of the following values: {statements}."
                # line1 += "\n".join(prompt_clarifications)
                line2 = f"Give each line a level value of {rank} and a category of '{category}'."
                formatted_search_instructions.append(line1)
                formatted_search_instructions.append(line2)

        Utils.stderr_logger.debug("formatted_search_instructions:")
        Utils.stderr_logger.debug(formatted_search_instructions)

        Utils.stderr_logger.debug("end format_search_instructions")
        return "\n".join(formatted_search_instructions)

    @staticmethod
    def get_source_language(source_path: str) -> str:
        source_file_type = SourceLocationTraceAnalyzer.get_file_extension(source_path)
        source_language = SourceLocationTraceAnalyzer.what_language(source_file_type)
        if not source_language:
            logging.warning(f"File type '{source_file_type}' is not yet supported.")
            return None

        return source_language

    @staticmethod
    def get_completion_with_retry(messages, model, max_vllm_retries):
        Utils.stderr_logger.debug("start get_completion_with_retry")

        for attempt in range(max_vllm_retries):
            Utils.stderr_logger.debug(f"Get completion attempt:  (attempt {attempt + 1}/{max_vllm_retries})")
            try:
                Utils.stdout_logger.info(f"Attempting LLM call (attempt {attempt + 1}/{max_vllm_retries})")
                Utils.stdout_logger.info(f"Input messages: {messages[-1]['content']}")
                chat_completion = SourceLocationTraceAnalyzer.client.chat.completions.create(
                    messages=messages,
                    model=model,
                    temperature=SourceLocationTraceAnalyzer.TEMPERATURE,
                )
                response = chat_completion.choices[0].message.content
                Utils.stdout_logger.info(f"LLM response: {response}")
                Utils.stdout_logger.info("LLM call received")

                # Update token counts
                SourceLocationTraceAnalyzer.TOTAL_PROMPT_TOKENS += chat_completion.usage.prompt_tokens
                SourceLocationTraceAnalyzer.TOTAL_COMPLETION_TOKENS += chat_completion.usage.completion_tokens

                Utils.stderr_logger.debug("end get_completion_with_retry")
                return response
            except Exception as e:
                Utils.stderr_logger.error(f"LLM call failed: {str(e)}")
                if attempt < max_vllm_retries - 1:
                    Utils.stdout_logger.info(f"Retrying in {SourceLocationTraceAnalyzer.RETRY_DELAY} seconds...")
                    time.sleep(SourceLocationTraceAnalyzer.RETRY_DELAY)
                else:
                    Utils.stderr_logger.error("Max retries reached. Giving up.")
                    Utils.stderr_logger.debug(f"end get_completion_with_retry raise Exception: {e}")
                    raise

    @staticmethod
    def run(input_source_path: str):
        Utils.stderr_logger.debug("start run")
        Utils.stderr_logger.debug(f"input_source_path: {input_source_path}")

        input_source_language = SourceLocationTraceAnalyzer.get_source_language(
            input_source_path
        )
        search_config = SourceLocationTraceAnalyzer.load_language_search_config(
            language=input_source_language
        )
        search_instructions = SourceLocationTraceAnalyzer.format_search_instructions(
            language_config=search_config
        )

        Utils.stderr_logger.debug("search_instructions:")
        Utils.stderr_logger.debug(search_instructions)

        # llm_model = "gpt-3.5-turbo-0125"

        system_content = """\
You are an AI assistant specialized in analyzing Python functions and identifying critical decision points.

The user is automation, so no additional explanation, summaries, or markdown formatting is required.
"""
        # messages = [
        #     {'role': 'system', 'content': system_content},
        #     {'role': 'user', 'content': search_instructions},
        # ]

    @staticmethod
    def convert_to_hierarchical(code, include_example=False):
        Utils.stderr_logger.debug("start convert_to_hierarchical")

        SourceLocationTraceAnalyzer.TOTAL_CONVERT_HIERARCHICAL_CALLS += 1

        Utils.stdout_logger.info("Converting code to hierarchical structure")

        example = """
        ### Example of tree-style hierarchical structure:
        
        ```python
        def main_function(input):
            preprocessed_data = preprocess(input)
            result = process(preprocessed_data)
            return result

        def preprocess(data):
            cleaned_data = clean_data(data)
            normalized_data = normalize_data(cleaned_data)
            return normalized_data

        def clean_data(data):
            # Implementation of data cleaning
            pass

        def normalize_data(data):
            # Implementation of data normalization
            pass

        def process(data):
            feature_vector = extract_features(data)
            result = classify(feature_vector)
            return result

        def extract_features(data):
            # Implementation of feature extraction
            pass

        def classify(feature_vector):
            # Implementation of classification
            pass
        ```
        """ if include_example else ""

        prompt = f"""
        Convert the following Python code into a tree-style hierarchical structure with multiple levels of sub-functions.
        Each significant step or logical block should be its own function, and functions can call other sub-functions.
        Ensure that the main function calls these sub-functions in the correct order, creating a tree-like structure.

        ### Original Code:
        {code}

        {example}

        ### Instructions:
        Please first analyze the codes step by step, and then provide the converted code in a Python code block (```python ... ```). When providing the final converted code, make sure to include all the functions in a flattened format, where each function is defined separately.
        """

        messages = [
            {'role': 'system', 'content': 'You are an AI assistant specialized in refactoring Python code into a tree-style hierarchical structure.'},
            {'role': 'user', 'content': prompt},
        ]

        if "starcoder2" in SourceLocationTraceAnalyzer.MODEL.lower():
            
            # remove the system message
            messages = messages[1:]

        best_conversion = None
        max_subfunctions = 0

        for _ in range(SourceLocationTraceAnalyzer.REPEAT_CONVERT_HIERARCHICAL_NUM):
            Utils.stderr_logger.debug(f"Attempt {_ + 1} of {SourceLocationTraceAnalyzer.REPEAT_CONVERT_HIERARCHICAL_NUM} for converting code to tree-style hierarchical structure")
            response = SourceLocationTraceAnalyzer.get_completion_with_retry(messages, model="gpt-4o-mini", max_vllm_retries=SourceLocationTraceAnalyzer.MAX_VLLM_RETRIES)
            code_blocks = Utils.extract_code_blocks(response)

            if code_blocks:
                converted_code = code_blocks[0]
                subfunctions = len(Utils.extract_functions(converted_code)) - 1  # Subtract 1 to exclude the main function

                if subfunctions > max_subfunctions:
                    max_subfunctions = subfunctions
                    best_conversion = converted_code

        if best_conversion:
            Utils.stdout_logger.info(f"Converted code to tree-style hierarchical structure with {max_subfunctions} sub-functions")
            # split nested functions
            best_conversion = Utils.split_nested_functions(best_conversion)
            Utils.stderr_logger.debug("end convert_to_hierarchical: best conversion")
            return best_conversion
        else:
            Utils.stderr_logger.error("Failed to convert code to tree-style hierarchical structure")
            code = Utils.split_nested_functions(code)
            Utils.stderr_logger.debug("end convert_to_hierarchical: conversion failed")
            return code


# Main loop to process file(s)
if __name__ == "__main__":
    Utils.setup_loggers(name=Path(__file__).stem, logger_stderr_level = logging.DEBUG)

    logging.basicConfig(level=logging.DEBUG)
    logging.getLogger("boto3").setLevel(logging.CRITICAL)
    logging.getLogger("botocore").setLevel(logging.CRITICAL)
    logging.getLogger("urllib3").setLevel(logging.CRITICAL)
    logging.getLogger("httpcore").setLevel(logging.CRITICAL)
    logging.getLogger("httpx").setLevel(logging.CRITICAL)

    source_path = "/Users/scaswell/VerticalRelevance/Projects/Internal/Trace-Injection/distributed-tracing/src/examples/content.py"
    Utils.stderr_logger.debug("start __main__")

    dependency_graph = None
    try:
        full_code = Utils.get_source_code(source_path)
        # Convert to tree-style hierarchical structure
        hierarchical_code = SourceLocationTraceAnalyzer.convert_to_hierarchical(full_code, include_example=False)
        Utils.stdout_logger.info(f"Converted code to tree-style hierarchical structure:\n{hierarchical_code}")

        functions = Utils.extract_functions(hierarchical_code)
        imports = Utils.extract_imports(full_code)
        functions_and_imports = functions | imports

        # Create a dependency graph
        # dependency_graph = Utils.create_dependency_graph(functions)
        dependency_graph = Utils.create_dependency_graph(functions_and_imports)
        Utils.stdout_logger.info(f"Dependency graph:\n{Utils.get_dependency_graph_str(dependency_graph)}")
    except Exception as e:
        Utils.stderr_logger.error(f"Failed to convert code to hierarchical structure: {str(e)}")

    if dependency_graph is None:
        Utils.stderr_logger.error("Failed to create dependency graph")
        sys.exit(1)

    # Sort functions based on their dependencies (bottom-up)
    sorted_functions = Utils.topological_sort(dependency_graph)
    Utils.stdout_logger.info(f"Sorted functions: {sorted_functions}")

    Utils.stderr_logger.debug("end __main__")






    # response = SourceLocationTraceAnalyzer.run(input_source_path=source_path)
    # print(json.dumps(response))
    # print(response)
