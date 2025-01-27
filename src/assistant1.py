import sys
import os
import json
import logging
import openai
from pprint import pprint

# logging.basicConfig(format="%(levelname)s:%(message)s", level=logging.DEBUG)
logging.basicConfig(level=logging.DEBUG)
logging.getLogger("boto3").setLevel(logging.CRITICAL)
logging.getLogger("botocore").setLevel(logging.CRITICAL)
logging.getLogger("urllib3").setLevel(logging.CRITICAL)
logging.getLogger("httpcore").setLevel(logging.CRITICAL)
logging.getLogger("httpx").setLevel(logging.CRITICAL)


class SourceLocationTraceAnalyzer:

    @staticmethod
    def get_file_extension(file_path):
        _, ext = os.path.splitext(file_path)
        return ext.lower()

    @staticmethod
    def what_language(file_type: str) -> str:
        file_type_language_mapping = {".py": "python 3", ".js": "node"}
        return file_type_language_mapping.get(file_type, None)

    @staticmethod
    def load_language_search_config(language: str) -> dict:
        file_path = "".join(language.split()) + "-search-config2.json"
        with open(file_path, "r", encoding="utf-8") as file:
            config_data = json.load(file)

        return config_data

    @staticmethod
    def format_search_instructions(language_config: dict):
        formatted_search_instructions = []

        prompt_override = language_config.get("prompt_override", [])
        if len(prompt_override) > 0:
            formatted_search_instructions = prompt_override[:]
        else:
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
                line2 = f"Give each line a level value of {rank} and a category of '{category}'."
                formatted_search_instructions.append(line1)
                formatted_search_instructions.append(line2)

        logging.debug("formatted_search_instructions:")
        logging.debug(formatted_search_instructions)
        return "\n".join(formatted_search_instructions)

    @staticmethod
    def get_source_language(source_path: str) -> str:
        source_file_type = SourceLocationTraceAnalyzer.get_file_extension(source_path)
        source_language = SourceLocationTraceAnalyzer.what_language(source_file_type)
        if not source_language:
            logging.warning(f"File type '{source_file_type}' is not yet supported.")
            return None

        return source_language

    @staticmethod
    def run(input_source_path: str):
        input_source_language = SourceLocationTraceAnalyzer.get_source_language(
            input_source_path
        )

        search_config = SourceLocationTraceAnalyzer.load_language_search_config(
            language=input_source_language
        )
        search_instructions = SourceLocationTraceAnalyzer.format_search_instructions(
            language_config=search_config
        )

        #         content = f"""\
        # Perform the following text searches of the included source code.
        # Treat the included source code as a line-based text file.

        # {search_instructions}

        # To obtain the source line number, reconstruct the input document as line-based text.
        # For each found item, return the search term, the category, the level, the source line number,
        # and the source line.
        # Don't include any occurrences if contained in string literals.

        # Format the output as a valid JSON document without markdown constructs.
        # """
        logging.debug("search_instructions:")
        logging.debug(search_instructions)

        # TODO replace with config
        llm_model = "gpt-4o-mini"
        # llm_model = "gpt-3.5-turbo-0125"
        client = openai.OpenAI()
        with open(input_source_path, "rb") as source_file:
            client_file = client.files.create(file=source_file, purpose="assistants")

        assistant_instructions = f"""\
You are an AI assistant specialized in analyzing Python functions and have vast experience in code tracing.
You have a code interpreter available to you as you analyze {input_source_language} source files.

The user is automation, so no additional explanation, summaries, or formatting is required.
"""
        assistant = client.beta.assistants.create(
            name="Code Tracing Expert",
            model=llm_model,
            tools=[{"type": "code_interpreter"}],
            tool_resources={"code_interpreter": {"file_ids": [client_file.id]}},
        )
        thread = client.beta.threads.create()
        _ = client.beta.threads.messages.create(
            thread_id=thread.id, role="user", content=search_instructions
        )

        run1 = client.beta.threads.runs.create_and_poll(
            thread_id=thread.id,
            assistant_id=assistant.id,
            instructions=assistant_instructions,
        )

        logging.debug("Usage:")
        logging.debug(run1.usage)
        logging.debug(f"Run terminated with status '{run1.status}'")
        if run1.status == "completed":
            run1_steps = client.beta.threads.runs.steps.list(
                thread_id=thread.id, run_id=run1.id
            )
            logging.debug("run steps:")
            logging.debug(run1_steps)

            messages = client.beta.threads.messages.list(thread_id=thread.id)
            logging.debug(f"messages.data len: {len(messages.data)}")
            logging.debug(
                f"messages.data[0].content len: {len(messages.data[0].content)}"
            )
            logging.debug(
                f"logger effective level: {logging.getLogger().getEffectiveLevel()}"
            )
            for data in messages.data:
                logging.debug("item:")
                logging.debug(data)
                logging.debug(f"class: {data.content.__class__}")
                for content in data.content:
                    logging.debug("content:")
                    logging.debug(content.text.value)

            if len(messages.data) < 2:
                # TODO handle this condition better
                response = '{"response": "No data"}'
                logging.debug("No content")
                pprint(response)
                return response

            if len(messages.data[0].content) > 0:
                response = messages.data[0].content[0].text.value
                logging.debug("response:")
                logging.debug(response)
            else:
                response = '{"response": "No content"}'
                logging.debug("No content")

            return response
        else:
            response = f"Thread error: thread terminated with status '{run1.status}'"
            logging.error(f"Thread terminated with status '{run1.status}'")
            return response

        # _ = client.beta.threads.messages.create(
        #     thread_id=thread.id, role="user", content=content2
        # )
        # run2 = client.beta.threads.runs.create_and_poll(
        #     thread_id=thread.id,
        #     assistant_id=assistant.id,
        #     instructions=assistant_instructions,
        # )
        # logging.debug(f"Thread terminated with status '{run1.status}'")
        # if run1.status == "completed":
        #     run1_steps = client.beta.threads.runs.steps.list(
        #         thread_id=thread.id, run_id=run1.id
        #     )
        #     logging.debug("run steps:")
        #     logging.debug(run1_steps)

        #     messages = client.beta.threads.messages.list(thread_id=thread.id)
        #     logging.debug(f"messages.data len: {len(messages.data)}")
        #     logging.debug(
        #         f"messages.data[0].content len: {len(messages.data[0].content)}"
        #     )
        #     logging.debug(
        #         f"logger effective level: {logging.getLogger().getEffectiveLevel()}"
        #     )
        #     for data in messages.data:
        #         logging.debug("item:")
        #         logging.debug(data)
        #         logging.debug(f"class: {data.content.__class__}")
        #         for content in data.content:
        #             logging.debug("content:")
        #             logging.debug(content.text.value)

        #     if len(messages.data) < 2:
        #         # TODO handle this condition better
        #         logging.debug("Nothing found")
        #         sys.exit(0)

        #     if len(messages.data.content) > 0:
        #         response = messages.data[0].content[0].text.value
        #         logging.debug("response:")
        #         logging.debug(response)
        #     else:
        #         response = '{"response": "No content"}'
        #         logging.debug("No content")

        #     pprint(response)
        #     return None
        # else:
        #     logging.error(f"Thread terminated with status '{run.status}'")


# Main loop to process file(s)
if __name__ == "__main__":
    source_path = "/Users/scaswell/VerticalRelevance/Projects/Internal/Trace-Injection/distributed-tracing/src/examples/content.py"
    response = SourceLocationTraceAnalyzer.run(input_source_path=source_path)
    # print(json.dumps(response))
    print(response)
