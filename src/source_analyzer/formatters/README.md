# Python Code Analysis: Formatters Package

## Overview

The Formatters package implements a flexible formatting package using design patterns like Factory and Singleton. The package is designed to convert JSON data into Markdown format with different implementation strategies. The architecture allows for easy addition of new formatters while maintaining a consistent interface for client code.

## Core Components

### 1. `formatter.py` - Base Framework

This module establishes the foundation of the formatting system with three main classes:

#### `FormatterError`
- A custom exception class for handling formatting-related errors
- Extends the standard Python `Exception` class

#### `FormatterObject`
- An abstract base class implementing the Singleton pattern
- Provides core functionality for JSON formatting operations
- Contains utility instances for logging, JSON operations, and generic utilities
- Defines the `format_json()` method that subclasses must implement

#### `FormatterFactory`
- Implements the Factory pattern to dynamically create formatter instances
- Uses reflection to load formatter classes based on module and class names
- Maintains a singleton instance to ensure consistent formatter creation

### 2. `coded_json_to_markdown_formatter.py` - Direct Implementation

This module provides a concrete implementation of the `FormatterObject`:

#### `CodedJsonToMarkdownFormatter`
- Directly implements the formatting logic in code
- Transforms JSON analysis data into structured Markdown reports
- Processes data based on priority levels defined in configuration
- Generates a comprehensive report with sections for:
  - Model information header
  - Analysis summary
  - Priority-based findings
  - Code block analysis
  - Token usage statistics

### 3. `jinja2_json_to_markdown_formatter.py` - Template-Based Implementation

This module offers an alternative implementation using Jinja2 templates:

#### `Jinja2JsonToMarkdownFormatter`
- Uses Jinja2 templating engine to separate formatting logic from code
- Loads templates from configurable file paths
- Renders JSON data through templates to produce Markdown output
- Provides more flexibility for changing output format without code changes

## Key Design Patterns

1. **Singleton Pattern**: Ensures only one instance of each formatter exists
2. **Factory Pattern**: Dynamically creates appropriate formatter instances
3. **Template Method Pattern**: Defines the skeleton of the formatting algorithm in the base class

## Data Flow

1. Client code obtains a formatter from the `FormatterFactory`
2. The factory dynamically loads and instantiates the requested formatter
3. The client calls `format_json()` with data and variables
4. The formatter processes the data according to its implementation
5. Formatted Markdown is returned to the client

## Key Differences Between Implementations

| Feature        | CodedJsonToMarkdownFormatter             | Jinja2JsonToMarkdownFormatter             |
| -------------- | ---------------------------------------- | ----------------------------------------- |
| Logic Location | Embedded in code                         | Separated in templates                    |
| Flexibility    | Requires code changes for format changes | Can modify templates without code changes |
| Dependencies   | None beyond base classes                 | Requires Jinja2 library                   |
| Complexity     | Higher code complexity                   | Simpler code, complexity in templates     |

[<- back to Source Code Analysis](../README.md)