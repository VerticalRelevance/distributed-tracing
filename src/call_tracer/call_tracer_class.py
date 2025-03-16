"""
Module for tracing function calls in Python source code.

This module provides functionality to trace function calls in Python source code,
starting from an entry point and recursively following the call chain. It can handle
calls to functions within the same file, imported functions, and functions in external
files within a specified search path.
"""

# TODO add check for required env vars


import ast
import os
import hashlib
import logging
from typing import Dict, List, Optional, Any

from call_tracer.renderers.renderer import RendererFactory, RendererUtils
from common.configuration import Configuration

# TODO write stderr to LOG_FILE_STDERR
# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class CallTracer:
    """
    A class for tracing function calls in Python source code.

    This class analyzes Python source code to build a tree of function calls,
    starting from a specified entry point. It can trace calls within the same file,
    imported functions, and functions in external files within a specified search path.
    """

    def __init__(self, configuration: Configuration, source_file: str, search_paths: List[str]):
        """
        Initialize the CallTracer with a source file and search paths.

        Args:
            source_file: Full path to the source file to analyze
            search_paths: List of paths to search for external modules
        """
        self._config = configuration
        self.source_file = os.path.abspath(source_file)
        self.search_paths = [os.path.abspath(path) for path in search_paths]
        self.visited_files = set()
        self.visited_functions = set()
        self.module_cache = {}  # Cache for parsed modules
        self.import_map = {}  # Maps imported names to their modules
        self.class_attribute_map = {}  # Maps class attributes to their types
        self.class_file_map = {}  # Maps class names to their file paths
        logger.info(f"Initialized CallTracer with source file: {self.source_file}")
        logger.info(f"Search paths: {self.search_paths}")

    def _generate_id(self, data: Dict) -> str:
        """
        Generate a unique ID for a dictionary using MD5 hash.

        Args:
            data: Dictionary to hash

        Returns:
            MD5 hash of the dictionary as a string
        """
        # Create a copy to avoid modifying the original
        data_copy = data.copy()
        # Remove the id field if it exists to avoid circular reference
        if "id" in data_copy:
            del data_copy["id"]

        # Convert dictionary to string and hash
        data_str = str(sorted(data_copy.items()))
        return hashlib.md5(data_str.encode()).hexdigest()

    def _parse_file(self, file_path: str) -> ast.Module:
        """
        Parse a Python file into an AST.

        Args:
            file_path: Path to the file to parse

        Returns:
            AST of the parsed file
        """
        if file_path in self.module_cache:
            return self.module_cache[file_path]

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                source = f.read()

            tree = ast.parse(source, filename=file_path)
            self.module_cache[file_path] = tree

            # Index all classes in this file
            self._index_classes_in_file(tree, file_path)

            return tree
        except Exception as e:  # pylint: disable=broad-exception-caught
            logger.error(f"Error parsing file {file_path}: {e}")
            return None

    def _index_classes_in_file(self, tree: ast.Module, file_path: str) -> None:
        """
        Index all classes in a file for quick lookup.

        Args:
            tree: AST of a Python module
            file_path: Path to the file being analyzed
        """
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                self.class_file_map[node.name] = file_path

    def _find_imports(self, tree: ast.Module) -> Dict[str, str]:
        """
        Find all imports in an AST and map them to their module paths.

        Args:
            tree: AST of a Python module

        Returns:
            Dictionary mapping imported names to their module paths
        """
        imports = {}

        class ImportVisitor(ast.NodeVisitor):
            def visit_Import(self, node):
                for name in node.names:
                    alias = name.asname if name.asname else name.name
                    imports[alias] = name.name
                self.generic_visit(node)

            def visit_ImportFrom(self, node):
                if node.module:
                    for name in node.names:
                        alias = name.asname if name.asname else name.name
                        if node.level == 0:  # absolute import
                            imports[alias] = f"{node.module}.{name.name}"
                        else:  # relative import
                            # Handle relative imports based on the current file's package
                            imports[alias] = f"relative.{node.module}.{name.name}"
                self.generic_visit(node)

        ImportVisitor().visit(tree)
        logger.debug(f"Found imports: {imports}")
        return imports

    def _analyze_class_attributes(
        self, tree: ast.Module, file_path: str
    ) -> Dict[str, Dict[str, str]]:
        """
        Analyze class attributes to determine their types.

        Args:
            tree: AST of a Python module
            file_path: Path to the file being analyzed

        Returns:
            Dictionary mapping class names to dictionaries of attribute names and their types
        """
        class_attrs = {}

        class ClassAttributeVisitor(ast.NodeVisitor):
            def visit_ClassDef(self, node):
                class_name = node.name
                attrs = {}

                # Find __init__ method to analyze attribute assignments
                init_method = None
                for item in node.body:
                    if isinstance(item, ast.FunctionDef) and item.name == "__init__":
                        init_method = item
                        break

                if init_method:
                    # Analyze attribute assignments in __init__
                    for stmt in init_method.body:
                        if isinstance(stmt, ast.Assign):
                            for target in stmt.targets:
                                if (
                                    isinstance(target, ast.Attribute)
                                    and isinstance(target.value, ast.Name)
                                    and target.value.id == "self"
                                ):
                                    attr_name = target.attr

                                    # Try to determine the type of the attribute
                                    if isinstance(stmt.value, ast.Call):
                                        if isinstance(stmt.value.func, ast.Name):
                                            # Case: self.attr = ClassName()
                                            attrs[attr_name] = stmt.value.func.id
                                        elif isinstance(stmt.value.func, ast.Attribute):
                                            # Case: self.attr = module.ClassName()
                                            if isinstance(
                                                stmt.value.func.value, ast.Name
                                            ):
                                                attrs[attr_name] = (
                                                    f"{stmt.value.func.value.id}.{stmt.value.func.attr}"    # pylint: disable=line-too-long
                                                )

                class_attrs[class_name] = attrs
                self.generic_visit(node)

        ClassAttributeVisitor().visit(tree)

        # Store in the global map with file path as context
        for class_name, attrs in class_attrs.items():
            self.class_attribute_map[f"{file_path}:{class_name}"] = attrs

        return class_attrs

    def _find_module_path(self, module_name: str) -> Optional[str]:
        """
        Find the file path for a module name.

        Args:
            module_name: Name of the module to find

        Returns:
            File path of the module if found, None otherwise
        """
        # Handle relative imports
        if module_name.startswith("relative."):
            parts = module_name.split(".")
            current_dir = os.path.dirname(self.source_file)
            # Navigate up the directory tree based on the number of dots
            level = 1  # Default for relative imports starting with "relative."
            for _ in range(level):
                current_dir = os.path.dirname(current_dir)

            # Reconstruct the module path
            module_path = os.path.join(current_dir, *parts[1:-1])
            module_file = os.path.join(module_path, f"{parts[-1]}.py")

            if os.path.exists(module_file):
                return module_file
            return None

        # Handle absolute imports
        module_path = module_name.replace(".", os.path.sep)

        # Check in search paths
        for search_path in self.search_paths:
            # Try as a direct module file
            potential_path = os.path.join(search_path, f"{module_path}.py")
            if os.path.exists(potential_path):
                return potential_path

            # Try as a directory with __init__.py
            potential_dir = os.path.join(search_path, module_path)
            potential_init = os.path.join(potential_dir, "__init__.py")
            if os.path.exists(potential_init):
                return potential_init

        logger.warning(f"Could not find module path for {module_name}")
        return None

    def _find_function_in_tree(
        self, tree: ast.Module, function_name: str
    ) -> Optional[ast.FunctionDef]:
        """
        Find a function definition in an AST.

        Args:
            tree: AST of a Python module
            function_name: Name of the function to find

        Returns:
            Function definition node if found, None otherwise
        """
        # If function_name contains a class name (e.g., "ClassName.method_name")
        if "." in function_name:
            class_name, method_name = function_name.split(".", 1)

            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef) and node.name == class_name:
                    for item in node.body:
                        if (
                            isinstance(item, ast.FunctionDef)
                            and item.name == method_name
                        ):
                            return item
        else:
            # Look for standalone function
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef) and node.name == function_name:
                    return node

        return None

    def _find_class_in_tree(
        self, tree: ast.Module, class_name: str
    ) -> Optional[ast.ClassDef]:
        """
        Find a class definition in an AST.

        Args:
            tree: AST of a Python module
            class_name: Name of the class to find

        Returns:
            Class definition node if found, None otherwise
        """
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef) and node.name == class_name:
                return node
        return None

    def _extract_function_calls(
        self, func_node: ast.FunctionDef
    ) -> List[Dict[str, Any]]:
        """
        Extract all function calls from a function definition.

        Args:
            func_node: Function definition node

        Returns:
            List of dictionaries containing information about each function call
        """
        calls = []

        class CallVisitor(ast.NodeVisitor):
            def visit_Call(self, node):
                call_info = {
                    "lineno": node.lineno,
                    "col_offset": node.col_offset,
                }

                # Handle different types of function calls
                if isinstance(node.func, ast.Name):
                    # Simple function call: func()
                    call_info["name"] = node.func.id
                    call_info["type"] = "direct"
                    calls.append(call_info)
                elif isinstance(node.func, ast.Attribute):
                    # Attribute call: obj.method() or module.func()
                    if isinstance(node.func.value, ast.Name):
                        if node.func.value.id == "self":
                            # Self method call: self.method()
                            call_info["name"] = node.func.attr
                            call_info["type"] = "self"
                            calls.append(call_info)
                        else:
                            # Module or object method call: module.func() or obj.method()
                            call_info["name"] = f"{node.func.value.id}.{node.func.attr}"
                            call_info["type"] = "attribute"
                            calls.append(call_info)
                    elif isinstance(node.func.value, ast.Attribute):
                        # Handle nested attributes like self.attr.method()
                        if (
                            isinstance(node.func.value.value, ast.Name)
                            and node.func.value.value.id == "self"
                        ):
                            # Self attribute method call: self.attr.method()
                            call_info["name"] = (
                                f"{node.func.value.attr}.{node.func.attr}"
                            )
                            call_info["type"] = "self_attribute"
                            calls.append(call_info)
                        else:
                            # Nested attribute call: module.submodule.func()
                            # Recursively build the full name
                            parts = []
                            current = node.func
                            while isinstance(current, ast.Attribute):
                                parts.insert(0, current.attr)
                                current = current.value
                            if isinstance(current, ast.Name):
                                parts.insert(0, current.id)
                                call_info["name"] = ".".join(parts)
                                call_info["type"] = "nested_attribute"
                                calls.append(call_info)

                self.generic_visit(node)

        CallVisitor().visit(func_node)
        return calls

    def _resolve_function_call(
        self,
        call_info: Dict[str, Any],
        current_file: str,
        current_class: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Resolve a function call to its definition.

        Args:
            call_info: Dictionary containing information about the function call
            current_file: Path to the file containing the call
            current_class: Name of the class containing the call (if applicable)

        Returns:
            Dictionary with information about the resolved function
        """
        call_type = call_info["type"]
        call_name = call_info["name"]

        logger.info(f"Resolving function call: {call_name} (type: {call_type})")

        # Initialize result with call information
        result = {
            "name": call_name,
            "type": call_type,
            "lineno": call_info["lineno"],
            "col_offset": call_info["col_offset"],
            "calls": [],
            "file_path": None,
            "qualified_name": None,
            "found": False,
        }

        # Handle self method calls
        if call_type == "self" and current_class:
            # Look for the method in the current class
            tree = self._parse_file(current_file)
            class_node = self._find_class_in_tree(tree, current_class)

            if class_node:
                for node in class_node.body:
                    if isinstance(node, ast.FunctionDef) and node.name == call_name:
                        result["file_path"] = current_file
                        result["qualified_name"] = f"{current_class}.{call_name}"
                        result["found"] = True

                        # Add function calls from this method
                        if (
                            f"{current_file}:{current_class}.{call_name}"
                            not in self.visited_functions
                        ):
                            self.visited_functions.add(
                                f"{current_file}:{current_class}.{call_name}"
                            )
                            result["calls"] = self._trace_function_calls(
                                node, current_file, current_class
                            )
                        break

        # Handle self attribute method calls (self.attr.method())
        elif call_type == "self_attribute" and current_class:
            # Set the qualified name to include "self."
            result["qualified_name"] = f"self.{call_name}"

            # First, analyze class attributes to find the type of the attribute
            tree = self._parse_file(current_file)
            self._analyze_class_attributes(tree, current_file)

            # Get the attribute and method name
            attr_name, method_name = call_name.split(".", 1)

            # Look up the attribute type in our class attribute map
            class_attrs = self.class_attribute_map.get(
                f"{current_file}:{current_class}", {}
            )
            attr_type = class_attrs.get(attr_name)

            if attr_type:
                logger.info(f"Found attribute type for {attr_name}: {attr_type}")

                # If the attribute type is an imported class
                imports = self._find_imports(tree)
                if "." in attr_type and attr_type.split(".")[0] in imports:
                    module_name = imports[attr_type.split(".")[0]]
                    class_name = attr_type.split(".")[1]
                    module_path = self._find_module_path(module_name)

                    if module_path:
                        module_tree = self._parse_file(module_path)
                        if module_tree:
                            class_node = self._find_class_in_tree(
                                module_tree, class_name
                            )
                            if class_node:
                                for node in class_node.body:
                                    if (
                                        isinstance(node, ast.FunctionDef)
                                        and node.name == method_name
                                    ):
                                        result["file_path"] = module_path
                                        # Keep the qualified_name as "self.attr.method"
                                        result["found"] = True

                                        # Add function calls from this method
                                        if (
                                            f"{module_path}:{class_name}.{method_name}"
                                            not in self.visited_functions
                                        ):
                                            self.visited_functions.add(
                                                f"{module_path}:{class_name}.{method_name}"
                                            )
                                            result["calls"] = (
                                                self._trace_function_calls(
                                                    node, module_path, class_name
                                                )
                                            )
                                        break
                else:
                    # Check if the class is defined in the current file
                    class_node = self._find_class_in_tree(tree, attr_type)
                    if class_node:
                        for node in class_node.body:
                            if (
                                isinstance(node, ast.FunctionDef)
                                and node.name == method_name
                            ):
                                result["file_path"] = current_file
                                # Keep the qualified_name as "self.attr.method"
                                result["found"] = True

                                # Add function calls from this method
                                if (
                                    f"{current_file}:{attr_type}.{method_name}"
                                    not in self.visited_functions
                                ):
                                    self.visited_functions.add(
                                        f"{current_file}:{attr_type}.{method_name}"
                                    )
                                    result["calls"] = self._trace_function_calls(
                                        node, current_file, attr_type
                                    )
                                break
                    else:
                        # Search for the class in all files
                        # First check if we've already indexed this class
                        if attr_type in self.class_file_map:
                            class_file = self.class_file_map[attr_type]
                            class_tree = self._parse_file(class_file)
                            class_node = self._find_class_in_tree(class_tree, attr_type)

                            if class_node:
                                for node in class_node.body:
                                    if (
                                        isinstance(node, ast.FunctionDef)
                                        and node.name == method_name
                                    ):
                                        result["file_path"] = class_file
                                        # Keep the qualified_name as "self.attr.method"
                                        result["found"] = True

                                        # Add function calls from this method
                                        if (
                                            f"{class_file}:{attr_type}.{method_name}"
                                            not in self.visited_functions
                                        ):
                                            self.visited_functions.add(
                                                f"{class_file}:{attr_type}.{method_name}"
                                            )
                                            result["calls"] = (
                                                self._trace_function_calls(
                                                    node, class_file, attr_type
                                                )
                                            )
                                        break
                        else:
                            # Search in all files in search paths
                            for search_path in self.search_paths:
                                for root, _, files in os.walk(search_path):
                                    for file in files:
                                        if file.endswith(".py"):
                                            file_path = os.path.join(root, file)
                                            file_path_abs = os.path.abspath(file_path)

                                            # Skip already visited files
                                            if file_path_abs in self.visited_files:
                                                continue

                                            self.visited_files.add(file_path_abs)

                                            # Parse the file
                                            tree = self._parse_file(file_path_abs)
                                            if not tree:
                                                continue

                                            # Look for the class
                                            class_node = self._find_class_in_tree(
                                                tree, attr_type
                                            )
                                            if class_node:
                                                self.class_file_map[attr_type] = (
                                                    file_path_abs
                                                )
                                                for node in class_node.body:
                                                    if (
                                                        isinstance(
                                                            node, ast.FunctionDef
                                                        )
                                                        and node.name == method_name
                                                    ):
                                                        result["file_path"] = (
                                                            file_path_abs
                                                        )
                                                        # Keep the qualified_name as
                                                        # "self.attr.method"
                                                        result["found"] = True

                                                        # Add function calls from this method
                                                        if (
                                                            f"{file_path_abs}:{attr_type}.{method_name}"    # pylint: disable=line-too-long
                                                            not in self.visited_functions
                                                        ):
                                                            self.visited_functions.add(
                                                                f"{file_path_abs}:{attr_type}.{method_name}"    # pylint: disable=line-too-long
                                                            )
                                                            result["calls"] = (
                                                                self._trace_function_calls(
                                                                    node,
                                                                    file_path_abs,
                                                                    attr_type,
                                                                )
                                                            )
                                                        break
                                                if result["found"]:
                                                    break
                                        if result["found"]:
                                            break
                                    if result["found"]:
                                        break
                                if result["found"]:
                                    break
            else:
                # If we can't determine the attribute type, search for any method with this name
                logger.warning(
                    f"Could not determine type of attribute {attr_name} in class {current_class}"
                )

                # First, check if the method is in the same file
                # This is a common case for utility classes
                tree = self._parse_file(current_file)
                for node in ast.walk(tree):
                    if isinstance(node, ast.ClassDef):
                        for item in node.body:
                            if (
                                isinstance(item, ast.FunctionDef)
                                and item.name == method_name
                            ):
                                result["file_path"] = current_file
                                # Keep the qualified_name as "self.attr.method"
                                result["found"] = True

                                # Add function calls from this method
                                if (
                                    f"{current_file}:{node.name}.{method_name}"
                                    not in self.visited_functions
                                ):
                                    self.visited_functions.add(
                                        f"{current_file}:{node.name}.{method_name}"
                                    )
                                    result["calls"] = self._trace_function_calls(
                                        item, current_file, node.name
                                    )
                                break
                        if result["found"]:
                            break

                # If not found in the current file, search in all files
                if not result["found"]:
                    for search_path in self.search_paths:
                        for root, _, files in os.walk(search_path):
                            for file in files:
                                if file.endswith(".py"):
                                    file_path = os.path.join(root, file)
                                    file_path_abs = os.path.abspath(file_path)

                                    # Skip already visited files
                                    if file_path_abs in self.visited_files:
                                        continue

                                    self.visited_files.add(file_path_abs)

                                    # Parse the file
                                    tree = self._parse_file(file_path_abs)
                                    if not tree:
                                        continue

                                    # Look for any class with the method
                                    for node in ast.walk(tree):
                                        if isinstance(node, ast.ClassDef):
                                            for item in node.body:
                                                if (
                                                    isinstance(item, ast.FunctionDef)
                                                    and item.name == method_name
                                                ):
                                                    result["file_path"] = file_path_abs
                                                    # Keep the qualified_name as "self.attr.method"
                                                    result["found"] = True

                                                    # Add function calls from this method
                                                    if (
                                                        f"{file_path_abs}:{node.name}.{method_name}"
                                                        not in self.visited_functions
                                                    ):
                                                        self.visited_functions.add(
                                                            f"{file_path_abs}:{node.name}.{method_name}"    # pylint: disable=line-too-long
                                                        )
                                                        result["calls"] = (
                                                            self._trace_function_calls(
                                                                item,
                                                                file_path_abs,
                                                                node.name,
                                                            )
                                                        )
                                                    break
                                            if result["found"]:
                                                break
                                    if result["found"]:
                                        break
                            if result["found"]:
                                break
                        if result["found"]:
                            break

        # Handle direct function calls
        elif call_type == "direct":
            # First, check if it's a function in the current file
            tree = self._parse_file(current_file)
            func_node = self._find_function_in_tree(tree, call_name)

            if func_node:
                result["file_path"] = current_file
                result["qualified_name"] = call_name
                result["found"] = True

                # Add function calls from this function
                if f"{current_file}:{call_name}" not in self.visited_functions:
                    self.visited_functions.add(f"{current_file}:{call_name}")
                    result["calls"] = self._trace_function_calls(
                        func_node, current_file
                    )
            else:
                # Check if it's an imported function
                imports = self._find_imports(tree)
                if call_name in imports:
                    module_name = imports[call_name]
                    module_path = self._find_module_path(module_name)

                    if module_path:
                        module_tree = self._parse_file(module_path)
                        if module_tree:
                            imported_func = self._find_function_in_tree(
                                module_tree, call_name
                            )
                            if imported_func:
                                result["file_path"] = module_path
                                result["qualified_name"] = f"{module_name}.{call_name}"
                                result["found"] = True

                                # Add function calls from this function
                                if (
                                    f"{module_path}:{call_name}"
                                    not in self.visited_functions
                                ):
                                    self.visited_functions.add(
                                        f"{module_path}:{call_name}"
                                    )
                                    result["calls"] = self._trace_function_calls(
                                        imported_func, module_path
                                    )
                else:
                    # Search in all files in search paths
                    for func_info in self._search_function_in_paths(call_name):
                        result["file_path"] = func_info["file_path"]
                        result["qualified_name"] = func_info["qualified_name"]
                        result["found"] = True
                        result["calls"] = func_info["calls"]
                        break

        # Handle attribute calls (module.func or obj.method)
        elif call_type == "attribute" or call_type == "nested_attribute":
            parts = call_name.split(".")
            module_or_obj = parts[0]

            # Check if it's an imported module
            tree = self._parse_file(current_file)
            imports = self._find_imports(tree)

            if module_or_obj in imports:
                module_name = imports[module_or_obj]
                # If it's a module, find the module path
                module_path = self._find_module_path(module_name)

                if module_path:
                    # If it's a module.function call
                    if len(parts) == 2:
                        func_name = parts[1]
                        module_tree = self._parse_file(module_path)
                        if module_tree:
                            func_node = self._find_function_in_tree(
                                module_tree, func_name
                            )
                            if func_node:
                                result["file_path"] = module_path
                                result["qualified_name"] = f"{module_name}.{func_name}"
                                result["found"] = True

                                # Add function calls from this function
                                if (
                                    f"{module_path}:{func_name}"
                                    not in self.visited_functions
                                ):
                                    self.visited_functions.add(
                                        f"{module_path}:{func_name}"
                                    )
                                    result["calls"] = self._trace_function_calls(
                                        func_node, module_path
                                    )
                    # If it's a module.class.method call
                    elif len(parts) == 3:
                        class_name = parts[1]
                        method_name = parts[2]
                        module_tree = self._parse_file(module_path)
                        if module_tree:
                            class_node = self._find_class_in_tree(
                                module_tree, class_name
                            )
                            if class_node:
                                for node in class_node.body:
                                    if (
                                        isinstance(node, ast.FunctionDef)
                                        and node.name == method_name
                                    ):
                                        result["file_path"] = module_path
                                        result["qualified_name"] = (
                                            f"{module_name}.{class_name}.{method_name}"
                                        )
                                        result["found"] = True

                                        # Add function calls from this method
                                        if (
                                            f"{module_path}:{class_name}.{method_name}"
                                            not in self.visited_functions
                                        ):
                                            self.visited_functions.add(
                                                f"{module_path}:{class_name}.{method_name}"
                                            )
                                            result["calls"] = (
                                                self._trace_function_calls(
                                                    node, module_path, class_name
                                                )
                                            )
                                        break
            else:
                # It might be a class instance method call
                # This is complex and would require type inference
                # For now, we'll just mark it as not found
                pass

        # Generate ID for this result
        result["id"] = self._generate_id(result)
        return result

    def _search_function_in_paths(self, function_name: str) -> List[Dict[str, Any]]:
        """
        Search for a function in all files in the search paths.

        Args:
            function_name: Name of the function to search for

        Returns:
            List of dictionaries with information about matching functions
        """
        results = []

        # Skip the original source file to avoid circular references
        source_file_abs = os.path.abspath(self.source_file)

        for search_path in self.search_paths:
            for root, _, files in os.walk(search_path):
                for file in files:
                    if file.endswith(".py"):
                        file_path = os.path.join(root, file)
                        file_path_abs = os.path.abspath(file_path)

                        # Skip the original source file
                        if file_path_abs == source_file_abs:
                            continue

                        # Skip already visited files
                        if file_path_abs in self.visited_files:
                            continue

                        self.visited_files.add(file_path_abs)

                        # Parse the file
                        tree = self._parse_file(file_path_abs)
                        if not tree:
                            continue

                        # Look for standalone function
                        func_node = self._find_function_in_tree(tree, function_name)
                        if func_node:
                            result = {
                                "file_path": file_path_abs,
                                "qualified_name": function_name,
                                "calls": [],
                            }

                            # Add function calls from this function
                            if (
                                f"{file_path_abs}:{function_name}"
                                not in self.visited_functions
                            ):
                                self.visited_functions.add(
                                    f"{file_path_abs}:{function_name}"
                                )
                                result["calls"] = self._trace_function_calls(
                                    func_node, file_path_abs
                                )

                            results.append(result)
                            continue

                        # Look for class methods
                        for node in ast.walk(tree):
                            if isinstance(node, ast.ClassDef):
                                for item in node.body:
                                    if (
                                        isinstance(item, ast.FunctionDef)
                                        and item.name == function_name
                                    ):
                                        result = {
                                            "file_path": file_path_abs,
                                            "qualified_name": f"{node.name}.{function_name}",
                                            "calls": [],
                                        }

                                        # Add function calls from this method
                                        if (
                                            f"{file_path_abs}:{node.name}.{function_name}"
                                            not in self.visited_functions
                                        ):
                                            self.visited_functions.add(
                                                f"{file_path_abs}:{node.name}.{function_name}"
                                            )
                                            result["calls"] = (
                                                self._trace_function_calls(
                                                    item, file_path_abs, node.name
                                                )
                                            )

                                        results.append(result)

        return results

    def _trace_function_calls(
        self,
        func_node: ast.FunctionDef,
        file_path: str,
        class_name: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Trace all function calls within a function.

        Args:
            func_node: Function definition node
            file_path: Path to the file containing the function
            class_name: Name of the class containing the function (if applicable)

        Returns:
            List of dictionaries with information about each function call
        """
        # Extract all function calls
        calls = self._extract_function_calls(func_node)

        # Resolve each call
        resolved_calls = []
        for call in calls:
            resolved = self._resolve_function_call(call, file_path, class_name)
            resolved_calls.append(resolved)

        return resolved_calls

    def _analyze_class_init(self, file_path: str, class_name: str) -> None:
        """
        Analyze a class's __init__ method to find attribute assignments.

        Args:
            file_path: Path to the file containing the class
            class_name: Name of the class to analyze
        """
        tree = self._parse_file(file_path)
        if not tree:
            return

        class_node = self._find_class_in_tree(tree, class_name)
        if not class_node:
            return

        # Find __init__ method
        init_method = None
        for node in class_node.body:
            if isinstance(node, ast.FunctionDef) and node.name == "__init__":
                init_method = node
                break

        if not init_method:
            return

        # Analyze attribute assignments
        class_attrs = {}
        for stmt in init_method.body:
            if isinstance(stmt, ast.Assign):
                for target in stmt.targets:
                    if (
                        isinstance(target, ast.Attribute)
                        and isinstance(target.value, ast.Name)
                        and target.value.id == "self"
                    ):
                        attr_name = target.attr

                        # Try to determine the type of the attribute
                        if isinstance(stmt.value, ast.Call):
                            if isinstance(stmt.value.func, ast.Name):
                                # Case: self.attr = ClassName()
                                class_attrs[attr_name] = stmt.value.func.id
                            elif isinstance(stmt.value.func, ast.Attribute):
                                # Case: self.attr = module.ClassName()
                                if isinstance(stmt.value.func.value, ast.Name):
                                    class_attrs[attr_name] = (
                                        f"{stmt.value.func.value.id}.{stmt.value.func.attr}"
                                    )

        # Store in the global map
        self.class_attribute_map[f"{file_path}:{class_name}"] = class_attrs

    def trace(self, entry_point: str) -> Dict[str, Any]:
        """
        Trace function calls starting from an entry point.

        Args:
            entry_point: Name of the function or method to start tracing from

        Returns:
            Dictionary with the call tree
        """
        logger.info(f"Starting trace from entry point: {entry_point}")

        # Reset visited sets
        self.visited_files = set([self.source_file])
        self.visited_functions = set()
        self.class_attribute_map = {}
        self.class_file_map = {}

        # Parse the source file
        tree = self._parse_file(self.source_file)
        if not tree:
            logger.error(f"Failed to parse source file: {self.source_file}")
            return {"error": f"Failed to parse source file: {self.source_file}"}

        # Find the entry point function
        func_node = None
        class_name = None

        # Check if entry_point is a method (Class.method)
        if "." in entry_point:
            class_name, method_name = entry_point.split(".", 1)
            class_node = self._find_class_in_tree(tree, class_name)

            if class_node:
                # Analyze class attributes
                self._analyze_class_init(self.source_file, class_name)

                for node in class_node.body:
                    if isinstance(node, ast.FunctionDef) and node.name == method_name:
                        func_node = node
                        break
        else:
            # Look for standalone function
            func_node = self._find_function_in_tree(tree, entry_point)

        if not func_node:
            logger.error(f"Entry point {entry_point} not found in {self.source_file}")
            return {
                "error": f"Entry point {entry_point} not found in {self.source_file}"
            }

        # Create the root node
        root = {
            "name": entry_point,
            "type": "entry_point",
            "file_path": self.source_file,
            "qualified_name": entry_point,
            "calls": [],
        }

        # Add the entry point to visited functions
        qualified_name = f"{class_name}.{method_name}" if class_name else entry_point
        self.visited_functions.add(f"{self.source_file}:{qualified_name}")

        # Trace function calls from the entry point
        root["calls"] = self._trace_function_calls(
            func_node, self.source_file, class_name
        )

        # Generate ID for the root
        root["id"] = self._generate_id(root)

        logger.info(f"Trace completed for entry point: {entry_point}")
        return root

    def display_trace(self, data: Dict[str, Any]) -> None:
        """
        Display the call tree in a human-readable format.

        Args:
            trace_result: Dictionary with the call tree
        """
        renderer_utils = RendererUtils(configuration=self._config)
        renderer = RendererFactory(configuration=self._config).get_renderer(
            module_name=renderer_utils.desired_renderer_module_name,
            class_name=renderer_utils.desired_renderer_class_name,
            data=data,
        )
        renderer.render()
