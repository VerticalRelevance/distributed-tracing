# distributed-tracing
Initial work toward building application distributed tracing knowledge  
  

## Notes
 - This repo is currently developed with Python 3.13.1.
 - Currently the input file used for processing is content.py. In the future files will be read from a local repostiory whose location is passed into via the command line.

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

