import sys
import os
import json
import logging
import openai

logging.basicConfig(format="%(levelname)s:%(message)s", level=logging.CRITICAL)
logging.getLogger("boto3").setLevel(logging.CRITICAL)
logging.getLogger("botocore").setLevel(logging.CRITICAL)
logging.getLogger("urllib3").setLevel(logging.CRITICAL)
logging.getLogger("requests").setLevel(logging.CRITICAL)


def get_file_extension(file_path):
    _, ext = os.path.splitext(file_path)
    return ext.lower()


def what_language(file_type: str) -> str:
    file_type_language_mapping = {".py": "python 3", ".js": "node"}
    return file_type_language_mapping.get(file_type, None)


def load_language_search_config(language: str) -> dict:
    file_path = "".join(language.split()) + "-search-config.json"
    with open(file_path, "r", encoding="utf-8") as file:
        data = json.load(file)

    return data


def format_search_instructions(language_config: dict):
    formatted_search_instructions = []
    prompt_clarifications = language_config.get("prompt_clarifications", [])
    if len(prompt_clarifications) > 0:
        formatted_search_instructions.append("\n".join(prompt_clarifications))
    prompt_locators = language_config.get("prompt_locators")
    for locator in prompt_locators:
        statements = ",".join(locator.get("statements"))
        rank = locator.get("rank")
        category = locator.get("category")
        line1 = f"Locate lines containing one of the following values: {statements}."
        # line1 += "\n".join(prompt_clarifications)
        line2 = (
            f"Give each line a level value of {rank} and a category of '{category}'."
        )
        formatted_search_instructions.append(line1)
        formatted_search_instructions.append(line2)

    logging.debug("formatted_search_instructions:")
    logging.debug(formatted_search_instructions)
    return "\n".join(formatted_search_instructions)




def get_source_language(source_path: str) -> str:
    source_file_type = get_file_extension(source_path)
    source_language = what_language(source_file_type)
    if not source_language:
        logging.warning(f"File type '{source_file_type}' is not yet supported.")
        return None

    return source_language


# TODO replace with loop to find files in directory or file name from args
input_source_path = "content.py"
input_source_language = get_source_language(input_source_path)

search_config = load_language_search_config(language=input_source_language)
search_instructions = format_search_instructions(language_config=search_config)

content = f"""\
Perform the following text searches of the included source code.
Treat the included source code as a line-based text file.

{search_instructions}

To obtain the source line number, reconstruct the input document as line-based text.
For each found item, return the search term, the category, the level, the source line number,
and the source line.
Don't include any occurrences if contained in string literals.

Format the output as a valid JSON document without markdown constructs.
"""
logging.debug("content:")
logging.debug(content)

# TODO replace with config
llm_model = "gpt-4o-mini"
client = openai.OpenAI()
with open(input_source_path, "rb") as source_file:
    client_file = client.files.create(file=source_file, purpose="assistants")

assistant_instructions = """\
You are an expert in all known programming languages. You analyze source code, understand code
structure, and have vast experience in code tracing.
The user is an automation app, so no additional explanation, summaries, or formatting is required.
"""

thread = client.beta.threads.create()

assistant = client.beta.assistants.create(
    name="Code Tracing Expert",
    # instructions=assistant_instructions,
    model=llm_model,
    tools=[{"type": "code_interpreter"}],
    tool_resources={"code_interpreter": {"file_ids": [client_file.id]}},
)

message = client.beta.threads.messages.create(
    thread_id=thread.id, role="user", content=content
)

run = client.beta.threads.runs.create_and_poll(
    thread_id=thread.id, assistant_id=assistant.id, instructions=assistant_instructions
)

logging.debug(f"Thread terminated with status '{run.status}'")
if run.status == "completed":
    run_steps = client.beta.threads.runs.steps.list(thread_id=thread.id, run_id=run.id)
    logging.debug("run steps:")
    logging.debug(run_steps)

    messages = client.beta.threads.messages.list(thread_id=thread.id)
    logging.debug(f"messages.data len: {len(messages.data)}")
    logging.debug(f"messages.data[0].content len: {len(messages.data[0].content)}")
    if len(messages.data) < 2:
        # TODO handle this condition better
        logging.debug("Nothing found")
        sys.exit(0)

    response = messages.data[0].content[0].text.value
    logging.debug("response:")
    logging.debug(response)

    # TODO replace with write to file
    print(response)

    for data in messages.data:
        logging.debug("item:")
        logging.debug(data)
        logging.debug(f"class: {data.content.__class__}")
        for content in data.content:
            logging.debug("content:")
            logging.debug(content.text.value)
else:
    logging.error(f"Thread terminated with status '{run.status}'")
