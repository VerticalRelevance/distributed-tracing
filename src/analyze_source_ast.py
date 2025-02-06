import sys
import time
from pathlib import Path
import ast
from pprint import pformat
import openai
from analyze_source_ast_utils import SourceCodeAnalyzerUtils
from utilities import Utilities

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
        self.utils = Utilities()
        self.ast_utils = SourceCodeAnalyzerUtils()
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

    def analyze_source_code(self, source_code: str):
        """
        Analyze the source code
        """
        # Parse the source code
        tree_builder = SourceCodeTreeBuilder()
        try:
            parsed_ast = ast.parse(source_code)
            tree_builder.visit(parsed_ast)
        except SyntaxError as e:
            self.utils.error(__class__, f"Error parsing source code: {e}")
            return None

        self.utils.debug(__class__, f"tree_builder.root class: {type(tree_builder.root).__name__}")
        return tree_builder.root

    def get_completion_with_retry(self, messages, model, max_vllm_retries: int, retry_delay: int):
        self.utils.debug(__class__, "start get_completion_with_retry")

        total_completion_tokens = 0
        total_prompt_tokens = 0
        for attempt in range(max_vllm_retries):
            if not self.utils.is_silent():
                self.utils.info(__class__, f"Get completion attempt: (attempt {attempt + 1}/{max_vllm_retries})")
            self.utils.debug(__class__, f"Get completion attempt: (attempt {attempt + 1}/{max_vllm_retries})")
            try:
                self.utils.debug(__class__, f"Input messages: {messages[-1]['content']}")
                chat_completion = self.client.chat.completions.create(
                    messages=messages,
                    model=model,
                    temperature=self.ast_utils.get_temperature(),
                )
                response = chat_completion.choices[0].message.content
                if not self.utils.is_silent():
                    self.utils.info(__class__, "LLM response received")

                # Update token counts
                total_prompt_tokens += chat_completion.usage.prompt_tokens
                total_completion_tokens += chat_completion.usage.completion_tokens
                self.utils.debug(__class__, "tokens:")
                self.utils.debug(__class__, pformat(chat_completion.usage))
                self.utils.debug(__class__, "total tokens:")
                self.utils.debug(__class__, pformat(
                    {"total_prompt_tokens": total_prompt_tokens
                    ,"total_completion_tokens": total_completion_tokens
                }))
                self.utils.debug(__class__, "end get_completion_with_retry")
                return response
            except Exception as e:
                if not self.utils.is_silent():
                    self.utils.error(__class__, f"LLM call failed: {str(e)}")
                if attempt < self.ast_utils().get_max_vllm_retries() - 1:
                    if not self.utils.is_silent():
                        self.utils.info(__class__, f"Retrying in {retry_delay} seconds...")
                    time.sleep(retry_delay)
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
            {'role': 'system',
             'content': 'You are an AI assistant specialized in Python code analysis.'},
            {'role': 'user', 'content': prompt},
        ]

        if "starcoder2" in self.ast_utils.get_ai_model().lower():
            # remove the system message
            messages = messages[1:]

        if not self.utils.is_silent():
            self.utils.info(__class__, "Analyzing code")
        response = self.get_completion_with_retry(messages, model=self.ast_utils.get_ai_model(), max_vllm_retries=self.ast_utils.get_max_vllm_retries)
        self.utils.debug(__class__, f"LLM response: {response}")

        self.utils.info(__class__, "Analysis complete")
        self.utils.info(__class__, response)

        self.utils.debug(__class__, "end analyze_function_for_decision_points")


    def process_file(self, input_source_path: str):
        self.utils.debug(__class__, "start process_file")
        self.utils.debug(__class__, f"input_source_path: {input_source_path}")
        self.utils.info(__class__, "")
        self.utils.info(__class__, f"Process file '{input_source_path}'")

        try:
            full_code = self.utils.get_ascii_file_contents(source_path=input_source_path)
            self.utils.debug(__class__, f"full_code len: {len(full_code)}")
            if len(full_code) == 0:
                self.utils.warning(__class__, f"Skipping empty file '{input_source_path}'")
                return

            source_tree = self.analyze_source_code(source_code=full_code)
            self.utils.debug(__class__, f"source_tree class: {type(source_tree).__name__} name: {type(source_tree).__name__}")
            if source_tree:
                self.utils.debug(__class__, f"source_tree: {type(source_tree).__name__}")
                self.utils.info(__class__, "\n--- Source Code Tree Structure ---")
                self.utils.info(__class__, self.tree_dumps(node=source_tree))

        except Exception as e:
            self.utils.error(__class__, f"Failed to build source tree: {str(e)}", exc_info=True)
            return

        # TODO change to return if no source_tree was returned
        if source_tree:
            self.utils.info(__class__, "\n--- OpenAI Analysis ---")

        try:
            # Analyze the code
            self.analyze_function_for_decision_points(full_code)
        except:
            self.utils.error(__class__, f"Failed to analyze source code", exc_info=True)
            self.utils.debug(__class__, "end process_file (error)")
            return

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
            self.utils.debug(__class__, f"root: {root}")
            self.utils.debug(__class__, f"dirs: {dirs}")
            self.utils.debug(__class__, f"files: {files}")
            for file in files:
                if file.endswith(".py"):
                    source_path = f"{root}/{file}"
                    self.process_file(source_path)

        self.utils.debug(__class__, "end process_directory")

def main():

    utils: Utilities = Utilities()
    utils.debug(__name__, "start __main__")
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

    if utils.is_file(source_path):
        analyzer.process_file(source_path)
    else:
        if utils.is_dir(source_path):
            analyzer.process_directory(source_path)
        else:
            utils.error(__name__, f"Source path '{source_path}' is neither a file nor a directory")

    utils.debug(__name__, "end __main__")

if __name__ == "__main__":
    main()
