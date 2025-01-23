import sys
import json
import logging
import boto3
from botocore.exceptions import ClientError
from pprint import pformat

def streaming_body_to_string(streaming_body):
    # try:
    #     # Read the content of the StreamingBody object
    #     byte_content = streaming_body.read()
    #     # Decode the bytes to a string (assuming UTF-8 encoding)
    #     string_content = byte_content.decode("utf-8")
    #     return string_content
    # except Exception as e:
    #     print(f"An error occurred: {e}")
    #     return None
    logging.debug(f"body class: {type(streaming_body)}")
    byte_content = streaming_body.read()
    logging.debug(f"byte content class: {type(byte_content)}")
    string_content = byte_content.decode("utf-8")
    logging.debug(f"string content type: {type(string_content)}")
    return string_content

def string_to_json(string: str) -> dict:
    return json.loads(string)

def bytes_to_string(byte_value: bytes) -> str:
    # Convert the byte to a string
    string_value = byte_value.decode('utf-8')

    # Return the result
    return string_value

def until(condition_func):
    while not condition_func():
        yield

def main():

    # Create a Bedrock client
    bedrock_client = boto3.client('bedrock-runtime', region_name='us-west-2')

    # Define the model ID and inference profile name
    # model_id = "anthropic.claude-3-5-sonnet-20241022-v2:0"
    inference_profile_name = "arn:aws:bedrock:us-west-2:899456967600:inference-profile/us.anthropic.claude-3-5-sonnet-20241022-v2:0"  # Replace with your specific profile name if needed
    input_source_path = "./examples/content.py"
    source_code = []
    line_number = 0
    line = "Initial value"
    logging.debug("source code:")
    with open(input_source_path, "r") as source_file:
        for _ in until(lambda: len(line) == 0):
            line = source_file.readline()
            # if line is None:
            #     break
            if len(line) == 0:
                break
            if line_number > 400:
                break
            source_code.append(line.rstrip('\n'))
            line_number += 1
            logging.debug(f"{line_number:3} ({len(line)}): {line}")
    logging.debug(f"found {line_number} lines")
    logging.debug(f"last line: '{line}' length: {len(line)}")

    # logging.debug("source code:")
    # for line in source_code:
    #     line_number += 1
    #     logging.debug(f"{line_number}%-3s: {line}")
    # logging.debug(f"found {line_number} lines")

    search_instructions = """\
Find all decisions points (if, elif, else). For each decision point, determine the containing method and any called methods."
Lines are terminated with a '\n' character.
Consider decision points with multi-line conditions as one decision point.
Include comment lines when determining the source line number.
"""
    # Input for the model
    user_prompt = f"""\
Perform the following text searches of the following source code:
<source_code>
{source_code}
</source_code>

Search the source code with these search instructions:
<search_instructions>
{search_instructions}
</search_instructions>

For each found item, return the search term, the containing method name, any called method names, the source line number, and the source line.
If there is no containing module (i.e., the containing method is the root level), use the string 'N/A (at module level)' as the containing module name.
Don't include any occurrences if contained in string literals.
When calculating line numbers, include comment lines and blank lines.

Format the output as a valid JSON document without markdown constructs.
Include the source code in the response with line numbers.
"""
#     user_prompt = f"""\
# Consider the following source code, bounded by <source_code></source_code>. Lines are terminated by the '\n' character.
# How many lines are in the source code?
# Add the source code to the output with line numbers.

# <source_code>
# {source_code}
# </source_code>
# """
    user_message =  {"role": "user", "content": user_prompt}
    messages = [user_message]
    logging.debug("messages:")
    logging.debug(pformat(messages))
    # sys.exit(0)

    # Construct the payload
    body = {
        "anthropic_version": "bedrock-2023-05-31",
        "system": "You are an expert in the Python 3 language.",
        "messages": messages,
        "max_tokens": 3000,
        "temperature": 0.0
    }

    try:
        # Call Bedrock's invoke_model with an inference profile
        logging.info("Invoke the model.")
        response = bedrock_client.invoke_model(
            modelId=inference_profile_name,
            body=json.dumps(body),
            contentType="application/json",
        )

        # Parse the response
        logging.info("Parse the response.")
        # logging.debug("body type:")
        # logging.debug(type(response["body"]))
        # logging.debug("body:")
        # logging.debug(response["body"])
        # response = json.loads(response["body"])
        # logging.info("Model Output:")
        # logging.info(json.dumps(response, indent=4))

        output_message = streaming_body_to_string(response.get("body"))
        # print(f"output message: {output_message}")
        output_message_dict = string_to_json(output_message)
        logging.debug(pformat(output_message_dict))

        logging.debug("messages:")
        for message in output_message_dict.get("content"):
            logging.info(message.get("text", ""))

    except ClientError as err:
        message=err.response["Error"]["Message"]
        logging.error("A client error occurred: %s", message)
    except Exception as e:
        logging.error(f"An error occurred: {e}")

if __name__ == "__main__":
    logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)-8s - %(message)s", level=logging.DEBUG)
    logging.getLogger("boto3").setLevel(logging.CRITICAL)
    logging.getLogger("botocore").setLevel(logging.CRITICAL)
    logging.getLogger("urllib3").setLevel(logging.CRITICAL)
    logging.getLogger("requests").setLevel(logging.CRITICAL)

    main()
