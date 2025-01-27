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

from analyze_source_ast import SourceLocationTraceAnalyzer

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
                    imports[alias.name] = f"(import: {alias.asname}" or f"import: {alias.name}"
            elif isinstance(node, ast.ImportFrom):
                module = node.module
                for alias in node.names:
                    imports[alias.name] = f"import: {module}.{alias.name}"
        Utils.stdout_logger.info(f"Extracted {len(imports)} imports: {', '.join(imports.keys())}")
        # Utils.stdout_logger.info(f"Extracted {len(imports)} imports: {', '.join(imports.values())}")

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
                functions[f"f: {node.name}"] = func_code
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
