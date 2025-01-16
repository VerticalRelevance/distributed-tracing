# from tabnanny import verbose
# import warnings
import sys
import json
import pprint
from dotenv import load_dotenv, find_dotenv

from langchain import hub
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain.chains.retrieval import create_retrieval_chain
from langchain_community.document_loaders import TextLoader
from langchain_community.vectorstores import FAISS
from langchain_openai import ChatOpenAI
from langchain_openai import OpenAIEmbeddings


def load_language_search_config(language: str) -> dict:
    file_path = "".join(language.split()) + "-search-config.json"
    with open(file_path, "r", encoding="utf-8") as file:
        data = json.load(file)

    return data


def load_document_from_file(input_file: str) -> list:
    # loader = CSVLoader(file_path=csv_file)
    loader = TextLoader(file_path=input_file)
    file_documents = loader.load()
    return file_documents


def format_search_instructions(search_config: dict):
    formatted_search_instructions = []
    for item in search_config:
        # Locate lines containing one of the following values: def, async def, return, yield, await.
        # Give each line a level value of 1 and a category of 'Function Entry/Exit points'
        statements = ",".join(item.get("statements"))
        rank = item.get("rank")
        category = item.get("category")
        line1 = f"Locate lines containing one of the following values: {statements}."
        line2 = (
            f"Give each line a level value of {rank} and a category of '{category}'."
        )
        formatted_search_instructions.append(line1)
        formatted_search_instructions.append(line2)

    return formatted_search_instructions


_ = load_dotenv(find_dotenv())  # read local .env file

# warnings.filterwarnings('ignore')

# account for deprecation of LLM model
# Get the current date
# current_date = datetime.datetime.now().date()

# Define the date after which the model should be set to "gpt-3.5-turbo"
# target_date = datetime.date(2024, 6, 12)

# Set the model variable based on the current date
# if current_date > target_date:
#     llm_model = "gpt-3.5-turbo"
# else:
#     llm_model = "gpt-3.5-turbo-0301"

llm_model = "gpt-4o-mini"
source_language = "python 3"  # TODO get this value as a configuration item

search_config = load_language_search_config(language=source_language)
# pprint.pprint(search_config, stream=sys.stderr)

search_instructions = format_search_instructions(search_config=search_config)
# print()
# print("search instructions:")
# pprint.pprint(search_instructions)

llm = ChatOpenAI(model=llm_model)

# operators = get_language_decision_operators(llm=llm)
# print()
# print("operators list:")
# pprint.pprint(operators)


# Load the source file
documents = load_document_from_file(
    "/Users/scaswell/VerticalRelevance/Projects/SRE/AWS_DataMeshFoundations/src/ops/post_setup.py"
)

# Create embeddings and vector store
embeddings = OpenAIEmbeddings()
vectorstore = FAISS.from_documents(documents, embeddings)

# scan_file_prompt = ChatPromptTemplate.from_template(
instructions = f"""\
Perform the following text searches of the included source code. Treat the included source code as
a line-based text file.

{search_instructions}

To obtain the source line number, reconstruct the input document line-based text.
For each found item, return the search term, the category, the level, the source line number, and the source line.
Don't include any of the following points if contained in string literals.

Format the output as JSON.
"""
# print()
# print("instructions:")
# pprint.pprint(instructions)

# input_context = """\
# You are an expert in all known programming languages.

# Query: {input}

# Response:
# """
retrieval_qa_chat_prompt = hub.pull("langchain-ai/retrieval-qa-chat")
# print()
# print("retrieval qa chat prompt:")
# pprint.pprint(retrieval_qa_chat_prompt)
# retrieval_qa_chat_prompt = PromptTemplate(
#   input_variables=["input"],
#   template=input_context
# )

combine_docs_chain = create_stuff_documents_chain(llm, retrieval_qa_chat_prompt)
retrieval_chain = create_retrieval_chain(
    vectorstore.as_retriever(),
    combine_docs_chain,
)
input_values = {"input": instructions}

print("", file=sys.stderr)
print("call chain.invoke", file=sys.stderr)
response = retrieval_chain.invoke(input_values)

# print()
# print("invoke response:")
# pprint.pprint(response.get('answer'))

answer = response.get("answer")
# try:
#     response_json = json.loads(answer)
#     pprint.pprint(json.dumps(response_json))
# except JSONDecodeError as jde:
#     print("", file=sys.stderr)
#     pprint.pprint(answer)
pprint.pprint(answer)
# response_json_sorted = sorted(response_json, key=lambda x: x["trace_score"])
# print(json.dumps(response_json_sorted))
# response_json.sort(key=lambda x: x["trace_score"])

# overall_chain = SequentialChain(
#     chains=[decision_operators_chain, retrieval_chain],
#     input_variables=["language"],
#     output_variables=["decision_points"],
#     verbose=True
# )

# print(overall_chain("python 3"))

# Step 4: Answer questions in a loop
# def ask_question(question):
#   print(f"question is: {question}")
#   response = retrieval_chain.invoke({"input": question})
#   # pprint.pprint(dir(response))
#   # print(response.get('answer'))
#   return response.get('answer')

# Main loop to interact with the user
# if __name__ == "__main__":
#   question = "Display the results."
#   answer = ask_question(question)
#   print(answer)
