# Distributed Tracing: Trace Injection Advisor
Trace Injection Advisor is an AI-powered solution that provides advice regarding trace injection based on a single file or a local repository.

## Project Structure

## Getting Started
1. Clone the distributed tracing repository:
```bash
git clone https://github.com/VerticalRelevance/distributed-tracing
```
2. Set up the development environment:
   * Set up a Python virtual environment
   * From the repository root, install requirements:
```bash
pip install -U -r requirements-dev.txt
pip install -U -r requirements.txt
```
3. Clone a remote repository to be analyzed to a local disk location outside the distributed tracing local repository.
4. Change to the `src` directory in the `distributed-tracing` repository root:
```bash
cd /path/to/root/distributed-tracing/src
```
5. Set the `PYTHONPATH` environment variable:
```bash
export PYTHONPATH=..:.:source_analyzer
```
6. Run the source analyzer:
```bash
python source_analyzer/source_analyzer.py (path to file or local repository) > (some location).md 2> (some location).err
```




## Notes
 - This repo is currently developed with Python 3.13.1.

## Running
 1. From the repository root, set up required packages:
```bash
pip install -r requirements.txt
```
 2. Change to the source directory
```bash
cd src
```
 3. Create environment variable with your OpenAI API key:
```bash
export OPENAI_API_KEY="sk-proj-xyzzy..."
```
 4. Run Python:
```bash
python assistant.py >assistance.json 2>assistance.err
```

## Other
Other files found in the src directory:
 - analyze_source.py: an attempt to scan the source using embeddings and vectors; does not have the ability to present line numbers
 - analyze_source_text.py: an attempt to scan the source by appending it to the prompt; does not have the ability to present line numbers


## TODO
[ ] see TODO and FUTURE tags in the code
[ ] swap out Python logging for a modern logger
[ ] add unit and integration tests
[ ] standardize some of the repetitive code
