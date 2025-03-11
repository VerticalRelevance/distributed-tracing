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

### Running source_analyzer
1. Set the `PYTHONPATH` environment variable:
```bash
export PYTHONPATH=..:.:source_analyzer
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

### Running call_tracer
1. Set the `PYTHONPATH` environment variable:
```bash
export PYTHONPATH=..:.:call_tracer
```
2. Run the source analyzer:
```bash
python call_tracer/main.py (path to file or local repository) > (some location).md 2> (some location).err
```

## Package: Source Analyzer
### Package Details
* Refer to the [Source Code Analyzer documentation](src/source_analyzer/README.md) for details.

### Source Analyzer: Configuration
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
└── any additional configuration as defined by the specific formatter class (reuqirement based on the model)

ai_model
├── max_llm_retries: the number of times to try calling the AI model in case of error (required)
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

## Source Analyzer remaining
TODO see TODO and FUTURE tags in the code  
TODO swap out Python logging for a modern logger  
TODO add unit and integration tests  
TODO standardize some of the repetitive code  
TODO OpenAI model  

## Call Tracer remaining
TODO change print statements to logging statements  
TODO add unit and integration tests  
