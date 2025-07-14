# Call Tracer Logic Explanation

## Overview

This Python code implements a call tracer tool designed to analyze Python source code and build comprehensive function call trees starting from specified entry points. The tool uses Abstract Syntax Tree (AST) parsing to recursively trace function calls across files, handling complex scenarios including class methods, imported functions, attribute method calls, and cross-file dependencies. It provides configurable filtering options and flexible output rendering to help developers understand code execution flow and dependencies.

## Main Components and Logic Flow

### Core Classes

- **CallTracer**: The main analysis class that orchestrates the entire tracing process.
  - Initializes with source file, entry point, and search paths for module resolution.
  - Manages AST parsing and caching for performance optimization.
  - Tracks visited files and functions to prevent infinite recursion.
  - Provides configurable node filtering and duplicate elimination.
  - Generates structured call trees with detailed metadata.

### Tracing Process

The tool follows this logical flow.

- **Initialization**
   - Sets up configuration, logging, and path utilities.
   - Configures search paths for module resolution.
   - Initializes caching mechanisms for parsed ASTs.
   - Sets up tracking for visited files and functions.

- **Entry Point Resolution**
   - Parses the source file into an AST.
   - Locates the specified entry point function or method.
   - Handles both standalone functions and class methods.
   - Creates the root node of the call tree.

- **Recursive Call Tracing**
   - Extracts all function calls from each function body.
   - Resolves each call to its definition across files.
   - Handles various call types (direct, self, attribute, imported).
   - Builds nested call trees with comprehensive metadata.

- **Output Generation**
   - Applies configurable filtering to remove unwanted nodes.
   - Eliminates duplicate sibling nodes in the call tree.
   - Generates unique IDs for each node using MD5 hashing.
   - Renders output using pluggable renderer system.

### Call Resolution Types

The tracer handles multiple types of function calls.

- **Direct Calls**:  Simple function calls within the same scope
- **Self Method Calls**:  Class method calls using `self.method()`
- **Attribute Calls**:  Method calls on class attributes (`self.attr.method()`)
- **Imported Function Calls**:  Calls to functions from imported modules
- **Module Function Calls**:  Calls using module.function syntax
- **Nested Attribute Calls**:  Complex chained method calls

## Key Features

- **Cross-File Analysis**: Traces function calls across multiple Python files within specified search paths
- **Class Attribute Analysis**: Analyzes class `__init__` methods to determine attribute types for accurate method resolution
- **Import Resolution**: Handles both absolute and relative imports to resolve external function calls
- **Circular Reference Prevention**: Tracks visited functions and files to prevent infinite recursion
- **Configurable Filtering**: Optional filtering of built-in functions and leaf nodes to focus on relevant code paths
- **Duplicate Elimination**: Removes duplicate sibling nodes while preserving tree structure
- **AST Caching**: Caches parsed ASTs for improved performance when analyzing large codebases
- **Comprehensive Metadata**: Includes file paths, line numbers, qualified names, and call types in output
- **Flexible Rendering**: Pluggable renderer system for customized output formats
- **Built-in Function Detection**: Identifies and optionally filters Python built-in functions
- **Comprehensive Logging**: Multi-level logging (TRACE, DEBUG, INFO, etc.) with structured output.

## Technical Details

- **AST Analysis**:
   - Uses Python's `ast` module for parsing source code
   - Implements custom AST visitors for extracting function calls
   - Handles complex AST node types (Call, Attribute, Name, etc.)
   - Supports both function definitions and class method definitions

- **Module Resolution**:
   - Searches specified paths for imported modules
   - Handles both `.py` files and package directories with `__init__.py`
   - Supports relative imports with proper path resolution
   - Maintains a global class-to-file mapping for efficient lookups

- **Call Resolution Logic**:
   - **Self Method Calls**: Resolves `self.method()` within the same class
   - **Attribute Method Calls**: Uses class attribute analysis to resolve `self.attr.method()`
   - **Direct Function Calls**: Searches current file first, then imported modules
   - **Module Function Calls**: Resolves `module.function()` using import mappings

- **Filtering and Optimization**:
   - Configurable filtering of built-in functions and leaf nodes
   - Duplicate sibling elimination based on function signatures
   - Visited function tracking to prevent redundant analysis
   - Optional node filtering to reduce output complexity

- **Data Structures**:
   - **Module Cache**: Stores parsed ASTs to avoid re-parsing files
   - **Import Map**: Maps imported names to their module paths
   - **Class Attribute Map**: Maps class attributes to their types
   - **Class File Map**: Maps class names to their file locations
   - **Visited Sets**: Track processed files and functions

- **Error Handling**:
   - Graceful handling of unparseable files
   - Comprehensive logging of resolution failures
   - Fallback strategies for unresolved function calls
   - Detailed error reporting with context information

## Configuration

Configuration for the Source Analyzer is stored in `config.yaml` in the `src/source_analyzer` directory. The configuration consists of the following sections.


The Call Tracer supports several configuration options:

- **enable_node_filtering**: Boolean flag to enable/disable filtering of built-in functions and leaf nodes
- **Renderer Configuration**: Specifies the output renderer module and class for formatting results
- **Search Paths**: List of directories to search for imported modules
- **Logging Levels**: Configurable logging verbosity for debugging and monitoring

## Submodules

| Module    | Purpose                                | Documentation                    |
| --------- | -------------------------------------- | -------------------------------- |
| Renderers | Flexible rendering of call tree output | [renderers](renderers/README.md) |

## Usage Patterns

- **Single Function Tracing**: Trace calls starting from a standalone function
- **Method Tracing**: Trace calls starting from a class method using `ClassName.method_name` syntax
- **Cross-Module Analysis**: Analyze function calls that span multiple files and packages
- **Filtered Analysis**: Use node filtering to focus on application code while excluding built-ins
- **Batch Analysis**: Process multiple entry points or files for comprehensive code analysis

## Output Structure

The call tracer generates structured output with the following node properties:

- **name**: Function or method name
- **type**: Call type (entry_point, direct, self, attribute, etc.)
- **file_path**: Absolute path to the file containing the function
- **qualified_name**: Fully qualified name including class/module context
- **lineno**: Line number where the call occurs
- **col_offset**: Column offset of the call
- **calls**: Nested array of child function calls
- **found**: Boolean indicating if the function definition was located
- **id**: Unique MD5 hash identifier for the node
