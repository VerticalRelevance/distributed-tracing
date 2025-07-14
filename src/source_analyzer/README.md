# Source Code Analyzer Logic Explanation

## TODO refactor with Call Tracer README

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


## Configuration
Configuration for the Source Analyzer is stored in `config.yaml` in the `src/source_analyzer` directory. The configuration consists of the following sections:

```
aws
└── region: The AWS region for use with Bedrock models (required if a Bedrock model is configured below)

tracing_priorities:
├── List of tracing priorities. The AI model will be asked to look for these priorities in list order. (required)

clarifications:
├── List of additional clarifications given to the model prompt. These are placed into the prompt in the order listed. (optional)

formatter
├── class
│   └── name: the Python class to be used for formatting the analyzer output (required)
├── module
│   └── name: the Python module containing the class to be used for formatting (required)
└── any additional configuration as defined by the specific formatter class (requirement based on the model)

ai_model
├── max_llm_tries: the number of times to try calling the AI model in case of error (required)
├── retry_delay: the number of seconds between retries of calling the AI model in case of error (required)
├── temperature: the model temperature, between 0.0 and 1.0, inclusive (required)
├── custom
│   └── any custom values defined by the specific model
├── class
│   └── name: the Python class to be used for calling the AI model
├── module
│   └── name: the Python module containing the specific module class
└── model_stop
    └── reasons
        └── valid
            └── list of valid stop reasons for the model; any other error causes the code to enter into an error state
```
