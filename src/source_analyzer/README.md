# Source Code Analyzer Logic Explanation

## Overview

This Python code implements a source code analyzer tool designed to analyze Python source files and identify optimal locations for adding trace statements using AI-powered analysis. The tool leverages configurable AI models (such as OpenAI or AWS Bedrock) to intelligently analyze code structure and recommend critical points for instrumentation based on user-defined priorities. It can process individual files or entire directories, providing formatted output with detailed recommendations for trace statement placement.

## Main Components and Logic Flow

### Core Classes

- **SourceCodeAnalyzer**: The main analysis class that orchestrates the entire process:
  - Initializes dependencies (utilities, configuration, AI model, formatter)
  - Manages AI model interactions with retry logic
  - Processes source files and directories
  - Generates formatted output

### Analysis Process

The tool follows this logical flow:

- **Initialization**
 - Sets up utilities (GenericUtils, LoggingUtils, PathUtils)
 - Loads configuration from YAML file
 - Initializes AI model and formatter using factory patterns
 - Configures retry and token tracking settings

- **File Processing**
 - Loads Python source file content
 - Validates file exists and is not empty
 - Handles errors gracefully with detailed logging

- **AI-Powered Analysis**
 - Constructs detailed prompts with source code and tracing priorities
 - Sends prompts to configured AI model with retry logic
 - Analyzes responses for optimal trace point locations
 - Tracks token usage and validates stop reasons

- **Output Generation**
 - Processes AI model's JSON response
 - Applies configured formatter to generate structured output
 - Returns formatted recommendations to caller or displays to console

### Directory Processing

- Recursively walks directory structures
- Identifies Python files (.py extension)
- Processes each file individually
- Provides comprehensive logging of the process

## Key Features

- **AI Model Integration**: Flexible support for multiple AI models through factory pattern (OpenAI, AWS Bedrock, etc.)
- **Configurable Analysis Priorities**: User-defined priorities guide the AI's analysis focus.
- **Robust Error Handling**: Comprehensive retry logic with exponential backoff for AI model calls.
- **Token Usage Tracking**: Monitors and reports prompt and completion token consumption.
- **Function-Specific Analysis**: Optional focus on specific functions or methods within source files.
- **Flexible Output Formatting**: Pluggable formatter system for customized output formats.
- **Comprehensive Logging**: Multi-level logging (TRACE, DEBUG, INFO, etc.) with structured output.
- **Batch Processing**: Support for analyzing entire directories recursively.
- **JSON-Structured Output**: AI responses formatted as structured JSON with detailed recommendations.

## Technical Details

- **Configuration Management**: Uses YAML-based configuration with support for.
 - AI model settings (temperature, retry logic, token limits)
 - Tracing priorities and clarifications
 - Formatter and model class selection
 - AWS region configuration for Bedrock models

- **AI Model Abstraction**: 
  - Factory pattern for model selection
  - Standardized interface for different AI providers
  - Automatic retry logic with configurable attempts and delays
  - Token limit detection and handling
  - Stop reason validation

- **Error Handling**:
  - Custom exception hierarchy (ModelException, ModelMaxTokenLimitException)
  - Graceful degradation with informative error messages
  - Comprehensive logging of failures and retries

- **Prompt Engineering**:
  - Dynamic prompt construction based on configuration
  - Support for function-specific analysis
  - Structured JSON response format requirements
  - Integration of user-defined priorities and clarifications

- **Output Processing**:
  - JSON response parsing and validation
  - Metadata injection (model info, token usage, timing)
  - Flexible formatting through pluggable formatter system

- **File System Operations**:
  - Path validation and error handling
  - ASCII file content loading
  - Recursive directory traversal
  - Support for both single file and batch processing modes

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

formatter:
├── class:
│   └── name: the Python class to be used for formatting the analyzer output (required)
├── module:
│   └── name: the Python module containing the class to be used for formatting (required)
└── any additional configuration as defined by the specific formatter class (requirement based on the model)

ai_model:
├── max_llm_tries: the number of times to try calling the AI model in case of error (required)
├── retry_delay: the number of seconds between retries of calling the AI model in case of error (required)
├── temperature: the model temperature, between 0.0 and 1.0, inclusive (required)
├── custom:
│   └── any custom values defined by the specific model
├── class:
│   └── name: the Python class to be used for calling the AI model
├── module:
│   └── name: the Python module containing the specific module class
└── model_stop:
    └── reasons:
        └── valid:
            └── list of valid stop reasons for the model; any other error causes the code to enter into an error state
```
