import ast
import logging
from pathlib import Path
import sys

from utilities import GenericUtils, LoggingUtils, PathUtils


class SourceCodeNode:  # pylint: disable=too-few-public-methods
    # pylint: disable=line-too-long
    """
    A node in the source code tree representing a code element (module, class, function, or import).

    Attributes:
        name (str): The name of the code element
        type (str): The type of the code element (root, module, class, function, import, import_from)
        source_location (tuple, optional): Tuple of (line_number, column_offset, end_line_number)
        children (dict): Dictionary of child nodes keyed by their names

    """
    # pylint: enable=line-too-long

    def __init__(self, name, node_type, source_location=None):
        """
        Initialize a new SourceCodeNode.

        Args:
            name (str): The name of the code element
            node_type (str): The type of the code element
            source_location (tuple, optional): Source location information as (line, col, end_line)
        """
        self.name = name
        self.type = node_type
        self.source_location = source_location
        self.children = {}  # Use dict for easier management of unique children

    def add_child(self, child):
        """
        Add a child node to this node, ensuring uniqueness by name.

        Args:
            child (SourceCodeNode): The child node to add

        Returns:
            SourceCodeNode: The added child node or existing node if name already exists
        """
        # Ensure unique children by name
        if child.name not in self.children:
            self.children[child.name] = child
        return self.children[child.name]


class SourceCodeTreeBuilder(ast.NodeVisitor):
    """
    AST visitor that builds a tree representation of Python source code structure.
    Tracks imports, classes, and functions to create a hierarchical view of the code.

    Attributes:
        root (SourceCodeNode): The root node of the tree
        current_branch (list): Stack tracking the current position in the tree during traversal
    """

    def __init__(self):
        """
        Initialize a new SourceCodeTreeBuilder with an empty root node.
        """
        self.root = SourceCodeNode("Root", "root")
        self.current_branch = [self.root]

    def _add_module_to_tree(
        self, module_name, node_type="module", source_location=None
    ):
        """
        Add a module node to the tree, creating intermediate nodes as needed.

        Args:
            module_name (str): Dot-separated module path
            node_type (str, optional): Type of node. Defaults to "module"
            source_location (tuple, optional): Source location information

        Returns:
            SourceCodeNode: The leaf node that was added
        """
        # Split module name into parts
        parts = module_name.split(".")
        current_node = self.current_branch[-1]

        for part in parts:
            # Add or get existing child node
            current_node = current_node.add_child(
                SourceCodeNode(part, node_type, source_location)
            )

        return current_node

    def visit_Import(self, node):  # pylint: disable=invalid-name
        """
        Process an Import node in the AST.

        Args:
            node (ast.Import): The Import node to process
        """
        for alias in node.names:
            self._add_module_to_tree(
                alias.name,
                "import",
                source_location=(node.lineno, node.col_offset, node.end_lineno),
            )
        self.generic_visit(node)

    def visit_ImportFrom(self, node):  # pylint: disable=invalid-name
        """
        Process an ImportFrom node in the AST.

        Args:
            node (ast.ImportFrom): The ImportFrom node to process
        """
        module = node.module or ""
        for alias in node.names:
            full_name = f"{module}.{alias.name}" if module else alias.name
            self._add_module_to_tree(
                full_name,
                "import_from",
                source_location=(node.lineno, node.col_offset, node.end_lineno),
            )
        self.generic_visit(node)

    def visit_ClassDef(self, node):  # pylint: disable=invalid-name
        """
        Process a ClassDef node in the AST.

        Args:
            node (ast.ClassDef): The ClassDef node to process
        """
        # Create class node
        class_node = SourceCodeNode(
            node.name,
            "class",
            source_location=(node.lineno, node.col_offset, node.end_lineno),
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

    def visit_FunctionDef(self, node):  # pylint: disable=invalid-name
        """
        Process a FunctionDef node in the AST.

        Args:
            node (ast.FunctionDef): The FunctionDef node to process
        """
        # Create function node
        func_node = SourceCodeNode(
            node.name,
            "function",
            source_location=(node.lineno, node.col_offset, node.end_lineno),
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


class SourceCodeTreePrinter:
    """
    Prints the tree structure of the source code.

    Attributes:
        root (SourceCodeNode): The root node of the tree
    """

    def __init__(self, root):
        """
        Initialize a new SourceCodeTreePrinter with the root node of the tree.

        Args:
            root (SourceCodeNode): The root node of the tree
        """
        self.root = root

    def print_tree(self, node=None, indent=""):
        """
        Recursively print the tree structure starting from the given node.

        Args:
            node (SourceCodeNode, optional): The node to start printing from. Defaults to the root node.
            indent (str, optional): The indentation string for the current level. Defaults to "".
        """
        if node is None:
            node = self.root

        # Print the current node
        print(f"{indent}{node.name} ({node.type})")

        # Print children
        for child in node.children.values():
            self.print_tree(child, indent + "  ")


class SourceCodeTreeSearcher:
    """
    Searches for nodes in the source code tree by name.

    Attributes:
        root (SourceCodeNode): The root node of the tree
    """

    def __init__(self, root):
        """
        Initialize a new SourceCodeTreeSearcher with the root node of the tree.

        Args:
            root (SourceCodeNode): The root node of the tree
        """
        self.root = root

    def find_node(self, name, node=None):
        """
        Find a node in the tree by its name.

        Args:
            name (str): The name of the node to find
            node (SourceCodeNode, optional): The node to start searching from. Defaults to the root node.

        Returns:
            SourceCodeNode: The found node or None if not found
        """
        if node is None:
            node = self.root

        # Check if current node matches
        if node.name == name:
            return node

        # Search in children
        for child in node.children.values():
            found = self.find_node(name, child)
            if found:
                return found

        return None


class SourceCodeTracer:
    """
    Traces the execution of source code and records the execution path.

    Attributes:
        root (SourceCodeNode): The root node of the tree
        execution_path (list): List of nodes representing the execution path
    """

    def __init__(self):
        """
        Initialize a new SourceCodeTracer with the root node of the tree.

        Args:
            root (SourceCodeNode): The root node of the tree
        """
        self._logging_utils = LoggingUtils()
        self._path_utils = PathUtils()
        self.execution_path = []

    def tree_dumps(self, node) -> str:
        """
        Generate a string representation of the source code tree.

        Args:
            node (SourceCodeNode): The root node of the tree to dump

        Returns:
            str: A formatted string representation of the tree
        """
        self._logging_utils.debug(__name__, "start tree_dumps")
        self._logging_utils.debug(__name__, f"tree_dumps type(node): {type(node)}")
        tree_str_parts = []
        return self._tree_to_str(node, tree_str_parts)

    def _tree_to_str(self, node, tree_str_parts: list[str], prefix="", is_last=True):
        # pylint: disable=line-too-long
        """
        Recursively convert a tree node and its children to a string  with branch-like representation.

        Args:
            node (SourceCodeNode): The current node to process
            tree_str_parts (list[str]): List to accumulate string parts
            prefix (str, optional): Prefix for the current line. Defaults to ""
            is_last (bool, optional): Whether this is the last child. Defaults to True

        Returns:
            str: The complete string representation of the tree
        """
        # pylint: enable=line-too-long

        self._logging_utils.trace(__class__, "start _tree_to_str")
        self._logging_utils.debug(__class__, f"_tree_to_str type(node): {type(node)}")

        # Prepare line number and type string
        location_info = (
            f" (line {node.source_location[0]})" if node.source_location else ""
        )
        type_info = f"[{node.type}]"

        # Prepare prefix for current node
        connector = "└── " if is_last else "├── "
        tree_str_parts.append(
            f"{prefix}{connector}{node.name} {type_info}{location_info}"
        )

        # Prepare prefix for children
        child_prefix = prefix + ("    " if is_last else "│   ")

        # Get sorted children to ensure consistent output
        sorted_children = sorted(node.children.values(), key=lambda x: x.name)

        # Recursively print children
        for i, child in enumerate(sorted_children):
            is_child_last = i == len(sorted_children) - 1
            self._tree_to_str(child, tree_str_parts, child_prefix, is_child_last)

        return "\n".join(tree_str_parts)

    def build_source_tree(self, source_code: str):
        """
        Parse and analyze Python source code to build a tree representation.

        Args:
            source_code (str): The Python source code to analyze

        Returns:
            SourceCodeNode: The root node of the parsed source tree, or None if parsing fails
        """
        # Parse the source code
        tree_builder = SourceCodeTreeBuilder()
        try:
            parsed_ast = ast.parse(source_code)
            tree_builder.visit(parsed_ast)
        except SyntaxError as e:
            self._logging_utils.error(__class__, f"Error parsing source code: {e}")
            return None

        self._logging_utils.debug(
            __class__, f"tree_builder.root class: {type(tree_builder.root).__name__}"
        )
        return tree_builder.root

    def trace_source(self, node=None):
        """
        Trace the execution of the source code starting from the given node.

        Args:
            node (SourceCodeNode, optional): The node to start tracing from. Defaults to the root node.
        """
        if node is None:
            node = self.root

        # Add the current node to the execution path
        self.execution_path.append(node)

        # If the node has children, trace the first child
        if node.children:
            first_child = next(iter(node.children.values()))
            self.trace_source(first_child)

    def process_file(self, input_source_path: str, input_entry_point: str):
        """
        Process a single Python source file.

        Args:
            input_source_path (str): Path to the Python source file

        Returns:
            bool: True if processing succeeded, None otherwise
        """
        self._logging_utils.trace(__class__, "start process_file")
        self._logging_utils.debug(__class__, f"input_source_path: {input_source_path}")
        try:
            full_code = self._path_utils.get_ascii_file_contents(
                source_path=input_source_path
            )
            self._logging_utils.debug(__class__, f"full_code len: {len(full_code)}")
            if len(full_code) == 0:
                self._logging_utils.warning(__class__, "Source file is empty")
                return
        except Exception as e:  # pylint: disable=broad-exception-caught
            self._logging_utils.error(
                __class__, f"Failed to build source tree: {str(e)}", exc_info=True
            )
            raise Exception(f"Failed to build source tree: {str(e)}") from e

        self._logging_utils.success(
            __class__, f"\n# Source File: {Path(input_source_path).name}"
        )
        self._logging_utils.success(__class__, f"Full file path: '{input_source_path}'")

        source_tree = self.build_source_tree(source_code=full_code)
        self._logging_utils.debug(
            __class__,
            f"source_tree class: {type(source_tree).__name__} name: {type(source_tree).__name__}",  # pylint: disable=line-too-long
        )
        if not source_tree:
            return

        self._logging_utils.debug(
            __class__, f"source_tree: {type(source_tree).__name__}"
        )

        tree_printer = SourceCodeTreePrinter(root=source_tree)
        tree_printer.print_tree()

        parts = input_entry_point.split(".")
        print(parts)

        finder = SourceCodeTreeSearcher(root=source_tree)
        found_node = finder.find_node(name=parts[0], node=source_tree)
        if not found_node:
            print("not found")
            return

        self._logging_utils.debug(
            __class__,
            f"found_node: {found_node.name} type: {found_node.type}",
        )
        print("search found tree:")
        tree_printer.print_tree(node=found_node)
        if len(parts) > 1:
            # Find the function/method within the class
            found_function_node = finder.find_node(name=parts[1], node=found_node)
            if not found_function_node:
                print("function not found")
                return

            self._logging_utils.debug(
                __class__,
                f"found_function_node: {found_function_node.name} type: {found_function_node.type}",  # pylint: disable=line-too-long
            )
            tree_printer.print_tree(node=found_function_node)

            # self._logging_utils.success(__class__, "")
            # self._logging_utils.success(__class__, "## Source Code Tree Structure")
            # self._logging_utils.success(__class__, "```")
            # self._logging_utils.success(
            #     __class__, self.tree_dumps(node=source_tree)
            # )
            # self._logging_utils.success(__class__, "```")

        # except Exception as e:  # pylint: disable=broad-exception-caught
        #     self._logging_utils.error(
        #         __class__, f"Failed to build source tree: {str(e)}", exc_info=True
        #     )
        #     return


def main():
    logging_utils: LoggingUtils = LoggingUtils()
    logging_utils.trace(__name__, "start __main__")
    path_utils = PathUtils()
    if len(sys.argv) < 3:
        print("Usage: python trace_entry_point.py <source_path> <entry_point>")
        sys.exit(0)
    if len(sys.argv) > 3:
        print("Usage: python trace_entry_point.py <source_path> <entry_point>")
        sys.exit(1)

    logging_utils.info(__name__, "Starting...")
    source_path = sys.argv[1]
    entry_point = sys.argv[2]
    logging_utils.debug(
        __name__, f"source_path: {source_path} entry_point: {entry_point}"
    )
    tracer: SourceCodeTracer = SourceCodeTracer()

    if path_utils.is_file(source_path):
        logging_utils.debug(__name__, "Path(source_path)")
        logging_utils.debug(__name__, Path(source_path))
        tracer.process_file(source_path, entry_point)


if __name__ == "__main__":
    main()
