# pylint: disable=line-too-long
"""
Module for tracing function calls in Python source code.

This module provides functionality to trace function calls in Python source code,
starting from an entry point and recursively following the call chain. It can handle
calls to functions within the same file, imported functions, and functions in external
files within a specified search path.
"""
# pylint: enable=line-too-long

# FUTURE add check for required env vars

import ast
import os
import hashlib
from typing import Dict, List, Optional, Any

from call_tracer.renderers.renderer import RendererFactory, RendererUtils
from common.logging_utils import ClassLogger, LoggingUtils
from common.configuration import Configuration
from common.path_utils import PathUtils


class CallTracer:
    # pylint: disable=line-too-long
    """
    A class for tracing function calls in Python source code.

    This class analyzes Python source code to build a tree of function calls,
    starting from a specified entry point. It can trace calls within the same file,
    imported functions, and functions in external files within a specified search path.
    """
    # pylint: enable=line-too-long

    def __init__(self, configuration: Configuration, source_file: str, search_paths: List[str]):
        # pylint: disable=line-too-long
        """
        Initialize the CallTracer with a source file and search paths.

        Args:
            configuration: Configuration object containing settings for the call tracer
            source_file: Full path to the source file to analyze
            search_paths: List of paths to search for external modules
        """
        # pylint: enable=line-too-long
        self._config = configuration
        self._logger: ClassLogger = LoggingUtils().get_class_logger(self.__class__.__name__)
        self._path_utils = PathUtils()
        self.source_file = self._path_utils.abspath(source_file)
        self.search_paths = [self._path_utils.abspath(path) for path in search_paths]
        self.visited_files = set()
        self.visited_functions = set()
        self.module_cache = {}  # Cache for parsed modules
        self.import_map = {}  # Maps imported names to their modules
        self.class_attribute_map = {}  # Maps class attributes to their types
        self.class_file_map = {}  # Maps class names to their file paths

        # Node filtering configuration
        self.enable_node_filtering = self._config.bool_value('enable_node_filtering', False)

        print(f"Initialized CallTracer with source file: {self.source_file}")
        print(f"Search paths: {self.search_paths}")
        print(f"Node filtering enabled: {self.enable_node_filtering}")
        self._logger.debug("Configuration items:")
        self._logger.debug(str(configuration.items()), enable_pformat=False)

    def _is_builtin_function(self, func_name: str) -> bool:
        """
        Check if a function name is a built-in function.

        Args:
            func_name: Name of the function to check

        Returns:
            True if the function is a built-in, False otherwise
        """
        # Common built-in functions
        builtins = {
            'abs', 'all', 'any', 'ascii', 'bin', 'bool', 'bytearray', 'bytes',
            'callable', 'chr', 'classmethod', 'compile', 'complex', 'delattr',
            'dict', 'dir', 'divmod', 'enumerate', 'eval', 'exec', 'filter',
            'float', 'format', 'frozenset', 'getattr', 'globals', 'hasattr',
            'hash', 'help', 'hex', 'id', 'input', 'int', 'isinstance',
            'issubclass', 'iter', 'len', 'list', 'locals', 'map', 'max',
            'memoryview', 'min', 'next', 'object', 'oct', 'open', 'ord',
            'pow', 'print', 'property', 'range', 'repr', 'reversed', 'round',
            'set', 'setattr', 'slice', 'sorted', 'staticmethod', 'str', 'sum',
            'super', 'tuple', 'type', 'vars', 'zip', '__import__'
        }
        return func_name in builtins

    def _should_exclude_node(self, node_data: Dict[str, Any]) -> bool:
        """
        Determine if a node should be excluded based on filtering criteria.

        Args:
            node_data: Dictionary containing node information

        Returns:
            True if the node should be excluded, False otherwise
        """
        if not self.enable_node_filtering:
            return False

        # Check if it's a direct call to a built-in function
        if (node_data.get("type") == "direct" and
            self._is_builtin_function(node_data.get("name", ""))):
            return True

        # Only exclude leaf nodes (nodes with no children) that are not entry points
        # Entry points should never be filtered out
        if node_data.get("type") == "entry_point":
            return False

        # Check if the node has no children (empty calls list)
        # Only exclude if it's a leaf node AND it's a direct call
        calls = node_data.get("calls", [])
        if not calls and node_data.get("type") == "direct":
            return True

        return False

    def _create_node_signature(self, node: Dict[str, Any]) -> str:
        """
        Create a unique signature for a node based on its key properties.

        Args:
            node: Dictionary containing node information

        Returns:
            String signature that uniquely identifies the node
        """
        # Create signature based on name, type, and file_path
        # This identifies functionally equivalent nodes
        signature_parts = [
            node.get("name", ""),
            node.get("type", ""),
            node.get("file_path", ""),
            node.get("qualified_name", "")
        ]
        return "|".join(str(part) for part in signature_parts)

    def _eliminate_duplicate_siblings(self, nodes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Eliminate duplicate sibling nodes while preserving the tree structure.

        Args:
            nodes: List of sibling node dictionaries to process

        Returns:
            List of nodes with duplicate siblings removed
        """
        seen_signatures = set()
        unique_nodes = []

        for node in nodes:
            # Create a signature for this node
            node_signature = self._create_node_signature(node)

            # If we haven't seen this signature among siblings, include it
            if node_signature not in seen_signatures:
                seen_signatures.add(node_signature)

                # Create a copy of the node to avoid modifying the original
                unique_node = node.copy()

                # Recursively process children to eliminate duplicates at all levels
                if "calls" in unique_node and unique_node["calls"]:
                    unique_node["calls"] = self._eliminate_duplicate_siblings(unique_node["calls"])

                unique_nodes.append(unique_node)
            else:
                self._logger.debug(
                    f"Eliminating duplicate sibling: {node.get('name', 'unknown')} "
                    f"(type: {node.get('type', 'unknown')}, signature: {node_signature})")

        return unique_nodes

    def _filter_nodes(self, nodes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Filter out nodes based on exclusion criteria and recursively filter children.
        Also eliminates duplicate sibling nodes.

        Args:
            nodes: List of node dictionaries to filter

        Returns:
            Filtered list of nodes with duplicate siblings eliminated
        """
        filtered_nodes = []

        # First apply exclusion filtering if enabled
        if self.enable_node_filtering:
            for node in nodes:
                # Recursively filter children first
                if "calls" in node and node["calls"]:
                    node["calls"] = self._filter_nodes(node["calls"])

                # After filtering children, check if this node should be excluded
                if not self._should_exclude_node(node):
                    filtered_nodes.append(node)
                else:
                    self._logger.debug(
                        f"Excluding node: {node.get('name', 'unknown')} "
                        f"(type: {node.get('type', 'unknown')})")
        else:
            # If filtering is disabled, just recursively process children
            for node in nodes:
                node_copy = node.copy()
                if "calls" in node_copy and node_copy["calls"]:
                    node_copy["calls"] = self._filter_nodes(node_copy["calls"])
                filtered_nodes.append(node_copy)

        # Always eliminate duplicate siblings regardless of filtering setting
        return self._eliminate_duplicate_siblings(filtered_nodes)

    def _generate_id(self, data: Dict) -> str:
        # pylint: disable=line-too-long
        """
        Generate a unique ID for a dictionary using MD5 hash.

        Args:
            data: Dictionary to hash

        Returns:
            MD5 hash of the dictionary as a string
        """
        # pylint: enable=line-too-long
        # Create a copy to avoid modifying the original
        data_copy = data.copy()
        # Remove the id field if it exists to avoid circular reference
        if "id" in data_copy:
            del data_copy["id"]

        # Convert dictionary to string and hash
        data_str = str(sorted(data_copy.items()))
        return hashlib.md5(data_str.encode()).hexdigest()

    def _parse_file(self, file_path: str) -> ast.Module:
        # pylint: disable=line-too-long
        """
        Parse a Python file into an AST.

        Args:
            file_path: Path to the file to parse

        Returns:
            AST of the parsed file
        """
        # pylint: enable=line-too-long
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
            self._logger.error(f"Error parsing file {file_path}: {e}")
            return None

    def _index_classes_in_file(self, tree: ast.Module, file_path: str) -> None:
        # pylint: disable=line-too-long
        """
        Index all classes in a file for quick lookup.

        Args:
            tree: AST of a Python module
            file_path: Path to the file being analyzed
        """
        # pylint: enable=line-too-long
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                self.class_file_map[node.name] = file_path

    def _find_imports(self, tree: ast.Module) -> Dict[str, str]:
        # pylint: disable=line-too-long
        """
        Find all imports in an AST and map them to their module paths.

        Args:
            tree: AST of a Python module

        Returns:
            Dictionary mapping imported names to their module paths
        """
        # pylint: enable=line-too-long
        imports = {}

        class ImportVisitor(ast.NodeVisitor):
            """ Defines methods for processing Import-related nodes in an AST tree """
            def visit_Import(self, node):   # pylint: disable=invalid-name
                """ Visits an Import node in an AST tree. """
                for name in node.names:
                    alias = name.asname if name.asname else name.name
                    imports[alias] = name.name
                self.generic_visit(node)

            def visit_ImportFrom(self, node): # pylint: disable=invalid-name
                """ Visits an Import node in an AST tree. """
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
        self._logger.debug(f"Found imports: {imports}")
        return imports

    def _analyze_class_attributes(
        self, tree: ast.Module, file_path: str
    ) -> Dict[str, Dict[str, str]]:
        # pylint: disable=line-too-long
        """
        Analyze class attributes to determine their types.

        Args:
            tree: AST of a Python module
            file_path: Path to the file being analyzed

        Returns:
            Dictionary mapping class names to dictionaries of attribute names and their types
        """
        # pylint: enable=line-too-long

        class_attrs = {}

        class ClassAttributeVisitor(ast.NodeVisitor):
            """ Defines methods for processing Class-related nodes in an AST tree """
            def visit_ClassDef(self, node): # pylint: disable=invalid-name
                """ Visits a ClassDef node in an AST tree. """
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
                        elif isinstance(stmt, ast.AnnAssign):
                            # Get the target (left side of assignment)
                            target = stmt.target
                            if isinstance(target, ast.Name):
                                target_name = target.id
                            elif isinstance(target, ast.Attribute):
                                # Handle cases like self.attribute
                                # target_name = f"{ast.unparse(target.value)}.{target.attr}"
                                target_name = target.attr
                            else:
                                target_name = ast.unparse(target)

                            # Get the annotation (type hint)
                            annotation = stmt.annotation
                            if isinstance(annotation, ast.Name):
                                attr_name = annotation.id
                            elif isinstance(annotation, ast.Constant):
                                attr_name = repr(annotation.value)
                            else:
                                # For complex annotations, unparse the entire annotation
                                attr_name = ast.unparse(annotation)

                            attrs[target_name] = attr_name

                class_attrs[class_name] = attrs
                self.generic_visit(node)

        ClassAttributeVisitor().visit(tree)

        # Store in the global map with file path as context
        for class_name, attrs in class_attrs.items():
            self._logger.debug(f"Found class attrs: {class_name}")
            self._logger.debug(attrs, enable_pformat=True)
            self._logger.debug(f"file path: {file_path}")
            file_path = self.class_file_map.get(class_name, file_path)  # Use the file path from the global map
                                                                        # if available, otherwise use the provided one
            self.class_attribute_map[f"{file_path}:{class_name}"] = attrs

        self._logger.debug(f"class attribute map: {self.class_attribute_map}")
        self._logger.debug(f"Return class attrs: {class_attrs}")

        return class_attrs

    def _find_module_path(self, module_name: str) -> Optional[str]:
        # pylint: disable=line-too-long
        """
        Find the file path for a module name.

        Args:
            module_name: Name of the module to find

        Returns:
            File path of the module if found, None otherwise
        """
        # pylint: enable=line-too-long

        # Handle relative imports
        self._logger.debug(f"handle module path '{module_name}'")
        if module_name.startswith("."):
            parts = module_name.split(".")
            self._logger.debug(f"parts: {parts}")
            current_dir = self._path_utils.dirname(self.source_file)

            # Navigate up the directory tree based on the number of dots
            level = 1  # Default for relative imports starting with "relative."
            for _ in range(level):
                current_dir = self._path_utils.dirname(current_dir)
            self._logger.debug(f"current_dir: {current_dir}")

            # Reconstruct the module path
            module_path = self._path_utils.join(current_dir, *parts[1:-1])
            module_file = self._path_utils.join(module_path, f"{parts[-1]}.py")
            self._logger.debug(f"module_path: {module_path} module_file: {module_file}")

            return module_file if self._path_utils.file_exists(module_file) else None

        # Handle absolute imports
        module_path = module_name.replace(".", self._path_utils.sep)
        assert self.search_paths is not None
        self._logger.debug(f"module_path: {module_path}")

        self._logger.debug(f"len(search_paths): {len(self.search_paths)}")
        # Check in search paths
        for search_path in self.search_paths:
            self._logger.debug(f"search path: {search_path}")
            # Try as a direct module file
            potential_path = self._path_utils.join(search_path, f"{module_path}.py")
            self._logger.debug(f"potential path: {potential_path},{self._path_utils.file_exists(potential_path)}")

            if self._path_utils.file_exists(potential_path):
                self._logger.debug(f"potential path exists: {potential_path}")
                return potential_path

            # Try as a directory with __init__.py
            potential_dir = self._path_utils.join(search_path, module_path)
            self._logger.debug(f"potential dir: {potential_dir}")
            potential_init = self._path_utils.join(potential_dir, "__init__.py")
            self._logger.debug(f"potential init: {potential_init}")
            if self._path_utils.file_exists(potential_init):
                self._logger.debug(f"potential init exists: {potential_init}")
                return potential_init

            # Try as a directory without __init__.py
            if self._path_utils.is_dir(potential_dir):
                self._logger.debug(f"potential dir exists: {potential_dir}")
                return potential_dir

            # Try as a path to a module file
            parts = module_name.split(".")
            self._logger.debug(f"parts: {parts}")
            if len(parts) > 1:
                potential_module_path = f"{self._path_utils.join(search_path, *parts[:-1])}.py"
                self._logger.debug(f"potential module path: {potential_module_path}")
                if self._path_utils.file_exists(potential_module_path):
                    self._logger.debug(f"potential path exists: {potential_module_path}")
                    return potential_module_path

        self._logger.warning(f"Could not find module path for {module_name}")
        self._logger.debug(f"Could not find module path for {module_name}")
        return None

    def _find_function_in_tree(
        self, tree: ast.Module, function_name: str
    ) -> Optional[ast.FunctionDef]:
        # pylint: disable=line-too-long
        """
        Find a function definition in an AST.

        Args:
            tree: AST of a Python module
            function_name: Name of the function to find

        Returns:
            Function definition node if found, None otherwise
        """
        # pylint: enable=line-too-long
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
        # pylint: disable=line-too-long
        """
        Find a class definition in an AST.

        Args:
            tree: AST of a Python module
            class_name: Name of the class to find

        Returns:
            Class definition node if found, None otherwise
        """
        # pylint: enable=line-too-long
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef) and node.name == class_name:
                return node
        return None

    def _extract_function_calls(
        self, func_node: ast.FunctionDef
    ) -> List[Dict[str, Any]]:
        # pylint: disable=line-too-long
        """
        Extract all function calls from a function definition.

        Args:
            func_node: Function definition node

        Returns:
            List of dictionaries containing information about each function call
        """
        # pylint: enable=line-too-long
        calls = []

        class CallVisitor(ast.NodeVisitor):
            """ Defines methods for processing Call-related nodes in an AST tree """
            def visit_Call(self, node): # pylint: disable=invalid-name
                """ Visits Call node in an AST tree. """
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
        # pylint: disable=line-too-long
        """
        Resolve a function call to its definition.

        Args:
            call_info: Dictionary containing information about the function call
            current_file: Path to the file containing the call
            current_class: Name of the class containing the call (if applicable)

        Returns:
            Dictionary with information about the resolved function
        """
        # pylint: enable=line-too-long
        call_type = call_info["type"]
        call_name = call_info["name"]

        self._logger.debug(f"Resolving function call: {call_name} (type: {call_type})")

        # Initialize result with call information
        result = self._initialize_result_dict(call_info)

        # Resolve based on call type
        if call_type == "self" and current_class:
            self._resolve_self_method_call(result, call_name, current_file, current_class)
        elif call_type == "self_attribute" and current_class:
            self._resolve_self_attribute_method_call(result, call_name, current_file, current_class)
        elif call_type == "direct":
            self._resolve_direct_function_call(result, call_name, current_file)
        elif call_type in ["attribute", "nested_attribute"]:
            self._resolve_attribute_call(result, call_name, current_file)

        # Generate ID for this result
        result["id"] = self._generate_id(result)
        return result

    def _initialize_result_dict(self, call_info: Dict[str, Any]) -> Dict[str, Any]:
        # pylint: disable=line-too-long
        """
        Initialize the result dictionary with call information.

        Args:
            call_info: Dictionary containing information about the function call

        Returns:
            Dictionary initialized with basic call information
        """
        # pylint: enable=line-too-long
        return {
            "name": call_info["name"],
            "type": call_info["type"],
            "lineno": call_info["lineno"],
            "col_offset": call_info["col_offset"],
            "calls": [],
            "file_path": None,
            "qualified_name": None,
            "found": False,
        }

    def _resolve_self_method_call(
        self, result: Dict[str, Any], call_name: str, current_file: str, current_class: str
    ) -> None:
        # pylint: disable=line-too-long
        """
        Resolve a self.method() call.

        Args:
            result: Dictionary to store the resolution result
            call_name: Name of the method being called
            current_file: Path to the file containing the call
            current_class: Name of the class containing the call
        """
        # pylint: enable=line-too-long
        tree = self._parse_file(current_file)
        class_node = self._find_class_in_tree(tree, current_class)

        if class_node:
            for node in class_node.body:
                if isinstance(node, ast.FunctionDef) and node.name == call_name:
                    result["file_path"] = current_file
                    result["qualified_name"] = f"{current_class}.{call_name}"
                    result["found"] = True

                    # Add function calls from this method
                    function_key = f"{current_file}:{current_class}.{call_name}"
                    if function_key not in self.visited_functions:
                        self.visited_functions.add(function_key)
                        calls = self._trace_function_calls(
                            node, current_file, current_class
                        )
                        # Apply filtering if enabled
                        result["calls"] = self._filter_nodes(calls)
                    break

    def _resolve_self_attribute_method_call(
        self, result: Dict[str, Any], call_name: str, current_file: str, current_class: str
    ) -> None:
        # pylint: disable=line-too-long
        """
        Resolve a self.attribute.method() call.

        Args:
            result: Dictionary to store the resolution result
            call_name: Name of the attribute method being called (in the format "attribute.method")
            current_file: Path to the file containing the call
            current_class: Name of the class containing the call
        """
        # pylint: enable=line-too-long
        # Set the qualified name to include "self."
        result["qualified_name"] = f"self.{call_name}"

        # First, analyze class attributes to find the type of the attribute
        tree = self._parse_file(current_file)
        self._analyze_class_attributes(tree, current_file)

        # Get the attribute and method name
        attr_name, method_name = call_name.split(".", 1)

        # Look up the attribute type in our class attribute map
        class_attrs = self.class_attribute_map.get(f"{current_file}:{current_class}", {})
        self._logger.debug(f"path: {current_file}:{current_class} class_attrs: {class_attrs}")
        attr_type = class_attrs.get(attr_name)

        if attr_type:
            self._logger.debug(f"Found attribute type for {attr_name}: {attr_type}")
            self._resolve_known_attribute_type(result, attr_type, method_name, tree, current_file)
        else:
            self._logger.debug(f"unknown attr_type for '{attr_name}'")
            self._resolve_unknown_attribute_type(
                result, attr_name, method_name, current_class, current_file
            )

    def _resolve_known_attribute_type(
        self, result: Dict[str, Any], attr_type: str, method_name: str, tree, current_file: str
    ) -> None:
        # pylint: disable=line-too-long
        """
        Resolve method when attribute type is known.

        Args:
            result: Dictionary to store the resolution result
            attr_type: Type of the attribute
            method_name: Name of the method being called
            tree: AST of the current file
            current_file: Path to the current file
        """
        # pylint: enable=line-too-long
        # If the attribute type is an imported class
        imports = self._find_imports(tree)
        if "." in attr_type and attr_type.split(".")[0] in imports:
            self._resolve_imported_class_method(
                result, attr_type, method_name, imports, current_file
            )
        else:
            # Check if the class is defined in the current file
            class_node = self._find_class_in_tree(tree, attr_type)
            if class_node:
                self._resolve_method_in_class_node(
                    result, class_node, method_name, current_file, attr_type
                )
            else:
                # Search for the class in all files
                self._search_class_in_all_files(result, attr_type, method_name)

    def _resolve_imported_class_method(
        self, result: Dict[str, Any], attr_type: str, method_name: str, imports: Dict,
        current_file: str   # pylint: disable=unused-argument
    ) -> None:
        # pylint: disable=line-too-long
        """
        Resolve method from an imported class.

        Args:
            result: Dictionary to store the resolution result
            attr_type: Type of the attribute (in the format "module.class")
            method_name: Name of the method being called
            imports: Dictionary of imports in the current file
            current_file: Path to the current file
        """
        # pylint: enable=line-too-long
        module_name = imports[attr_type.split(".")[0]]
        class_name = attr_type.split(".")[1]
        module_path = self._find_module_path(module_name)

        if module_path:
            module_tree = self._parse_file(module_path)
            if module_tree:
                class_node = self._find_class_in_tree(module_tree, class_name)
                if class_node:
                    self._resolve_method_in_class_node(
                        result, class_node, method_name, module_path, class_name
                    )

    def _resolve_method_in_class_node(
        self, result: Dict[str, Any], class_node, method_name: str, file_path: str, class_name: str
    ) -> None:
        # pylint: disable=line-too-long
        """
        Find and resolve a method in a class node.

        Args:
            result: Dictionary to store the resolution result
            class_node: AST node of the class
            method_name: Name of the method being called
            file_path: Path to the file containing the class
            class_name: Name of the class
        """
        # pylint: enable=line-too-long
        for node in class_node.body:
            if isinstance(node, ast.FunctionDef) and node.name == method_name:
                result["file_path"] = file_path
                result["found"] = True

                # Add function calls from this method
                function_key = f"{file_path}:{class_name}.{method_name}"
                if function_key not in self.visited_functions:
                    self.visited_functions.add(function_key)
                    calls = self._trace_function_calls(node, file_path, class_name)
                    # Apply filtering if enabled
                    result["calls"] = self._filter_nodes(calls)
                break

    def _search_class_in_all_files(
        self, result: Dict[str, Any], attr_type: str, method_name: str
    ) -> None:
        # pylint: disable=line-too-long
        """
        Search for a class in all files and resolve its method.

        Args:
            result: Dictionary to store the resolution result
            attr_type: Type of the attribute (class name)
            method_name: Name of the method being called
        """
        # pylint: enable=line-too-long
        # First check if we've already indexed this class
        if attr_type in self.class_file_map:
            class_file = self.class_file_map[attr_type]
            class_tree = self._parse_file(class_file)
            class_node = self._find_class_in_tree(class_tree, attr_type)

            if class_node:
                self._resolve_method_in_class_node(
                    result, class_node, method_name, class_file, attr_type
                )
        else:
            # Search in all files in search paths
            self._search_class_in_search_paths(result, attr_type, method_name)

    def _search_class_in_search_paths(
        self, result: Dict[str, Any], attr_type: str, method_name: str
    ) -> None:
        # pylint: disable=line-too-long
        """
        Search for a class in all search paths.

        Args:
            result: Dictionary to store the resolution result
            attr_type: Type of the attribute (class name)
            method_name: Name of the method being called
        """
        # pylint: enable=line-too-long
        for search_path in self.search_paths:
            if self._search_class_in_path(result, attr_type, method_name, search_path):
                break

    def _search_class_in_path(
        self, result: Dict[str, Any], attr_type: str, method_name: str, search_path: str
    ) -> bool:
        # pylint: disable=line-too-long
        """
        Search for a class in a specific path.

        Args:
            result: Dictionary to store the resolution result
            attr_type: Type of the attribute (class name)
            method_name: Name of the method being called
            search_path: Path to search in

        Returns:
            True if the class and method were found, False otherwise
        """
        # pylint: enable=line-too-long
        for root, _, files in os.walk(search_path):
            for file in files:
                if file.endswith(".py"):
                    file_path = self._path_utils.join(root, file)
                    file_path_abs = self._path_utils.abspath(file_path)

                    # Skip already visited files
                    if file_path_abs in self.visited_files:
                        continue

                    self.visited_files.add(file_path_abs)

                    # Parse the file
                    tree = self._parse_file(file_path_abs)
                    if not tree:
                        continue

                    # Look for the class
                    class_node = self._find_class_in_tree(tree, attr_type)
                    if class_node:
                        self.class_file_map[attr_type] = file_path_abs
                        self._resolve_method_in_class_node(
                            result, class_node, method_name, file_path_abs, attr_type
                        )
                        if result["found"]:
                            return True
        return False

    def _resolve_unknown_attribute_type(
        self, result: Dict[str, Any], attr_name: str, method_name: str, current_class: str,
        current_file: str
    ) -> None:
        # pylint: disable=line-too-long
        """
        Resolve method when attribute type is unknown.

        Args:
            result: Dictionary to store the resolution result
            attr_name: Name of the attribute
            method_name: Name of the method being called
            current_class: Name of the class containing the call
            current_file: Path to the file containing the call
        """
        # pylint: enable=line-too-long
        self._logger.warning(
            f"Could not determine type of attribute {attr_name} "
            f"in class {current_class}"
        )
        self._logger.debug(
            f"Could not determine type of attribute {attr_name} "
            f"in class {current_class}"
        )

        # First, check if the method is in the same file
        if self._search_method_in_current_file(result, method_name, current_file):
            return

        # If not found in the current file, search in all files
        if not result["found"]:
            self._search_method_in_all_files(result, method_name)

    def _search_method_in_current_file(
        self, result: Dict[str, Any], method_name: str, current_file: str
    ) -> bool:
        # pylint: disable=line-too-long
        """
        Search for a method in the current file.

        Args:
            result: Dictionary to store the resolution result
            method_name: Name of the method being called
            current_file: Path to the current file

        Returns:
            True if the method was found, False otherwise
        """
        # pylint: enable=line-too-long
        tree = self._parse_file(current_file)
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                for item in node.body:
                    if isinstance(item, ast.FunctionDef) and item.name == method_name:
                        result["file_path"] = current_file
                        result["found"] = True

                        # Add function calls from this method
                        function_key = f"{current_file}:{node.name}.{method_name}"
                        if function_key not in self.visited_functions:
                            self.visited_functions.add(function_key)
                            calls = self._trace_function_calls(
                                item, current_file, node.name
                            )
                            # Apply filtering if enabled
                            result["calls"] = self._filter_nodes(calls)
                        return True
        return False

    def _search_method_in_all_files(self, result: Dict[str, Any], method_name: str) -> None:
        # pylint: disable=line-too-long
        """
        Search for a method in all files.

        Args:
            result: Dictionary to store the resolution result
            method_name: Name of the method being called
        """
        # pylint: enable=line-too-long
        for search_path in self.search_paths:
            if self._search_method_in_path(result, method_name, search_path):
                break

    def _search_method_in_path(self,
        result: Dict[str, Any], method_name: str, search_path: str) -> bool:
        # pylint: disable=line-too-long
        """
        Search for a method in a specific path.

        Args:
            result: Dictionary to store the resolution result
            method_name: Name of the method being called
            search_path: Path to search in

        Returns:
            True if the method was found, False otherwise
        """
        # pylint: enable=line-too-long
        for root, _, files in os.walk(search_path):
            for file in files:
                if file.endswith(".py"):
                    file_path = self._path_utils.join(root, file)
                    file_path_abs = self._path_utils.abspath(file_path)

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
                                if isinstance(item, ast.FunctionDef) and item.name == method_name:
                                    result["file_path"] = file_path_abs
                                    result["found"] = True

                                    # Add function calls from this method
                                    function_key = f"{file_path_abs}:{node.name}.{method_name}"
                                    if function_key not in self.visited_functions:
                                        self.visited_functions.add(function_key)
                                        calls = self._trace_function_calls(
                                            item, file_path_abs, node.name
                                        )
                                        # Apply filtering if enabled
                                        result["calls"] = self._filter_nodes(calls)
                                    return True
        return False

    def _resolve_direct_function_call(
        self, result: Dict[str, Any], call_name: str, current_file: str
    ) -> None:
        # pylint: disable=line-too-long
        """
        Resolve a direct function call.

        Args:
            result: Dictionary to store the resolution result
            call_name: Name of the function being called
            current_file: Path to the file containing the call
        """
        # pylint: enable=line-too-long
        # First, check if it's a function in the current file
        tree = self._parse_file(current_file)
        func_node = self._find_function_in_tree(tree, call_name)

        if func_node:
            result["file_path"] = current_file
            result["qualified_name"] = call_name
            result["found"] = True

            # Add function calls from this function
            function_key = f"{current_file}:{call_name}"
            if function_key not in self.visited_functions:
                self.visited_functions.add(function_key)
                calls = self._trace_function_calls(func_node, current_file)
                # Apply filtering if enabled
                result["calls"] = self._filter_nodes(calls)
        else:
            self._resolve_imported_or_external_function(result, call_name, tree, current_file)

    def _resolve_imported_or_external_function(
        self, result: Dict[str, Any], call_name: str, tree, current_file: str   # pylint: disable=unused-argument
    ) -> None:
        # pylint: disable=line-too-long
        """
        Resolve an imported function or search in external files.

        Args:
            result: Dictionary to store the resolution result
            call_name: Name of the function being called
            tree: AST of the current file
            current_file: Path to the current file
        """
        # pylint: enable=line-too-long
        # Check if it's an imported function
        imports = self._find_imports(tree)
        if call_name in imports:
            self._resolve_imported_function(result, call_name, imports)
        else:
            # Search in all files in search paths
            for func_info in self._search_function_in_paths(call_name):
                result["file_path"] = func_info["file_path"]
                result["qualified_name"] = func_info["qualified_name"]
                result["found"] = True
                # Apply filtering if enabled
                result["calls"] = self._filter_nodes(func_info["calls"])
                break

    def _resolve_imported_function(
        self, result: Dict[str, Any], call_name: str, imports: Dict
    ) -> None:
        # pylint: disable=line-too-long
        """
        Resolve an imported function.

        Args:
            result: Dictionary to store the resolution result
            call_name: Name of the function being called
            imports: Dictionary of imports in the current file
        """
        # pylint: enable=line-too-long
        module_name = imports[call_name]
        module_path = self._find_module_path(module_name)

        if module_path:
            module_tree = self._parse_file(module_path)
            if module_tree:
                imported_func = self._find_function_in_tree(module_tree, call_name)
                if imported_func:
                    result["file_path"] = module_path
                    result["qualified_name"] = f"{module_name}.{call_name}"
                    result["found"] = True

                    # Add function calls from this function
                    function_key = f"{module_path}:{call_name}"
                    if function_key not in self.visited_functions:
                        self.visited_functions.add(function_key)
                        calls = self._trace_function_calls(imported_func, module_path)
                        # Apply filtering if enabled
                        result["calls"] = self._filter_nodes(calls)

    def _resolve_attribute_call(
        self, result: Dict[str, Any], call_name: str, current_file: str
    ) -> None:
        # pylint: disable=line-too-long
        """
        Resolve an attribute call (module.func or obj.method).

        Args:
            result: Dictionary to store the resolution result
            call_name: Name of the attribute call (in the format "module.func" or "obj.method")
            current_file: Path to the file containing the call
        """
        # pylint: enable=line-too-long
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
                    self._resolve_module_function_call(result, parts[1], module_name, module_path)
                # If it's a module.class.method call
                elif len(parts) == 3:
                    self._resolve_module_class_method_call(
                        result, parts[1], parts[2], module_name, module_path
                    )
        else:
            # It might be a class instance method call
            # This is complex and would require type inference
            # For now, we'll just mark it as not found
            pass

    def _resolve_module_function_call(
        self, result: Dict[str, Any], func_name: str, module_name: str, module_path: str
    ) -> None:
        # pylint: disable=line-too-long
        """
        Resolve a module.function call.

        Args:
            result: Dictionary to store the resolution result
            func_name: Name of the function being called
            module_name: Name of the module containing the function
            module_path: Path to the module file
        """
        # pylint: enable=line-too-long
        module_tree = self._parse_file(module_path)
        if module_tree:
            func_node = self._find_function_in_tree(module_tree, func_name)
            if func_node:
                result["file_path"] = module_path
                result["qualified_name"] = f"{module_name}.{func_name}"
                result["found"] = True

                # Add function calls from this function
                function_key = f"{module_path}:{func_name}"
                if function_key not in self.visited_functions:
                    self.visited_functions.add(function_key)
                    calls = self._trace_function_calls(func_node, module_path)
                    # Apply filtering if enabled
                    result["calls"] = self._filter_nodes(calls)

    def _resolve_module_class_method_call(
        self, result: Dict[str, Any], class_name: str,
        method_name: str, module_name: str, module_path: str
    ) -> None:
        # pylint: disable=line-too-long
        """
        Resolve a module.class.method call.

        Args:
            result: Dictionary to store the resolution result
            class_name: Name of the class containing the method
            method_name: Name of the method being called
            module_name: Name of the module containing the class
            module_path: Path to the module file
        """
        # pylint: enable=line-too-long
        module_tree = self._parse_file(module_path)
        if module_tree:
            class_node = self._find_class_in_tree(module_tree, class_name)
            if class_node:
                for node in class_node.body:
                    if isinstance(node, ast.FunctionDef) and node.name == method_name:
                        result["file_path"] = module_path
                        result["qualified_name"] = f"{module_name}.{class_name}.{method_name}"
                        result["found"] = True

                        # Add function calls from this method
                        function_key = f"{module_path}:{class_name}.{method_name}"
                        if function_key not in self.visited_functions:
                            self.visited_functions.add(function_key)
                            calls = self._trace_function_calls(
                                node, module_path, class_name
                            )
                            # Apply filtering if enabled
                            result["calls"] = self._filter_nodes(calls)
                        break

    def _search_function_in_paths(self, function_name: str) -> List[Dict[str, Any]]:
        # pylint: disable=line-too-long
        """
        Search for a function in all files in the search paths.

        Args:
            function_name: Name of the function to search for

        Returns:
            List of dictionaries with information about matching functions
        """
        # pylint: enable=line-too-long
        results = []

        # Skip the original source file to avoid circular references
        source_file_abs = self._path_utils.abspath(self.source_file)

        for search_path in self.search_paths:
            for root, _, files in os.walk(search_path):
                for file in files:
                    if file.endswith(".py"):
                        file_path = self._path_utils.join(root, file)
                        file_path_abs = self._path_utils.abspath(file_path)

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
                                calls = self._trace_function_calls(
                                    func_node, file_path_abs
                                )
                                # Apply filtering if enabled
                                result["calls"] = self._filter_nodes(calls)

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
                                            calls = self._trace_function_calls(
                                                item, file_path_abs, node.name
                                            )
                                            # Apply filtering if enabled
                                            result["calls"] = self._filter_nodes(calls)

                                        results.append(result)

        return results

    def _trace_function_calls(
        self,
        func_node: ast.FunctionDef,
        file_path: str,
        class_name: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        # pylint: disable=line-too-long
        """
        Trace all function calls within a function.

        Args:
            func_node: Function definition node
            file_path: Path to the file containing the function
            class_name: Name of the class containing the function (if applicable)

        Returns:
            List of dictionaries with information about each function call
        """
        # pylint: enable=line-too-long
        # Extract all function calls
        calls = self._extract_function_calls(func_node)

        # Resolve each call
        resolved_calls = []
        for call in calls:
            resolved = self._resolve_function_call(call, file_path, class_name)
            resolved_calls.append(resolved)

        return resolved_calls

    def _analyze_class_init(self, file_path: str, class_name: str) -> None:
        # pylint: disable=line-too-long
        """
        Analyze a class's __init__ method to find attribute assignments.

        Args:
            file_path: Path to the file containing the class
            class_name: Name of the class to analyze
        """
        # pylint: enable=line-too-long
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
        # pylint: disable=line-too-long
        """
        Trace function calls starting from an entry point.

        Args:
            entry_point: Name of the function or method to start tracing from

        Returns:
            Dictionary with the call tree
        """
        # pylint: enable=line-too-long
        print(f"Starting trace from entry point: {entry_point}")

        # Reset visited sets
        self.visited_files = set([self.source_file])
        self.visited_functions = set()
        self.class_attribute_map = {}
        self.class_file_map = {}

        # Parse the source file
        tree = self._parse_file(self.source_file)
        if not tree:
            self._logger.error(f"Failed to parse source file: {self.source_file}")
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
            self._logger.error(f"Entry point {entry_point} not found in {self.source_file}")
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
        calls = self._trace_function_calls(
            func_node, self.source_file, class_name
        )

        # Apply filtering if enabled
        root["calls"] = self._filter_nodes(calls)

        # Generate ID for the root
        root["id"] = self._generate_id(root)

        print(f"Trace completed for entry point: {entry_point}")
        return root

    def display_trace(self, data: Dict[str, Any]) -> None:
        # pylint: disable=line-too-long
        """
        Display the call tree in a human-readable format.

        Args:
            data: Dictionary with the call tree
        """
        # pylint: enable=line-too-long
        renderer_utils = RendererUtils(configuration=self._config)
        renderer = RendererFactory(configuration=self._config).get_renderer(
            module_name=renderer_utils.desired_renderer_module_name,
            class_name=renderer_utils.desired_renderer_class_name,
            data=data,
        )
        renderer.render()
