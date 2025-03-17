# Distributed Tracing: Trace Injection Advisor
Trace Injection Advisor is an AI-powered solution that provides advice regarding trace injection based on a single file or a local repository.

## Project Structure
1. Python Source Code: `src/`
   1. Package: `source_analyzer/`
   2. Package: `call_tracer/`
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
### General Setup
1. Clone the distributed tracing repository:
```bash
git clone https://github.com/VerticalRelevance/distributed-tracing
```
1. Set up the development environment:
   * Set up a Python virtual environment
   * From the repository root, install requirements:
```bash
pip install -U -r requirements.txt
pip install -U -r requirements-dev.txt
```
1. Clone a remote repository to be analyzed to a local disk location outside the distributed tracing local repository.
2. Change to the `src` directory in the `distributed-tracing` repository root:
```bash
cd /path/to/root/distributed-tracing/src
```

### Running Call Tracer
1. Set the `PYTHONPATH` environment variable:
```bash
export PYTHONPATH=common:.:call_tracer
```
2. Run the call tracer:
```bash
python call_tracer/main.py (path to file or local repository) > (some location).md 2> (some location).err
```

### Running Source Analyzer
1. Set the `PYTHONPATH` environment variable:
```bash
export PYTHONPATH=common:.:source_analyzer
```
2. Set up configuration file (see [source_analyzer_configuration](#source-analyzer-configuration))
3. Create any model-specific environment variables.
* For example, for an OpenAI model:
```bash
export OPENAI_API_KEY="sk-proj-xyzzy..."
```
* For a model accessed via AWS Bedrock, set up AWS credentials.
4. Run the source analyzer:
```bash
python source_analyzer/main.py (path to file or local repository) > (some location).md 2> (some location).err
```

## Package Details
For more information on each package, refer to the following:
 
| Package         | Documentation                            |
| --------------- | ---------------------------------------- |
| Call Tracer     | [Package](src/call_tracer/README.md)     |
| Source Analyzer | [Package](src/source_analyzer/README.md) |

## General Project Topics

### Project Spelling Words
Some IDEs, such as Visual Studio Code, contain core or plug-in functionality to mark or otherwise
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
TODO add unit and integration tests
TODO update docstrings


## Source Analyzer remaining
TODO see TODO and FUTURE tags in the code  
TODO swap out Python logging for a modern logger  
TODO add unit and integration tests  
TODO standardize some of the repetitive code  
TODO OpenAI model  
TODO update docstrings
