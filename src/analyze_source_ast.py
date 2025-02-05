import sys
import time
from pathlib import Path
import ast
from pprint import pformat
import openai
from analyze_source_ast_utils import SourceCodeAnalyzerUtils

class SourceCodeNode:
    def __init__(self, name, node_type, source_location=None):
        self.name = name
        self.type = node_type
        self.source_location = source_location
        self.children = {}  # Use dict for easier management of unique children

    def add_child(self, child):
        # Ensure unique children by name
        if child.name not in self.children:
            self.children[child.name] = child
        return self.children[child.name]

class SourceCodeTreeBuilder(ast.NodeVisitor):
    def __init__(self):
        self.root = SourceCodeNode("Root", "root")
        self.current_branch = [self.root]

    # def build_tree(self, source_code):
    #     tree = ast.parse(source_code)
    #     self.visit(tree)
    #     return self.root

    def _add_module_to_tree(self, module_name, node_type='module', source_location=None):
        # Split module name into parts
        parts = module_name.split('.')
        current_node = self.current_branch[-1]

        for part in parts:
            # Add or get existing child node
            current_node = current_node.add_child(
                SourceCodeNode(part, node_type, source_location)
            )

        return current_node

    def visit_Import(self, node):
        for alias in node.names:
            self._add_module_to_tree(
                alias.name,
                'import',
                source_location=(node.lineno, node.col_offset, node.end_lineno)
            )
        self.generic_visit(node)

    def visit_ImportFrom(self, node):
        module = node.module or ''
        for alias in node.names:
            full_name = f"{module}.{alias.name}" if module else alias.name
            self._add_module_to_tree(
                full_name,
                'import_from',
                source_location=(node.lineno, node.col_offset, node.end_lineno)
            )
        self.generic_visit(node)

    def visit_ClassDef(self, node):
        # Create class node
        class_node = SourceCodeNode(
            node.name,
            "class",
            source_location=(node.lineno, node.col_offset, node.end_lineno)
        )

        # Add to current branch
        current_parent = self.current_branch[-1]
        current_parent.add_child(class_node)

        # Push this class as the current branch
        self.current_branch.append(class_node)

        # Visit children of the class
        self.generic_visit(node)

        # Pop back to previous branch
        self.current_branch.pop()

    def visit_FunctionDef(self, node):
        # Create function node
        func_node = SourceCodeNode(
            node.name,
            "function",
            source_location=(node.lineno, node.col_offset, node.end_lineno)
        )

        # Add to current branch
        current_parent = self.current_branch[-1]
        current_parent.add_child(func_node)

        # Push this function as the current branch
        self.current_branch.append(func_node)

        # Visit children of the function
        self.generic_visit(node)

        # Pop back to previous branch
        self.current_branch.pop()

class SourceCodeAnalyzer:
    def __init__(self):
        self.utils = SourceCodeAnalyzerUtils()
        self.client = openai.OpenAI()

    def tree_dumps(self, node) -> str:
        """
        Recursively build string from the tree structure
        """
        self.utils.debug(__name__, "start tree_dumps")
        self.utils.debug(__name__, f"tree_dumps type(node): {type(node)}")
        tree_str_parts = []
        return self._tree_to_str(node, tree_str_parts)

    def _tree_to_str(self, node, tree_str_parts: list[str], prefix='', is_last=True):
        """
        Recursively dump the tree structure with branch-like representation
        """
        self.utils.debug(__name__, "start _tree_to_str")
        self.utils.debug(__name__, f"_tree_to_str type(node): {type(node)}")

        # Prepare line number and type string
        # print(f"node name: {node.name} class: {type(node).__name__} source location: {node.source_location}")
        location_info = f" (line {node.source_location[0]})" if node.source_location else ""
        type_info = f"[{node.type}]"

        # Prepare prefix for current node
        connector = '└── ' if is_last else '├── '
        tree_str_parts.append(f"{prefix}{connector}{node.name} {type_info}{location_info}")

        # Prepare prefix for children
        child_prefix = prefix + ('    ' if is_last else '│   ')

        # Get sorted children to ensure consistent output
        sorted_children = sorted(node.children.values(), key=lambda x: x.name)

        # Recursively print children
        for i, child in enumerate(sorted_children):
            is_child_last = (i == len(sorted_children) - 1)
            self._tree_to_str(child, tree_str_parts, child_prefix, is_child_last)

        return '\n'.join(tree_str_parts)

    # def print_tree(self, node, prefix='', is_last=True):
    #     """
    #     Recursively print the tree structure with branch-like representation
    #     """
    #     # Prepare line number and type string
    #     # print(f"node name: {node.name} class: {type(node).__name__} source location: {node.source_location}")
    #     location_info = f" (line {node.source_location[0]})" if node.source_location else ""
    #     type_info = f"[{node.type}]"

    #     # Prepare prefix for current node
    #     connector = '└── ' if is_last else '├── '
    #     print(f"{prefix}{connector}{node.name} {type_info}{location_info}")

    #     # Prepare prefix for children
    #     child_prefix = prefix + ('    ' if is_last else '│   ')

    #     # Get sorted children to ensure consistent output
    #     sorted_children = sorted(node.children.values(), key=lambda x: x.name)

    #     # Recursively print children
    #     for i, child in enumerate(sorted_children):
    #         is_child_last = (i == len(sorted_children) - 1)
    #         self.print_tree(child, child_prefix, is_child_last)

    def analyze_source_code(self, source_code: str):
        """
        Analyze the source code
        """
        # try:
        #     source_code = self.utils.get_source_code_from_file(file_path)
        #     print(f"len(source_code): {len(source_code)}")
        # except FileNotFoundError:
        #     print(f"Error: File {file_path} not found.")
        #     return None

        # Parse the source code
        tree_builder = SourceCodeTreeBuilder()
        try:
            parsed_ast = ast.parse(source_code)
            tree_builder.visit(parsed_ast)
        except SyntaxError as e:
            print(f"Error parsing source code: {e}")
            return None

        print(f"tree_builder.root class: {type(tree_builder.root).__name__}")
        return tree_builder.root

    def get_completion_with_retry(self, messages, model, max_vllm_retries):
        self.utils.debug(__class__, "start get_completion_with_retry")

        total_completion_tokens = 0
        total_prompt_tokens = 0
        for attempt in range(self.utils.get_max_vllm_retries()):
            if not self.utils.is_silent():
                self.utils.info(__class__, f"Get completion attempt: (attempt {attempt + 1}/{self.utils.get_max_vllm_retries()})")
            self.utils.debug(__class__, f"Get completion attempt: (attempt {attempt + 1}/{self.utils.get_max_vllm_retries()})")
            try:
                self.utils.debug(__class__, f"Input messages: {messages[-1]['content']}")
                chat_completion = self.client.chat.completions.create(
                    messages=messages,
                    model=model,
                    temperature=self.utils.get_temperature(),
                )
                response = chat_completion.choices[0].message.content
                # self.utils.info(__class__, f"LLM response: {response}")
                if not self.utils.is_silent():
                    self.utils.info(__class__, "LLM response received")

                # Update token counts
                total_prompt_tokens += chat_completion.usage.prompt_tokens
                total_completion_tokens += chat_completion.usage.completion_tokens
                self.utils.debug(__class__, "tokens:")
                self.utils.debug(__class__, pformat(chat_completion.usage))
                self.utils.debug(__class__, f"total tokens:")
                self.utils.debug(__class__, pformat(
                    {"total_prompt_tokens": total_prompt_tokens
                    ,"total_completion_tokens": total_completion_tokens
                }))
                self.utils.debug(__class__, "end get_completion_with_retry")
                return response
            except Exception as e:
                if not self.utils.is_silent():
                    self.utils.error(__class__, f"LLM call failed: {str(e)}")
                if attempt < self.utils().get_max_vllm_retries() - 1:
                    if not self.utils.is_silent():
                        self.utils.info(__class__, f"Retrying in {self.utils.get.retry_delay} seconds...")
                    time.sleep(self.utils.get.retry_delay())
                else:
                    self.utils.error(__class__, "Max retries reached. Giving up.")
                    self.utils.debug(__class__, f"end get_completion_with_retry raise Exception: {e}")
                    raise


    def analyze_function_for_decision_points(self, source_code):
        trace_strategy = [
            "Exception Handling Blocks",
            "Function Entry/Exit Points",
            "Complex Algorithm Sections",
            "Performance-Critical Code Paths",
            "State Changes",
            "External Resource Interactions",
            "Conditional Branches"
        ]

        self.utils.debug(__class__, "start analyze_function_for_decision_points")

        prompt1 = f"""


Here's a prioritized list of critical areas trace statements should be place in Python code.

1. Exception Handling Blocks
    - Add traces in try/except blocks to capture specific error conditions and exception details
    - Record input values, stack trace, and context when exceptions occur
2. Function Entry/Exit Points
    - Log input parameters and return values to track function behavior
    - Help diagnose unexpected function outputs or side effects
3. Complex Algorithm Sections
    - Trace key computational steps in algorithms with multiple branches
    - Capture intermediate calculation results and decision points
6. Performance-Critical Code Paths
    - Place traces in loops or recursive functions to monitor execution time
    - Track iteration counts, computational complexity
7. State Changes
    - Log modifications to critical object states or global variables
    - Help track unexpected mutations or state transitions
8. External Resource Interactions
    - Trace database queries, file operations, network calls
    - Capture connection details, transaction outcomes, potential failures
9. Conditional Branches
    - Add traces in complex conditional logic to understand which code paths are executed
    - Record conditions that trigger specific branches

Tracing strategy: Start with highest-priority areas, use targeted, informative log messages that capture context and key data points.

Given the above apporach,
analyze the following Python code contained below surrounded by backticks.
Before performing the analysis, reconstruct the code as line-based text, with
each line terminated by a newline character.

In the response, include the decision point search term and the source line text where the search term was located.
Do not include any occurrences if contained in string literals.
Do not include any occurrences if contained on a commented source line.
Format the response as a valid JSON document.

```
{source_code}
```
        """

        prompt = f"""
Analyze the following Python source code and identify critical locations for adding trace statements based on these priorities:

{', '.join(trace_strategy)}

Provide a detailed breakdown of:
1. Specific code blocks/lines to trace. Include the function/method name and parent if applicable.
2. Rationale for tracing
3. Recommended trace information to capture

Source Code:
```python
{source_code}
```
"""

        messages = [
            {'role': 'system', 'content': 'You are an AI assistant specialized in Python code analysis.'},
            {'role': 'user', 'content': prompt},
        ]

        if "starcoder2" in self.utils.get_ai_model().lower():
            # remove the system message
            messages = messages[1:]

        if not self.utils.is_silent():
            self.utils.info(__class__, "Analyzing code")
        response = self.get_completion_with_retry(messages, model=self.utils.get_ai_model(), max_vllm_retries=self.utils.get_max_vllm_retries)
        self.utils.debug(__class__, f"LLM response: {response}")

        # text_blocks = self.utils.extract_text_blocks(response)
        # if text_blocks:
        #     for block in text_blocks:
        #         self.utils.debug(__class__, f"Text block: {block}")
        #         if block.startswith("### Analysis"):
        #             self.utils.info(block)
        self.utils.info(__class__, "Analysis complete")
        self.utils.info(__class__, response)

        self.utils.debug(__class__, "end analyze_function_for_decision_points")


    def process_file(self, input_source_path: str):
        self.utils.debug(__class__, "start process_file")
        self.utils.debug(__class__, f"input_source_path: {input_source_path}")
        self.utils.info(__class__, "")
        self.utils.info(__class__, f"Process file '{input_source_path}'")

        dependency_graph = None
        try:
            full_code = self.utils.get_source_code_from_file(source_path=input_source_path)
            self.utils.debug(__class__, f"full_code len: {len(full_code)}")

            # source_tree = self.analyze_source_code(file_path=input_source_path)
            source_tree = self.analyze_source_code(source_code=full_code)
            self.utils.debug(__class__, f"source_tree class: {type(source_tree).__name__} name: {type(source_tree).__name__}")
            if source_tree:
                print(f"source_tree: {type(source_tree).__name__}")
                print("\n--- Source Code Tree Structure ---")
                # self.print_tree(node=source_tree)
                self.utils.info(__class__, self.tree_dumps(node=source_tree))

            functions = self.utils.extract_functions(full_code)
            self.utils.debug(__class__, f"Extracted functions:\n{pformat(functions.keys())}")
            self.utils.debug(__class__, "Extracted function class:")
            self.utils.debug(__class__, pformat( {k: v[0] for k, v in functions.items()} ))
            functions_new = self.utils.extract_functions_new(full_code, source_tree)
            self.utils.debug(__class__, f"Extracted functions (new):\n{pformat(functions_new.keys())}")
            self.utils.debug(__class__, "Extracted function (new) class:")
            self.utils.debug(__class__, pformat( {k: v[0] for k, v in functions_new.items()} ))
            imports = self.utils.extract_imports(full_code)
            self.utils.debug(__class__, f"Extracted imports:\n{pformat(imports.values())}")
            self.utils.debug(__class__, "Extracted import class:")
            self.utils.debug(__class__, pformat( {k: v[0] for k, v in imports.items()} ))
            functions_and_imports = functions | imports

            if source_tree:
                # Future placeholder for OpenAI analysis
                print("\n--- OpenAI Analysis Placeholder ---")
                print("Note: OpenAI integration would go here for analyzing decision points and external references.")

        except Exception as e:
            self.utils.error(__class__, f"Failed to analyze code: {str(e)}", exc_info=True)
            return False

        # try:
        #     dependency_graph = self.utils.create_dependency_graph(functions_and_imports)
        #     self.utils.debug(__class__, f"dependency_graph: {pformat(dependency_graph)}")
        # except Exception as e:
        #     self.utils.error(__class__, f"Failed to create dependency graph: {str(e)}", exc_info=True)
        #     return False

        # if dependency_graph is None:
        #     self.utils.error(__class__, "Failed to create dependency graph")
        #     return False

        try:
            # loop over functions
            # for function_name, (_, function_code) in functions.items():
            #     self.utils.debug(__class__, f"function_name: {function_name}")
            #     self.utils.info(__class__, f"Function: {function_name}")

            #     # Analyze the code
            #     self.analyze_function_for_decision_points(function_code)
                # Analyze the code
            self.analyze_function_for_decision_points(full_code)
        except:
            # self.utils.error(__class__, f"Failed to analyze code function '{function_name}'", exc_info=True)
            self.utils.error(__class__, f"Failed to analyze source code", exc_info=True)
            self.utils.debug(__class__, "end process_file (error)")
            return False

        # # Sort functions based on their dependencies (bottom-up)
        # sorted_functions = self.utils.topological_sort(dependency_graph)
        # self.utils.debug(__class__, f"sorted_functions: {sorted_functions}")

        self.utils.debug(__class__, "end process_file")
        return True

    def process_directory(self, source_path: str) -> None:
        self.utils.debug(__class__, "start process_directory")
        self.utils.debug(__class__, f"source_path: {source_path}")
        if not self.utils.is_silent():
            self.utils.info(__class__, f"Process directory '{source_path}'")

        if not Path(source_path).exists():
            self.utils.error(__class__, f"Source path '{source_path}' does not exist")
            return
        if not Path(source_path).is_dir():
            self.utils.error(__class__, f"Source path '{source_path}' is not a directory")
            return

        for root, dirs, files in Path(source_path).walk():
            # self.utils.debug(pformat(path))
            self.utils.debug(__class__, f"root: {root}")
            self.utils.debug(__class__, f"dirs: {dirs}")
            self.utils.debug(__class__, f"files: {files}")
            for file in files:
                if file.endswith(".py"):
                    source_path = f"{root}/{file}"
                    self.process_file(source_path)

        self.utils.debug(__class__, "end process_directory")

def main():

    utils: SourceCodeAnalyzerUtils = SourceCodeAnalyzerUtils()
    utils.debug(__name__, "start __main__")
    # be_silent: bool = os.getenv("SILENT", "false").lower() == "True"
    # utils.set_silent(be_silent)
    if not utils.is_silent():
        utils.info(__name__, "Starting...")

    # Check if file path is provided
    if len(sys.argv) < 2:
        print(f"Usage: python {sys.argv[0]} source_directory_path|source_file_path")
        sys.exit(1)

    analyzer: SourceCodeAnalyzer = SourceCodeAnalyzer()

    # Analyze the source code
    source_path = sys.argv[1]
    utils.debug(__name__, f"source_path: {source_path}")

    # source_tree = analyzer.analyze_source_code(source_path)

    # if source_tree:
    #     print(f"source_tree: {type(source_tree).__name__}")
    #     print("\n--- Source Code Tree Structure ---")
    #     analyzer.print_tree(node=source_tree)

    #     # Future placeholder for OpenAI analysis
    #     print("\n--- OpenAI Analysis Placeholder ---")
    #     print("Note: OpenAI integration would go here for analyzing decision points and external references.")

    if Path(source_path).is_file():
        analyzer.process_file(source_path)
    else:
        if Path(source_path).is_dir():
            analyzer.process_directory(source_path)
        else:
            utils.error(__name__, f"Source path '{source_path}' is neither a file nor a directory")

    # source_file = os.getenv("SOURCE_FILE")
    # if source_file:
    #     utils.debug(f"source_file: {source_file}")
    #     analyzer.process_file(input_source_path=source_file)
    # else:
    #     utils.debug("SOURCE_FILE not set")
    #     source_dir = os.getenv("SOURCE_DIR")
    #     if source_dir:
    #         utils.debug(f"source_dir: {source_dir}")
    #         analyzer.process_directory(source_dir)
    #     else:
    #         utils.debug("SOURCE_DIR not set")
    #         msg = "Please set either SOURCE_FILE or SOURCE_DIR environment variable."
    #         utils.error(msg)
    #         raise ValueError(msg)

    utils.debug(__name__, "end __main__")

if __name__ == "__main__":
    main()
