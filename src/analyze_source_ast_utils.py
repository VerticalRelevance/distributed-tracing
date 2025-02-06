import logging
import os

class SourceCodeAnalyzerUtils:
    # Instance attributes
    # stdout_logger = None
    # stderr_logger = None

    def __init__(self):
        # self.stdout_logger: logging.Logger = None
        # self.stderr_logger: logging.Logger = None
        self.ai_model = None
        self.max_vllm_retries = None
        self.retry_delay = None
        # self.repeat_convert_hierarchical_num = None
        self.temperature = None

        logging.getLogger("boto3").setLevel(logging.CRITICAL)
        logging.getLogger("botocore").setLevel(logging.CRITICAL)
        logging.getLogger("urllib3").setLevel(logging.CRITICAL)
        logging.getLogger("httpcore").setLevel(logging.CRITICAL)
        logging.getLogger("httpx").setLevel(logging.CRITICAL)

    # Instance methods

    # def setup_stdout_logger(self, name: str, logger_level: int = logging.INFO) ->  logging.Logger:
    #     if not self.stdout_logger:
    #         # Configure the stdout logger
    #         self.stdout_logger = logging.getLogger(f"{name}.stdout")
    #         self.stdout_logger.setLevel(logger_level)

    #         console_handler = logging.StreamHandler(stream=sys.stdout)
    #         console_handler.setLevel(logger_level)

    #         formatter = logging.Formatter("%(message)s")
    #         console_handler.setFormatter(formatter)

    #         self.stdout_logger.addHandler(console_handler)

    #     return self.stdout_logger

    # def setup_stderr_logger(self, name: str, logger_level: int = logging.ERROR) -> logging.Logger:
    #     if not self.stderr_logger:
    #         # Configure the stderr logger
    #         self.stderr_logger = logging.getLogger(f"{name}.stderr")
    #         self.stderr_logger.setLevel(logger_level)

    #         console_handler = logging.StreamHandler(stream=sys.stderr)
    #         console_handler.setLevel(logger_level)

    #         formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    #         console_handler.setFormatter(formatter)

    #         self.stderr_logger.addHandler(console_handler)

    #     return self.stderr_logger

    # def setup_loggers(self, name: str, logger_stdout_level: int = logging.INFO, logger_stderr_level: int = logging.ERROR) -> list[logging.Logger]:
    #     return (
    #         self.setup_stdout_logger(name, logger_stdout_level),
    #         self.setup_stderr_logger(name, logger_stderr_level)
    #     )


    # def create_dependency_graph(self, graph_items: dict) -> dict:
    #     self.debug(__class__, "start create_dependency_graph")
    #     self.debug(__class__, f"graph_items: {pformat(graph_items)}")
    #     graph = {item_name: set() for item_name in graph_items}
    #     for item_name, (_, item_code) in graph_items.items():
    #         for other_item in graph_items:
    #             if other_item in item_code and other_item != item_name:
    #                 graph[item_name].add(other_item)

    #     self.debug(__class__, "end create_dependency_graph")
    #     return graph

    # def extract_imports(self, code) -> dict:
    #     self.debug(__class__, "start extract_imports")
    #     self.debug(__class__, "Extracting imports from code")
    #     tree = ast.parse(code)
    #     imports = {}
    #     for node in ast.walk(tree):
    #         if isinstance(node, ast.Import):
    #             for alias in node.names:
    #                 imports[alias.name] = (type(node), alias.asname or alias.name)
    #         elif isinstance(node, ast.ImportFrom):
    #             module = node.module
    #             for alias in node.names:
    #                 imports[alias.name] = (type(node), f"{module}.{alias.name}")
    #     self.debug(__class__, f"Extracted {len(imports)} imports: {', '.join(imports.keys())}")
    #     # self.stdout_logger.info(f"Extracted {len(imports)} imports: {', '.join(imports.values())}")

    #     self.debug(__class__, "end extract_imports")
    #     return imports

    # def extract_functions(self, code) -> dict:
    #     self.debug(__class__, "start extract_functions")
    #     self.debug(__class__, f"type(code): {type(code)}")
    #     self.debug(__class__, "Extracting functions from code")
    #     tree = ast.parse(code)
    #     functions = {}
    #     for node in ast.walk(tree):
    #         if isinstance(node, ast.FunctionDef):
    #             self.debug(__class__, "node:")
    #             self.debug(__class__, vars(node))
    #             func_code = ast.get_source_segment(code, node)
    #             functions[node.name] = (node, func_code)
    #     self.debug(__class__, f"Extracted {len(functions)} functions: {', '.join(functions.keys())}")

    #     self.debug(__class__, "end extract_functions")
    #     return functions

    # def extract_functions_new(self, code, tree: dict) -> dict:
    #     """
    #     Walk a tree of SourceCodeNode instances and extract all function nodes with their source code.

    #     Args:
    #         root_node (SourceCodeNode): The root node of the tree to traverse
    #         source_code (str): Original source code as a string

    #     Returns:
    #         dict[str, str]: Dictionary mapping function names to their source code

    #     Raises:
    #         ValueError: If source_location contains invalid line numbers
    #         IndexError: If source_location refers to lines outside the source code range
    #     """
    #     functions = {}
    #     source_lines = code.splitlines()
    #     total_lines = len(source_lines)

    #     def _get_indentation(line):
    #         """Helper function to get the indentation level of a line."""
    #         return len(line) - len(line.lstrip())

    #     def _extract_function_source(start_line, end_line):
    #         """
    #         Extract function source code while preserving indentation relative to function definition.

    #         Args:
    #             start_line (int): Starting line number (1-based)
    #             end_line (int): Ending line number (1-based)

    #         Returns:
    #             str: Properly indented function source code

    #         Raises:
    #             ValueError: If start_line > end_line
    #             IndexError: If line numbers are out of range
    #         """
    #         # Validate line numbers
    #         if start_line > end_line:
    #             raise ValueError(f"Invalid line numbers: start_line ({start_line}) > end_line ({end_line})")

    #         if start_line < 1:
    #             raise ValueError(f"Invalid start_line: {start_line} (must be >= 1)")

    #         if end_line > total_lines:
    #             raise IndexError(f"end_line ({end_line}) exceeds source code length ({total_lines})")

    #         # Convert to 0-based indexing
    #         start_idx = start_line - 1
    #         end_idx = end_line

    #         # Get the lines
    #         function_lines = source_lines[start_idx:end_idx]

    #         if not function_lines:
    #             raise ValueError(f"No source code found between lines {start_line} and {end_line}")

    #         # Get the base indentation from the first line
    #         base_indent = _get_indentation(function_lines[0])

    #         # Remove the base indentation from all lines while preserving relative indentation
    #         normalized_lines = []
    #         for line in function_lines:
    #             if line.strip():  # Only process non-empty lines
    #                 current_indent = _get_indentation(line)
    #                 # If this line is indented relative to the function definition,
    #                 # preserve the relative indentation
    #                 if current_indent >= base_indent:
    #                     normalized_lines.append(line[base_indent:])
    #                 else:
    #                     # This case shouldn't happen with valid Python code,
    #                     # but handle it gracefully
    #                     normalized_lines.append(line)
    #             else:
    #                 # Preserve empty lines
    #                 normalized_lines.append('')

    #         return '\n'.join(normalized_lines)

    #     def _traverse(node):
    #         # Check if current node is a function
    #         if node.type in ("FunctionDef", "AsyncFunctionDef"):
    #             if node.source_location:
    #                 try:
    #                     start_line, end_line = node.source_location
    #                     function_source = _extract_function_source(start_line, end_line)
    #                     functions[node.name] = function_source
    #                 except (ValueError, IndexError) as e:
    #                     print(f"Warning: Could not extract source for function '{node.name}': {str(e)}")

    #         # Recursively traverse all children
    #         for child in node.children.values():
    #             _traverse(child)

    #     _traverse(tree)
    #     return functions

    # def extract_code_blocks(self, response):
    #     """Extract all code blocks from the response."""
    #     self.debug(__class__, "start extract_code_blocks")
    #     self.debug(__class__, f"extract_code_blocks response type: {response}")
    #     self.debug(__class__, "end extract_code_blocks")
    #     return re.findall(r'```python\s*(.*?)\s*```', response, re.DOTALL)

    # def extract_text_blocks(self, response) -> list:
    #     """Extract blocks of text from a string where blocks start with '###'."""
    #     lines = response.splitlines()  # Split the string into individual lines
    #     blocks = []  # List to store the extracted blocks
    #     current_block = []  # Temporary list to store lines for the current block

    #     for line in lines:
    #         if line.startswith("###"):
    #             # If there's already a block being constructed, finalize it
    #             if current_block:
    #                 blocks.append("\n".join(current_block))
    #                 current_block = []  # Start a new block
    #         current_block.append(line)

    #     # Append the last block if it exists
    #     if current_block:
    #         blocks.append("\n".join(current_block[:-1]))  # Exclude the ending "###" of the last block

    #     return blocks

    # def extract_function(self, code_block, function_name: str):
    #     """Extract a specific function from a code block."""
    #     self.debug(__class__, "start extract_function")
    #     self.debug(__class__, f"extract_function code_block type: {type(code_block)}")
    #     try:
    #         tree = ast.parse(code_block)
    #     except:
    #         self.utils.error(__class__, f"Failed to parse code block for function: {function_name} from\n{code_block}")
    #         return None
    #     for node in ast.walk(tree):
    #         if isinstance(node, ast.FunctionDef) and node.name == function_name:
    #             return ast.get_source_segment(code_block, node)

    #     self.debug(__class__, "end extract_function")
    #     return None

    def get_ai_model(self) -> str:
        if not self.ai_model:
            self.ai_model = os.getenv("AI_MODEL", "gpt-4o-mini")
        return self.ai_model

    def get_max_vllm_retries(self) -> int:
        if not self.max_vllm_retries:
            self.max_vllm_retries = int(os.getenv("MAX_VLLM_RETRIES", "10"))
        self.max_vllm_retries = max(self.max_vllm_retries, 1)
        return self.max_vllm_retries

    def get_retry_delay(self) -> int:
        if not self.retry_delay:
            self.retry_delay = int(os.getenv("RETRY_DELAY", "0"))
        self.retry_delay = max(self.retry_delay, 0)
        return self.retry_delay

    # def get_repeat_convert_hierarchical_num(self) -> int:
    #     if not self.repeat_convert_hierarchical_num:
    #         self.repeat_convert_hierarchical_num = int(os.getenv("REPEAT_CONVERT_HIERARCHICAL_NUM", "3"))
    #     self.repeat_convert_hierarchical_num = max(self.repeat_convert_hierarchical_num, 1)
    #     return self.repeat_convert_hierarchical_num

    def get_temperature(self) -> float:
        if not self.temperature:
            self.temperature = float(os.getenv("TEMPERATURE", "0.0"))
        self.temperature = max(self.temperature, 0.0)
        return self.temperature

