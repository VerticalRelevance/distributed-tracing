# Source Code Analyzer Logic Explanation

## Overview

This Python code implements a source code analyzer tool designed to analyze Python code and identify optimal locations for adding trace statements. The goal of the tool is to ease the pain of code instrumentation by identifying the optimal points in Python code to add tracing or logging statements based on intelligent analysis of code structure and flow.


## Main Components and Logic Flow

### 1. Core Classes

- **SourceCodeNode**: Represents a node in the source code tree (module, class, function, etc.) with attributes for name, type, source location, and children.

- **SourceCodeTreeBuilder**: An AST (Abstract Syntax Tree) visitor that builds a hierarchical tree representation of Python source code. It traverses the AST and creates nodes for:
  - Imports
  - Classes
  - Functions

- **SourceCodeAnalyzer**: The main analysis class that:
  - Parses source code
  - Builds the source tree
  - Uses AI models to analyze the code and identify critical locations for trace statements

### 2. Analysis Process

The tool follows this logical flow:

1. **Initialization**: Sets up utilities, configuration, a model (AI/LLM), and a formatter

2. **Source Code Parsing**: Uses Python's [ast](https://docs.python.org/3/library/ast.html) module to parse source code into an Abstract Syntax Tree (AST)

3. **Tree Building**: Walks through the AST to build a hierarchical representation that shows the structure of:
   - Import statements
   - Class definitions
   - Function/method definitions

4. **AI-Powered Analysis**: Uses an AI model to analyze the code and identify optimal trace statement locations based on configured priorities

5. **Output Formatting**: Formats the AI's recommendations into a structured output

### 3. Key Features

- **Tree Representation**: Builds a visual tree representation of the code structure
- **Prioritized Analysis**: Uses configurable priorities to identify critical trace points
- **Robust Error Handling**: Implements retry logic for AI model calls
- **Detailed Logging**: Comprehensive logging at various levels (TRACE, DEBUG, INFO, etc.)

### 4. Command-Line Interface

The tool can be invoked to analyze:
- A single Python file: `python main.py file.py`
- A directory of Python files: `python main.py directory/`

### 5. Environment

The following environment variables are used for run-time configuration of the tool:

| Name | Purpose | Default |
| ---- | ------- | ------- |
| TODO |         |         |

## Technical Details

1. **AST Traversal**: The tool uses Python's built-in `ast` module to parse code and the visitor pattern to traverse the tree.

2. **AI Integration**: The tool sends prompts to an AI model asking it to identify critical locations for trace statements based on specified priorities.

3. **Retry Mechanism**: Implements robust retry logic to handle API failures when communicating with the AI model.

4. **Formatting**: The AI's output is formatted according to configured templates.

5. **Configuration**: Uses YAML-based configuration to control analysis priorities, model settings, and other parameters.


## Submodules

| Module     | Purpose                                         | Documentation                      |
| ---------- | ----------------------------------------------- | ---------------------------------- |
| Formatters | Flexible formatting of model output             | [formatters](formatters/README.md) |
| Models     | Flexible choice of model from several available | [models](models/README.md)         |
