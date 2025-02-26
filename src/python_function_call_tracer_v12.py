import ast
import os
import sys
import argparse
import builtins
import json
from typing import Dict, List, Set, Tuple, Optional
from stdlib_list import stdlib_list


class FunctionCallVisitor(ast.NodeVisitor):
    """AST visitor to collect function calls within a function or method."""


class FunctionCallVisitor(ast.NodeVisitor):
    """AST visitor to collect function calls within a function or method."""

    def __init__(self):
        self.calls = []
        self.call_sources = {}  # Maps function calls to their source objects
        self.variable_sources = {}  # Maps variables to their source modules

    def visit_Assign(self, node):
        # Track variable assignments
        if isinstance(node.value, ast.Call) and isinstance(
            node.value.func, ast.Attribute
        ):
            if isinstance(node.value.func.value, ast.Name):
                # Case like: var = module.function()
                module_name = node.value.func.value.id
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        self.variable_sources[target.id] = module_name
        self.generic_visit(node)

    def visit_AnnAssign(self, node):
        # Track annotated assignments
        if (
            node.value
            and isinstance(node.value, ast.Call)
            and isinstance(node.value.func, ast.Attribute)
        ):
            if isinstance(node.value.func.value, ast.Name):
                # Case like: var: Type = module.function()
                module_name = node.value.func.value.id
                if isinstance(node.target, ast.Name):
                    self.variable_sources[node.target.id] = module_name
        self.generic_visit(node)

    def visit_Call(self, node):
        # Get the name of the function being called
        if isinstance(node.func, ast.Name):
            # Direct function call: function_name()
            self.calls.append(node.func.id)
            self.call_sources[node.func.id] = None
        elif isinstance(node.func, ast.Attribute):
            # Method call: object.method()
            if isinstance(node.func.value, ast.Name):
                # Store the object name as the source
                self.calls.append(node.func.attr)
                self.call_sources[node.func.attr] = node.func.value.id

                # Check if we know the source module of this object
                if node.func.value.id in self.variable_sources:
                    # This links the method call to the original module
                    self.call_sources[node.func.attr] = self.variable_sources[
                        node.func.value.id
                    ]
            else:
                self.calls.append(node.func.attr)
                self.call_sources[node.func.attr] = None

        # Continue visiting child nodes
        self.generic_visit(node)


class ModuleVisitor(ast.NodeVisitor):
    """AST visitor to collect module imports."""

    def __init__(self):
        self.imports = {}  # Dict[str, str] mapping imported name to module path
        self.import_aliases = (
            {}
        )  # Dict[str, str] mapping aliases to original module names
        self.all_imports = []  # List of all imported modules

    def visit_Import(self, node):
        for alias in node.names:
            # Regular import: import module
            if alias.asname:
                self.imports[alias.asname] = alias.name
                self.import_aliases[alias.asname] = alias.name
            else:
                self.imports[alias.name] = alias.name

            # Add to all_imports
            self.all_imports.append(alias.name)

    def visit_ImportFrom(self, node):
        module_path = node.module or ""
        for alias in node.names:
            # From import: from module import name
            if alias.asname:
                self.imports[alias.asname] = f"{module_path}.{alias.name}"
                self.import_aliases[alias.asname] = module_path
            else:
                self.imports[alias.name] = f"{module_path}.{alias.name}"
                self.import_aliases[alias.name] = module_path

            # Add to all_imports
            if module_path:
                self.all_imports.append(module_path)


class FunctionDefVisitor(ast.NodeVisitor):
    """AST visitor to collect all function and method definitions in a file with inheritance info."""

    def __init__(self):
        self.functions = {}  # Dict[str, ast.FunctionDef]
        self.classes = {}  # Dict[str, Dict[str, ast.FunctionDef]]
        self.class_hierarchy = (
            {}
        )  # Dict[str, List[str]] mapping class names to their base classes
        self.imports = {}  # Will be populated with import info
        self.import_aliases = {}  # Will be populated with import aliases
        self.all_imports = []  # Will be populated with all imported modules

    def visit_FunctionDef(self, node):
        # Store function definition
        self.functions[node.name] = node
        self.generic_visit(node)

    def visit_ClassDef(self, node):
        # Create dict for this class's methods
        class_methods = {}

        # Store all method definitions within this class
        for item in node.body:
            if isinstance(item, ast.FunctionDef):
                class_methods[item.name] = item

        # Store the class's base classes
        base_classes = []
        for base in node.bases:
            if isinstance(base, ast.Name):
                base_classes.append(base.id)
            elif isinstance(base, ast.Attribute):
                # Handle cases like module.ClassName
                base_classes.append(base.attr)

        self.class_hierarchy[node.name] = base_classes
        self.classes[node.name] = class_methods
        self.generic_visit(node)


class CallTracer:
    """Main class to trace function calls through Python source files with inheritance detection."""

    def __init__(self, base_directory: str, json_output: bool = False):
        self.base_directory = base_directory
        self.file_cache = {}  # Dict[str, Dict] to cache parsed files
        self.visited_calls = (
            set()
        )  # Set[Tuple[str, str]] to track visited (file, function) pairs
        self.class_methods_cache = (
            {}
        )  # Dict[str, Set[str]] to cache methods available in each class
        self.module_map = {}  # Dict[str, str] to map file paths to module names
        self.standard_library_modules = self._get_standard_library_modules()
        self.builtin_functions = set(dir(builtins))  # Get all built-in function names
        self.imported_libraries = set()  # Set to track all imported libraries
        self.json_output = json_output
        self.call_tree = {}  # For JSON output
        self.current_node = None  # For tracking current position in call tree

    def _get_standard_library_modules(self) -> Set[str]:
        """Get a set of standard library module names."""
        try:
            import stdlib_list

            return set(stdlib_list.stdlib_list())
        except ImportError:
            # Fallback to a basic list if stdlib_list is not available
            return {
                "os",
                "sys",
                "math",
                "re",
                "datetime",
                "time",
                "json",
                "csv",
                "random",
                "collections",
                "itertools",
                "functools",
                "pathlib",
                "shutil",
                "subprocess",
                "argparse",
                "logging",
                "unittest",
                "typing",
                "io",
                "pickle",
                "socket",
                "threading",
                "multiprocessing",
            }

    def get_module_name(self, file_path: str) -> str:
        """Determine the module name for a file path."""
        if file_path in self.module_map:
            return self.module_map[file_path]

        # Convert file path to module path
        rel_path = os.path.relpath(file_path, self.base_directory)
        if rel_path.startswith(".."):
            # File is outside base directory, use filename as module
            module_name = os.path.splitext(os.path.basename(file_path))[0]
        else:
            # Replace directory separators with dots and remove .py extension
            module_name = os.path.splitext(rel_path)[0].replace(os.path.sep, ".")

        self.module_map[file_path] = module_name
        return module_name

    def parse_file(self, file_path: str) -> Tuple[Dict, Dict, Dict, Dict, Dict, List]:
        """Parse a Python file and extract all function/method definitions and class hierarchies."""
        if file_path in self.file_cache:
            return self.file_cache[file_path]

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                source = f.read()

            tree = ast.parse(source)

            # Collect all imports
            import_visitor = ModuleVisitor()
            import_visitor.visit(tree)

            # Collect all function and method definitions
            visitor = FunctionDefVisitor()
            visitor.visit(tree)
            visitor.imports = import_visitor.imports
            visitor.import_aliases = import_visitor.import_aliases
            visitor.all_imports = import_visitor.all_imports

            # Add to imported libraries
            for imp in import_visitor.all_imports:
                self.imported_libraries.add(imp)

            # Store in cache
            result = (
                visitor.functions,
                visitor.classes,
                visitor.class_hierarchy,
                visitor.imports,
                visitor.import_aliases,
                visitor.all_imports,
            )
            self.file_cache[file_path] = result
            return result

        except Exception as e:
            print(f"Error parsing {file_path}: {e}")
            return {}, {}, {}, {}, {}, []

    def get_qualified_name(self, file_path: str, name: str) -> str:
        """Get the fully qualified name for a function or method."""
        module_name = self.get_module_name(file_path)

        if "." in name:
            # It's a method call (ClassName.method_name)
            class_name, method_name = name.split(".", 1)
            return f"{module_name}.{class_name}.{method_name}"
        else:
            # It's a function call
            return f"{module_name}.{name}"

    def get_all_methods_for_class(self, file_path: str, class_name: str) -> Set[str]:
        """Get all methods available in a class, including inherited ones."""
        cache_key = f"{file_path}:{class_name}"
        if cache_key in self.class_methods_cache:
            return self.class_methods_cache[cache_key]

        functions, classes, class_hierarchy, imports, _, _ = self.parse_file(file_path)

        # If class doesn't exist in this file
        if class_name not in classes:
            return set()

        # Start with methods defined directly in the class
        methods = set(classes[class_name].keys())

        # Add methods from base classes
        base_classes = class_hierarchy.get(class_name, [])
        for base in base_classes:
            # Check if base class is in the same file
            if base in classes:
                methods.update(self.get_all_methods_for_class(file_path, base))
            else:
                # Check if base class is imported
                if base in imports:
                    # Try to resolve the import
                    imported_path = imports[base]
                    base_file = self.find_file_for_import(
                        imported_path, os.path.dirname(file_path)
                    )
                    if base_file:
                        methods.update(self.get_all_methods_for_class(base_file, base))
                else:
                    # Search for base class in other files
                    base_file = self.find_file_for_class(
                        base, os.path.dirname(file_path)
                    )
                    if base_file:
                        methods.update(self.get_all_methods_for_class(base_file, base))

        # Cache and return
        self.class_methods_cache[cache_key] = methods
        return methods

    def is_inherited_method(
        self, file_path: str, class_name: str, method_name: str
    ) -> Tuple[bool, Optional[str], Optional[str]]:
        """Check if a method is inherited and return source class and file if it is."""
        functions, classes, class_hierarchy, imports, _, _ = self.parse_file(file_path)

        # If method is defined directly in the class, it's not inherited
        if class_name in classes and method_name in classes[class_name]:
            return False, None, None

        # Check base classes
        base_classes = class_hierarchy.get(class_name, [])
        for base in base_classes:
            # Check if base class is in the same file
            if base in classes and method_name in classes[base]:
                return True, base, file_path

            # Check if base is imported
            base_file = file_path
            if base in imports:
                imported_path = imports[base]
                base_file = self.find_file_for_import(
                    imported_path, os.path.dirname(file_path)
                )

            if not base_file or base not in classes:
                base_file = self.find_file_for_class(base, os.path.dirname(file_path))

            if not base_file:
                continue

            # Check if method is in this base class
            _, base_classes, _, _, _, _ = self.parse_file(base_file)
            if base in base_classes and method_name in base_classes[base]:
                return True, base, base_file

            # If not found in direct parent, check if it's in a grandparent
            is_inherited, source_class, source_file = self.is_inherited_method(
                base_file, base, method_name
            )
            if is_inherited:
                qualified_source = f"{base}.{source_class}" if source_class else base
                return True, qualified_source, source_file

        return False, None, None

    def find_file_for_import(
        self, import_path: str, starting_dir: str
    ) -> Optional[str]:
        """Find the file that contains a particular import."""
        # Split the import path
        parts = import_path.split(".")

        # Try to find the module in Python's standard paths
        try:
            # This assumes the module can be imported
            module_name = parts[0]
            try:
                # Try to find the module in the current directory first
                potential_file = os.path.join(starting_dir, f"{module_name}.py")
                if os.path.isfile(potential_file):
                    return potential_file

                # Check subdirectories
                for root, dirs, files in os.walk(self.base_directory):
                    for file in files:
                        if file == f"{module_name}.py":
                            return os.path.join(root, file)
            except Exception:
                pass
        except Exception:
            pass

        return None

    def find_function_in_file(
        self, file_path: str, function_name: str
    ) -> Tuple[Optional[ast.FunctionDef], Optional[str]]:
        """
        Find a function definition in a file.
        Returns (function_def, source_file) tuple.
        """
        functions, classes, _, _, _, _ = self.parse_file(file_path)

        # Check if it's a direct function
        if function_name in functions:
            return functions[function_name], file_path

        # Check if it's a method (format: ClassName.method_name)
        if "." in function_name:
            class_name, method_name = function_name.split(".", 1)
            if class_name in classes and method_name in classes[class_name]:
                return classes[class_name][method_name], file_path

            # Check if it's an inherited method
            is_inherited, source_class, source_file = self.is_inherited_method(
                file_path, class_name, method_name
            )
            if is_inherited and source_class and source_file:
                if "." in source_class:
                    # Handle multi-level inheritance
                    parts = source_class.split(".")
                    current_file = source_file
                    current_class = parts[-1]  # Get the last class in the chain

                    _, source_classes, _, _, _, _ = self.parse_file(current_file)
                    if (
                        current_class in source_classes
                        and method_name in source_classes[current_class]
                    ):
                        return source_classes[current_class][method_name], current_file
                else:
                    # Simple inheritance from a direct parent
                    _, source_classes, _, _, _, _ = self.parse_file(source_file)
                    if (
                        source_class in source_classes
                        and method_name in source_classes[source_class]
                    ):
                        return source_classes[source_class][method_name], source_file

        return None, None

    def find_file_for_class(self, class_name: str, starting_dir: str) -> Optional[str]:
        """Search for a file that contains the specified class."""
        for root, _, files in os.walk(starting_dir):
            for file in files:
                if file.endswith(".py"):
                    file_path = os.path.join(root, file)
                    _, classes, _, _, _, _ = self.parse_file(file_path)

                    if class_name in classes:
                        return file_path

        return None

    def find_file_for_function(
        self, function_name: str, starting_dir: str
    ) -> Optional[str]:
        """Search for a file that contains the specified function."""
        for root, _, files in os.walk(starting_dir):
            for file in files:
                if file.endswith(".py"):
                    file_path = os.path.join(root, file)
                    functions, classes, _, _, _, _ = self.parse_file(file_path)

                    # Check direct functions
                    if function_name in functions:
                        return file_path

                    # Check if it's a method (format: ClassName.method_name)
                    if "." in function_name:
                        class_name, method_name = function_name.split(".", 1)
                        if class_name in classes and method_name in classes[class_name]:
                            return file_path

                        # Check if it's an inherited method
                        is_inherited, _, _ = self.is_inherited_method(
                            file_path, class_name, method_name
                        )
                        if is_inherited:
                            return file_path

        return None

    def extract_calls_from_function(
        self, function_def: ast.FunctionDef
    ) -> Tuple[List[str], Dict[str, str]]:
        """Extract all function calls from a function definition."""
        visitor = FunctionCallVisitor()
        visitor.visit(function_def)
        return visitor.calls, visitor.call_sources

    def get_package_for_import(
        self, import_name: str, imports: Dict[str, str], import_aliases: Dict[str, str]
    ) -> str:
        """Determine the package name for an imported object."""
        if import_name in imports:
            # Direct import
            return imports[import_name].split(".")[0]
        elif import_name in import_aliases:
            # Aliased import
            return import_aliases[import_name]
        return ""

    def trace_calls(self, file_path: str, function_name: str, indent: int = 0) -> Dict:
        """Recursively trace function calls starting from the specified function."""
        # Create a unique key for this file+function pair
        key = (file_path, function_name)

        # Initialize node for JSON output
        node = {
            "name": function_name,
            "qualified_name": self.get_qualified_name(file_path, function_name),
            "file": file_path,
            "calls": [],
        }

        # Skip if we've already processed this function
        if key in self.visited_calls:
            node["status"] = "already_traced"
            if not self.json_output:
                qualified_name = self.get_qualified_name(file_path, function_name)
                print(f"{' ' * indent}↳ {qualified_name} (already traced)")
            return node

        self.visited_calls.add(key)

        # Get the qualified name
        qualified_name = self.get_qualified_name(file_path, function_name)

        # Check if it's a method and if it's inherited
        is_inherited_method = False
        inheritance_info = None
        source_file = None
        class_name = None

        if "." in function_name:
            class_name, method_name = function_name.split(".", 1)
            is_inherited, source_class, source_file_path = self.is_inherited_method(
                file_path, class_name, method_name
            )

            if is_inherited and source_class:
                is_inherited_method = True
                inheritance_info = source_class
                source_file = source_file_path
                node["inherited"] = True
                node["inherited_from"] = source_class
                node["source_file"] = source_file_path

        # Find the function definition
        function_def, func_source_file = self.find_function_in_file(
            file_path, function_name
        )
        if func_source_file and func_source_file != file_path:
            source_file = func_source_file
            qualified_name = self.get_qualified_name(source_file, function_name)
            node["source_file"] = func_source_file
            node["qualified_name"] = qualified_name

        if not function_def:
            if is_inherited_method:
                inherited_qualified = self.get_qualified_name(
                    source_file or file_path, inheritance_info
                )
                node["status"] = "not_found"
                node["inherited_qualified"] = inherited_qualified
                if not self.json_output:
                    print(
                        f"{' ' * indent}↳ {qualified_name} (inherited from {inherited_qualified}, definition not found)"
                    )
            else:
                node["status"] = "not_found"
                if not self.json_output:
                    print(f"{' ' * indent}↳ {qualified_name} (definition not found)")
            return node

        # Print function with inheritance information if applicable
        if is_inherited_method:
            inherited_qualified = self.get_qualified_name(
                source_file or file_path, inheritance_info
            )
            node["inherited_qualified"] = inherited_qualified
            if not self.json_output:
                print(
                    f"{' ' * indent}→ {qualified_name} (inherited from {inherited_qualified})"
                )
        else:
            if not self.json_output:
                print(f"{' ' * indent}→ {qualified_name}")

        # Extract all function calls within this function
        calls, call_sources = self.extract_calls_from_function(function_def)

        # The file where the function is actually defined
        actual_file = source_file or file_path

        # Get imports for this file
        _, classes, _, imports, import_aliases, _ = self.parse_file(actual_file)

        for call in calls:
            call_node = {"name": call}

            # Check if this is a built-in function
            if call in self.builtin_functions:
                # Check if it's also from an imported library
                source_obj = call_sources.get(call)
                if source_obj and (
                    source_obj in imports or source_obj in import_aliases
                ):
                    # It's both built-in and imported, show the import source
                    package_name = ""
                    if source_obj in import_aliases:
                        package_name = import_aliases[source_obj]
                    elif source_obj in imports:
                        package_name = imports[source_obj].split(".")[0]

                    if package_name:
                        call_node["type"] = "imported"
                        call_node["package"] = package_name
                        node["calls"].append(call_node)
                        if not self.json_output:
                            print(
                                f"{' ' * (indent + 2)}↳ {call} (imported from {package_name})"
                            )
                        continue

                # Otherwise, just show as built-in
                call_node["type"] = "built-in"
                node["calls"].append(call_node)
                if not self.json_output:
                    print(f"{' ' * (indent + 2)}↳ {call} (built-in)")
                continue

            # For method calls within a class, we need to qualify them
            if "." in function_name and not "." in call:
                # This is a method call within the same class
                current_class_name = function_name.split(".")[0]
                qualified_call = f"{current_class_name}.{call}"

                # Check if it exists as a method
                call_def, _ = self.find_function_in_file(actual_file, qualified_call)
                if call_def:
                    child_node = self.trace_calls(
                        actual_file, qualified_call, indent + 2
                    )
                    node["calls"].append(child_node)
                    continue

            # Check if the call exists in the current file
            call_def, call_source = self.find_function_in_file(actual_file, call)
            if call_def:
                # If it's a method but not qualified with class name, add the class name
                if (
                    not "." in call and call in classes.get(class_name, {})
                    if class_name
                    else False
                ):
                    qualified_call = f"{class_name}.{call}"
                    child_node = self.trace_calls(
                        call_source or actual_file, qualified_call, indent + 2
                    )
                    node["calls"].append(child_node)
                else:
                    child_node = self.trace_calls(
                        call_source or actual_file, call, indent + 2
                    )
                    node["calls"].append(child_node)
            else:
                # Check if this is a call on an imported object
                source_obj = call_sources.get(call)
                library_info = ""
                package_name = ""

                # Check if the source object is a built-in module
                if source_obj in self.standard_library_modules:
                    # Check if the method is a built-in function
                    try:
                        module = __import__(source_obj)
                        if hasattr(module, call) and callable(getattr(module, call)):
                            call_node["type"] = "imported"
                            call_node["package"] = source_obj
                            node["calls"].append(call_node)
                            if not self.json_output:
                                print(
                                    f"{' ' * (indent + 2)}↳ {source_obj}.{call} (imported from {source_obj})"
                                )
                            continue
                    except ImportError:
                        pass

                # Check if the source object is from an imported module
                if source_obj:
                    # First check if it's directly an imported module
                    if source_obj in import_aliases:
                        package_name = import_aliases[source_obj]
                        library_info = f" (imported from {package_name})"
                        call_node["type"] = "imported"
                        call_node["package"] = package_name
                    elif source_obj in imports:
                        package_name = imports[source_obj].split(".")[0]
                        library_info = f" (imported from {package_name})"
                        call_node["type"] = "imported"
                        call_node["package"] = package_name
                    else:
                        # Check if it's a variable that was assigned from an imported module
                        # This is a simplified approach - in a real solution we would need to track variable assignments
                        for var_name, var_source in call_sources.items():
                            if var_name == source_obj and var_source in imports:
                                package_name = imports[var_source].split(".")[0]
                                library_info = f" (imported from {package_name})"
                                call_node["type"] = "imported"
                                call_node["package"] = package_name
                                break
                            elif (
                                var_name == source_obj and var_source in import_aliases
                            ):
                                package_name = import_aliases[var_source]
                                library_info = f" (imported from {package_name})"
                                call_node["type"] = "imported"
                                call_node["package"] = package_name
                                break

                    # If it's a standard library module
                    if not package_name and source_obj in self.standard_library_modules:
                        package_name = source_obj
                        library_info = f" (imported from {package_name})"
                        call_node["type"] = "imported"
                        call_node["package"] = package_name

                # Search for the call in other files in the same directory
                call_file = self.find_file_for_function(
                    call, os.path.dirname(actual_file)
                )

                if call_file:
                    # Check if this is a method in another class
                    for cls_name, methods in classes.items():
                        if call in methods:
                            qualified_call = f"{cls_name}.{call}"
                            qualified_name = self.get_qualified_name(
                                call_file, qualified_call
                            )
                            call_node["qualified_name"] = qualified_name
                            call_node["file"] = call_file
                            call_node["type"] = "external"
                            if library_info:
                                call_node["library_info"] = library_info
                            if not self.json_output:
                                print(
                                    f"{' ' * (indent + 2)}↳ {qualified_name} (in {os.path.basename(call_file)}){library_info}"
                                )
                            child_node = self.trace_calls(
                                call_file, qualified_call, indent + 4
                            )
                            node["calls"].append(child_node)
                            break
                    else:
                        qualified_call = self.get_qualified_name(call_file, call)
                        call_node["qualified_name"] = qualified_call
                        call_node["file"] = call_file
                        call_node["type"] = "external"
                        if library_info:
                            call_node["library_info"] = library_info
                        if not self.json_output:
                            print(
                                f"{' ' * (indent + 2)}↳ {qualified_call} (in {os.path.basename(call_file)}){library_info}"
                            )
                        child_node = self.trace_calls(call_file, call, indent + 4)
                        node["calls"].append(child_node)
                else:
                    # Check if this is a method call on an object
                    if source_obj:
                        # Try to determine the class of the object
                        obj_class = None

                        # Check if it's a method call on self
                        if source_obj == "self" and class_name:
                            obj_class = class_name

                        # Check for methods on imported objects
                        if not library_info and source_obj in call_sources:
                            # Check if the object itself was created from an imported module
                            obj_source = call_sources.get(source_obj)
                            if obj_source in imports:
                                package_name = imports[obj_source].split(".")[0]
                                library_info = f" (imported from {package_name})"
                                call_node["type"] = "imported"
                                call_node["package"] = package_name
                            elif obj_source in import_aliases:
                                package_name = import_aliases[obj_source]
                                library_info = f" (imported from {package_name})"
                                call_node["type"] = "imported"
                                call_node["package"] = package_name

                        # Format the call with package name if available
                        if package_name and package_name != source_obj:
                            if obj_class:
                                call_node["type"] = "external"
                                call_node["status"] = "unresolved"
                                call_node["source_obj"] = source_obj
                                call_node["obj_class"] = obj_class
                                call_node["package"] = package_name
                                if not self.json_output:
                                    print(
                                        f"{' ' * (indent + 2)}↳ {package_name}.{obj_class}.{call} (external/unresolved){library_info}"
                                    )
                            else:
                                # Fix: Don't duplicate the function name
                                call_node["type"] = "external"
                                call_node["status"] = "unresolved"
                                call_node["source_obj"] = source_obj
                                call_node["package"] = package_name
                                if not self.json_output:
                                    print(
                                        f"{' ' * (indent + 2)}↳ {package_name}.{source_obj}.{call} (external/unresolved)"
                                    )
                        else:
                            if obj_class:
                                call_node["type"] = "external"
                                call_node["status"] = "unresolved"
                                call_node["obj_class"] = obj_class
                                if library_info:
                                    call_node["library_info"] = library_info
                                if not self.json_output:
                                    print(
                                        f"{' ' * (indent + 2)}↳ {obj_class}.{call} (external/unresolved){library_info}"
                                    )
                            else:
                                call_node["type"] = "external"
                                call_node["status"] = "unresolved"
                                call_node["source_obj"] = source_obj
                                if library_info:
                                    call_node["library_info"] = library_info
                                if not self.json_output:
                                    print(
                                        f"{' ' * (indent + 2)}↳ {source_obj}.{call} (external/unresolved){library_info}"
                                    )

                    else:
                        # Try to find if this is a direct import
                        if call in imports:
                            import_path = imports[call]
                            # Fix: Don't include the function name twice
                            call_node["type"] = "external"
                            call_node["status"] = "unresolved"
                            call_node["import_path"] = import_path
                            if not self.json_output:
                                print(
                                    f"{' ' * (indent + 2)}↳ {import_path} (external/unresolved)"
                                )
                        else:
                            call_node["type"] = "external"
                            call_node["status"] = "unresolved"
                            if library_info:
                                call_node["library_info"] = library_info
                            if not self.json_output:
                                print(
                                    f"{' ' * (indent + 2)}↳ {call} (external/unresolved){library_info}"
                                )

                    node["calls"].append(call_node)

        return node


def main():
    parser = argparse.ArgumentParser(
        description="Trace function calls in Python source files"
    )
    parser.add_argument("source_file", help="Path to the Python source file")
    parser.add_argument(
        "function_name",
        help="Name of the function to trace (use ClassName.method_name for methods)",
    )
    parser.add_argument("--json", action="store_true", help="Output results as JSON")

    args = parser.parse_args()

    source_file = os.path.abspath(args.source_file)
    function_name = args.function_name

    # Check if the source file exists
    if not os.path.isfile(source_file):
        print(f"Error: Source file '{source_file}' not found")
        sys.exit(1)

    # Initialize call tracer
    tracer = CallTracer(os.path.dirname(source_file), json_output=args.json)

    if not args.json:
        print(f"Tracing calls from '{function_name}' in {source_file}...")
        print("-" * 60)

    # Start tracing
    call_tree = tracer.trace_calls(source_file, function_name)

    if not args.json:
        print("-" * 60)
        print(
            f"Call tracing complete. Traced {len(tracer.visited_calls)} unique function calls."
        )

        # Print all imported libraries found during tracing
        if tracer.imported_libraries:
            print("\nImported libraries found during tracing:")
            for lib in sorted(tracer.imported_libraries):
                print(f"- {lib}")
    else:
        # Create the final JSON output
        result = {
            "source_file": source_file,
            "function_name": function_name,
            "unique_calls_count": len(tracer.visited_calls),
            "imported_libraries": sorted(list(tracer.imported_libraries)),
            "call_tree": call_tree,
        }
        print(json.dumps(result, indent=2))


if __name__ == "__main__":
    """
    python python_function_call_tracer_v12.py path/to/source.py function_name|ClassName.method_name
    # For JSON output:
    python python_function_call_tracer_v12.py path/to/source.py function_name|ClassName.method_name --json
    """
    main()
