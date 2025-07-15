# Distributed Tracing: Trace Injection Advisor
Trace Injection Advisor is an AI-powered solution that provides advice regarding trace injection based on a single file or a local repository.

## Project Structure
1. Python Source Code: `src/`
   1. Package: `call_tracer/`
   2. Package: `common/`
   3. Package: `source_analyzer/`
2. Python Test Code: `tests/`
   1. Unit Test Code: `unit/`
      1. Package: `source_analyzer/`
      2. Package: `call_tracer/`
   2. Integration Test Code: `integration/`
      1. Package: `source_analyzer/`
      2. Package: `call_tracer/`

## Python Version
 - All Python code in this repository has been developed and tested with Python 3.13.1.

## Getting Started

### Logging
Logging is performed by the `loguru` package via an interface class `common/logging_utils.py`.
The following environment variables are used to configure the logger.

| Name                 | Required | Default  | Description                                              |
| -------------------- | -------- | -------- | -------------------------------------------------------- |
| LOG_FILE_NAME        | Yes      | N/A      | Path to a file where the log should be written           |
| LOG_FILE_COMPRESSION | No       | "zip"    | The log file compression format                          |
| LOG_FILE_RETENTION   | No       | "7 days" | The amount of time to retain rotated log files           |
| LOG_FILE_ROTATION    | No       | "10 MB"  | The size the log file that triggers rotation of the file |
| LOG_LEVEL            | No       | DEBUG    | sets the Loguru logging level                            |

### General Setup
1. Clone the distributed tracing repository:
```bash
git clone https://github.com/VerticalRelevance/distributed-tracing
```
2. Set up the development environment:
   * Set up a Python virtual environment
   * From the repository root, install requirements:
```bash
pip install -U -r requirements.txt
pip install -U -r requirements-dev.txt
```
3. Clone a remote repository to be analyzed to a local disk location outside the distributed tracing local repository.
4. Change to the `src` directory in the `distributed-tracing` repository root:
```bash
cd /path/to/root/distributed-tracing/src
```

### Running Call Tracer
1. Set the `PYTHONPATH` environment variable.
```bash
export export PYTHONPATH=common:.:call_tracer:call_tracer/renderers:source_analyzer:source_analyzer/models
```
2. Set the `LOG_FILE` environment variable.
```bash
export LOG_FILE="/absolute/path/to/some/location/distributed-tracing/source_analyzer.err"`
```
3. (Optional) Set the `LOG_LEVEL` environment variable. Default is DEBUG.
```bash
export LOG_LEVEL="DEBUG"
```
4. (OPtional) Set other logging environment variables.
5. Run the call tracer.
```bash
python call_tracer/main.py source_file_path entry_point search_paths
```

### Running Source Analyzer Standalone
1. Set the `PYTHONPATH` environment variable.
```bash
export PYTHONPATH=common:.:source_analyzer:source_analyzer/models
```
2. Set up configuration file (see [source_analyzer_configuration](#source-analyzer-configuration)).
3. Create any necessary model-specific environment variables.
* For example, for an OpenAI model:
```bash
export OPENAI_API_KEY="sk-proj-xyzzy..."
```
* For a model accessed via AWS Bedrock, set up AWS credentials.
4. Set the `LOG_FILE` environment variable.
```bash
export LOG_FILE="/absolute/path/to/some/location/distributed-tracing/source_analyzer.err"`
```
5. (Optional) Set the `LOG_LEVEL` environment variable. Default is DEBUG.
``bash
export LOG_LEVEL="DEBUG"
```
6. (Optional) Set other logging environment variables.
7. Run the source analyzer.
```bash
python source_analyzer/main.py file_path or local_repository_path
```

## Package Details
For more information on each package, refer to the following.
 
| Package         | Documentation                            |
| --------------- | ---------------------------------------- |
| Call Tracer     | [Package](src/call_tracer/README.md)     |
| Source Analyzer | [Package](src/source_analyzer/README.md) |

## General Project Topics

### Project Spelling Words
Some IDE's, such as Visual Studio Code, contain core or plug-in functionality to mark or otherwise
detect misspelled words in project files. Sometimes, due to the quirkiness of element naming, there
are words that would otherwise be considered misspelled, that should be considered spelled
correctly.  

This project contains a file in the root directory named [project-words.txt](project-words.txt).
The file contains a list of such words that an IDE can use as a dictionary of valid words.

To configure the Visual Studio Code `cSpell` plug-in to use this file as a custom dictionary, 
add the following to the workspace or folder configuration:

```json
{
  "settings": {
    "cSpell.customDictionaries": {
      "project-words": {
        "name": "project-words",
        "path": "${workspaceRoot}/project-words.txt",
        "description": "Words used in this project",
        "addWords": true
      },
      "custom": true, // Enable the `custom` dictionary
      "internal-terms": false // Disable the `internal-terms` dictionary
    }
  }
}
```

## Call Tracer remaining

TODO see TODO and FUTURE tags in the code  
TODO add dynamic setting of max tokens to fasthtml renderer
TODO add unit and integration tests

## Source Analyzer remaining

TODO see TODO and FUTURE tags in the code  
TODO add unit and integration tests  
TODO standardize some of the repetitive code  
TODO add OpenAI model  
